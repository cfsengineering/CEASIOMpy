
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
 
#ifndef SURF_DCGEOMETRY_H
#define SURF_DCGEOMETRY_H

#include "forward.h"
#include "dcfaceset.h"
#include <genua/morton.h>
#include <genua/point.h>

/** Geometric criteria used in Delaunay triangulation.

  DcGeometry contains geometry (as opposed to topology) information needed for
  generalized constrained Delaunay triangulation. It stores (at least) the
  2-dimensional coordinates of each mesh vertex (s,t) in the, possibly metric,
  plane where the Delaunay condition is fulfilled and implements a lookup
  function locateTriangle which finds the triangle closest to some (e.g. newly
  inserted) vertex.

  Child classes can overload the criteria functions (encroaches((), etc); the
  default implementation works in the (s,t) plane.

  \ingroup meshgen
  \sa DelaunayCore
  */
class DcGeometry
{
public:

  enum Orient { Clockwise, Colinear, CounterClockwise };

  enum PointLoc { Inside,   ///< point is inside the triangle returned
                  Outside,  ///< point is outside of the domain
                  OnEdge1,  ///< point is on first edge (0-1)
                  OnEdge2,  ///< point is on second edge (1-2)
                  OnEdge3,  ///< point is on third edge (2-0)
                  OnVertex1, ///< point matches first vertex within tolerance
                  OnVertex2, ///< point matches second vertex within tolerance
                  OnVertex3, ///< point matches third vertex within tolerance
                  BeyondEdge1, ///< on the outboard side of first edge
                  BeyondEdge2, ///< on the outboard side of second edge
                  BeyondEdge3 ///< on the outboard side of third edge
                };

  enum EdgeIntersection { NoEdgeIntersection = 0,
                          EdgesIntersect,
                          EdgesTouch,
                          EdgesColinear };

  /// construct with default quantization range
  DcGeometry(Real stmin = -0.1, Real stmax = 1.1)
    : m_sqptsize(0.0), ncall(0), niter(0)
  {
    quantRange(stmin, stmax);
  }

  /// virtual destructor
  virtual ~DcGeometry() {}

  /// pre-allocate space for n vertices
  virtual void reserve(uint n);

  /// change quantization range
  void quantRange(Real stmin, Real stmax) {
    m_qoffset = stmin;
    const int nshift = 1 + sizeof(size_t) * 4;
    m_qscale = (std::numeric_limits<size_t>::max() >> nshift) / (stmax - stmin);
  }

  /// access squared min distance between points
  Real pointTolerance() const {return m_sqptsize;}

  /// set squared min distance between points
  void pointTolerance(Real sqd) {m_sqptsize = sqd;}

  /// append vertex (s-t space)
  uint stInsertVertex(const Vct2 &pst) {
    m_st.push_back(pst);
    return m_st.size()-1;
  }

  /// access s-t vertices
  const PointList<2> & stVertices() const {return m_st;}

  /// access s-t vertex
  const Vct2 & stVertex(uint k) const {return m_st[k];}

  /// access s-t vertex
  Vct2 & stVertex(uint k) {return m_st[k];}

  /// assign/copy vertex set
  void assign(const PointList<2> & pts) {m_st = pts;}

  /// evaluate whether a, b, c occur in counterclockwise order
  virtual int orientation(uint a, uint b, uint c) const;

  /// determine how the orientation changes when a is moved to pa
  int orientChanged(const uint vi[], uint a, const Vct2 &pa) const;

  /// check whether edge (as,at) intersects (bs,bt)
  virtual int edgesIntersect(uint as, uint at, uint bs, uint bt) const;

  /// add a face to triangle search data structure (empty)
  virtual void insertFace(const DelaunayCore &core, uint f);

  /// add a face to triangle search data structure
  size_t insertFace(uint f, const uint vix[]) {
    size_t key = mortonKey(vix);
    m_fmap.insert(key, f);
    return key;
  }

  /// remove face from search data structure (empty)
  virtual void eraseFace(const DelaunayCore &core, uint f);

  /// remove face from search data structure
  bool eraseFace(uint, const uint vix[]) {
    return eraseFaceKey( mortonKey(vix) );
  }

  /// given its key, erase face from map
  bool eraseFaceKey(size_t key) {
    return m_fmap.erase(key);
  }

  /// encroachment criterion
  virtual bool encroaches(const DelaunayCore &core,
                          const uint vf[], uint v) const;

  /// true if vertex encroaches ball around protected edge
  virtual bool encroachesEdge(uint src, uint trg, uint v) const;

  /// locate triangle in which to find v (empty)
  virtual int locateTriangle(const DelaunayCore &core,
                             uint v, uint &nearest)  const;

  /// recompute z-ordering of all faces following vertex smoothing pass
  void remapFaces(const DelaunayCore &core);

  /// clear out everything
  virtual void clear();

  /// planar orientation test
  static int orientationPlanar(const Vct2 & pa, const Vct2 & pb,
                               const Vct2 & pc);

  /// planar encroachment test
  static bool encroachCircle(const Vct2 & p0, const Vct2 & p1,
                             const Vct2 & p2, const Vct2 & ptest);

  /// point inside smallest ball touching ps and pt?
  template <uint ND>
  static bool encroachesBall(const SVector<ND> &ps,
                             const SVector<ND> &pt, const SVector<ND> &v)
  {
    Real dsq = sq( v - 0.5*(ps + pt) );

    // testing
    dsq = std::min(std::min(dsq, sq(v - ps)), sq(v- pt));

    return dsq < 0.25*sq(pt - ps);
  }

  // debug
  uint calls() const {return ncall;}
  uint iterations() const {return niter;}

protected:

  /// compute Morton key for center of triangle with vertices vix[]
  size_t mortonKey(const uint vix[]) const {
    assert(vix[0] < m_st.size());
    assert(vix[1] < m_st.size());
    assert(vix[2] < m_st.size());

    // profile! could be vectorized (SSE2) if hotspot
    const Vct2 & p1( m_st[vix[0]] );
    const Vct2 & p2( m_st[vix[1]] );
    const Vct2 & p3( m_st[vix[2]] );
    const Real third(1.0 / 3.0);
    const int nbits( sizeof(size_t)*4 );
    Real uc = (p1[0] + p2[0] + p3[0])*third;
    Real vc = (p1[1] + p2[1] + p3[1])*third;
    intptr_t a( (uc - m_qoffset)*m_qscale );
    intptr_t b( (vc - m_qoffset)*m_qscale );
    return interleave_bits<size_t, nbits>(a, b);
  }

  int walkEdge(const DelaunayCore &core,
               const Vct2 &pt, uint &iface) const;

protected:

  /// vertices in the definition plane
  PointList<2> m_st;

  /// keep sorted ordering of faces
  DcIndexMap m_fmap;

  /// quantization parameters
  Real m_qoffset, m_qscale;

  /// squared distance at which two points are considered identical
  Real m_sqptsize;

  /// call statistics
  mutable uint ncall, niter;
};

#endif // DCGEOMETRY_H
