
/* Copyright (C) 2017 David Eller <david@larosterna.com>
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

#ifndef GENUA_TRNLSP_H
#define GENUA_TRNLSP_H

#include "dmatrix.h"
#include "dvector.h"
#include <exception>

namespace mkl
{

extern int Success;
extern int InvalidOption;
extern int OutOfMemory;
extern int IterationsExceeded;
extern int RadiusTooSmall;
extern int Converged;
extern int SingularJacobian;
extern int NoXChange;
extern int Extremum;

int trnlspbc_init(void *handle, const int &n, const int &m, const float *x,
                  const float *LW, const float *UP, const float *eps,
                  const int &iter1, const int &iter2, const float &rs);

int trnlspbc_init(void *handle, const int &n, const int &m, const double *x,
                  const double *LW, const double *UP, const double *eps,
                  const int &iter1, const int &iter2, const double &rs);

int trnlspbc_check(void *handle, const int &n, const int &m, const float *fjac,
                   const float *fvec, const float *LW, const float *UP,
                   const float *eps, int *info);

int trnlspbc_check(void *handle, const int &n, const int &m, const double *fjac,
                   const double *fvec, const double *LW, const double *UP,
                   const double *eps, int *info);

int trnlspbc_solve(void *handle, float *fvec, float *fjac, int &request);

int trnlspbc_solve(void *handle, double *fvec, double *fjac, int &request);

int trnlspbc_delete(void *handle, const float *unused);

int trnlspbc_delete(void *handle, const double *unused);

/** Wrapper around trust-region solver from MKL.
 *
 * Solves a bound-constrained nonlinear least-squares problem by means of a
 * trust-region approach with dense linear algebra. This class just provides
 * a C++ wrapper to hide the error-prone interface.
 *
 * The problem to be solved must be encapsulated in an object that supports
 * the following interface:
 *
 * \verbatim
 * class LeastSquares {
 *   void eval(const DVector<T> &x, DVector<T> &f);
 *   void jacobian(const DVector<T> &x, DMatrix<T> &J);
 * };
 * \endverbatim
 */
template <typename FloatType> class TrustRegionSolverTpl
{
public:
  TrustRegionSolverTpl(int nx, int mf) : m_nvar(nx), m_mfun(mf)
  {
    FloatType meps = std::numeric_limits<FloatType>::epsilon();
    m_eps[0] = 1e-6;      // minimum permitted TR radius
    m_eps[1] = 1e-6;      // covergence tolerance for |f(x)|_2
    m_eps[2] = 4 * meps;  // Jacobian singularity
    m_eps[3] = 1e-6;      // minimum step length
    m_eps[4] = 1e-6;      // extremum, model does not change along step
    m_eps[5] = 1e-5;      // precision of the trial step
  }

  ~TrustRegionSolverTpl()
  {
    if (m_handle != nullptr)
      trnlspbc_delete(&m_handle, m_xcur.pointer());
  }

  /// set convergence criteria
  void convergence(FloatType tol, FloatType minStepLength = 0,
                   FloatType minTrustRadius = 0)
  {
    m_eps[1] = tol;
    if (minStepLength > 0)
      m_eps[3] = minStepLength;
    if (minTrustRadius > 0)
      m_eps[0] = minTrustRadius;
  }

  /// set initial trust-region radius
  void initialRadius(FloatType delta) { m_rs = delta; }

  /// set lower/upper bounds on the variables
  void bounds(const DVector<FloatType> &xlo, const DVector<FloatType> &xup)
  {
    m_xlo = xlo;
    m_xup = xup;
  }

  /// set lower/upper bounds on the variables
  void bounds(const FloatType *xlo, const FloatType *xup)
  {
    m_xlo.allocate(m_nvar);
    m_xup.allocate(m_nvar);
    std::copy_n(xlo, m_nvar, m_xlo.begin());
    std::copy_n(xup, m_nvar, m_xup.begin());
  }

  /// run solver loop
  template <class LeastSquaresProblem>
  int solve(LeastSquaresProblem &&lsp, DVector<FloatType> &x)
  {
    assert(x.size() >= m_nvar);
    m_xcur.allocate(m_nvar);
    m_fval.allocate(m_mfun);
    m_fjac.resize(m_mfun, m_nvar);
    std::copy_n(x.begin(), m_nvar, m_xcur.begin());
    int stat = init();
    if (stat != mkl::Success)
      return stat;

    int request = 0;
    while (request >= 0) {
      trnlspbc_solve(&m_handle, m_fval.pointer(), m_fjac.pointer(), request);
      if (request == 2)
        lsp.jacobian(m_xcur, m_fjac);
      else if (request == 1)
        lsp.eval(m_xcur, m_fval);
    }

    std::copy_n(m_xcur.pointer(), m_nvar, x.begin());
    return request;
  }

private:

  /// initialize solver
  int init()
  {
    if (m_xlo.size() != m_nvar) {
      m_xlo.allocate(m_nvar);
      m_xlo = -std::numeric_limits<FloatType>::max();
    }
    if (m_xup.size() != m_nvar) {
      m_xup.allocate(m_nvar);
      m_xup = std::numeric_limits<FloatType>::max();
    }
    int stat = mkl::trnlspbc_init(&m_handle, m_nvar, m_mfun, m_xcur.pointer(),
                                  m_xlo.pointer(), m_xup.pointer(), m_eps,
                                  m_maxiter, m_stepiter, m_rs);
    if (stat == OutOfMemory)
      throw std::runtime_error("MKL TR solver: Out of memory.");
    else if (stat == InvalidOption)
      throw std::runtime_error("MKL TR solver: Invalid option in init()");
    else if (stat != Success)
      throw std::runtime_error(
          "MKL TR solver: Undocumented error code in init().");

    int info[6];
    stat = mkl::trnlspbc_check(&m_handle, m_nvar, m_mfun, m_fjac.pointer(),
                               m_fval.pointer(), m_xlo.pointer(),
                               m_xup.pointer(), m_eps, info);
    assert(stat == Success);
    if (info[0] != 0)
      throw std::runtime_error("MKL TR solver: Invalid handle.");
    if (info[1] != 0)
      throw std::runtime_error("MKL TR solver: Invalid fjac.");
    if (info[2] != 0)
      throw std::runtime_error("MKL TR solver: Invalid fvec.");
    if (info[3] != 0)
      throw std::runtime_error("MKL TR solver: Invalid lower bound.");
    if (info[4] != 0)
      throw std::runtime_error("MKL TR solver: Invalid upper bound.");
    if (info[5] != 0)
      throw std::runtime_error("MKL TR solver: Invalid convergence criteria.");

    return stat;
  }

private:
  /// opaque handle to solver data
  void *m_handle = nullptr;

  /// problem size
  int m_nvar, m_mfun;

  /// stopping criteria
  FloatType m_eps[6];

  /// outer iterations
  int m_maxiter = 1024;

  /// step iterations
  int m_stepiter = 128;

  /// initial size of the trust region
  FloatType m_rs = 100.0;

  /// current value of x
  DVector<FloatType> m_xcur;

  /// upper/lower bounds
  DVector<FloatType> m_xlo, m_xup;

  /// vector of function values
  DVector<FloatType> m_fval;

  /// Jacobian of f with respect to x
  DMatrix<FloatType> m_fjac;
};

typedef TrustRegionSolverTpl<double> DTrustRegionSolver;
typedef TrustRegionSolverTpl<float> STrustRegionSolver;
}

#endif  // TRNLSP_H
