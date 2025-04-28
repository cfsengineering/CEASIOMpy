
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
 
#include <cstdlib>
#include "facetree.h"

using namespace std;

FaceTree::FaceTree(const TriMesh & t) : level(0)
{
  const uint nf(t.nfaces());
  faces.resize(nf);
  idx.resize(nf);
  for (uint i=0; i<nf; ++i) {
    faces[i] = t.face(i);
    idx[i] = i;
  }
  init();
}

FaceTree::FaceTree(const FaceArray & fcs, const Indices & ix, uint lvl)
    : faces(fcs), idx(ix), level(lvl)
{
  init();
}

void FaceTree::init()
{
  assert(!idx.empty());

  // compute center and bounding box
  ctr = vct(0,0,0);
  Real fa, area(0);
  Indices fix;
  srf = faces[0].mesh();
  for (uint i=0; i<idx.size(); ++i) {
    const uint *vi( face(i).vertices() );
    fix.insert(fix.end(), vi, vi+3);
    fa = norm(face(i).normal());
    area += fa;
    ctr += fa*face(i).center();
  }
  ctr /= area;
  sort_unique(fix);
  
  Vct3 p1, p2;
  p1 = vct(huge, huge, huge);
  p2 = -1.0*p1;
  for (uint i=0; i<fix.size(); ++i) {
    const Vct3 & q(srf->vertex(fix[i]));
    for (uint k=0; k<3; ++k) {
      p1[k] = min(p1[k], q[k]);
      p2[k] = max(p2[k], q[k]);
    }
  }
  bb = BndBox(p1,p2);

  // find covariance matrix and principal directions
  Vct3 q;
  Mtx33 covar;
  for (uint i=0; i<fix.size(); ++i) {
    q = srf->vertex(fix[i]) - ctr;
    covar += dyadic(q,q);
  }

  // approximate first principal direction
  pcp = vct(1,1,1);
  for (uint i=0; i<4; i++)
    pcp = (covar*pcp).normalized();
}

bool FaceTree::isLeft(const TriFace & f) const
{
  // triangle classification
  Real pd[3];
  const uint *vi(f.vertices());
  for (uint k=0; k<3; ++k)
    pd[k] = dot( srf->vertex(vi[k]) - ctr, pcp);

  if ( (pd[0] < 0 and pd[1] < 0) or
       (pd[1] < 0 and pd[2] < 0) or
       (pd[0] < 0 and pd[2] < 0) )
    return true;
  else
    return false;
}

void FaceTree::fork()
{
  // split, create two new boxes
  if (idx.size() < 2)
    return;

  // split list
  Indices li, ri;
  for (uint i=0; i<idx.size(); ++i) {
    if (isLeft(face(i)))
      li.push_back(idx[i]);
    else
      ri.push_back(idx[i]);
  }

  // split only if both lists not empty
  if (li.size() > 0 and ri.size() > 0) {
    lft = FaceTreePtr( new FaceTree(faces, li, level+1) );
    rgt = FaceTreePtr( new FaceTree(faces, ri, level+1) );
  }
}

void FaceTree::split(uint depth, uint npmin)
{
  // recursive splitting
  fork();
  if ( (not isLeaf()) and level < depth and idx.size() > 2*npmin) {
    lft->split(depth, npmin);
    rgt->split(depth, npmin);
  }
}

void FaceTree::collectEdges(Indices & eix) const
{
  eix.clear();
  const uint nf(idx.size());
  TriMesh::nb_edge_iterator ite, efirst, elast;
  for (uint i=0; i<nf; ++i) {
    efirst = srf->f2eBegin(idx[i]);
    elast = srf->f2eEnd(idx[i]);
    for (ite = efirst; ite != elast; ++ite)
      eix.push_back(ite.index());
  }
  sort_unique(eix);
}

uint FaceTree::intersect(const FaceTree & other, FaceIsecMap & m) const
{
  uint ni(0);
  if (not bbintersects(other))
    return 0;

  // check sibling intersections
  if (not isLeaf()) {
    if (not other.isLeaf()) {
      if (lft->bbintersects(other.left()))
        ni += lft->intersect(other.left(), m);
      if (lft->bbintersects(other.right()))
        ni += lft->intersect(other.right(), m);
      if (rgt->bbintersects(other.left()))
        ni += rgt->intersect(other.left(), m);
      if (rgt->bbintersects(other.right()))
        ni += rgt->intersect(other.right(), m);
    } else {
      if (lft->bbintersects(other))
        ni += lft->intersect(other, m);
      if (rgt->bbintersects(other))
        ni += rgt->intersect(other, m);
    }
  }

  // compute intersections element by element
  else {

    // collect own and other's edges
    Indices eda, edb;
    collectEdges( eda );
    other.collectEdges( edb ); 
    
    // intersect own faces with other's edges
    uint nf = nfaces();
    uint ne = edb.size();
    for (uint i=0; i<nf; ++i) {
      for (uint j=0; j<ne; ++j) {
        EdgeFaceIsec isc(face(i), other.edge(edb[j]));
        if (isc.valid(false) and (not isc.touching(gmepsilon))) {
          m[face(i)].push_back(isc);
          ++ni;
        }
      }
    }

    // intersect other's faces with own edges
    nf = other.nfaces();
    ne = eda.size();
    for (uint i=0; i<nf; ++i) {
      for (uint j=0; j<ne; ++j) {
        EdgeFaceIsec isc(other.face(i), edge(eda[j]));
        if (isc.valid(false) and (not isc.touching(gmepsilon))) {
          m[other.face(i)].push_back(isc);
          ++ni;
        }
      }
    }
  }

  return ni;
}

uint FaceTree::selfIntersect(FaceIsecMap & m) const
{
  uint ni(0);

  // check sibling intersections
  if (not isLeaf()) {
    ni += lft->selfIntersect(m);
    ni += rgt->selfIntersect(m);
    if (lft->bbintersects(*rgt))
      ni += lft->intersect(*rgt, m);
  }

  // compute intersections element by element
  else {

    // collect own edges
    Indices eda;
    collectEdges( eda );

    // intersect own faces with own edges
    const uint *vi;
    uint s, t;
    const uint nf(nfaces());
    const uint ne(eda.size());
    for (uint i=0; i<nf; ++i) {
      vi = faces[i].vertices();
      for (uint j=0; j<ne; ++j) {
        s = edge(eda[j]).source();
        t = edge(eda[j]).target();
        if ( s == vi[0] or s == vi[1] or s == vi[2] or 
             t == vi[0] or t == vi[1] or t == vi[2] )
          continue;
        EdgeFaceIsec isc(faces[i], edge(eda[j]));
        if (isc.valid() and (not isc.touching(gmepsilon))) {
          m[faces[i]].push_back(isc);
          ++ni;
        }
      }
    }
  }

  return ni;
}

void FaceTree::intersectPlane(const Plane & pln, Indices & ifaces) const
{
  Real dp[2];
  dp[0] = pln.distance(bb.lower());
  dp[1] = pln.distance(bb.upper());
  if ((dp[0]*dp[1]) > 0.0)
    return;

  if (not isLeaf()) {
    rgt->intersectPlane(pln, ifaces);
    lft->intersectPlane(pln, ifaces);
  } else {
    ifaces.insert(ifaces.end(), idx.begin(), idx.end());
  }
}

void FaceTree::intersectPlane(const Plane & pln, SegmentArray & segments) const
{
  Real dp[2];
  dp[0] = pln.distance(bb.lower());
  dp[1] = pln.distance(bb.upper());
  if ((dp[0]*dp[1]) > 0.0)
    return;

  if (not isLeaf()) {
    rgt->intersectPlane(pln, segments);
    lft->intersectPlane(pln, segments);
  } else {
    Segment s;
    const int nf = nfaces();
    for (int i=0; i<nf; ++i) {
      if ( s.intersects(face(i), pln) ) {
        s.iface = idx[i];
        segments.push_back(s);
      }
    }
  }
}
