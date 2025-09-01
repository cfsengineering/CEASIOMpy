
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

#ifndef GENUA_LU_H
#define GENUA_LU_H

#include "defines.h"
#include "xcept.h"
#include <eeigen/LU>

#ifndef HAVE_NO_LAPACK
#include "lapack_interface.h"
#else
#include <eeigen/SparseLU>
#endif

#include <vector>
#include <iostream>

/** LU Decomposition.

  LuDecomp always factors the matrix passed in the constructor inplace, i.e.
  it overwrites the constructor argument. In the same manner, the arguments
  to solve() are overwritten by the respective solution.

  LAPACK is used if available; if not, the partial-pivoting implementation
  from the eeigen library is called instead.

  \ingroup numerics

  */
template <class MatrixType>
class LuDecomp
{
public:
  typedef typename MatrixType::value_type value_type;
  typedef eeigen::Matrix<value_type, eeigen::Dynamic, eeigen::Dynamic> EMatrix;
  typedef eeigen::Map<EMatrix> EMView;

  /// initialize and factor
  LuDecomp(MatrixType &a) { factor(a); }

#ifndef HAVE_NO_LAPACK

  /// empty initialization
  LuDecomp() : plu(0) {}

  /// factorize a, overwrites a, returns status
  int factor(MatrixType &a)
  {
    assert(a.nrows() == a.ncols());
    plu = a.pointer();
    ip.resize(a.nrows());
    int status;
    lapack::getrf(a.nrows(), a.ncols(), plu, a.nrows(), &(ip[0]), status);
    return status;
  }

  /// solve Ax=b, overwrite b
  int msolve(MatrixType &b) const
  {
    assert(plu != 0);
    assert(ip.size() == b.nrows());
    int n, status;
    n = ip.size();
    lapack::getrs('N', n, b.ncols(), plu, n, &(ip[0]), b.pointer(), n, status);
    return status;
  }

  /// solve Ax=b, overwrite b
  template <class VectorType>
  int vsolve(VectorType &b) const
  {
    assert(plu != 0);
    assert(ip.size() == b.size());
    int n, status;
    n = ip.size();
    lapack::getrs('N', n, 1, plu, n, &(ip[0]), b.pointer(), n, status);
    return status;
  }

  /// compute the one-norm of matrix a
  value_type onorm(const MatrixType &a) const
  {
    return lapack::lange('O', a.nrows(), a.ncols(), a.pointer(), a.nrows());
  }

  /// compute reciprocal condition number from factorization
  value_type rcond(value_type anorm) const
  {
    assert(plu != 0);
    value_type rcd;
    int n, info(0);
    n = ip.size();
    std::vector<value_type> work(4 * n);
    std::vector<int> iwork(n);
    lapack::gecon('O', n, plu, n, anorm, rcd, &(work[0]), &(iwork[0]), info);
    return rcd;
  }

  /// compute inverse matrix (after factoring), copy into mi
  int inverse(MatrixType &mi) const
  {
    assert(plu);
    int info(0), lwork, n = ip.size();
    assert(mi.nrows() == n);
    assert(mi.ncols() == n);
    if (mi.pointer() != plu)
      memcpy(mi.pointer(), plu, n * n * sizeof(value_type));
    lwork = 128 * n;
    std::vector<value_type> work(lwork);
    lapack::getri(n, mi.pointer(), n, &ip[0], &work[0], lwork, info);
    return info;
  }

#else

  /// empty initialization
  LuDecomp() {}

  /// factorize a, overwrites a, returns status
  int factor(MatrixType &a)
  {
    assert(a.nrows() == a.ncols());
    EMatrix tmp(a.nrows(), a.ncols());
    memcpy(tmp.data(), a.pointer(), a.size() * sizeof(value_type));
    m_factor = eeigen::PartialPivLU<EMatrix>(tmp);
    return 0;
  }

  /// solve Ax=b, overwrite b
  int msolve(MatrixType &b) const
  {
    EMView bview(b.pointer(), b.nrows(), b.ncols());
    EMatrix xtmp = m_factor.solve(bview);
    memcpy(b.pointer(), xtmp.data(), b.size() * sizeof(value_type));
    return 0;
  }

  /// solve Ax=b, overwrite b
  template <class VectorType>
  int vsolve(VectorType &b) const
  {
    EMView bview(b.pointer(), b.size(), 1);
    EMatrix xtmp = m_factor.solve(bview);
    memcpy(b.pointer(), xtmp.data(), b.size() * sizeof(value_type));
    return 0;
  }

  /// compute inverse matrix (after factoring), copy into mi
  int inverse(MatrixType &mi) const
  {
    EMatrix tmp = m_factor.inverse();
    mi.resize(tmp.rows(), tmp.cols());
    memcpy(mi.pointer(), mi.data(), mi.size() * sizeof(value_type));
    return 0;
  }

#endif

private:
#ifndef HAVE_NO_LAPACK

  /// lu-factorization
  typename MatrixType::value_type *plu;

  /// permutation
  std::vector<int> ip;

#else

  /// factorization object in libEigen
  eeigen::PartialPivLU<EMatrix> m_factor;

#endif
};

template <class MatrixType>
MatrixType lu_solve_copy(const MatrixType &a, const MatrixType &b)
{
  int status;
  MatrixType at(a), bt(b);
  LuDecomp<MatrixType> lu;
  status = lu.factor(at);

  // in debug mode, abort on assertion to generate backtrace
  assert(status == 0);
  if (status != 0)
    throw Error("LU factorization failed in Lapack.");
  status = lu.msolve(bt);
  assert(status == 0);
  if (status != 0)
    throw Error("LU solution process failed in Lapack.");
  return bt;
}

template <class MatrixType, class VectorType>
VectorType lu_solve_copy(const MatrixType &a, const VectorType &b)
{
  int status;
  MatrixType at(a);
  VectorType bt(b);
  LuDecomp<MatrixType> lu;
  status = lu.factor(at);
  assert(status == 0);
  if (status != 0)
    throw Error("LU factorization failed in Lapack.");
  status = lu.vsolve(bt);
  assert(status == 0);
  if (status != 0)
    throw Error("LU solution process failed in Lapack.");
  return bt;
}

template <class MatrixType>
int lu_solve(MatrixType &a, MatrixType &b)
{
  int stat;
  LuDecomp<MatrixType> lu;
  stat = lu.factor(a);
  if (stat != 0)
    return stat;
  stat = lu.msolve(b);
  return stat;
}

template <class MatrixType, class VectorType>
int lu_solve(MatrixType &a, VectorType &b)
{
  int stat;
  LuDecomp<MatrixType> lu;
  stat = lu.factor(a);
  if (stat != 0)
    return stat;
  stat = lu.vsolve(b);
  return stat;
}

/** LU-based linear solution of banded problems.
 *
 * This interface solves a banded problem by means of the LAPACK subroutine
 * ?GBSV, where only the populated bands are stored. See the LAPACK user guide
 * or man-page of DGBSV for details.
 *
 * Small-width banded problems are common in spline interpolation.
 *
 * \ingroup numerics
 * \sa lu_solve
 */
template <class MatrixType>
int banded_lu_solve(int kl, int ku, MatrixType &a, MatrixType &b)
{
#ifndef HAVE_NO_LAPACK

  int stat(0);
  int n = a.ncols();
  int nrhs = b.ncols();
  int lda = a.ldim();
  int ldb = b.ldim();

  assert(a.nrows() >= uint(2 * kl + ku + 1));
  assert(b.nrows() == uint(n));

  std::vector<int> ipiv(n);

  lapack::gbsv(n, kl, ku, nrhs, a.pointer(), lda, &ipiv[0],
               b.pointer(), ldb, stat);

  return stat;

#else

  // eeigen doesn't have a banded solver, so we use the sparse direct LU
  // solver instead. Probably better to just call the dense solver for
  // small dimensions.

  typedef typename MatrixType::value_type FloatType;
  typedef eeigen::SparseMatrix<FloatType, eeigen::ColMajor> SpMatrixType;
  typedef eeigen::Matrix<FloatType, eeigen::Dynamic, eeigen::Dynamic> DenseType;
  typedef eeigen::Map<DenseType> DenseMap;

  typedef eeigen::Triplet<FloatType, int> Trip;
  std::vector<Trip> trips;
  trips.reserve(a.size());

  const size_t nc = a.ncols();
  const size_t nr = a.nrows();
  for (size_t j = 0; j < nc; ++j)
  {
    for (size_t i = 0; i < nr; ++i)
    {
      // int brow = kl+ku+i-col;
      size_t r = i + j - kl - ku;
      if (a(i, j) != 0)
        trips.emplace_back(r, j, a(i, j));
    }
  }

  SpMatrixType spm;
  spm.setFromTriplets(trips.begin(), trips.end());

  eeigen::SparseLU<SpMatrixType> solver;
  solver.analyzePattern(spm);
  solver.factorize(spm);

  DenseMap bmap(b.pointer(), b.nrows(), b.ncols());
  DenseType xe = solver.solve(bmap);
  if (solver.info() != eeigen::Success)
    return 1;

  memcpy(b.pointer(), xe.data(), b.size() * sizeof(FloatType));
  return 0;

#endif
}

/** LU-based linear solution of banded problems.
 *
 * This interface solves a banded problem by means of the LAPACK subroutine
 * ?GBSV, where only the populated bands are stored. See the LAPACK user guide
 * or man-page of DGBSV for details.
 *
 * Small-width banded problems are common in spline interpolation.
 *
 * \ingroup numerics
 * \sa lu_solve
 */
template <class MatrixType, class VectorType>
int banded_lu_solve(int kl, int ku, MatrixType &a, VectorType &b)
{
#ifndef HAVE_NO_LAPACK

  int stat(0);
  int n = a.ncols();
  int nrhs = 1;
  int lda = a.ldim();
  int ldb = b.size();

  assert(a.nrows() >= uint(2 * kl + ku + 1));
  assert(b.size() == uint(n));

  std::vector<int> ipiv(n);

  lapack::gbsv(n, kl, ku, nrhs, a.pointer(), lda, &ipiv[0],
               b.pointer(), ldb, stat);

  return stat;

#else

  // eeigen doesn't have a banded solver, so we use the sparse direct LU
  // solver instead. Probably better to just call the dense solver for
  // small dimensions.

  typedef typename MatrixType::value_type FloatType;
  typedef eeigen::SparseMatrix<FloatType, eeigen::ColMajor> SpMatrixType;
  typedef eeigen::Matrix<FloatType, eeigen::Dynamic, eeigen::Dynamic> DenseType;
  typedef eeigen::Map<DenseType> DenseMap;

  typedef eeigen::Triplet<FloatType, int> Trip;
  std::vector<Trip> trips;
  trips.reserve(a.size());

  const size_t nc = a.ncols();
  const size_t nr = a.nrows();
  for (size_t j = 0; j < nc; ++j)
  {
    for (size_t i = 0; i < nr; ++i)
    {
      // int brow = kl+ku+i-col;
      size_t r = i + j - kl - ku;
      if (a(i, j) != 0)
        trips.emplace_back(r, j, a(i, j));
    }
  }

  SpMatrixType spm;
  spm.setFromTriplets(trips.begin(), trips.end());

  eeigen::SparseLU<SpMatrixType> solver;
  solver.analyzePattern(spm);
  solver.factorize(spm);

  DenseMap bmap(b.pointer(), b.size(), 1);
  DenseType xe = solver.solve(bmap);
  if (solver.info() != eeigen::Success)
    return 1;

  memcpy(b.pointer(), xe.data(), b.size() * sizeof(FloatType));
  return 0;

#endif
}

/** Compute inverse of a small matrix using fully-pivoting LU.
 *
 * This is a small wrapper around the full-pivot LU implementation in eeigen
 * for the stable computation of the inverse. The return value indicates whether
 * a is invertible; if it is not, ainv is not written to.
 *
 * \ingroup numerics
 * \sa qrinv, pplu_inv
 */
template <typename Scalar, uint N>
inline bool pivlu_inv(const Scalar a[], Scalar ainv[])
{
  typedef eeigen::Matrix<Scalar, N, N> EMatrix;
  EMatrix tmp;
  memcpy(tmp.data(), a, N * N * sizeof(Scalar));
  eeigen::FullPivLU<EMatrix> lu;
  lu.compute(tmp);
  bool invertible = lu.isInvertible();
  if (invertible)
  {
    tmp = lu.inverse();
    memcpy(ainv, tmp.data(), N * N * sizeof(Scalar));
  }
  return invertible;
}

/** Compute inverse of a small matrix using partially-pivoting LU.
 *
 * This is a small wrapper around the LU implementation in eeigen.
 * The return value indicates whether
 * a is invertible; if it is not, ainv is not written to.
 *
 * \ingroup numerics
 * \sa qrinv, pivlu_inv
 */
template <typename Scalar, uint N>
inline bool pplu_inv(const Scalar a[], Scalar ainv[])
{
  typedef eeigen::Matrix<Scalar, N, N> EMatrix;
  EMatrix tmp;
  memcpy(tmp.data(), a, N * N * sizeof(Scalar));
  eeigen::PartialPivLU<EMatrix> lu;
  lu.compute(tmp);
  bool invertible = lu.isInvertible();
  if (invertible)
  {
    tmp = lu.inverse();
    memcpy(ainv, tmp.data(), N * N * sizeof(Scalar));
  }
  return invertible;
}

#endif
