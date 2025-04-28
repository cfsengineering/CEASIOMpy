
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
 
#include <genua/trimesh.h>
#include <genua/meshfields.h>
#include <predicates/predicates.h>
#include "waketrace.h"

Real WakeTrace::csSharpEdge = 0.707;

WakeTrace::WakeTrace(const TriMesh & m) : msh(m)
{
  jrsExactInit();
}

void WakeTrace::addViz(MeshFields & mvz) const
{
  mvz.addLine2(pts);
}

void WakeTrace::search(uint ifirst, const Vct3 & v)
{
  // clear state 
  ifaces.clear();
  iedges.clear();
  pts.clear();
  
  // first stage: identify triangle to start with 
  Vct3 p = msh.vertex(ifirst);
  pts.push_back(p);
  
  TriMesh::nb_face_iterator itf, flast;
  flast = msh.v2fEnd(ifirst);
  for (itf = msh.v2fBegin(ifirst); itf != flast; ++itf) {
    uint eix = touched(itf.index(), p, v);
    if (eix != NotFound) {
      ifaces.push_back(itf.index());
      iedges.push_back(eix);
      pts.push_back( itspoint(p, v, itf->normal(), eix) );
      break;
    }
  }
  
  // abort if first triangle not found
  if (ifaces.empty())
    return;
  
  // continuation
  bool cont(true);
  Real ccs(1.0);
  do {
  
    cont = advance(v);
    uint n = pts.size() - 1;
    ccs = cosarg(pts[n] - pts[n-1], v);
    
  } while ( cont and ccs > 0.0 );
  
  if (ccs <= 0.0) {
    pts.pop_back();
    ifaces.pop_back();
    iedges.pop_back();
  }
  
}

uint WakeTrace::touched(uint fix, const Vct3 & prev, const Vct3 & v) const
{
  // triangle normal 
  Vct3 fn = msh.face(fix).normal();
  
  TriMesh::nb_edge_iterator ite, efirst, elast;
  efirst = msh.f2eBegin(fix);
  elast = msh.f2eEnd(fix);
  for (ite = efirst; ite != elast; ++ite) {
    if (esliced(prev, v, fn, ite.index() ) == 1) 
      return ite.index();
  } 

  return NotFound;
}

int WakeTrace::esliced(const Vct3 & p, const Vct3 & v, const Vct3 & fn,
                       uint e) const
{
  // plane is normal to fn and contains p and p+v
  Vct3 p1(p + v), p2(p1 + fn);
  const Vct3 & src( msh.vertex(msh.edge(e).source()) );
  const Vct3 & trg( msh.vertex(msh.edge(e).target()) );
   
  if ( norm(p-trg) < gmepsilon )
    return 0;
  else if ( norm(p-src) < gmepsilon )
    return 0;
  
  Real os = jrsOrient3d( p, p1, p2, src );
  Real ot = jrsOrient3d( p, p1, p2, trg );
  
  // return 
  // zero if plane touched edge end point
  // minus one if edge is completely on one side
  // one if edge intersects plane
  
  if (os == 0 or ot == 0)
    return 0;
  else if ( sign(os) == sign(ot) )
    return -1;
  else
    return 1;
}

Vct3 WakeTrace::itspoint(const Vct3 & p, const Vct3 & v, const Vct3 & fn,
                         uint e) const
{
  Vct3 pn = cross(v,fn).normalized();
  const Vct3 & src( msh.vertex(msh.edge(e).source()) );
  const Vct3 & trg( msh.vertex(msh.edge(e).target()) );
    
  // fails if edge e is aligned with v, plane parallel to edge
  Real pnd = dot( pn, trg-src );
  if ( fabs(pnd) < gmepsilon )
    return 0.5*(src+trg);
  
  Real t = dot( pn, p-src ) / pnd;
  return (1-t)*src + t*trg; 
}

bool WakeTrace::advance(const Vct3 & v)
{
  // determine next face to process
  uint fix = ifaces.back();
  uint eix = iedges.back();
  
  // stop on illegal topology
  uint edeg = msh.edegree(eix);
  if (edeg == 1)
    return false;
  else if (edeg > 2)
    throw Error("WakeTrace: Illegal edge topology (multiple connection)");
  
  // determine next face and check for sharp edge
  const uint *nbf = msh.firstFaceIndex(eix);
  uint fnext = (nbf[0] != fix) ? nbf[0] : nbf[1];
  const Vct3 fn = msh.face(fnext).normal();
  
  if (cosarg(fn,v) > csSharpEdge)
    return false;
  
  // ok, have next face to test, now check edges for wake intersection
  const uint *nbe = msh.firstEdgeIndex(fnext);
  for (int k=0; k<3; ++k) {
    if (nbe[k] == eix)
      continue;
    int esl = esliced(pts.back(), v, fn, nbe[k]);
    if (esl == 1) {
      iedges.push_back(nbe[k]);
      ifaces.push_back(fnext);
      pts.push_back(itspoint(pts.back(), v, fn, nbe[k]));
      return true;
    }
  }

  return false;
}



