
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
 
#include "wakesurf.h"
#include "skinsurf.h"
#include "stitchedsurf.h"
#include "symsurf.h"
#include <genua/pattern.h>
#include <genua/dbprint.h>

using namespace std;

void WakeSurf::init(SurfacePtr wng)
{
  wing = wng;

  // lifting surfaces are often symmetric
  const SymSurf *sym(0);
  sym = dynamic_cast<const SymSurf*>(wing.get());

  // determine how many spanwise wake segments are needed
  const StitchedSurf *sts(0);
  if (sym)
    sts = dynamic_cast<const StitchedSurf*>(sym->baseSurface().get());
  else
    sts = dynamic_cast<const StitchedSurf*>(wing.get());

  if (sym)
    cout << "Symmetric wing surface detected." << endl;

  if (sts != 0) {

    breakPoints = sts->breakPoints();

    // mirror break points for a mirrored wing surface
    if (sym) {
      breakPoints *= 0.5;
      const int nbp = breakPoints.size();
      Vector tmp(2*nbp-1);
      std::copy(breakPoints.begin(), breakPoints.end(), tmp.begin());
      for (int i=0; i<nbp-1; ++i) {
        tmp[nbp+i] = 1.0 - breakPoints[nbp-2-i];
      }
      tmp.swap(breakPoints);
    }

    cout << "Stitched surface, bp = " << breakPoints << endl;

    const int nseg = breakPoints.size() - 1;
    SurfaceArray segments(nseg);
    for (int i=0; i<nseg; ++i)
      segments[i] = createSegment(breakPoints, i, i+1);

    if (nseg == 1) {
      wakeGeo = segments[0];
    } else {
      StitchedSurf *swake = new StitchedSurf("WakeGeometry");
      swake->init(segments, breakPoints);
      wakeGeo.reset(swake);
    }
  } else {

    cout << "Plain wing surface." << endl;

    breakPoints.resize(2);
    breakPoints[0] = 0.0;
    breakPoints[1] = 1.0;
    wakeGeo = createSegment(breakPoints, 0, 1);
  }
}

SurfacePtr WakeSurf::createSegment(const Vector &vbreak,
                                   uint iv1, uint iv2) const
{
  assert(iv2 > iv1);

  Vector vpos, tmp;
  vpos.insert(vpos.end(), vbreak.begin()+iv1, vbreak.begin()+iv2+1);

  SkinSurfPtr psf(new SkinSurf("WakeSegment"+str(iv1)));

  // TODO : Adaptively increase number of streamwise curves until
  // tight accuracy requiremennts are met, *or* extract actual curve
  // of the wing trailing edge and try to match that exactly.

  // insert breakpoints so that a a cubic segment can be created
  const uint ncurve = 8;
  CurvePtrArray cpa;

  // create streamwise curves with zero downstream curvature
  if (vpos.size() < ncurve) {
    tmp.clear();
    interpolate_pattern(vpos, ncurve, tmp);
    tmp.swap(vpos);
  }

  const int nc = vpos.size();
  cpa.resize(nc);

  cout << "Segment " << iv1 << " vpos = " << vpos << endl;

  if (shapeFlag == Bump) {

    // use plain bump with offset
    for (int i=0; i<nc; ++i) {

      // bump coordinate
      Real fs(fwdScale), rs(rearScale), dz(0.0);
      if (bumpHeight != 0 and bumpWidth > 0) {
        Real sb = 2*(vpos[i] - bumpPos) / bumpWidth;
        if (sb > -1.0 and sb < 1.0) {
          dz = bumpHeight * sq(1.0 - sq(sb));
        }
      }

      cpa[i] = createStreamCurve(vpos[i], dz, fs, rs);
    }

  } else if (shapeFlag == Interpolate) {

    for (int i=0; i<nc; ++i) {
      Real bf = bumpFactor(vpos[i]);
      if (bf <= 0.0) {
        cpa[i] = createStreamCurveZC(vpos[i]);
      } else {
        Vct3 pShift = wing->eval(0.0, vpos[i]) - wing->eval(0.0, bumpPos);
        CurvePtr ca = createStreamCurveZC(vpos[i]);
        CurvePtr cb = createStreamCurve(vpos[i], bumpPoint+pShift);
        cpa[i] = blendCurve(*ca, *cb, bf);
      }
    }

  } else {
    // plain wake, no extras
    for (int i=0; i<nc; ++i)
      cpa[i] = createStreamCurveZC(vpos[i]);
  }

  psf->init(cpa, true, true);

  return psf;
}

CurvePtr WakeSurf::createStreamCurve(Real v, Real zShift,
                                     Real fScale, Real rScale) const
{
  assert(wing);

  // compute wing trailing edge point and local wake normal direction
  Vct3 bp[4], wt, z, S, Su, Sv;
  wing->plane(0.0, v, S, Su, Sv);
  bp[0] = 0.5*S;
  z = cross(Su,Sv).normalized();
  wt = -Su;
  wing->plane(1.0, v, S, Su, Sv);
  bp[0] += 0.5*S;
  z -= cross(Su,Sv).normalized();
  z *= zShift / norm(z);
  wt += Su;
  normalize(wt);

  // determine downstream wake point
  Real wlen = norm(farTangent);
  bp[3] = bp[0] + farTangent + z;

  // wake tangent at wing trailing edge
  Vct3 ft = wt * wlen * fScale/3.0;
  bp[1] = bp[0] + ft;

  // wake tangent at downstream edge
  Vct3 rt = farTangent * rScale/3.0;
  bp[2] = bp[3] - rt;

  //  // debug
  //  dbprint("StreamCurve at v =", v);
  //  for (int i=0; i<4; ++i)
  //    dbprint("bp ", bp[i]);

  // create Bezier curve
  CurvePtr bez(new Curve("StreamwiseWakeCurve"));
  bez->bezier(bp);
  return bez;
}

CurvePtr WakeSurf::createStreamCurveZC(Real v) const
{
  assert(wing);

  const Real fScale = fwdScale;
  const Real rScale = rearScale;

  // compute wing trailing edge point and local wake normal direction
  Vct3 bp[4], wt, S, Su, Sv;
  wing->plane(0.0, v, S, Su, Sv);
  bp[0] = 0.5*S;
  wt = -Su;
  wing->plane(1.0, v, S, Su, Sv);
  bp[0] += 0.5*S;
  wt += Su;
  normalize(wt);

  // wake tangent at wing trailing edge
  Real wlen = norm(farTangent);
  Vct3 ft = wt * wlen * fScale/3.0;
  bp[1] = bp[0] + ft;

  // determine downstream wake points using zero curvature condition
  Vct3 rt = farTangent * rScale/3.0;
  bp[2] = bp[1] + rt;
  bp[3] = bp[1] + 2.0*rt;

  // create Bezier curve
  CurvePtr bez(new Curve("StreamwiseWakeCurve"));
  bez->bezier(bp);

  cout << "ZC last bp dist " << norm(bp[3] - bp[0])
       << " c(1)-c(0) " << norm(bez->eval(1) - bez->eval(0)) << endl;

  return bez;
}

CurvePtr WakeSurf::createStreamCurve(Real v, const Vct3 & Pip) const
{
  assert(wing);

  const Real fScale = fwdScale;
  const Real rScale = rearScale;

  // construct curve from two Bezier segments, i.e. seven control points
  PointList<3> cp(7);

  // compute wing trailing edge point and local wake tangent direction
  Vct3 S, Su, Sv, tng;
  wing->plane(0.0, v, S, Su, Sv);
  cp[0] = 0.5*S;
  tng = -Su;
  wing->plane(1.0, v, S, Su, Sv);
  cp[0] += 0.5*S;
  tng += Su;
  normalize(tng);

  Real d1 = norm(Pip - cp[0]) / 3.0;
  cp[1] = cp[0] + fScale*d1*tng;

  Vct3 nft = farTangent;
  Real wlen = normalize(nft);
  cp[2] = Pip - rScale*d1*nft;
  cp[3] = Pip;

  Real d2 = (wlen - 3*d1) / 3.0;
  cp[4] = Pip + 1*d2*nft;
  cp[5] = Pip + 2*d2*nft;
  cp[6] = Pip + 3*d2*nft;

  // approximate streamwise parameter at Pip
  Real ti = dot(Pip - cp[0], farTangent) / sq(farTangent);
  ti = clamp(ti, 0.0, 1.0);

  Vector knots(11);
  knots[0] = knots[1] = knots[2] = knots[3] = 0.0;
  knots[4] = knots[5] = knots[6] = ti;
  knots[7] = knots[8] = knots[9] = knots[10] = 1.0;

  cout << "IP knots: " << knots << endl;


  CurvePtr civ(new Curve("StreamwiseWakeCurve"));
  civ->initSpline(knots, cp);

  cout << "IP last cp dist " << norm(cp.back() - cp.front())
       << " c(1)-c(0) " << norm(civ->eval(1) - civ->eval(0)) << endl;

  return civ;



  /* solution which just interpolates point and tangents

  const Real fScale = fwdScale;
  const Real rScale = rearScale;

  // interpolated points and curve tangents
  PointList<3> pts(4), tng(4);

  // compute wing trailing edge point and local wake tangent direction
  Vct3 S, Su, Sv;
  wing->plane(0.0, v, S, Su, Sv);
  pts[0] = 0.5*S;
  tng[0] = -Su;
  wing->plane(1.0, v, S, Su, Sv);
  pts[0] += 0.5*S;
  tng[0] += Su;
  normalize(tng[0]);

  // wake tangent at wing trailing edge
  Real wlen = norm(farTangent);
  tng[0] *= wlen * fScale;

  // interpolation condition
  Vct3 rt = farTangent * rScale;

  // approximate streamwise parameter at Pip
  Real ti = dot(Pip - pts[0], farTangent) / sq(farTangent);
  ti = clamp(ti, 0.0, 1.0);

  pts[1] = Pip;
  tng[1] = farTangent * ( (1.0-ti)*fScale + ti*rScale );

  pts[3] = Pip + (1.0 - ti)*farTangent;
  tng[3] = rt;

  pts[2] = 0.5*(pts[1] + pts[3]);
  tng[2] = 0.5*(tng[1] + tng[3]);

  // do not prescribe parameterization yet
  Vector up;

  CurvePtr civ(new Curve("StreamwiseWakeCurve"));
  civ->interpolate(pts, tng, up);
  return civ;

  */

  //  Real ti = dot(Pip - pts[0], farTangent) / sq(farTangent);
  //  ti = clamp(ti, 0.0, 1.0);
  // bp[3] = Pip - cb(1-ti)*bp[0] - 3*ti*sq(1-ti)*bp[1] + (1-ti)*sq(ti)*rt;
  // bp[3] /= 3*(1-ti)*sq(ti) + cb(ti);

  // determine downstream wake points using zero curvature condition
  // bp[2] = bp[3] - rt/3.0;

  // create Bezier curve
  // CurvePtr bez(new Curve("StreamwiseWakeCurve"));
  // bez->bezier(bp);
  // return bez;
}

void WakeSurf::paramap(const Vector &vwing, Vector &vwake, Real tol) const
{
  assert(wing);
  assert(wakeGeo);

  const int np = vwing.size();
  vwake = vwing;

  for (int i=0; i<np; ++i) {

    // determine target point on wing
    Real v = vwing[i];
    Vct3 P = wing->eval(0.0, v);

    // compute actual point with current estimate for v
    for (int k=0; k<8; ++k) {

      Vct3 S, Su, Sv;
      wakeGeo->plane(0.0, v, S, Su, Sv);
      Vct3 r = S - P;
      Real dsq = sq(r);
      if (dsq < sq(tol))
        break;

      Real rdv = dot(r, Sv);

      // give up when change of distance with v is
      // normal to the current distance - no point in trying
      if (rdv < gmepsilon)
        break;

      // backtracking
      Real alpha = 1.0;
      Real vt = v - alpha * dsq / rdv;
      for (int ka=1; ka<4; ++ka) {
        Real dt = sq( wakeGeo->eval(0.0,vt) - P );
        if (dt < dsq)
          break;
        alpha *= 0.5;
        vt = v - alpha * dsq / rdv;
      }
      v = vt;
    }

    vwake[i] = v;
  }
}

CurvePtr WakeSurf::blendCurve(const AbstractCurve &ca,
                              const AbstractCurve &cb, Real t, uint np) const
{
  PointList<3> pts(np), tng(np);
  Vct3 S, St;
  Vector up = equi_pattern(np);
  for (uint i=0; i<np; ++i) {
    ca.tgline(up[i], S, St);
    pts[i] = (1.0 - t)*S;
    tng[i] = (1.0 - t)*St;
    cb.tgline(up[i], S, St);
    pts[i] += t*S;
    tng[i] += t*St;
  }

  CurvePtr bcp(new Curve("BlendedCurve"));
  // bcp->interpolate(pts, tng, up);
  bcp->interpolate(pts, up);
  return bcp;
}

XmlElement WakeSurf::toXml(bool) const
{
  XmlElement xe("WakeSurf");
  return xe;
}

void WakeSurf::fromXml(const XmlElement&)
{
  throw Error("XML i/o for WakeSurf not implemented.");
}



