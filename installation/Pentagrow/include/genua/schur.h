
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

#ifndef GENUA_SCHUR_H
#define GENUA_SCHUR_H

#include "smatrix.h"
#include <eeigen/Eigenvalues>

/** Compute the full Schur decomposition.
 *
 * A = U * T * U^T
 *
 * Uses eeigen.
 *
 */
template <uint N, class NumType>
void schur_decomposition(const SMatrix<N, N, NumType> &A,
                         SMatrix<N, N, NumType> &T,
                         SMatrix<N, N, NumType> &U)
{
  typedef typename SMatrix<N, N, NumType>::EigenMatrix EigenMatrix;
  eeigen::RealSchur<EigenMatrix> schur(A.cmap(), true);
  T.mmap() = schur.matrixT();
  U.mmap() = schur.matrixU();
}

/** Compute the only the block-diagonal Schur matrix T
 *
 * A = U * T * U^T
 *
 * Uses eeigen.
 *
 */
template <uint N, class NumType>
void schur_matrix(const SMatrix<N, N, NumType> &A,
                  SMatrix<N, N, NumType> &T)
{
  typedef typename SMatrix<N, N, NumType>::EigenMatrix EigenMatrix;
  eeigen::RealSchur<EigenMatrix> schur(A.cmap(), false);
  T.mmap() = schur.matrixT();
}

// #ifndef HAVE_NO_LAPACK

// #include "lapack_interface.h"

// template <uint N, class NumType>
// bool schur(const SMatrix<N,N,NumType> &A, SMatrix<N,N,NumType> &U,
//            SMatrix<N,N,NumType> &T,
//            SVector<N,std::complex<NumType> > &lambda)
//{
//   // probably faster using eeigen (for small matrices)

//  // skip the balancing permutation step for now
//  // first step : balancing
//  //  NumType scale[N];
//  const int n(N), lda(N), lwork(8*N);
//  int ilo(1), ihi(n), info(0);
//  //  lapack::gebal('B', n, A.pointer(), lda, ilo, ihi, scale, info);
//  //  assert(info == 0);
//  //  if (info != 0)
//  //    return false;

//  // reduction to upper hessenberg form, store into T aliased as H
//  NumType tau[N], work[lwork];
//  T = A;
//  NumType *H = T.pointer();
//  lapack::gehd2(n, ilo, ihi, H, lda, tau, work, info);
//  assert(info == 0);
//  if (info != 0)
//    return false;

//  // generate Q from reflectors, store into U aliased as Q
//  U = T;
//  NumType *Q = U.pointer();
//  lapack::orghr(n, ilo, ihi, Q, lda, tau, work, lwork, info);
//  assert(info == 0);
//  if (info != 0)
//    return false;

//  // finally, generate Schur matrices
//  NumType wr[N], wi[N];
//  lapack::hseqr('S', 'V', n, ilo, ihi, H, lda, wr, wi, Q, lda,
//                work, lwork, info);
//  assert(info == 0);
//  if (info != 0)
//    return false;

//  // write eigenvalues
//  for (uint i=0; i<N; ++i)
//    lambda[i] = std::complex<NumType>(wr[i], wi[i]);

//  // when using balancing permutation, must transform
//  // back using dgebak (?)

//  return true;
//}

// #endif

#endif // SCHUR_H
