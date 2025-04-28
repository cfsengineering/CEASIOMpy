
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
 
#include "dcgeometry.h"
#include "delaunaycore.h"
#include <predicates/predicates.h>
#include <genua/dbprint.h>

void DcGeometry::reserve(uint n)
{
  m_st.reserve(n);
}

int DcGeometry::orientation(uint a, uint b, uint c) const
{
  return orientationPlanar(m_st[a], m_st[b], m_st[c]);
}

int DcGeometry::orientChanged(const uint vi[], uint a, const Vct2 &pa) const
{
  if (vi[0] == a)
    return DcGeometry::orientationPlanar(pa, m_st[vi[1]], m_st[vi[2]]);
  else if (vi[1] == a)
    return DcGeometry::orientationPlanar(m_st[vi[0]], pa, m_st[vi[2]]);
  else if (vi[2] == a)
    return DcGeometry::orientationPlanar(m_st[vi[0]], m_st[vi[1]], pa);
  else
    return orientation(vi[0], vi[1], vi[2]);
}

int DcGeometry::edgesIntersect(uint as, uint at, uint bs, uint bt) const
{
  // number of vertices which are found colinear with the other edge
  int ncolin = 0;

  int obs = orientation(as, at, bs);
  int obt = orientation(as, at, bt);
  ncolin += (obs == Colinear);
  ncolin += (obt == Colinear);

  // if bs and bt are both on the same side of a, then a and b cannot
  // possibly intersect; if both flags are 0, then b is perfectly aligned
  // with a and may or may nor intersect
  if (obs == obt) {
    if (obs != Colinear)
      return NoEdgeIntersection;
    else
      return EdgesColinear;
  }

  // again, if as and at are on the same side of b, there cannot be an
  // intersection unless both are exactly on b
  int oas = orientation(bs, bt, as);
  int oat = orientation(bs, bt, at);
  ncolin += (oas == Colinear);
  ncolin += (oat == Colinear);
  if (oas == oat) {
    if (oas != Colinear)
      return NoEdgeIntersection;
    else
      return EdgesColinear;
  }

  if (ncolin == 0)
    return EdgesIntersect;
  else
    return EdgesTouch;
}

void DcGeometry::insertFace(const DelaunayCore &core, uint f)
{
  assert(core.face(f).valid());
  insertFace(f, core.face(f).vertices());
}

void DcGeometry::eraseFace(const DelaunayCore &core, uint f)
{
  assert(core.face(f).valid());
  eraseFace(f, core.face(f).vertices());
}

int DcGeometry::orientationPlanar(const Vct2 &pa, const Vct2 &pb,
                                  const Vct2 &pc)
{
  double ori = jrsOrient2d(pa, pb, pc);

  int flag = (ori < 0.0) ? DcGeometry::Clockwise :
                           ( (ori > 0.0) ? DcGeometry::CounterClockwise :
                                           DcGeometry::Colinear );

  //  int flag = DcGeometry::CounterClockwise;
  //  if (ori < 0.0)
  //    flag = DcGeometry::Clockwise;
  //  else if (ori == 0)
  //    flag = DcGeometry::Colinear;

  return flag;
}

bool DcGeometry::encroaches(const DelaunayCore &,
                            const uint vf[], uint v) const
{
  const Vct2 & p0( m_st[vf[0]] );
  const Vct2 & p1( m_st[vf[1]] );
  const Vct2 & p2( m_st[vf[2]] );
  const Vct2 & ptest( m_st[v] );
  return encroachCircle( p0, p1, p2, ptest );
}

bool DcGeometry::encroachesEdge(uint src, uint trg, uint v) const
{
  return DcGeometry::encroachesBall( m_st[src], m_st[trg], m_st[v] );
}

bool DcGeometry::encroachCircle(const Vct2 &p0, const Vct2 &p1,
                                const Vct2 &p2, const Vct2 &ptest)
{
  assert(orientationPlanar(p0,p1,p2) == CounterClockwise);

  // requires that p0, p1, p2 are in counterclockwise order
  double ict = jrsInCircle(p0, p1, p2, ptest);
  return (ict > 0.0);
}

int DcGeometry::locateTriangle(const DelaunayCore &core,
                               uint v, uint &nearest) const
{
  ++ncall;
  const Vct2 & pt( m_st[v] );
  const int nbits( sizeof(size_t)*4 );
  size_t pta( (pt[0] - m_qoffset)*m_qscale );
  size_t ptb( (pt[1] - m_qoffset)*m_qscale );
  size_t ptz = interleave_bits<size_t,nbits>(pta, ptb);

  uint iface(NotFound);
  int loc = Outside;
  DcIndexMap::iterator pos;
  pos = m_fmap.near(ptz);

  if (pos != m_fmap.end()) {

    iface = m_fmap.triangle(pos);
    while (loc == Outside and iface != NotFound)
      loc = walkEdge(core, pt, iface);

    if (loc != Outside) {
      nearest = iface;
      return loc;
    }
  }

  dbprint("Point not in domain: ", pt, " vertices: ", m_st.size());

  nearest = NotFound;
  return Outside;
}

int DcGeometry::walkEdge(const DelaunayCore &core,
                         const Vct2 &pt, uint &iface) const
{
  ++niter;
  assert(core.face(iface).valid());
  const DcFace &fci( core.face(iface) );

  // first, check whether pt matches one of the triangles vertices
  // within the merge tolerance
  const uint *tv = fci.vertices();
  for (int k=0; k<3; ++k) {
    const Vct2 &pk( m_st[tv[k]] );
    if (sq(pt - pk) <= m_sqptsize)
      return DcGeometry::OnVertex1 + k;
  }

  uint isBeyondEdge = NotFound;
  for (int k=0; k<3; ++k) {
    const uint isrc = fci.esource(k);
    const uint itrg = fci.etarget(k);
    const Vct2 & src( m_st[isrc] );
    const Vct2 & trg( m_st[itrg] );
    double ori = jrsOrient2d(src, trg, pt);
    if (ori == 0.0) {

      // point is collinear with edge end points,
      // check whether pt is between edge end points
      Real el = sq(trg - src);
      Real tel = dot(pt - src, trg - src); // / el;
      if (tel >= 0.0 and tel <= el)
        return DcGeometry::OnEdge1 + k;

      // if the point is colinear with this edge but beyond
      // the edge end points, then it will be recognized as
      // outside by one of the other (following) edge tests - if the
      // following assert fails, then that has not happened.
      assert(k < 2);

    } else if (ori < 0) {

      // pt is in clockwise order with respect to edge end points,
      // so that it must lie outside the triangle. compute the next
      // triangle to test across this edge
      DcEdge *pe = core.findEdge(isrc, itrg);
      assert(pe != 0);
      assert(pe->valid());
      uint fnext = pe->otherFace(iface);

      // if there is no triangle across the edge and the point is beyond
      // this edge, then the point is outside of the triangulated region,
      // which is indicated by the BeyondEdgeX return value
      //
      // however, if there *is* a triangle on the other side of edge k, then
      // the walk should continue there

      if (fnext == NotFound) {

        dbprint(pt," beyond edge ",k,isrc,itrg);

        if (k == 2)
          return DcGeometry::BeyondEdge1 + k;

        // if this is not the last edge tested, check the other edges first;
        // if the point is beyond them but there is a neighbor face there,
        // continue with that one
        isBeyondEdge = k;

      } else {
        iface = fnext;
        return DcGeometry::Outside;
      }
    }

    // ori > 0
    // point is in counterclockwise order wrt to edge end points, could
    // be either inside or outside -> continue checking with the next edge

  }

  // if the point is on the outboard side of one edge which does not
  // have a neighbor triangle (border edge) and on the inboard side of the
  // two other edges, flag it as beyond edge
  if (isBeyondEdge < 3)
    return DcGeometry::BeyondEdge1 + isBeyondEdge;

  // point is not on nor to the 'right' of any edge, meaning that it must
  // lie in the interior of the triangle
  return DcGeometry::Inside;
}

void DcGeometry::remapFaces(const DelaunayCore &core)
{
  m_fmap.clear();
  const int nf = core.nAllFaces();
  for (int i=0; i<nf; ++i) {
    const DcFace & f( core.face(i) );
    if (not f.valid())
      continue;
    size_t key = mortonKey( f.vertices() );
    m_fmap.insert(key, i);
  }
}

void DcGeometry::clear()
{
  m_fmap.clear();
  m_st.clear();
}
