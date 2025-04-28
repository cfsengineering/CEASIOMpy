
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
 
#ifndef GENUA_LSE_H
#define GENUA_LSE_H

#include "forward.h"

/** Equality-constrained least-squares problem.

 Solves
  \f[
    \min | c - Ax | \mbox{subject} to Bx = d
  \f]
  using LAPACK routine ?GGLSE.

  \ingroup numerics
  \sa lls_solve

*/
int lse_solve(DMatrix<float> &a, DMatrix<float> &b, DVector<float> &c,
              DVector<float> &d, DVector<float> &x);

int lse_solve(DMatrix<double> &a, DMatrix<double> &b, DVector<double> &c,
              DVector<double> &d, DVector<double> &x);

int lse_solve(DMatrix<std::complex<float>> &a, DMatrix<std::complex<float>> &b,
              DVector<std::complex<float>> &c, DVector<std::complex<float>> &d,
              DVector<std::complex<float>> &x);

int lse_solve(DMatrix<std::complex<double>> &a,
              DMatrix<std::complex<double>> &b,
              DVector<std::complex<double>> &c,
              DVector<std::complex<double>> &d,
              DVector<std::complex<double>> &x);

int lse_msolve(DMatrix<float> &a, DMatrix<float> &b, DMatrix<float> &c,
               DMatrix<float> &d, DMatrix<float> &x);

int lse_msolve(DMatrix<double> &a, DMatrix<double> &b, DMatrix<double> &c,
               DMatrix<double> &d, DMatrix<double> &x);

int lse_msolve(DMatrix<std::complex<float>> &a, DMatrix<std::complex<float>> &b,
               DMatrix<std::complex<float>> &c, DMatrix<std::complex<float>> &d,
               DMatrix<std::complex<float>> &x);

int lse_msolve(DMatrix<std::complex<double>> &a,
               DMatrix<std::complex<double>> &b,
               DMatrix<std::complex<double>> &c,
               DMatrix<std::complex<double>> &d,
               DMatrix<std::complex<double>> &x);

#endif  // LSE_H
