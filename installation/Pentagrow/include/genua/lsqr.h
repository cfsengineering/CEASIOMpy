
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

#ifndef GENUA_LSQR_H
#define GENUA_LSQR_H

#include "stanfordsolver.h"
#include "dvector.h"
#include "abstractlinearsolver.h"
#include "xcept.h"

/** LSQR: Iterative solver for least-squares problems.

  The operator 'A' passed to solve() needs to provide the interface
  \verbatim
    void muladd(const DVector<Scalar> &x, DVector<Scalar> &y);
    void muladdTransposed(const DVector<Scalar> &x, DVector<Scalar> &y);
  \endverbatim
  which compute y = A*x and y = transpose(A)*x.

  This implementation differs from the LSQR paper in that it includes an
  additional termination criterion based on the scaled length of x. In trust-
  region methods for least-squares problems, a solution |s*x| < delta
  is often needed, and in that case, it may be advantageous to truncate LSQR
  early based on the scaled radius criterion.

  \ingroup numerics
  \sa CraigSolver, LsmrSolver
*/
template <typename Scalar> class LsqrSolver : public SolIterativeSolver
{
public:

  using SolIterativeSolver::ExitCode;

  /// optional termination: stop if |s*x| >= r
  void maxRadius(const DVector<Scalar> &s, Scalar r) {
    m_xrsq = sq(r);
    m_xscale = s;
  }

  /// optional termination: stop if |x| >= r
  void maxRadius(Scalar r) {
    m_xrsq = sq(r);
    m_xscale.clear();
  }

  /// minimize |Ax - b|^2 + lambda |x|^2
  template <class Operator>
  ExitCode solve(const Operator &A, const DVector<Scalar> &b,
                 DVector<Scalar> &x, Scalar lambda = 0)
  {
    // const size_t m = A.nrows();
    const size_t n = A.ncols();

    const Scalar ctol = (m_conlim > 0) ? (Scalar(1) / m_conlim) : 0;
    Scalar Anorm(0), Acond(0), dampsq(sq(lambda)), ddnorm(0);
    Scalar xnorm(0), xxnorm(0), cs2(-1), sn2(0), res2(0), z(0);

    // Set up the first vectors u and v for the bidiagonalization.
    // These satisfy  beta*u = b,  alfa*v = A'u.
    m_work[0].allocate(b.size());
    m_work[1].resize(n);
    m_work[2].resize(n);
    DVector<Scalar> & u( m_work[0] );
    DVector<Scalar> & v( m_work[1] );
    DVector<Scalar> & w( m_work[2] );

    u = b;
    Scalar alfa(0), beta(norm(u));
    if (beta > 0) {
      u /= beta;
      A.muladdTransposed(u, v);
      alfa = norm(v);
    }
    if (alfa > 0) {
      v /= alfa;
      w = v;
    }

    Scalar Arnorm = alfa * beta;
    if (Arnorm == 0)
      return SolutionIsZero;

    Scalar rhobar(alfa), phibar(beta), bnorm(beta);
    Scalar rnorm(beta), r1norm(rnorm), r2norm(rnorm);
    x.resize(n);
    for (size_t itn = 0; itn < m_maxiter; ++itn) {

      // Perform the next step of the bidiagonalization to obtain the
      // next beta, u, alfa, v.  These satisfy the relations
      //      beta*u  =  A*v  - alfa*u,
      //      alfa*v  =  A'*u - beta*v.
      u *= -alfa;
      A.muladd(v, u);

      beta = norm(u);
      if (beta > 0) {
        u /= beta;
        Anorm = std::sqrt(sq(Anorm) + sq(alfa) + sq(beta) + dampsq);
        // v = A'*u   - beta*v;
        v *= -beta;
        A.muladdTransposed(u, v);
        alfa = norm(v);
        if (alfa > 0)
          v /= alfa;
      }

      // Use a plane rotation to eliminate the damping parameter.
      // This alters the diagonal (rhobar) of the lower-bidiagonal matrix.
      Scalar rhobar1 = std::sqrt(sq(rhobar) + dampsq);
      Scalar cs1 = rhobar / rhobar1;
      Scalar sn1 = lambda / rhobar1;
      Scalar psi = sn1 * phibar;
      phibar = cs1 * phibar;

      // Use a plane rotation to eliminate the subdiagonal element (beta)
      // of the lower-bidiagonal matrix, giving an upper-bidiagonal matrix.
      Scalar rho = std::sqrt(sq(rhobar1) + sq(beta));
      Scalar cs = rhobar1 / rho;
      Scalar sn = beta / rho;
      Scalar theta = sn * alfa;
      rhobar = -cs * alfa;
      Scalar phi = cs * phibar;
      phibar = sn * phibar;
      Scalar tau = sn * phi;

      // Update x and w.
      Scalar t1 = phi / rho;
      Scalar t2 = -theta / rho;
      Scalar t3 = Scalar(1) / rho;

      // if a termination criterion based on |x| is given, store the
      // previous iterate x before updating
      if (m_xrsq > 0)
        m_work[0] = x;

#pragma omp simd reduction(+:ddnorm)
      for (size_t i=0; i<n; ++i) {
        ddnorm += sq( t3*w[i] );
        x[i] += t1*w[i];
        w[i] = t2*w[i] + v[i];
      }

      // once x has been updated, check the length criterion; if x is too long,
      // compute the Steihaug-Toint point from the previous value of x
      if (radiusExceeded(x)) {
        steihaugPoint(m_work[0], x);
        return MaxRadiusReached;
      }

      // Use a plane rotation on the right to eliminate the
      // super-diagonal element (theta) of the upper-bidiagonal matrix.
      // Then use the result to estimate  norm(x).
      Scalar delta = sn2 * rho;
      Scalar gambar = -cs2 * rho;
      Scalar rhs = phi - delta * z;
      Scalar zbar = rhs / gambar;
      xnorm = std::sqrt(xxnorm + sq(zbar));
      Scalar gamma = std::sqrt(sq(gambar) + sq(theta));
      cs2 = gambar / gamma;
      sn2 = theta / gamma;
      z = rhs / gamma;
      xxnorm += sq(z);

      // Test for convergence.
      // First, estimate the condition of the matrix  Abar,
      // and the norms of  rbar  and  Abar'rbar.
      Acond = Anorm * std::sqrt(ddnorm);
      Scalar res1  = sq(phibar);
      res2 += sq(psi);
      rnorm = std::sqrt(res1 + res2);
      Arnorm = alfa * std::fabs(tau);

      // Distinguish between
      //    r1norm = ||b - Ax|| and
      //    r2norm = rnorm in current code
      //           = sqrt(r1norm^2 + damp^2*||x||^2).
      //    Estimate r1norm from
      //    r1norm = sqrt(r2norm^2 - damp^2*||x||^2).
      // Although there is cancellation, it might be accurate enough.
      Scalar r1sq = sq(rnorm) - dampsq * xxnorm;
      r1norm = std::sqrt(std::fabs(r1sq));
      if (r1sq < 0)
        r1norm = -r1norm;
      r2norm = rnorm;

      // Now use these norms to estimate certain other quantities,
      // some of which will be small near a solution.
      Scalar test1 = rnorm / bnorm;
      Scalar test2 = Arnorm / (Anorm * rnorm);
      Scalar test3 = Scalar(1) / Acond;
      t1 = test1 / (1 + Anorm * xnorm / bnorm);
      Scalar rtol = m_btol + m_atol * Anorm * xnorm / bnorm;

      if (verbose())
        std::clog << '[' << itn << "] LSQR r1: " << r1norm
                  << " r2: " << r2norm << " cond(A): " << Acond <<  std::endl;

      // The following tests guard against extremely small values of
      // atol, btol  or  ctol.  (The user may have set any or all of
      // the parameters  atol, btol, conlim  to 0.)
      // The effect is equivalent to the normal tests using
      // atol = eps,  btol = eps,  conlim = 1/eps.
      if (1 + test3 <= 1)
        return ConLimTooLarge;
      else if (1 + test2 <= 1)
        return MachinePrecisionSolution;
      else if (1 + t1 <= 1)
        return MachinePrecisionResidual;
      else if (test3 <= ctol)
        return ConLimExceeded;
      else if (test2 <= m_atol)
        return SolutionToleranceAchieved;
      else if (test1 <= rtol)
        return ResidualToleranceAchieved;
    }
    return IterationLimit;
  }

private:

  /// check radius criterion if enabled
  bool radiusExceeded(const DVector<Scalar> &x) const {
    if (m_xrsq <= 0)
      return false;
    Scalar rsq = 0;
    const size_t n = x.size();
    if (m_xscale.size() != n) {
      rsq = dot(x,x);
    } else {
#pragma omp simd reduction(+:rsq)
      for (size_t i=0; i < n; ++i)
        rsq += sq( x[i] * m_xscale[i] );
    }
    return (rsq >= m_xrsq);
  }

  /// blend xp and x such that |x| = delta
  void steihaugPoint(const DVector<Scalar> &xp, DVector<Scalar> &x) {
    DVector<Scalar> &dst(m_work[1]);
    dst = x - xp;
    Scalar a = dot(dst, dst);
    Scalar b = 2.0 * dot(xp, dst);
    Scalar c = dot(xp, xp) - m_xrsq;

    if (verbose())
      std::clog << "[d] LSQR |xp| = "
                << norm(xp) << " |x| = " << norm(x)
                << " Delta = " << std::sqrt(m_xrsq) << std::endl;

    Scalar s, t1, t2;
    std::tie(t1,t2) = solve_quadratic(a, b, c);
    if (hint_unlikely(t1 > 0 and t2 > 0))
      s = std::min(t1, t2);
    else
      s = std::max(t1, t2);

    s = clamp(s, 0.0, 1.0);
    const size_t n = x.size();
#pragma omp simd
    for (size_t i=0; i<n; ++i)
      x[i] = (1.0 - s) * xp[i] + s * x[i];

    if (verbose())
      std::clog << "[i] LSQR - computed Steihaug-Toint point." << std::endl;
  }

private:

  /// work space, to avoid re-allocation when solve() is called often
  DVector<Scalar> m_work[3];

  /// scaling vector used to constrain |s*x|^2 < m_xrsq
  DVector<Scalar> m_xscale;

  /// permitted squared length of x (0 means no constraint)
  Scalar m_xrsq = 0;
};

/** Interface for optionally preconditioned LSQR.
 *
 * This class adapts the LsqrSolver template for use as a linear solver
 * that mostly complies with the common interface of AbstractLinearSolverTpl.
 * On construction, a right-side preconditioner M can be pased which should
 * bring the condition number of A*M^-1 closer to 1.
 *
 *
 * \ingroup numerics
 * \sa RpcOperator
 */
template <typename Scalar>
class PreconditionedLsqr : public AbstractLinearSolverTpl<Scalar>
{
public:

  typedef AbstractLinearSolverTpl<Scalar> Base;
  typedef boost::shared_ptr<Base> PreconPtr;

  /// create solver without preconditioner
  PreconditionedLsqr() : Base() { Base::m_implName = "LSQR"; }

  /// create solver without preconditioner
  PreconditionedLsqr(PreconPtr preconditioner) : Base(), m_rpc(preconditioner) {
    Base::m_implName = "PreconditionedLSQR";
  }

  /// full factorization (minimum interface)
  bool factor(const CsrMatrix<Scalar,1> *pa) {
    m_pa = pa;
    if (m_rpc != nullptr)
      return m_rpc->factor(pa);
    return true;
  }

  /// numerical factorization only (if supported)
  bool refactor(const CsrMatrix<Scalar,1> *pa) {
    m_pa = pa;
    if (m_rpc != nullptr)
      return m_rpc->refactor(pa);
    return true;
  }

  /// solve with multiple rhs
  virtual bool solve(const DMatrix<Scalar> &, DMatrix<Scalar> &) {
    throw Error("LSQR for multiple RHS not supported yet.");
  }

  /// solve single RHS (by default implemented in terms of the above)
  virtual bool solve(const DVector<Scalar> &b, DVector<Scalar> &x) {
    int stat;
    if (m_rpc != nullptr) {
      RpcOperator<Scalar> rop(*m_pa, m_rpc);
      stat = m_lsqr.solve(rop, b, x);
    } else {
      stat = m_lsqr.solve(*m_pa, b, x);
    }
    return m_lsqr.success(stat);
  }

private:

  /// matrix to solve with
  CsrMatrix<Scalar> *m_pa;

  /// instance of solver
  LsqrSolver<Scalar> m_lsqr;

  /// optional right preconditioner
  PreconPtr m_rpc;
};


#endif  // LSQR_H
