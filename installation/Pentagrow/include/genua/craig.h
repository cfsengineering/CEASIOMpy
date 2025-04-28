
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

#ifndef GENUA_CRAIG_H
#define GENUA_CRAIG_H

#include "stanfordsolver.h"
#include "csrmatrix.h"

/** Craig's method for under-determined systems.

   CRAIG finds a solution x to the linear equation Ax = b, where
   A is a real matrix with m rows and n columns, and b is a real
   m-vector.  If A is square and nonsingular, CRAIG finds the
   unique solution x = A(inv)b.
   If the system Ax = b is under-determined (i.e. there are many
   solutions), CRAIG finds the solution of minimum Euclidean length,
   namely    x = A inv(A A') b.  Thus, CRAIG solves the problem

            min  x'x  subject to  Ax = b.

   y returns a vector satisfying A'y = x.  Hence AA'y = b.

   A is an m by n matrix (ideally sparse),
   or a function handle such that
      y = A(x,1) returns y = A*x   (where x will be an n-vector);
      y = A(x,2) returns y = A'*x  (where x will be an m-vector).

   CRAIG uses an iterative (conjugate-gradient-like) method.
   For further information, see
   1. C. C. Paige and M. A. Saunders (1982a).
      LSQR: An algorithm for sparse linear equations and sparse least squares,
      ACM TOMS 8(1), 43-71.

   08 Apr 2003: First craig.m derived from Fortran 77 version of craig1.for.
                Michael Saunders, Systems Optimization Laboratory,
                Dept of MS&E, Stanford University.
   09 Apr 2003: Experimenting on singular systems (for inverse iteration).
                Separately, on full-rank Ax = b, "Acond" seems to
                over-estimate cond(A) drastically.
   02 Oct 2006: Output y such that x = A'y (already in the f77 version).
   15 Aug 2014: A can now be a matrix or a function handle, as in lsqrSOL.
   28 Aug 2014: Fixed glitches found by Dominique Orban.

   \ingroup numerics
   \sa SolIterativeSolver, LsmrSolver

  */
template <typename Scalar> class CraigSolver : public SolIterativeSolver
{
public:

  using SolIterativeSolver::ExitCode;
  typedef CsrMatrix<Scalar, 1> Operator;

  /// minimize |x|^2 such that |Ax = b|
  int solve(const Operator &A, const DVector<Scalar> &b, DVector<Scalar> &x)
  {
    const Scalar eps = std::numeric_limits<Scalar>::epsilon();
    const size_t m = A.nrows();
    const size_t n = A.ncols();

    if (x.size() != n)
      x.resize(n);

    Scalar ctol = 0;
    if (m_conlim > 0)
      ctol = Scalar(1) / conlim;

    // Set beta(1) and u(1) for the bidiagonalization.
    // beta*u = b.

    Scalar beta = norm(b);
    Scalar bnorm = beta;
    Scalar rnorm = beta;

    if (beta == 0)
      return 1;

    DVector<Scalar> u(b);
    u /= beta;

    // aanorm  is norm(L_k)**2, an estimate of norm(A)**2.  It is
    //                alfa1**2  +  (alfa2**2 + beta2**2)  +  ...
    Scalar aanorm(0);

    // ddnorm  is norm(D_k)**2, an estimate of norm( (A'A)inverse ).
    Scalar ddnorm(0);

    // xxnorm  is norm(x_k)**2  =  norm(z_k)**2.
    Scalar xxnorm(0);

    DVector<Scalar> v(n), w(n), y(n);
    Scalar alfa(1), z(-1), Anorm(0), Acond(0), xnorm(0);
    for (int itn = 0; itn < m_maxiter; ++itn) {

      // Perform the next step of the bidiagonalization to obtain the
      // next alfa, v, beta, u.  These satisfy the relations
      //      alfa*v  =  A'*u  -  beta*v.
      //      beta*u  =  A*v   -  alfa*u,

      // v = A'*u   - beta*v;
      v *= -beta;
      A.muladdTransposed(u, v);

      Scalar oldalf = alfa;
      alfa = norm(v);
      if (alfa == 0)
        return 2;
      v /= alfa;

      aanorm += sq(alfa);
      z *= -(beta / alfa);
      x += z * v;

      Scalar t1 = -beta / oldalf;
      Scalar t2 = z / alfa;
      Scalar t3 = Scalar(1) / alfa;

      w = u + t1 * w;
      y += t2 * w;
      ddnorm += sq(t3 * w);

      // u = A*v    - alfa*u;
      a *= -alfa;
      A.muladd(v, u);
      beta = norm(u);

      if (beta > 0)
        u /= beta;

      // Test for convergence.
      // We estimate various norms and then see if
      // the quantities test1 or test3 are suitably small.
      aanorm += sq(beta);
      Anorm = std::sqrt(aanorm);
      Acond = std::sqrt(ddnorm) * Anorm;
      xxnorm = xxnorm + sq(z);
      rnorm = std::fabs(beta * z);
      xnorm = std::sqrt(xxnorm);

      Scalar test1 = rnorm / bnorm;
      Scalar test3 = Scalar(1) / Acond;
      t1 = test1 / (1 + Anorm * xnorm / bnorm);
      Scalar rtol = m_btol + m_atol * Anorm * xnorm / bnorm;

      if (test3 <= eps)
        return ConLimTooLarge;
      else if (t1 <= eps)
        return MachinePrecisionResidual;
      else if (test3 < ctol)
        return ConLimExceeded;
      else if (test1 < rtol)
        return ResidualToleranceAchieved;
    }

    return IterationLimit;
  }
};

#endif  // CRAIG_H
