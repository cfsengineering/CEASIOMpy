
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

#ifndef GENUA_STANFORDSOLVER_H
#define GENUA_STANFORDSOLVER_H

#include "forward.h"
#include "propmacro.h"

/** Base class for iterative methods developed by Stanford/SOL.
 *
 * \ingroup numerics
 * \sa CraigSolver, LsmrSolver
 */
class SolIterativeSolver
{
public:

  enum ExitCode {
    SolutionIsZero = 0,
    ResidualToleranceAchieved,
    SolutionToleranceAchieved,
    ConLimExceeded,
    MachinePrecisionResidual,
    MachinePrecisionSolution,
    ConLimTooLarge,
    IterationLimit,
    IncompatibleProblem,
    MaxRadiusReached,
  };

  /// set convergence tolerances and maximum number of iterations
  void tolerance(int maxiter, double atoler, double btoler, double conlim=1e8)
  {
    m_maxiter = maxiter;
    m_atol = atoler;
    m_btol = btoler;
    m_conlim = conlim;
  }

  /// access text corresponding to error code
  static const char *statusMessage(int code);

  /// does exit code indicate succes (in some sense, at least)?
  static bool success(int code) {
    switch (code) {
    case SolutionIsZero:
      return false;
    case ResidualToleranceAchieved:
    case SolutionToleranceAchieved:
      return true;
    case ConLimExceeded:
      return false;
    case MachinePrecisionResidual:
    case MachinePrecisionSolution:
      return true;
    case ConLimTooLarge:
    case IterationLimit:
    case IncompatibleProblem:
      return false;
    case MaxRadiusReached:
      return true;
    }
    return false;
  }

protected:

  /// convergence criteria
  double m_atol = 1e-6;

  /// convergence criteria
  double m_btol = 1e-6;

  /// condition number limit (actually, limit for the estimated condition)
  double m_conlim = 1e8;

  /// permitted number of iteration
  size_t m_maxiter = 128;

private:

  /// whether to print iteration reports
  GENUA_PROP_INI(bool, verbose, false)

  /// error text messages
  static const char *s_error_msg[];
};

/** Wrapper for right preconditioning.
 *
 * A thin adapter class which permits the iterative solvers LSQR and LSMR to
 * be used with right-side preconditioning. The preconditioner must be square,
 * that is, of size n-by-n, and needs to support the transpose solve operation.
 *
 *
 * \ingroup numerics
 * \sa LsqrSolver, LsmrSolver
 */
template <typename Scalar>
class RpcOperator
{
public:

  typedef AbstractLinearSolverTpl<Scalar> Preconditioner;
  typedef boost::shared_ptr<Preconditioner> PreconPtr;

  /// initialize with right-preconditioning operator
  RpcOperator(const CsrMatrix<Scalar,1> &op,
              PreconPtr p = PreconPtr()) : m_op(op), m_pc(p) {}

  /// compute y <- this*x
  void muladd(const DVector<Scalar> &x, DVector<Scalar> &y)
  {
    m_w.allocate(x.size());
    if (m_pc != nullptr) {
      m_pc->transposed(false);
      m_pc->solve(x, m_w);
      m_op.muladd(m_w, y);
    } else {
      m_op.muladd(x, y);
    }
  }

  /// compute y <- transpose(this)*x
  void muladdTransposed(const DVector<Scalar> &x, DVector<Scalar> &y)
  {
    m_w.allocate(x.size());
    if (m_pc != nullptr) {
      m_op.muladdTransposed(x, m_w);
      m_pc->transposed(true);
      m_pc->solve(m_w, y);
    } else {
      m_op.muladdTransposed(x, y);
    }
  }

private:

  /// the original operator
  CsrMatrix<Scalar,1> &m_op;

  /// temporary for variable transformation
  DVector<Scalar> &m_w;

  /// transforms A*x = b to A*(M*z) = b
  PreconPtr m_pc;
};

#endif // STANFORDSOLVER_H

