
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
 
#include "dnrefine.h"
#include "dnmesh.h"
#include "planesurface.h"

#include <iostream>
using namespace std;

PlaneSurface::PlaneSurface(const Vct3 &po, const Vct3 &Su, const Vct3 &Sv, const string &s)
{
  rename(s);
  init(po, Su, Sv);
}

void PlaneSurface::init(const PointList<3> & pts, Real expfactor)
{
  assert(pts.size() > 2);
  const int np = pts.size();
  
  // compute center and normal
  Vct3 ctr;
  Real lsum(0);
  for (int i=1; i<np; ++i) {
    Vct3 mid = 0.5*(pts[i-1] + pts[i]);
    Real len = norm(pts[i-1] - pts[i]);
    ctr += len*mid;
    lsum += len;
  }      
  ctr /= lsum;
  
  Vct3 tn;
  for (int i=1; i<np; ++i) {
    Vct3 r1 = pts[i-1] - ctr;
    Vct3 r2 = pts[i] - ctr;
    tn += cross(r2, r1);
  }
  normalize(tn);
  
  // u-direction is always pointing at the first point
  tu = pts[0] - ctr;
  tu -= dot(tu,tn)*tn;
  tv = cross(tn, tu);

  // determine plane origin
  org = ctr;
  Vct2 pj;
  Real umin(huge), umax(-huge);
  Real vmin(huge), vmax(-huge);
  for (int i=0; i<np; ++i) {
    project(pts[i], pj, 0.0, 0.0);
    umin = min(umin, pj[0]);
    umax = max(umax, pj[0]);
    vmin = min(vmin, pj[1]);
    vmax = max(vmax, pj[1]);
  }
  
  org += expfactor*(umin*tu + vmin*tv);
  tu *= expfactor*(umax - umin);
  tv *= expfactor*(vmax - vmin);
}

Vct3 PlaneSurface::derive(Real u, Real v, uint du, uint dv) const
{
  Vct3 t;
  if (du == 0) {
    if (dv == 0)
      return eval(u,v);
    else if (dv == 1)
      return tv;
    else
      return t;
  } else if (du == 1) {
    if (dv == 0)
      return tu;
    else
      return t;
  } else
    return t;
}

void PlaneSurface::plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const
{
  S = org + u*tu + v*tv;
  Su = tu;
  Sv = tv;
}
    
bool PlaneSurface::project(const Vct3 & pt, Vct2 & q, Real, Real) const
{
  Vct3 dst = pt - org;
  q[0] = dot(dst,tu) / sq(tu);
  q[1] = dot(dst,tv) / sq(tv);
  return true;
}

void PlaneSurface::initMesh(const DnRefineCriterion & c, DnMesh & gnr) const
{
  const int nu = min(20, max(5, int(norm(tu) / c.maxLength())));
  const int nv = min(20, max(5, int(norm(tv) / c.maxLength())));
  gnr.init(nu, nv);
}

void PlaneSurface::initGridPattern(Vector &up, Vector &vp) const
{
  up.resize(3);
  vp.resize(3);
  up[0] = vp[0] = 0.0;
  up[1] = vp[1] = 0.5;
  up[2] = vp[2] = 1.0;
}

void PlaneSurface::apply()
{
  org = RFrame::forward(org);
  tu = RFrame::forward(tu);
  tv = RFrame::forward(tv);
  RFrame::clear();
}

XmlElement PlaneSurface::toXml(bool) const
{
  XmlElement xe("PlaneSurface");
  xe["name"] = ids;
  xe["origin"] = str(org);
  xe["utangent"] = str(tu);
  xe["vtangent"] = str(tv);
  return xe;
}
    
void PlaneSurface::fromXml(const XmlElement & xe)
{
  if (xe.name() != "PlaneSurface")
    throw Error("PlaneSurface: Incompatible XML representation: "+xe.name());
  
  rename(xe.attribute("name"));
  fromString(xe.attribute("origin"), org);
  fromString(xe.attribute("utangent"), tu);
  fromString(xe.attribute("vtangent"), tv);
}
    
Surface *PlaneSurface::clone() const
{
  return new PlaneSurface(*this);
}

