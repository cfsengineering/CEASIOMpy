
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
 
#include "srfprojector.h"
#include "surface.h"
#include "abstractcurve.h"
#include <genua/smallqr.h>
#include <genua/algo.h>
#include <genua/dbprint.h>

// one-dimensional functions for use with golden ratio search

namespace detail {

  class usearch {
  public:
    usearch(const Surface & s, const Vct3 & ptr, Real vv)
      : srf(s), pt(ptr), v(vv) {}
    Real operator()(Real u) {
      Vct3 r( srf.eval(u,v) - pt );
      return sq(r);
    }
  private:
    const Surface & srf;
    const Vct3 & pt;
    Real v;
  };

  class vsearch {
  public:
    vsearch(const Surface & s, const Vct3 & ptr, Real uu)
      : srf(s), pt(ptr), u(uu) {}
    Real operator()(Real v) {
      Vct3 r( srf.eval(u,v) - pt );
      return sq(r);
    }
  private:
    const Surface & srf;
    const Vct3 & pt;
    Real u;
  };

} // namespace detail

// ------------------ SrfProjector -------------------------

bool SrfProjector::intersect(const AbstractCurve &c, Vct2 &q, Real &t) const
{
  // use a negative q to start Gauss-Newton with a coarse search method
  if (t < 0) {
    Vct3 qt = searchIntersection(8, c, Vct3(), Vct3(1,1,1));
    q = Vct2(qt[0], qt[1]);
    t = qt[2];
  }

  // Gauss-Newton method with simple clamping to boundary
  Mtx33 J;
  Vct3 Sp, Su, Sv, Cp, Ct, D;
  const int itmax = 32;
  bool failed = false;
  for (int it=0; it<itmax; ++it) {
    srf.plane(q[0], q[1], Sp, Su, Sv);
    c.tgline(t, Cp, Ct);
    D = Sp - Cp;
    Real f = sq(D);
    if (f < tolsq)
      return true;

    for (int k=0; k<3; ++k) {
      J(k,0) =  Su[k];
      J(k,1) =  Sv[k];
      J(k,2) = -Ct[k];
    }

    // overwrite D with dx such that J*dx = D
    bool stat = qrlls<3,3>(J.pointer(), D.pointer());
    if (stat) {

      // change in variables needs to be J*dx = -D -> substract
      q[0] = clamp(q[0] - D[0], 0.0, 1.0);
      q[1] = clamp(q[1] - D[1], 0.0, 1.0);
      t    = clamp(t    - D[2], 0.0, 1.0);
      if (sq(D) < dpsq)
        return true;
    } else {
      failed = true;
      break;
    }
  }

  // fall through here if Gauss-Newton method failed completely
  // use repeated interval reduction approach instead (costly, >500 eval)
  Vct3 vd(0.5, 0.5, 0.5);
  Vct3 qt(0.5, 0.5, 0.5);

  // start with a very fine grid to catch global shape
  int n = 16;
  for (int it=0; it<itmax; ++it) {
    Vct3 lo = clamp(qt-vd, Vct3(0,0,0), Vct3(1,1,1));
    Vct3 hi = clamp(qt+vd, Vct3(0,0,0), Vct3(1,1,1));
    qt = searchIntersection(n, c, lo, hi);
    vd *= 2.0 / (n - 1);
    q = Vct2(qt[0], qt[1]);
    t = qt[2];
    if (sq(vd) < dpsq)
      return true;
    if (sq(srf.eval(q[0], q[1]) - c.eval(t)) < tolsq)
      return true;

    // reduce grid dimensions on each call
    n = std::max(4, n/2);
  }

  return false;
}

Vct3 SrfProjector::searchIntersection(int n, const AbstractCurve &c,
                                      const Vct3 &lo, const Vct3 &hi) const
{
  Real du = (hi[0] - lo[0]) / (n-1);
  Real dv = (hi[1] - lo[1]) / (n-1);
  Vct3 lp0 = c.eval(lo[2]);
  Vct3 lp1 = c.eval(hi[2]);
  Vct3 dl = (lp1 - lp0);
  Real ilsq = 1.0 / sq(dl);
  Vct3 qbest;
  Real dmin = std::numeric_limits<Real>::max();

  // omp for?
  for (int i=0; i<n; ++i) {
    Real ui = lo[0] + i*du;
    for (int j=0; j<n; ++j) {
      Real vj = lo[1] + j*dv;
      Vct3 S = srf.eval(ui, vj);
      Real trl = clamp(dot(S - lp0, dl) * ilsq, 0.0, 1.0);
      Real t = (1.0 - trl)*lo[2] + trl*hi[2];
      Real dsq = sq(S - c.eval(t));
      if (dsq < dmin) {
        dmin = dsq;
        qbest = Vct3(ui, vj, t);
      }
    }
  }

  return qbest;
}

bool SrfProjector::gaussNewton(const Vct3 & pt, Vct2 & q) const
{
  SMatrix<3,2,Real> a;
  Vct3 S, Su, Sv, rhs;

  // initial distance
  Real dsqmin = huge;
  Vct2 qbest(q), step, prev(q);

  // currently active constraint
  int c = SrfProjector::NONE;

  const int maxiter(16);
  for (int iter=0; iter<maxiter; ++iter) {

    // evaluate distance of pt to surface
    srf.plane(q[0], q[1], S, Su, Sv);
    Vct3 r(S - pt);
    Real dsq = dot(r,r);

    // jump out if tolerance achieved
    if (dsq < tolsq)
      return true;

//    // optimality condition
//    if (c == NONE) {
//      // normal cross distance : check if distance points
//      // along the local normal - projection point found
//      Vct3 nxr( cross(cross(Su,Sv), r) );
//      if (dot(nxr,nxr) < tolsq)
//        return true;
//    } else {
//      if ( c & (SrfProjector::ULO | SrfProjector::UHI) ) {
//        if ( fabs(dot(Sv,r)) < tolsq )
//          return true;
//      }
//      if ( c & (SrfProjector::VLO | SrfProjector::VHI) ) {
//        if ( fabs(dot(Su,r)) < tolsq )
//          return true;
//      }
//    }

    if (dsq < dsqmin) {

      // keep track of best solution
      // this will set dsqmin on first iteration
      dsqmin = dsq;
      qbest = q;
    } else {

      // current q is worse than best known last step,
      // apply backtracking
      Real alpha = 1.0;
      Real dp = sq(step[0]) + sq(step[1]);
      do {
        alpha *= 0.5;
        q = prev;
        advance(q, alpha*step);
        srf.plane(q[0], q[1], S, Su, Sv);
        r = S - pt;
        dsq = sq(r);
        if (dsq < dsqmin) {
          dsqmin = dsq;
          qbest = q;
          break;
        }
      } while (alpha*dp > dpsq);
    }

    // report convergence when Su, Sv are orthogonal to r
    if ( fabs(cosarg(Su,r)) < 1e-4 and fabs(cosarg(Sv,r)) < 1e-4 ) {
      q = qbest;
      return true;
    }

    // solve linear least-squares problem
    for (uint k=0; k<3; ++k) {
      a(k,0) = Su[k];
      a(k,1) = Sv[k];
      rhs[k] = -r[k];
    }
    if (not qrlls<3,2,Real>(a.pointer(), rhs.pointer())) {
      q = qbest;
      dbprint("qr failed.");
      return false;
    }

    // store previous q and advance a full step
    step[0] = rhs[0];
    step[1] = rhs[1];
    prev = q;
    c = advance(q, step);

    // check step length
    if (dot(q-prev, q-prev) < dpsq) {
      q = qbest;
      return true;
    }
  }

  // return the best result in any case
  q = qbest;
  // dbprint("Gauss-Newton projection failed:", dsqmin);
  return false;
}

bool SrfProjector::coordSearch(const Vct3 & pt, Vct2 & q) const
{
  Vct3 r( srf.eval(q[0],q[1]) - pt );
  Real dsqmin = dot(r,r);

  const Real dq = 0.125;
  Real ptol = sqrt(dpsq);
  Vct2 lo(vct(0.0,0.0)), hi(vct(1.0,1.0));

  lo[0] = std::max(0.0, q[0]-dq);
  lo[1] = std::max(0.0, q[1]-dq);
  hi[0] = std::min(1.0, q[0]+dq);
  hi[1] = std::min(1.0, q[1]+dq);

  for (int i=0; i<16; ++i) {

    detail::usearch usf(srf, pt, q[1]);
    q[0] = golden_ratio_minimum(usf, lo[0], hi[0], ptol);
    detail::vsearch vsf(srf, pt, q[0]);
    q[1] = golden_ratio_minimum(vsf, lo[1], hi[1], ptol);

    r = srf.eval(q[0], q[1]) - pt;
    Real dsq = dot(r,r);
    if (dsq < tolsq)
      return true;
    if (dsq < dsqmin) {
      lo = 0.5*(q + lo);
      hi = 0.5*(q + hi);
    } else {
      lo = 0.5*(lo + vct(0.0,0.0));
      hi = 0.5*(hi + vct(1.0,1.0));
    }
  }

  // dbprint("GR search projection failed:", dsqmin);
  return false;
}


bool SrfProjector::compassSearch(const Vct3 & pt, Vct2 & q) const
{
  // Gauss-Newton does not work, try compass search
  Real step = 1.0 / 16.0;
  Vct2 qbest(q), qt[4];

  Vct3 r( srf.eval(q[0],q[1]) - pt );
  Real dsqmin = dot(r,r);

  for (int iter=0; iter<32; ++iter) {

    // generate four trial points around q
    for (int k=0; k<4; ++k)
      qt[k] = q;
    advance(qt[0], vct(+step, 0.0));
    advance(qt[1], vct(-step, 0.0));
    advance(qt[2], vct(0.0, +step));
    advance(qt[3], vct(0.0, -step));

    // check if any of these is better than q
    bool improved = false;
    for (int k=0; k<4; ++k) {
      Real dsq = sq( srf.eval(qt[k][0], qt[k][1]) - pt );
      if (dsq < dsqmin) {
        dsqmin = dsq;
        qbest = q = qt[k];
        improved = true;
      }
    }

    // debug
    // dbprint(iter, " step ", step, " dsq ", dsqmin);

    // return if tolerance achieved
    if (dsqmin < tolsq)
      return true;

    // otherwise adapt steplength
    if (improved)
      step *= 2.0;
    else
      step *= 0.5;

    // give up if step too small
    if (step*step < dpsq)
      break;
  }

  // debug
  // Vct3 sp = srf.eval(q[0], q[1]);
  // Vct3 sn = srf.normal(q[0], q[1]);
  // dbprint("Angular optimality condition: ", deg(arg(pt-sp, sn)));

  // dbprint("Compass search projection failed:", dsqmin);
  return false;
}
