
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

#ifndef GENUA_EIG_H
#define GENUA_EIG_H

#include "defines.h"
#include "dvector.h"
#include "dmatrix.h"
#include "smatrix.h"
#include "smallqr.h"
#include "algo.h"
#include <eeigen/Eigenvalues>

#include <iostream>

// symmetric eigenvalue problems for heap-allocated matrices

int sym_eig(const DMatrix<float> &a, DVector<float> &lambda);
void sym_eig(const DMatrix<float> &a, DVector<float> &lambda,
             DMatrix<float> &z);

int sym_eig(const DMatrix<double> &a, DVector<double> &lambda);
void sym_eig(const DMatrix<double> &a, DVector<double> &lambda,
             DMatrix<double> &z);

// symmetric problems for stack-allocated problems

template <uint N, typename Type>
inline bool sym_eig(const SMatrix<N, N, Type> &a, SVector<N, Type> &lambda)
{

  typedef typename SMatrix<N, N, Type>::EigenMatrix EigenMatrix;
  const int option = eeigen::EigenvaluesOnly;
  eeigen::SelfAdjointEigenSolver<EigenMatrix> solver(a.cmap(), option);
  lambda.mmap() = solver.eigenvalues();
  return (solver.info() == eeigen::Success);
}

template <uint N, typename Type>
inline bool sym_eig(const SMatrix<N, N, Type> &a, SVector<N, Type> &lambda,
                    SMatrix<N, N, Type> &z)
{
  typedef typename SMatrix<N, N, Type>::EigenMatrix EigenMatrix;
  const int option = eeigen::ComputeEigenvectors;
  eeigen::SelfAdjointEigenSolver<EigenMatrix> solver(a.cmap(), option);
  lambda.mmap() = solver.eigenvalues();
  z.mmap() = solver.eigenvectors();
  return (solver.info() == eeigen::Success);
}

/** Closed-form solution of the 3x3 eigenvalue problem.
 *
 * \ingroup numerics
 * \sa sym_eig
 */
template <class Type>
inline void sym_eig3(const SMatrix<3, 3, Type> &a, SVector<3, Type> &eval)
{
  // check whether a is diagonal
  Type p1 = sq(a(0, 1)) + sq(a(0, 2)) + sq(a(1, 2));
  if (p1 == 0.0)
  {
    eval[0] = a(0, 0);
    eval[1] = a(1, 1);
    eval[2] = a(2, 2);
    return;
  }

  const Type i3(1.0 / 3.0);
  const Type i2(0.5);
  const Type i6(i2 * i3);
  const Type s120(i2 * std::sqrt(3.0));

  // scaled trace of a
  Type m = i3 * (a(0, 0) + a(1, 1) + a(2, 2));

  // K = M - m*I
  SMatrix<3, 3, Type> K(a);
  for (int k = 0; k < 3; ++k)
    K(k, k) -= m;

  Type q = i2 * det(K);
  Type p = std::sqrt(i3 * p1 + i6 * (sq(K(0, 0)) + sq(K(1, 1)) + sq(K(2, 2))));
  Type r = q / cb(p);

  if (r <= -1)
  {
    eval[2] = m + p;
    eval[1] = m - 2 * p;
  }
  else if (r >= 1)
  {
    eval[2] = m + 2 * p;
    eval[1] = m - p;
  }
  else
  {

    // TODO:
    // get rid of the trigonometric functions by using
    // PadeApproximant[Cos[ Acos[x] / 3 ], {x,0,{3,4}}]
    // with sufficiently high order

    Type cphi, sphi, phi = std::acos(r) * i3;
    sincosine(phi, sphi, cphi);
    Type cbeta = -i2 * cphi - s120 * sphi;
    eval[2] = m + 2 * p * cphi;
    eval[1] = m + 2 * p * cbeta;
  }

  // for consistency with lapack , we sort the eigenvalues in
  // ascending order

  eval[0] = 3 * m - eval[1] - eval[2];

  if (eval[0] > eval[1])
    std::swap(eval[0], eval[1]);
  if (eval[1] > eval[2])
    std::swap(eval[1], eval[2]);
  if (eval[0] > eval[1])
    std::swap(eval[0], eval[1]);
}

/// helper routine to extract single eigenvector for known eigenvalue
template <uint N, class Type>
inline void extract_eigenvector(const SMatrix<N, N, Type> &A, Type lambda,
                                SVector<N, Type> &z)
{
  SMatrix<N, N - 1, Type> B;
  SVector<N, Type> tau;

  for (int ki = 0; ki < int(N); ++ki)
  {

    for (int j = 0; j < ki; ++j)
    {
      for (int i = 0; i < int(N); ++i)
        B(i, j) = A(i, j);
      B(j, j) -= lambda;
    }
    for (int j = ki + 1; j < int(N); ++j)
    {
      for (int i = 0; i < int(N); ++i)
        B(i, j - 1) = A(i, j);
      B(j, j - 1) -= lambda;
    }

    // check for zero columns
    Type mincolsum = std::numeric_limits<Type>::max();
    for (int j = 0; j < int(N - 1); ++j)
    {
      Type colsum(0);
      for (int i = 0; i < int(N); ++i)
        colsum += std::fabs(B(i, j));
      mincolsum = std::min(mincolsum, colsum);
    }
    if (mincolsum < N * std::numeric_limits<Type>::epsilon())
      continue;

    // this will fail for the case z[ki] == 0
    bool ok = qr<N, N - 1>(B.pointer(), tau.pointer());
    if (not ok)
      continue;

    SVector<N, Type> r;
    for (int i = 0; i < int(N); ++i)
      r[i] = -A(i, ki);
    r[ki] += lambda;

    qrsolve<N, N - 1>(B.pointer(), tau.pointer(), r.pointer());
    for (int i = 0; i < ki; ++i)
      z[i] = r[i];
    z[ki] = Type(1.0);
    for (int i = ki; i < int(N - 1); ++i)
      z[i + 1] = r[i];

    return;
  }

  z = 0.0;
}

// nonsymmetric problems for heap-allocated matrices

int eig(const DMatrix<float> &a, DVector<std::complex<float>> &lambda);
int eig(const DMatrix<double> &a, DVector<std::complex<double>> &lambda);
int eig(const DMatrix<std::complex<float>> &a,
        DVector<std::complex<float>> &lambda);
int eig(const DMatrix<std::complex<double>> &a,
        DVector<std::complex<double>> &lambda);

#ifndef HAVE_NO_LAPACK

void eig(const DMatrix<float> &a, DVector<std::complex<float>> &lambda,
         DMatrix<float> &u, DMatrix<float> &v);
void eig(const DMatrix<double> &a, DVector<std::complex<double>> &lambda,
         DMatrix<double> &u, DMatrix<double> &v);
void eig(const DMatrix<std::complex<float>> &a,
         DVector<std::complex<float>> &lambda,
         DMatrix<std::complex<float>> &u, DMatrix<std::complex<float>> &v);
void eig(const DMatrix<std::complex<double>> &a,
         DVector<std::complex<double>> &lambda,
         DMatrix<std::complex<double>> &u, DMatrix<std::complex<double>> &v);

#endif

// nonsymmetric problems for stack-allocated matrices

template <uint N, typename Type>
inline bool eig(const SMatrix<N, N, Type> &a,
                SVector<N, typename detail::complex_version<Type>::complex_type> &lambda)
{
  typedef typename SMatrix<N, N, Type>::EigenMatrix EigenMatrix;
  eeigen::EigenSolver<EigenMatrix> solver(a.cmap(), false);
  lambda.mmap() = solver.eigenvalues();
  return (solver.info() == eeigen::Success);
}

template <uint N, typename Type>
inline bool eig(const SMatrix<N, N, Type> &a,
                SVector<N, typename detail::complex_version<Type>::complex_type> &lambda,
                SMatrix<N, N, typename detail::complex_version<Type>::complex_type> &z)
{
  typedef typename SMatrix<N, N, Type>::EigenMatrix EigenMatrix;
  eeigen::EigenSolver<EigenMatrix> solver(a.cmap(), true);
  lambda.mmap() = solver.eigenvalues();
  z.mmap() = solver.eigenvectors();
  return (solver.info() == eeigen::Success);
}

// generalized eigenvalue problems

/** Compute the eigenvalues lambda to the generalized eigenvalue problem
 */
void gen_eig(const CpxMatrix &a, const CpxMatrix &b, CpxVector &lambda);

/** Compute the eigenvalues lambda, left and right eigenvectors
    to the generalized eigenvalue problem
 */
void gen_eig(const CpxMatrix &a, const CpxMatrix &b, CpxVector &lambda,
             CpxMatrix &u, CpxMatrix &v);

/** Compute eigenvalues and right eigenvectors to
  generalized eigenvalue problem.
  */
void gen_eig(const CpxMatrix &a, const CpxMatrix &b,
             CpxVector &lambda, CpxMatrix &v);

/** Compute eigenvalues and eigenvectors of 'a' using the eeigen library.
 *
 * for the case where the size of a is known at compile time, such that
 * a*v = lambda*v, and a = v*diag(lambda)*inv(v)
 * Cost is about 25*N^3.
 *
 * \todo Avoid copies.
 *
 * \ingroup numerics
 * \sa sym_eig
 */
template <uint N, class NumType>
void eig(const SMatrix<N, N, NumType> &a,
         SVector<N, std::complex<NumType>> &lambda,
         SMatrix<N, N, std::complex<NumType>> &v)
{
  typedef eeigen::Matrix<NumType, int(N), int(N)> MatrixType;
  MatrixType ae;
  memcpy(ae.data(), a.pointer(), N * N * sizeof(NumType));

  eeigen::EigenSolver<MatrixType> egsolver(ae, true);
  memcpy(lambda.pointer(), egsolver.eigenvalues().data(),
         N * sizeof(std::complex<NumType>));
  memcpy(v.pointer(), egsolver.eigenvectors().data(),
         N * N * sizeof(std::complex<NumType>));
}

template <uint N, class NumType>
bool eig(const SMatrix<N, N, NumType> &a,
         SVector<N, std::complex<NumType>> &lambda,
         SMatrix<N, N, NumType> &vl, SMatrix<N, N, NumType> &vr)
{
#ifndef HAVE_NO_LAPACK
  const int n(N);
  const int lwork(8 * N);
  NumType work[lwork], wi[N], wr[N];

  int status(0);
  SMatrix<N, N, NumType> b(a);
  lapack::geev('V', 'V', n, b.pointer(), n, wr, wi, vl.pointer(), n,
               vr.pointer(), n, work, lwork, status);
  assert(status == 0);

  for (uint i = 0; i < N; ++i)
    lambda[i] = std::complex<NumType>(wr[i], wi[i]);

  return (status == 0);
#else
  eig(a, lambda, vr);
  return qrinv<N>(vr.pointer(), vl.pointer());
#endif
}

#endif
