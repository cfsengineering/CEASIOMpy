
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

#ifndef GENUA_LLS_H
#define GENUA_LLS_H

#include "defines.h"
#include "xcept.h"

#ifndef HAVE_NO_LAPACK
#include "lapack_interface.h"
#else
#include <eeigen/QR>
#endif

#include <sstream>
#include <vector>

/** Solve least-squares problem using QR.
 *
 * Calls LAPACK routine ?GELS to solve the least-squares problem
 * \f[
 *  \min || A x - b ||
 * \f]
 * where b is overwritten with the solution x on return.
 *
 * \ingroup numerics
 * \sa svd_solve
 */
template <class MatrixType>
int lls_solve(MatrixType &a, MatrixType &x)
{
#ifndef HAVE_NO_LAPACK
  typedef std::vector<typename MatrixType::value_type> WorkArray;
  assert(a.nrows() == x.nrows());

  int lda(a.ldim()), ldb(x.ldim());
  int m, n, nrhs, info(0), lwork(-1);
  m = a.nrows();
  n = a.ncols();
  nrhs = x.ncols();
  WorkArray work(1), rhs(x.size());
  std::copy(x.begin(), x.end(), rhs.begin());

  // first: workspace query
  lapack::gels('N', m, n, nrhs, a.pointer(), lda, &(rhs[0]), ldb,
               &(work[0]), lwork, info);

  if (info != 0)
    return info;

  lwork = static_cast<unsigned int>(fabs(work[0]));
  work.resize(lwork);

  // solve
  lapack::gels('N', m, n, nrhs, a.pointer(), lda, &(rhs[0]), ldb,
               &(work[0]), lwork, info);

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
  EMView xmap(x.pointer(), x.nrows(), x.ncols());

  // eeigen::HouseholderQR<EMatrix> qr(amap);
  eeigen::ColPivHouseholderQR<EMatrix> qr(amap);
  EMatrix y = qr.solve(xmap);
  x.resize(y.rows(), y.cols());
  memcpy(x.pointer(), y.data(), y.rows() * y.cols() * sizeof(value_type));

  return 0;

#endif
}

template <class MatrixType, class VectorType>
int lls_solve(MatrixType &a, VectorType &x)
{
#ifndef HAVE_NO_LAPACK
  typedef std::vector<typename MatrixType::value_type> WorkArray;
  assert(a.nrows() == x.size());

  int m, n, info(0), lwork(-1);
  m = a.nrows();
  n = a.ncols();
  int lda(a.ldim()), ldb(std::max(n, m));
  WorkArray work(1), rhs(ldb);
  std::copy(x.begin(), x.end(), rhs.begin());

  // first: workspace query
  lapack::gels('N', m, n, 1, a.pointer(), lda, &(rhs[0]), ldb,
               &(work[0]), lwork, info);

  if (info != 0)
    return info;

  lwork = static_cast<unsigned int>(work[0]);
  work.resize(lwork);

  // solve
  lapack::gels('N', m, n, 1, a.pointer(), lda, &(rhs[0]), ldb,
               &(work[0]), lwork, info);

  // copy result into x
  x.resize(n);
  typename WorkArray::iterator last(rhs.begin());
  std::advance(last, n);
  std::copy(rhs.begin(), last, x.begin());
  return info;
#else

  typedef typename MatrixType::value_type value_type;
  typedef eeigen::Matrix<value_type, eeigen::Dynamic, eeigen::Dynamic> EMatrix;
  typedef eeigen::Map<EMatrix> EMView;

  EMView amap(a.pointer(), a.nrows(), a.ncols());
  EMView xmap(x.pointer(), x.size(), 1);

  eeigen::ColPivHouseholderQR<EMatrix> qr(amap);
  // eeigen::HouseholderQR<EMatrix> qr(amap);
  EMatrix y = qr.solve(xmap);
  x.allocate(y.rows());
  memcpy(x.pointer(), y.data(), y.rows() * y.cols() * sizeof(value_type));

  return 0;

#endif
}

template <class MatrixType>
MatrixType lls_solve_copy(const MatrixType &a, const MatrixType &b)
{
  MatrixType at(a), x(b);
  int status = lls_solve(at, x);
  if (status != 0)
  {
    std::stringstream ss;
    ss << "Linear least squares solution failed in Lapack (*gels).\n";
    ss << "info = " << status << "\n";
    throw Error(ss.str());
  }
  return x;
}

template <class MatrixType, class VectorType>
VectorType lls_solve_copy(const MatrixType &a, const VectorType &b)
{
  MatrixType at(a);
  VectorType x(b);
  int status = lls_solve(at, x);
  if (status != 0)
  {
    std::stringstream ss;
    ss << "Linear least squares solution failed in Lapack (*gels).\n";
    ss << "info = " << status << "\n";
    throw Error(ss.str());
  }
  return x;
}

// equality-constrained least-squares solution wrapper have been
// moved to lse.h

#endif
