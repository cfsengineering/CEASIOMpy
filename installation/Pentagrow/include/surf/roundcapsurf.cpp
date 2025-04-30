
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
#include <genua/plane.h>
#include <genua/trimesh.h>
#include "dnmesh.h"
#include "roundcapsurf.h"

using namespace std;

RoundCapSurf::RoundCapSurf(const PointList<3> & bp, Real elv)
  : Surface("RoundCapSurf")
{
  init(bp, elv);
}

void RoundCapSurf::init(const PointList<3> & bp, Real elv)
{
  assert(bp.size() > 2);
  elevation = elv;
  pts = bp;

  // fix direction of parametrization
  if (elv > 0)
    std::reverse(pts.begin(), pts.end());
  
  const uint np(pts.size());
  // compute center and arclength parametrization
  Real lsum(0);
  useg.resize(np);
  for (uint i=1; i<np; ++i) {
    Vct3 mid = 0.5*(pts[i-1] + pts[i]);
    Real len = norm(pts[i-1] - pts[i]);
    ctr += len*mid;
    lsum += len;
    useg[i] = useg[i-1] + len;
  }      
  ctr /= lsum;
  useg /= lsum;
  
  // reference normal direction
  Vct3 tn;
  for (uint i=1; i<pts.size(); ++i) {
    Vct3 r1 = pts[i-1] - ctr;
    Vct3 r2 = pts[i] - ctr;
    tn += cross(r2, r1);
  }
  
  // radius values
  rmean = 0.0;
  radius.resize(pts.size());
  for (uint i=0; i<pts.size(); ++i) {
    radius[i] = pts[i] - ctr;
    rmean += norm(radius[i]);
  }
  rmean /= radius.size();
  
  // construct plane through points
  Plane pln;
  nrm = pln.fitNormal(ctr, pts);

  // scale normal according to elevation
  Real nsm = -sign(dot(nrm, tn));
  nrm *= nsm*fabs(elv)*rmean / norm(nrm);
}

Vct3 RoundCapSurf::eval(Real u, Real v) const
{
  assert(u >= 0 and u <= 1);
  assert(v >= 0 and v <= 1);
  
  uint i = segment(v);
  Real t = (v - useg[i]) / (useg[i+1] - useg[i]);
  Vct3 a = (1-t)*radius[i] + t*radius[i+1];
  Real w = sqrt(1.0 - sq(u));
  return ctr + u*a + w*nrm;
}

Vct3 RoundCapSurf::derive(Real u, Real v, uint du, uint dv) const
{
  if (du == 0 and dv == 0)
    return eval(u,v);
  else if (du == 0 and dv == 1) {
    uint i = segment(v);
    Real dtdu = 1./(useg[i+1] - useg[i]);
    Vct3 dadu = dtdu*(radius[i+1] - radius[i]);
    return u*dadu;
  } else if (du == 1 and dv == 0) {
    uint i = segment(v);
    Real t = (v - useg[i]) / (useg[i+1] - useg[i]);
    Vct3 a = (1-t)*radius[i] + t*radius[i+1];
    Real dwdv = -u/sqrt(1.1-sq(u));
    return a + dwdv*nrm;
  } else
    throw Error("RoundCapSurf: Higher order derivatives not implemented.");
}
    
uint RoundCapSurf::segment(Real u) const
{
  assert(useg.size() > 2);
  if (u < useg[1])
    return 0;
  if (u >= useg.back())
    return useg.size()-2;
    
  Vector::const_iterator pos;
  pos = std::lower_bound(useg.begin(), useg.end(), u);
  return std::min(useg.size()-2, size_t(std::distance(useg.begin(), pos)));
}

void RoundCapSurf::initMesh(const DnRefineCriterion &, DnMesh & gnr) const
{
//  const int n = max(4, int(useg.size() / (2*PI)));
//  gnr.init( equi_pattern(n), useg );

  Vector vbase = useg;
  Vector ubase = expand_pattern(useg.size()/2, 1.1);
  
//   const int nu = ubase.size();
//   const int nv = vbase.size();
//   PointGrid<2> qgrid(nu, nv);
//   for (int j=0; j<nv; ++j)
//     for (int i=0; i<nu; ++i)
//       qgrid(i,j) = vct(ubase[i], vbase[j]);
  
  gnr.init(ubase, vbase);
  //gnr.cleanup(gmepsilon, 1.0);  
}

void RoundCapSurf::merge(uint n, TriMesh & tmerge) const
{
  Vector up( equi_pattern(n) );
  PointGrid<3> pgrid(n, useg.size());
  for (uint j=0; j<useg.size(); ++j) {
    for (uint i=0; i<n-1; ++i) 
      pgrid(i,j) = eval(up[i], useg[j]);
    pgrid(n-1, j) = pts[j];
  }
  
  TriMesh tmp;
  tmp.triangulate(pgrid);
  // tmp.cleanup(0.5*tmp.shortestEdgeLength());
  
  // debug 
  // clog << "RCAP GRID:" << endl << pgrid << endl;
  // tmp.toXml().write( str(int(1000*ctr[0])) + "rcap.xml");
  
  tmerge.merge(tmp);
}

void RoundCapSurf::merge(const Vct3 & nref, uint n, TriMesh & tmerge) const
{
  Vector up( equi_pattern(n) );
  PointGrid<3> pgrid(n, useg.size());
  for (uint j=0; j<useg.size(); ++j) {
    for (uint i=0; i<n-1; ++i) 
      pgrid(i,j) = eval(up[i], useg[j]);
    pgrid(n-1, j) = pts[j];
  }
  
  TriMesh tmp;
  tmp.triangulate(pgrid);
  tmp.cleanup(0.5*tmp.shortestEdgeLength());
  
  if ( dot(nref,tmp.face(0).normal()) < 0 )
    tmp.reverse();
  
  tmerge.merge(tmp);
}

Triangulation RoundCapSurf::mesh(uint n) const
{
  Vector up = equi_pattern(n);
  PointGrid<3> pg(n, useg.size());
  for (uint i=0; i<n; ++i) {
    for (uint j=0; j<useg.size(); ++j) {
      pg(i,j) = eval(up[i], useg[j]);
    }
  }
  
  Triangulation tg;
  tg.triangulate(pg);
  tg.fixate();
  
  return tg;
}

void RoundCapSurf::apply()
{
  ctr = RFrame::forward(ctr);
  nrm = RFrame::forward(nrm);
  for (uint i=0; i<radius.size(); ++i)
    radius[i] = RFrame::forward(radius[i]);
  RFrame::clear();
}

XmlElement RoundCapSurf::toXml(bool) const
{
  XmlElement xe;
  return xe;  
}
    
void RoundCapSurf::fromXml(const XmlElement &)
{}

PointList<2> RoundCapSurf::boundary() const
{
  uint n = useg.size();
  PointList<2> bpts(n+11);
  for (uint i=0; i<5; ++i)
    bpts[i] = vct(0.2*i, 0.0);
  for (uint i=0; i<useg.size(); ++i)
    bpts[5+i] = vct(1.0, useg[i]);
  for (uint i=0; i<5; ++i)
    bpts[n+5+i] = vct(0.8-0.2*i, 1.0);
  bpts.back() = bpts.front();
  return bpts;
}

void RoundCapSurf::mgLimits(Real & lmax, Real & phimax) const
{
  Real ds;
  lmax = 0.0;
  phimax = min(PI/3.0, max(0.2*PI, PI/useg.size()));
  for (uint i=1; i<useg.size(); ++i) {
    ds = norm(eval(1.0, useg[i]) - eval(1.0, useg[i-1]));
    lmax = max(lmax, ds);
  }
}

