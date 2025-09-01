
/* Copyright (C) 2018 David Eller <david@larosterna.com>
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

#ifndef GENUA_SDIRK_H
#define GENUA_SDIRK_H

#include "forward.h"
#include "smatrix.h"
#include "dmatrix.h"
#include "propmacro.h"
#include <eeigen/Cholesky>

/** Interface for SDIRK integrators.

  Integration adapter for second-order dynamic systems of the form
  \f[
  M a + C v + K u = F(t)
  \f]
  where the numerical stiffness of the differential equation is introduced
  by the linear left-hand terms (e.g. eig(K,M) span a wide range).

  \ingroup numerics
  \sa OwrenSimonsen22, OwrenSimonsen23, OwrenSimonsen34, StdSecondOrderSystem
  */
class SecondOrderSystem
{
public:
  /// undefined system
  SecondOrderSystem() = default;

  /// virtual base class
  virtual ~SecondOrderSystem() = default;

  /// solve the system T*a = F(t) - K*u - C*v, with T = M + hg*C + sq(hg)*K
  virtual void aSolve(Real hg, Real t, const Vector &u,
                      const Vector &v, Vector &a) = 0;

  /// handle/store/write out a solution u, v at t (default does nothing)
  // virtual void store(Real t, const Vector &u, const Vector &v) {}
};

/** Dense-matrix interface for SDIRK integrators.

  This is an implementation of a second-order structural system using dense
  linear algebra, mostly for testing, debugging purposes or for problems with
  few degrees of freedom (i.e. O(100)) which do not justify the additional
  effort of using sparse-matrix operations.

  \ingroup numerics
  \sa OwrenSimonsen22, OwrenSimonsen23, OwrenSimonsen34, SecondOrderSystem
  */
class StdSecondOrderSystem : public SecondOrderSystem
{
public:
  /// virtual base class
  virtual ~StdSecondOrderSystem() = default;

  /// solve the system T*a = F(t) - K*u - C*v, with T = M + hg*C + sq(hg)*K
  virtual void aSolve(Real hg, Real t, const Vector &u,
                      const Vector &v, Vector &a) override;

  /// overload this: determine external force
  virtual void force(Real t, const Vector &u,
                     const Vector &v, Vector &f) = 0;

protected:
  typedef typename Matrix::EigenMatrix EMatrix;

  /// constant system matrices
  Matrix m_M, m_K, m_C;

  /// current iteration matrix T = M + hg*C + sq(hg)*K
  Matrix m_T;

  /// temporary storage
  Vector m_rhs;

  /// value of h*gamma for which T was factored
  Real m_hglast = 0;

  /// Cholesky factorization of T
  eeigen::LLT<EMatrix> m_llt;
};

/** Base class for SDIRK integrators.

  Implementations of various singly-diagonal implicit Runge-Kutta (SDIRK)
  schemes inherit from this class which implements the implicit Runge-Kutta
  stepping for 2nd order dynamic systems.

  Favorable properties of SDIRK integrators are:
  - the size of the integrated system is n, not 2*n as in state-space methods;
  - only a linear solve per stage is needed, no factorization;
  - all methods implemented here are L-stable;
  - high frequencies are damped more than using Newmark-alpha.

  \b Note: Do not use this class directly; only the child classes initialize the
  integration coefficients.

  \ingroup numerics
  \sa SecondOrderSystem, OwrenSimonsen22, OwrenSimonsen23, OwrenSimonsen34
  */
template <int N>
class SdirkBase
{
public:
  /// perform a single step from tn to tn + h, return error estimate if possible
  Real step(SecondOrderSystem &sys, Real tn, Real h, const Vector &un,
            const Vector &vn, Vector &us, Vector &vs)
  {
    allocate(un.size());

    Real hg = h * m_gamma;
    for (int r = 0; r < N; ++r)
    {

      // approximations to u, v at intermediate step
      // uses us, vs as workspace
      us.mmap() = un.cmap() + m_c[r] * h * vn.cmap();
      vs.mmap() = vn.cmap();
      for (int j = 0; j < r; ++j)
      {
        us.mmap() += sq(h) * m_abar(r, j) * m_k[j].cmap();
        vs.mmap() += h * m_abar(r, j) * m_k[j].cmap();
      }
      sys.aSolve(hg, tn + m_c[r] * h, us, vs, m_k[r]);
    }

    // final step result
    us.mmap() = un.cmap() + h * vn.cmap();
    vs.mmap() = vn.cmap();
    for (int r = 0; r < N; ++r)
    {
      us.mmap() += sq(h) * m_bbar[r] * m_k[r].cmap();
      vs.mmap() += h * m_bbar[r] * m_k[r].cmap();
    }

    // this doesn't work yet

    /*
    Real errorEst = 0;
    if (m_estage > 0) {
      m_uhat = un + h*vn;
      for (int r=0; r<m_estage; ++r)
        m_uhat += sq(h)*m_bhat[r]*m_k[r];
      errorEst = norm( us - m_uhat );
    }
    */

    return 0.0; // errorEst;
  }

  /// perform Richardson extrapolation, return error estimate
  Real richardson(SecondOrderSystem &sys, Real tn, Real h, const Vector &un,
                  const Vector &vn, Vector &us, Vector &vs)
  {
    // fine steps, final result in (us, vs)
    step(sys, tn, 0.5 * h, un, vn, m_uhat, m_vhat);
    step(sys, tn + 0.5 * h, 0.5 * h, m_uhat, m_vhat, us, vs);

    // coarse step into uhat, vhat
    step(sys, tn, h, un, vn, m_uhat, m_vhat);

    // order of the local truncation error is order + 1
    Real k2 = std::pow(2.0, m_order + 1);
    Real afine = k2 / (k2 - 1);
    Real acoarse = -1.0 / (k2 - 1);

    // error estimate of the displacement term
    Real ee = norm(us - m_uhat) / (k2 - 1);

    // Richardson extrapolation
    us = afine * us + acoarse * m_uhat;
    vs = afine * vs + acoarse * m_vhat;

    return ee;
  }

protected:
  /// compute the derived coefficients
  void initCoefficients()
  {
    m_abar = 0.0;
    for (int r = 0; r < N; ++r)
      for (int j = 0; j < N; ++j)
        for (int k = 0; k <= r; ++k)
          m_abar(r, j) += m_a(r, k) * m_a(k, j);

    m_bbar = 0.0;
    for (int r = 0; r < N; ++r)
      for (int k = r; k < N; ++k)
        m_bbar[r] += m_a(k, r) * m_b[k];

    SVector<N> bhb;
    for (int r = 0; r < m_estage; ++r)
      for (int k = r; k < m_estage; ++k)
        bhb[r] += m_a(k, r) * m_bhat[k];
    m_bhat = bhb;
  }

  /// compute the b, c for stiffly accurate rules
  void initOwrenSimonsen()
  {
    for (int r = 0; r < N; ++r)
    {
      m_c[r] = 0;
      for (int j = 0; j <= r; ++j)
        m_c[r] += m_a(r, j);
      m_b[r] = m_a(N - 1, r);
    }
    initCoefficients();
  }

  /// allocate workspace
  void allocate(size_t n)
  {
    BOOST_STATIC_ASSERT(N > 0);
    if (m_k[0].size() == n)
      return;
    for (int r = 0; r < N; ++r)
      m_k[r].allocate(n);
    m_uhat.allocate(n);
    m_vhat.allocate(n);
  }

  /// determine new stepsize from error estimate and tolerance
  Real nextStep(Real h, Real errorEst) const
  {
    Real hf = 0.9 * std::pow(m_tolerance / errorEst, m_order);

    // avoid unecessary refactorization: ignore small stepsize adjustments
    if (hf > 0.8 and hf < 1.5)
      return h;

    return h * std::max(m_hReduction, std::min(m_hExpansion, hf));
  }

protected:
  /// coefficients multiplying y'
  SMatrix<N, N> m_a, m_abar;

  /// result coefficients
  SVector<N> m_b, m_bbar;

  /// coefficients for error estimator (m_estage > 0)
  SVector<N> m_bhat;

  /// timestep coefficient
  SVector<N> m_c;

  /// workspace
  Vector m_k[N], m_uhat, m_vhat;

  /// diagonal coefficient gamma
  Real m_gamma;

  /// stepsize reduction limit
  Real m_hReduction = 0.25;

  /// stepsize expansion limit
  Real m_hExpansion = 4.00;

  /// order of the advancing method
  Real m_order = 2.0;

  /// number of stages of the embedded error estimator
  int m_estage = 0;

  /// error tolerance for state variables (u)
  GENUA_PROP_INI(Real, tolerance, 1e-4)
};

/** Second-order two-stage SDIRK method.
 *
 * This is the only L-stable, stiffly accurate 2-stage SDIRK-method of order 2;
 * dissipation is moderate. For adjustable dissipation, use the three- and
 * four-stage methods.
 *
 * B. Owren and H.H. Simonsen: "Alternative integration methods for problems
 * in structural dynamics." Comput. Methods Appl. Mech. Engrg., 122:1–10, 1995.
 *
 * \ingroup numerics
 * \sa OwrenSimonsen23, OwrenSimonsen34, SecondOrderSystem
 */
class OwrenSimonsen22 : public SdirkBase<2>
{
public:
  /// coefficients are fixed and cannot be adjusted
  OwrenSimonsen22();
};

/** Second-order three-stage SDIRK method.
 *
 * As opposed to the 2-stage method, numerical dissipation in this method can
 * be controlled. The default constructor yields the highest accuracy (with
 * order 3), for high dissipation, use gamma = 1 (order 2), for low
 * dissipation, gamma = 0.19.
 *
 * \todo Implement embedded error estimator
 *
 * B. Owren and H.H. Simonsen: "Alternative integration methods for problems
 * in structural dynamics." Comput. Methods Appl. Mech. Engrg., 122:1–10, 1995.
 *
 * \ingroup numerics
 * \sa OwrenSimonsen22, OwrenSimonsen34, SecondOrderSystem, SdirkBase
 */
class OwrenSimonsen23 : public SdirkBase<3>
{
public:
  /// for L-stability, 0.1804 < gamma < 2.1856
  OwrenSimonsen23(Real gamma = 0.43586652150845899941601945);
};

/** Third-order four-stage SDIRK method.
 *
 * Again, the default constructor yields the best accuracy (almost order 4)
 * which also has very strong dissipation. For less damping, choose
 * gamma = 0.23.
 *
 * \todo Implement embedded error estimator
 *
 * B. Owren and H.H. Simonsen: "Alternative integration methods for problems
 * in structural dynamics." Comput. Methods Appl. Mech. Engrg., 122:1–10, 1995.
 *
 * \ingroup numerics
 * \sa OwrenSimonsen23, OwrenSimonsen22, SecondOrderSystem, SdirkBase
 */
class OwrenSimonsen34 : public SdirkBase<4>
{
public:
  /// for L-stability, 0.2236 < gamma < 0.5728
  OwrenSimonsen34(Real gamma = 0.52572146143500483743340698);
};

#endif // SDIRK_H
