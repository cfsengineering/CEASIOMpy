
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
 
#include <genua/meshfields.h>
#include <genua/triface.h>
#include "guige.h"
#include "meshcomponent.h"
#include "ttintersector.h"
#include "ttintersection.h"
#include <predicates/predicates.h>

using namespace std;

TTIntersection::TTIntersection(const TTIntersector *tti, uint t1, uint t2) : 
               itor(tti), itri1(t1), itri2(t2), nsrc(NotFound), ntrg(NotFound) 
{
  const TriFace & f1( itor->face( itri1 ) );
  const TriFace & f2( itor->face( itri2 ) );
  if (f1.mesh() > f2.mesh())
    std::swap(itri1, itri2);
}

TTIntersection::TTIntersection(const TTIntersector *tti, uint t1, uint t2,
                               const Vct3 & ps, const Vct3 & pt)
                 : isrc(ps), itrg(pt), itor(tti), itri1(t1), itri2(t2),
                   nsrc(NotFound), ntrg(NotFound), bEnforced(true)
{
  const TriFace & f1( itor->face( itri1 ) );
  const TriFace & f2( itor->face( itri2 ) );
  if (f1.mesh() > f2.mesh()) {
    std::swap(itri1, itri2);
    std::swap(isrc, itrg);
  }
}

const MeshComponent *TTIntersection::firstPatch() const
{
  const TriFace & f( itor->face( itri1 ) );
  const MeshComponent *mp = dynamic_cast<const MeshComponent*>( f.mesh() );
  assert(mp != 0);
  return mp;
}

const MeshComponent *TTIntersection::secondPatch() const
{
  const TriFace & f( itor->face( itri2 ) );
  const MeshComponent *mp = dynamic_cast<const MeshComponent*>( f.mesh() );
  assert(mp != 0);
  return mp;
}

bool TTIntersection::intersect()
{
  if (itri1 == itri2)
    return false;
 
  const TriFace & f1( itor->face( itri1 ) );
  const TriFace & f2( itor->face( itri2 ) );
  
  // assume surfaces do not self-intersect
  if (f1.mesh() == f2.mesh())
    return false;

  // never compute intersections of touching neighbors
  if (firstPatch()->isNeighbor(secondPatch()))
    return false;
  
  // must use Moeller's intersection method, which handles
  // the case of exactly matching edges gracefully
  bool bi = moeller_intersect(f1, f2, isrc, itrg);
  assert(std::isfinite(dot(isrc,isrc)));
  assert(std::isfinite(dot(itrg,itrg)));
  if (bi and norm(isrc-itrg) < 1e-14)
    return false;
  else
    return bi;
}

TTIntersection::TTiConTop
    TTIntersection::nearestConnection(const TTIntersection & a, Real & dist) const
{
  Real dss = norm(isrc - a.isrc);
  Real dst = norm(isrc - a.itrg);
  Real dts = norm(itrg - a.isrc);
  Real dtt = norm(itrg - a.itrg);
  
  Real ilen = 1.0 / std::min( length(), a.length() );
  if (dss < dst and dss < dts and dss < dtt) {
    dist = dss * ilen;
    return tti_s2s;
  } else if (dst < dss and dst < dts and dst < dtt) {
    dist = dst * ilen;
    return tti_s2t;
  } else if (dts < dss and dts < dst and dts < dtt) {
    dist = dts * ilen;
    return tti_t2s;
  } else {
    dist = dtt * ilen;
    return tti_t2t;
  }
}

Vct2 TTIntersection::uvProjection(const TriFace & f, const Vct3 & p) const
{
  Vct3 uvh = f.project(p);
  const MeshComponent *mp = dynamic_cast<const MeshComponent*>( f.mesh() );
  assert(mp != 0);
  
  const uint *vi = f.vertices();
  const Vct2 & q1 = mp->parameter(vi[0]);
  const Vct2 & q2 = mp->parameter(vi[1]);
  const Vct2 & q3 = mp->parameter(vi[2]);
  
  Real u = uvh[0];
  Real v = uvh[1];
  Real w = 1.0 - u - v;
  Vct2 q = w*q1 + u*q2 + v*q3;
  
  // limit parameter values
  q[0] = min(1.0, max(0.0, q[0]));
  q[1] = min(1.0, max(0.0, q[1]));
  return q;
}

void TTIntersection::srcParameter(Vct2 & q1, Vct2 & q2) const
{
  const TriFace & f1( itor->face( itri1 ) );
  const TriFace & f2( itor->face( itri2 ) );
  q1 = uvProjection(f1, isrc);
  q2 = uvProjection(f2, isrc);
}
    
void TTIntersection::trgParameter(Vct2 & q1, Vct2 & q2) const
{
  const TriFace & f1( itor->face( itri1 ) );
  const TriFace & f2( itor->face( itri2 ) );
  q1 = uvProjection(f1, itrg);
  q2 = uvProjection(f2, itrg);
}

void TTIntersection::srcOnBoundary(Real tol, bool & ubound, bool & vbound) const
{
  Vct2 q1, q2;
  srcParameter(q1, q2);
  if (q1[0] < tol or q1[0] > 1.0-tol or q2[0] < tol or q2[0] > 1.0-tol)
    ubound = true;
  else
    ubound = false;
  if (q1[1] < tol or q1[1] > 1.0-tol or q2[1] < tol or q2[1] > 1.0-tol)
    vbound = true;
  else
    vbound = false;
}

void TTIntersection::trgOnBoundary(Real tol, bool & ubound, bool & vbound) const
{
  Vct2 q1, q2;
  trgParameter(q1, q2);
  if (q1[0] < tol or q1[0] > 1.0-tol or q2[0] < tol or q2[0] > 1.0-tol)
    ubound = true;
  else
    ubound = false;
  if (q1[1] < tol or q1[1] > 1.0-tol or q2[1] < tol or q2[1] > 1.0-tol)
    vbound = true;
  else
    vbound = false;
}

void TTIntersection::surfaces(SurfacePtr & psf1, SurfacePtr & psf2) const
{
  const TriFace & f1( itor->face( itri1 ) );
  const MeshComponent *mp1 = dynamic_cast<const MeshComponent*>( f1.mesh() );
  psf1 = mp1->surface();
  
  const TriFace & f2( itor->face( itri2 ) );
  const MeshComponent *mp2 = dynamic_cast<const MeshComponent*>( f2.mesh() );
  psf2 = mp2->surface();
}

Real TTIntersection::intersectsFace(uint tt) const
{
  if (tt == itri1 or tt == itri2)
    return -1.0;
  
  const TriFace & ft( itor->face( tt ) );
  if (ft.mesh() == itor->face(itri1).mesh())
    return -1.0;
  if (ft.mesh() == itor->face(itri2).mesh())
    return -1.0;
  
  const uint *vi = ft.vertices();
  const TriMesh & msh( *(ft.mesh()) );
  const Vct3 & p1( msh.vertex(vi[0]) );
  const Vct3 & p2( msh.vertex(vi[1]) );
  const Vct3 & p3( msh.vertex(vi[2]) );
  
  double os = jrsOrient3d(p1, p2, p3, isrc);
  double ot = jrsOrient3d(p1, p2, p3, itrg);
  
  if ( (os*ot) >= 0.0 )
    return -1.0;

  Vct3 uvt = ft.pierce(isrc, itrg);
  Real u = uvt[0];
  Real v = uvt[1];
  Real w = 1.0 - u - v;
  if (u > 1.0 or u < 0.0)
    return -1.0;
  else if (v > 1.0 or v < 0.0)
    return -1.0;
  else if (w > 1.0 or w < 0.0)
    return -1.0;
  else
    return uvt[2];
}

TTIntersectionPtr TTIntersection::split(Real t)
{
  // new end point somewhere along the line
  Vct3 ps = (1.0-t)*isrc + t*itrg;
  
  // cout << t << " 3-surface intersection at " << ps << endl;
  
  // create new segment from ps to itrg
  TTIntersectionPtr inew(new TTIntersection(*this));
  inew->isrc = ps;
  
  // set my own itrg to ps
  itrg = ps;
  
  return inew;
}

Real TTIntersection::localDimension() const
{
  const TriFace & f1( itor->face( itri1 ) );
  const TriFace & f2( itor->face( itri2 ) );
  const uint *vi = f1.vertices();
  const TriMesh *m = f1.mesh();
  Real lmin(huge);
  lmin = min(lmin, norm(m->vertex(vi[1]) - m->vertex(vi[0])));
  lmin = min(lmin, norm(m->vertex(vi[2]) - m->vertex(vi[0])));
  lmin = min(lmin, norm(m->vertex(vi[2]) - m->vertex(vi[1])));
  
  vi = f2.vertices();
  m = f2.mesh();
  lmin = min(lmin, norm(m->vertex(vi[1]) - m->vertex(vi[0])));
  lmin = min(lmin, norm(m->vertex(vi[2]) - m->vertex(vi[0])));
  lmin = min(lmin, norm(m->vertex(vi[2]) - m->vertex(vi[1])));
  return lmin;
}

void TTIntersection::addViz(MeshFields & mvz) const
{  
  if ( not std::isfinite(sq(isrc)) )
    throw Error("Source point not finite.");
  if ( not std::isfinite(sq(itrg)) )
    throw Error("Source point not finite.");
  
  uint a = mvz.addVertex(isrc);
  uint b = mvz.addVertex(itrg);
  mvz.addLine2(a,b);
}
