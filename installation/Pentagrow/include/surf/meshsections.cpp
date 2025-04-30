
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
#include <genua/plane.h>
#include <genua/meshfields.h>
#include "guige.h"
#include "meshsections.h"

using namespace std;

MeshSections::MeshSections(const TriMesh & m) : msh(m), ftree(m)
{
  ftree.split(16, 4);
  bb.findBbox(msh.vertices());
}

void MeshSections::triangleFromPlane(const Plane & pln)
{
  Vct3 ppl = pln.project(bb.lower());
  Vct3 ppu = pln.project(bb.upper());
  Vct3 ctr = 0.5*(ppl + ppu);
  Real r = norm(ppu-ppl);
  
  Vct3 d1 = (ppl-ctr).normalized();
  Vct3 d2 = cross(pln.vector(), d1).normalized();
    
  Real c, s;
  sincosine(PI/6., s, c);
  ptri[0] = ctr + r*(c*d1 - s*d2);
  ptri[1] = ctr + r*d2;
  ptri[2] = ctr + r*(-c*d1 - s*d2);
}

bool MeshSections::fintersect(uint ti, Vct3 & ps, Vct3 & pt) const
{
  const uint *vi = msh.face(ti).vertices();
  const Vct3 & q1( msh.vertex(vi[0]) );
  const Vct3 & q2( msh.vertex(vi[1]) );
  const Vct3 & q3( msh.vertex(vi[2]) );
  
  Vct3 isrc, itrg;
  int r, coplanar(0);
  r = tri_tri_intersection_test_3d(ptri[0].pointer(), ptri[1].pointer(), 
                                   ptri[2].pointer(), q1.pointer(), 
                                   q2.pointer(), q3.pointer(),
                                   &coplanar, ps.pointer(), pt.pointer());
  return (r != 0 and coplanar != 1); 
}

uint MeshSections::findPolygons(const Plane & pln)
{
  // locate intersection candidate triangles
  Indices tix;
  ftree.intersectPlane(pln, tix);
  sort(tix.begin(), tix.end());
  
  // construct single enclosing triangle
  triangleFromPlane(pln);

  // find first intersecting triangle
  Vct3 pnext;
  pgs.clear();
  uint fcur = newPolygon(tix);
  while (fcur != NotFound and (not tix.empty())) {
    PointList<3> & pgc( pgs.back() );
    uint fnext = nextTriangle(fcur, tix, pgc.back(), pnext);
    if (fnext != NotFound) {
      pgc.push_back(pnext);
      fcur = tix[fnext];
      tix.erase(tix.begin()+fnext);
    } else {
      
      // cout << "Completed polygon: " << endl << pgc << endl;
      
      fcur = newPolygon(tix);
    }
  }
  
  return pgs.size();
}

uint MeshSections::newPolygon(Indices & tix)
{
  if (tix.empty())
    return NotFound;
  
  Vct3 ps, pt;
  uint fcur(NotFound);
  while (fcur == NotFound and (not tix.empty())) {
    fcur = tix.back();
    tix.pop_back();
    if (not fintersect(fcur, ps, pt)) 
      fcur = NotFound;
  }
  
  if (fcur != NotFound) {
    PointList<3> pg(2);
    pg[0] = ps;
    pg[1] = pt;
    pgs.push_back(pg);
  }
  
  return fcur;
}

uint MeshSections::nextTriangle(uint ti, Indices & tix, 
                                const Vct3 & plast, Vct3 & pnext) const
{
  // determine neighbors
  Indices::iterator pos;
  TriMesh::nb_edge_iterator ite, elast;
  TriMesh::nb_face_iterator itf, flast;
  elast = msh.f2eEnd(ti);
  
  Vct3 ps, pt, pc;
  Real ds, dt, dn, dmin(huge);
  uint tibest(NotFound);
  for (ite = msh.f2eBegin(ti); ite != elast; ++ite) {
    uint ei = ite.index();
    flast = msh.e2fEnd(ei);
    for (itf = msh.e2fBegin(ei); itf != flast; ++itf) {
      uint fi = itf.index();
      if (fi != ti) {
        pos = lower_bound(tix.begin(), tix.end(), fi);
        if (pos != tix.end() and *pos == fi) {
          if (fintersect(fi, ps, pt)) {
            ds = norm(ps - plast);
            dt = norm(pt - plast);
            dn = min(ds, dt);
            if (dn < dmin) {
              dmin = dn;
              pnext = (ds < dt) ? pt : ps;
              tibest = fi;
            }
          } else {
            tix.erase(pos);
          }
        }
      }
    }
  }
  
  if (tibest == NotFound)
    return NotFound;
  
  pos = lower_bound(tix.begin(), tix.end(), tibest);
  assert(pos != tix.end() and *pos == tibest);
  return distance(tix.begin(), pos);
}

Real MeshSections::area(const Plane & pln) const
{
  Real asum(0.0), apg(0.0);
  Vct3 pn( pln.vector() );
  const int npg = pgs.size();
  for (int j=0; j<npg; ++j) {
    const PointList<3> & pts(pgs[j]);
    const int np = pts.size();
    apg = 0.0;
    for (int i=1; i<np; ++i) 
      apg += dot( pn, cross(pts[i-1]-ptri[0], pts[i]-ptri[0]) );
    asum += fabs(apg);
  }
  return 0.5*asum;
}

void MeshSections::addViz(MeshFields & mvz) const
{
  uint v[3];
  for (int k=0; k<3; ++k)
    v[k] = mvz.addVertex(ptri[k]);
  mvz.addTri3(v[0], v[1], v[2]);
  for (uint i=0; i<pgs.size(); ++i)
    mvz.addLine2(pgs[i]);
}

void MeshSections::areaDistribution(Real alpha, int n, Matrix & xa)
{
  // determine plane normal vector
  Real sina, cosa;
  sincosine(alpha, sina, cosa);
  
  Vct3 pn;
  pn[0] = cosa;
  pn[1] = 0.0;
  pn[2] = sina;
  
  // limits for plane motion
  Real dlo = dot(pn, bb.lower());
  Real dhi = dot(pn, bb.upper());
  Real shift = 0.02*(dhi - dlo);
  dlo -= shift;
  dhi += shift;  
  
  // compute slices and store area in xa
  xa.resize(n, 2);
  for (int i=0; i<n; ++i) {
    
    Real t = Real(i) / (n-1);
    Real xcut = (1.0-t)*dlo + t*dhi;
    Plane pln(pn, xcut);
  
    findPolygons(pln);
    xa(i,0) = xcut;
    xa(i,1) = area(pln);
  }
}

void MeshSections::writePlain(std::ostream & os) const
{
  const int nsec = pgs.size();
  for (int j=0; j<nsec; ++j) {
    os << endl;
    const int np = pgs[j].size();
    for (int i=0; i<np; ++i)
      os << pgs[j][i] << endl;
  }
}

void MeshSections::joinPolygons(Real tol)
{
  const int npg = pgs.size();
  if (npg < 2)
    return;

  PointList<3> psum;
  Indices iused(1);
  uint nmax(0);
  for (int i=0; i<npg; ++i) {
    uint n = pgs[i].size();
    if (n > nmax) {
      iused[0] = i;
      nmax = n;
    }
  }
  psum = pgs[iused[0]];

  while (iused.size() < uint(npg)) {
    Real dst, dmin = huge;
    int ibest(npg), imode(0);
    for (int i=0; i<npg; ++i) {
      if (binary_search(iused.begin(), iused.end(),uint(i)))
        continue;
      dst = norm(psum.front() - pgs[i].front());
      if (dst < dmin) {
        dmin = dst;
        ibest = i;
        imode = 0;
      }
      dst = norm(psum.front() - pgs[i].back());
      if (dst < dmin) {
        dmin = dst;
        ibest = i;
        imode = 1;
      }
      dst = norm(psum.back() - pgs[i].front());
      if (dst < dmin) {
        dmin = dst;
        ibest = i;
        imode = 2;
      }
      dst = norm(psum.back() - pgs[i].back());
      if (dst < dmin) {
        dmin = dst;
        ibest = i;
        imode = 3;
      }
    }
    assert(ibest != npg);
    insert_once(iused, uint(ibest));
    PointList<3> tmp(pgs[ibest]);
    if (imode == 0 or imode == 3)
      reverse(tmp.begin(), tmp.end());
    if (imode < 2)
      psum.insert(psum.begin(), tmp.begin(), tmp.end());
    else
      psum.insert(psum.end(), tmp.begin(), tmp.end());
  }
  pgs.resize(1);
  pgs[0].resize(1);
  pgs[0][0] = psum[0];
  const int np = psum.size();
  for (int i=1; i<np-1; ++i) {
    if (norm(psum[i] - pgs[0].back()) > tol)
      pgs[0].push_back(psum[i]);
  }
  pgs[0].push_back(psum.back());
}



