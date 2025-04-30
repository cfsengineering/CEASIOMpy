
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
 
#include <genua/pattern.h>
#include "openframe.h"
#include "wingtiparc.h"

using namespace std;

// ------------------- local scope functions ------------------------------

static Vct3 ptnormal(const PointList<3> & pts)
{
  // determine line segment center
  Vct3 ctr;
  Real slen(0);
  const uint np(pts.size());
  for (uint i=1; i<np; ++i) {
    Real len = norm(pts[i] - pts[i-1]);
    slen += len;
    ctr += 0.5*len*(pts[i] + pts[i-1]);
  }
  ctr /= slen;

  // compute normal vector
  Vct3 rnormal;
  PointList<3> rmid(np);
  for (uint i=0; i<np; ++i)
    rmid[i] = pts[i] - ctr;
  for (uint i=1; i<np; ++i)
    rnormal += cross(rmid[i-1], rmid[i]);
  normalize(rnormal);  
  return rnormal;
}

static Vct3 pfarthest(const Surface & srf, Real vpos, Real & ule)
{
  Vct3 p, root(srf.eval(0.0,vpos));
  const uint np(50);
  Real u, ulo, uhi, dst, dmax(0.0);
  for (uint i=1; i<np; ++i) {
    u = Real(i)/(np-1);
    p = srf.eval(u, vpos);
    dst = norm(p - root);
    if (dst > dmax) {
      dmax = dst;
      ulo = u - 1.0/(np-1);
      uhi = u + 1.0/(np-1);
    }
  }

  // binary search for farthest point
  Real dlo, dhi;
  ulo = max(0.0, ulo);
  uhi = min(1.0, uhi);
  u = 0.5*(ulo+uhi);
  dlo = norm(srf.eval(ulo,vpos) - root);
  dhi = norm(srf.eval(uhi,vpos) - root);
  while (fabs(uhi-ulo) > 1e-4) {
    u = 0.5*(ulo+uhi);
    p = srf.eval(u, vpos);
    dst = norm(p - root);
    if (dst > dhi and dst > dhi) {
      if (dlo > dhi) {
        uhi = u;
        dhi = dst;
      } else {
        ulo = u;
        dlo = dst;
      }
    } else if (dst > dhi) {
      uhi = u;
      dhi = dst;
    } else if (dst > dlo) {
      ulo = u;
      dlo = dst;
    } else
      break;
  }

  ule = u;
  return srf.eval(ule, vpos);
} 

//static inline bool uless(const Vct2 & a, const Vct2 & b)
//{
//  return a[0] < b[0];
//}

// -------------------- WingTipArc -----------------------------------------

void WingTipArc::initDimensions(const Surface & srf, Real vpos, Real /* s */,
                                PointList<3> & pts)
{  
  // first, extract the tip curve
  const uint np(160);
  Vector upar = cosine_pattern(np, 4*PI, 0.0, 0.7);
  pts.resize(np);
  for (uint i=0; i<np; ++i)
    pts[i] = srf.eval(upar[i], vpos);

  // find the normal direction, pointing outward into the tip arc
  vfwd = true;
  rnormal = ptnormal(pts);
  if (vpos < 0.5) {
    rnormal *= -1.0;
    vfwd = false;
  }

  // identify the 'backward' direction, pick point farthest from (0,vpos)
  Real ule;
  ple = pfarthest(srf, vpos, ule);
  back = srf.eval(0.0,vpos) - ple;
  rchord = normalize(back);

  // identify the 'upward' direction (will be downward for left tips)
  up = cross(back, rnormal);
  normalize(up);

  // leading- and trailing-edge tangents
  Vct3 tle, tte;
  tle = srf.derive(ule, vpos, 0, 1);
  if (vpos < 0.5)
    tle *= -1.0;
  tte = srf.derive(0.0, vpos, 0, 1);
  if (vpos < 0.5)
    tte *= -1.0;

  // slope angles
  alpha = arg(tle, rnormal);
  gamma = arg(tte, rnormal);

  // determine correct sign of slope angles
  alpha *= sign(dot(tle,back));
  gamma *= sign(-dot(tte,back));

  // spanwise radius of the circular tip arc
  // radius = s/(1.0 - sin(alpha));
  radius = rchord/cos(alpha);
}

void WingTipArc::scaleShift(Real sfc, Real sfh, Real db, Real y, 
                            PointList<3> & pts) const
{
  // scale and shift a point set 
  Vct3 r1, r2;
  const uint np(pts.size());
  for (uint i=0; i<np; ++i) {
    r1 = pts[i] - ple;
    r2 = sfc*dot(r1, back)*back + sfh*dot(r1, up)*up;
    pts[i] = ple + r2 + db*back + y*rnormal;
  }
}

void WingTipArc::init(const Surface & srf, Real vpos, Real s)
{
  PointList<3> pts;
  initDimensions(srf, vpos, s, pts);

  Real salpha, calpha, sbeta, cbeta;
  sincosine(alpha, salpha, calpha);
  
  // create sections through the circular tip arc
  const uint ns(16);
  CurvePtrArray cv(ns);
  Real sfc, sfh, db, v;
  for (uint i=0; i<ns; ++i) {

    // determine scaling factors for this section
    v = Real(i)/(ns-1);
//     // sfh = 0.05 + 0.95*sqrt(1.0 - sq(v));
//     beta = acos( max(-1.0, min(1.0, v*s/radius + sin(alpha))) );
//     db = radius*(cos(alpha) - sin(beta));
// 
//     sfc = 1.0 - (db + v*s*tan(gamma))/rchord;
//     sfh = sfc;

    sbeta = salpha + v*s/radius;
    cbeta = sqrt(1 - sq(sbeta));
    db = rchord*(1.0 - cbeta/calpha);
    sfh = sfc = cbeta/calpha - v*s/rchord*tan(gamma);

    // generate section points
    PointList<3> tmp(pts);
    scaleShift(sfc, sfh, db, v*s, tmp);

    // produce a spline curve from that
    OpenFrame *pc = new OpenFrame("TipArcCurve"+str(i));
    pc->init(tmp);
    cv[i] = CurvePtr(pc);
  }

  // change curve ordering if necessary
  if (not vfwd)
    std::reverse(cv.begin(), cv.end());

  // interpolate spline surface through sections
  skin.init(cv, true);
}

// void WingTipArc::seedMesh(const TriQuality & tq, PointList<2> & seed) const
// {
// /*
//   // create initial points at the extreme tip
//   const uint ninit(16);
//   PointList<2> tmp(ninit);
//   Vector up = cosine_pattern(ninit, 4*PI, 0.0, 0.7);
// 
//   if (vfwd) {
//     for (uint j=0; j<ninit; ++j)
//       tmp[j] = vct(up[j], 1.0);
//   } else {
//     for (uint j=0; j<ninit; ++j)
//       tmp[j] = vct(up[j], 0.0);
//   }
// 
//   // refine initial discretization
//   PointList<2> ins;
//   do {
//     ins.clear();
//     for (uint j=1; j<tmp.size(); ++j) {
//       const Vct2 & pa(tmp[j-1]);
//       const Vct2 & pb(tmp[j]);
//       if (tq.refine(pa, pb) == 1)
//         ins.push_back(0.5*(pa+pb));
//     }
//     tmp.insert(tmp.end(), ins.begin(), ins.end());
//     std::sort(tmp.begin(), tmp.end(), uless);
//   } while (not ins.empty());
// 
//   // extract the point pattern in u-direction
//   up.resize(tmp.size());
//   for (uint i=0; i<up.size(); ++i)
//     up[i] = tmp[i][0];
// 
//   // create a related pattern which is centered on the gaps
//   // between the values in up
//   Vector ugap(up.size()+1);
//   ugap.front() = 0.0;
//   ugap.back() = 1.0;
//   for (uint i=1; i<up.size(); ++i)
//     ugap[i] = 0.5*(up[i-1] + up[i]);
//   
//   // Now we have some seed points on the wing tip.
//   // We need to add points in a few sections very close to the tip,
//   // because the v-parametrization there is really lousy (v runs almost
//   // exactly downstream at the tip, it therefore is almost parallel to u)
//   Real t, v;
//   const uint ns(8);
//   for (uint i=0; i<ns; ++i) {
//     t = pow(Real(i+1)/ns, 2.);
//     if (vfwd)
//       v = 1.0 - t;
//     else
//       v = t;
//     if (i%2 == 1) {
//       for (uint j=0; j<up.size(); ++j)
//         tmp.push_back(vct(up[j], v));
//     } else {
//       for (uint j=0; j<ugap.size(); ++j)
//         tmp.push_back(vct(ugap[j], v));
//     }
//   }
// 
//   seed.insert(seed.end(), tmp.begin(), tmp.end());*/
// }

