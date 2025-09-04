
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 *
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */

#ifndef GENUA_SVD_H
#define GENUA_SVD_H

#include "defines.h"
#include "xcept.h"

#ifndef HAVE_NO_LAPACK
#include "lapack_interface.h"
#else
#include <eeigen/SVD>
#endif

#include <vector>
#include <sstream>
#include <algorithm>

template <class MatrixType, class VectorType>
int svd_inplace(MatrixType &a, MatrixType &u, VectorType &s, MatrixType &vt)
{
#ifndef HAVE_NO_LAPACK

  // dimensions
  lapack::lpint m, n, k, info;
  m = a.nrows();
  n = a.ncols();
  k = std::min(m, n);

  assert(u.nrows() == m);
  assert(u.ncols() == k);
  assert(vt.nrows() == k);
  assert(vt.ncols() == n);
  assert(s.size() == k);

  // workspace query
  std::vector<int> iwork(8 * k);
  std::vector<typename MatrixType::value_type> work(1);
  lapack::gesdd('S', m, n, a.pointer(), m, s.pointer(),
                u.pointer(), u.nrows(), vt.pointer(), vt.nrows(),
                &(work[0]), -1, &(iwork[0]), info);

  // allocate workspace
  uint lw = uint(work[0]);
  work.resize(lw);

  // compute SVD decomposition
  lapack::gesdd('S', m, n, a.pointer(), m, s.pointer(),
                u.pointer(), u.nrows(), vt.pointer(), vt.nrows(),
                &(work[0]), work.size(), &(iwork[0]), info);

  return info;

#else

  typedef typename MatrixType::value_type value_type;
  typedef eeigen::Matrix<value_type, eeigen::Dynamic, eeigen::Dynamic> EMatrix;
  typedef eeigen::Map<EMatrix> EMView;

  EMView amap(a.pointer(), a.nrows(), a.ncols());
  eeigen::JacobiSVD<EMatrix> solver(amap,
                                    eeigen::ComputeThinU | eeigen::ComputeThinV);

  u = MatrixType(solver.matrixU());
  vt = MatrixType(solver.matrixV().transpose());
  s = VectorType(solver.singularValues());

  return 0;

#endif
}

template <class MatrixType, class VectorType>
void svd(const MatrixType &a, MatrixType &u, VectorType &s, MatrixType &vt)
{
  MatrixType at(a);
  size_t m, n, k;
  m = a.nrows();
  n = a.ncols();
  k = std::min(m, n);
  u.resize(m, k);
  vt.resize(k, n);
  s.resize(k);
  int status = svd_inplace(at, u, s, vt);
  if (status != 0)
  {
    std::stringstream ss;
    ss << "SVD decomposition failed in Lapack.\n";
    ss << "Error code: " << status << "\n";
    throw Error(ss.str());
  }
}

// Solve least-squares problem using SVD
template <class MatrixType>
int svd_solve(MatrixType &a, MatrixType &x, double rcond = -1.0)
{
#ifndef HAVE_NO_LAPACK

  typedef typename MatrixType::value_type ElmType;
  typedef std::vector<ElmType> WorkArray;
  assert(a.nrows() == x.nrows());

  lapack::lpint info(0), lwork(-1), rank;
  lapack::lpint m = a.nrows();
  lapack::lpint n = a.ncols();
  lapack::lpint nrhs = x.ncols();
  lapack::lpint p = std::min(m, n);
  lapack::lpint lda(a.ldim()), ldb(x.ldim());
  lapack::lpint nlvl = std::max(1, int(1 + std::log2(double(p) / 16.0)));
  lapack::lpint liwork = p * (3 * nlvl + 11);
  WorkArray work(1), rhs(x.size()), s(p);
  std::vector<int> iwork(liwork);
  std::copy(x.begin(), x.end(), rhs.begin());

  // first: workspace query
  lapack::gelsd(m, n, nrhs, a.pointer(), lda, &(rhs[0]), ldb,
                &(s[0]), rcond, rank, &(work[0]), lwork, &(iwork[0]), info);

  if (info != 0)
    return info;

  lwork = static_cast<lapack::lpint>(fabs(work[0]));
  work.resize(lwork);

  // solve
  lapack::gelsd(m, n, nrhs, a.pointer(), lda, &(rhs[0]), ldb,
                &(s[0]), rcond, rank, &(work[0]), lwork, &(iwork[0]), info);

  // copy result into x
  x.resize(n, nrhs);
  for (int j = 0; j < nrhs; ++j)
    for (int i = 0; i < n; ++i)
      x(i, j) = rhs[i + j * m];
  return info;

#else

  typedef typename MatrixType::value_type value_type;
  typedef eeigen::Matrix<value_type, eeigen::Dynamic, eeigen::Dynamic> EMatrix;
  typedef eeigen::Map<EMatrix> EMView;

  EMView amap(a.pointer(), a.nrows(), a.ncols());
  eeigen::JacobiSVD<EMatrix> solver(amap,
                                    eeigen::ComputeThinU | eeigen::ComputeThinV);
  if (rcond >= 0.0)
    solver.setThreshold(rcond);

  EMView xmap(x.pointer(), x.nrows(), x.ncols());
  EMatrix y = solver.solve(xmap);
  x.resize(y.rows(), y.cols());
  memcpy(x.pointer(), y.data(), x.size() * sizeof(value_type));

  return 0;

#endif
}

// Solve least-squares problem using SVD
template <class MatrixType, class VectorType>
int svd_solve(MatrixType &a, VectorType &x, double rcond = -1.0)
{
#ifndef HAVE_NO_LAPACK
  typedef typename MatrixType::value_type ElmType;
  typedef std::vector<ElmType> WorkArray;
  assert(a.nrows() == x.size());

  lapack::lpint info(0), lwork(-1), rank;
  lapack::lpint m = a.nrows();
  lapack::lpint n = a.ncols();
  lapack::lpint nrhs = 1;
  lapack::lpint p = std::min(m, n);
  lapack::lpint lda(a.ldim()), ldb(x.size());
  lapack::lpint nlvl = std::max(1, int(1 + std::log2(double(p) / 16.0)));
  lapack::lpint liwork = p * (3 * nlvl + 11);
  WorkArray work(1), rhs(x.size()), s(p);
  std::vector<int> iwork(liwork);
  std::copy(x.begin(), x.end(), rhs.begin());

  // first: workspace query
  lapack::gelsd(m, n, nrhs, a.pointer(), lda, &(rhs[0]), ldb,
                &(s[0]), rcond, rank, &(work[0]), lwork, &(iwork[0]), info);

  if (info != 0)
    return info;

  lwork = static_cast<lapack::lpint>(fabs(work[0]));
  work.resize(lwork);

  // solve
  lapack::gelsd(m, n, nrhs, a.pointer(), lda, &(rhs[0]), ldb,
                &(s[0]), rcond, rank, &(work[0]), lwork, &(iwork[0]), info);

  // copy result into x
  x.resize(n);
  for (int i = 0; i < n; ++i)
    x[i] = rhs[i];
  return info;

#else

  typedef typename MatrixType::value_type value_type;
  typedef eeigen::Matrix<value_type, eeigen::Dynamic, eeigen::Dynamic> EMatrix;
  typedef eeigen::Map<EMatrix> EMView;

  EMView amap(a.pointer(), a.nrows(), a.ncols());
  eeigen::JacobiSVD<EMatrix> solver(amap,
                                    eeigen::ComputeThinU | eeigen::ComputeThinV);
  if (rcond >= 0.0)
    solver.setThreshold(rcond);

  EMView xmap(x.pointer(), x.size(), 1);
  EMatrix y = solver.solve(xmap);
  x.resize(y.rows());
  memcpy(x.pointer(), y.data(), x.size() * sizeof(value_type));

  return 0;

#endif
}

#endif
