
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
 
// Morton-ordered 2-dimensional triangle set.

#ifndef GENUA_TRISET_H
#define GENUA_TRISET_H

#include "morton.h"
#include "point.h"
#include <boost/intrusive/set.hpp>
#include <boost/intrusive/link_mode.hpp>
#include <boost/pool/pool.hpp>

class MxMesh;

namespace bin = boost::intrusive;

/** Triangles sorted by Morton ordering.

  TriSet stores a set of triangles sorted by the Morton code of their
  quantized center coordinates. Triangle indices are stored in tree-based
  containers ordered by Morton codes, which makes lookup, inserting and erasing
  efficient (amortized constant complexity). However, point lookup will only
  return the triangles whose center has the next lower and next higher
  Morton code. To find the triangle nearest to a point, a second search
  step using topological information is required.

  TriSet could be extended to triangles in more than 2 dimensions, but that
  may not be very useful because triangles which are near in 3D space may no
  longer be nearby topologically, making the second search stage inefficient.

  \sa MortonLess
  */
class TriSet
{
private:

  typedef bin::set_base_hook< bin::link_mode< boost::intrusive::normal_link >,
                              bin::optimize_size<true> > SetBase;

  typedef SVector<2,uint> QiPoint;

  class Node : public SetBase
  {
  public:

    /// construct triangle node
    Node(const QiPoint & pc, uint idx) : ctr(pc), ix(idx) {}
    // Node(const QiPoint & pc, uint idx) : zcode( encodeMorton(pc[0], pc[1]) ), ix(idx) {}

    /// access index
    uint index() const {return ix;}

    /// defines a triangle ordering
    bool operator< (const Node & a) const {
      MortonLess<uint,2> iless;
      return iless(ctr.pointer(), a.ctr.pointer());
//      return zcode < a.zcode;
    }

    /// triangle center / center of bounding box
    QiPoint ctr;

    // morton code for triangle center
    //uint zcode;

    /// triangle index
    uint ix;
  };

  class NodePtCompare {
  public:

    /// compare point and triangle
    bool operator() (const QiPoint & p, const Node & a) const {
      MortonLess<uint,2> iless;
      return iless(p.pointer(), a.ctr.pointer());
    }

    /// compare point and triangle
    bool operator() (const Node & a, const QiPoint & p) const {
      MortonLess<uint,2> iless;
      return iless(a.ctr.pointer(), p.pointer());
    }

//    /// compare point and triangle
//    bool operator() (const uint & pz, const Node & a) const {
//      return pz < a.zcode;
//    }

//    /// compare point and triangle
//    bool operator() (const Node & a, const uint & pz) const {
//      return a.zcode < pz;
//    }

  };

  typedef bin::set<TriSet::Node, bin::constant_time_size<false> > NodeSet;

public:

  typedef NodeSet::const_iterator const_iterator;

  /// empty set with default quantization range
  TriSet(Real qmin=0.0, Real qmax=1.0) : nodePool(sizeof(TriSet::Node))
  {
    qrange(qmin, qmax);
  }

  /// modify quantization range
  void qrange(Real qmin, Real qmax);

  /// fit quantization range to points present in pts
  void qrange(const PointList<2> & pts);

  /// insert a single triangle
  void insert(const PointList<2> & vtx, const uint v[], uint k) {
    Node *pn = construct(vtx, v, k);
    nodes.insert( *pn );
  }

  /// rebuild set from all triangles in tri
  void assign(const PointList<2> & vtx, const Indices & tri);

  /// erase a triangle from set
  void erase(const PointList<2> & vtx, const uint v[], uint k) {
    Node ni(triangleCenter(vtx,v), k);
    NodeSet::iterator pos = nodes.find(ni);
    if (pos != nodes.end())
      nodes.erase(pos);
  }

  /// find triangle index nearest to point p
  bool nearest(const Vct2 & p, uint & iLower, uint & iUpper) const {
    QiPoint qi( quant(p) );
    // uint pz = encodeMorton(qi[0], qi[1]);
    NodeSet::const_iterator lpos, upos;
    lpos = nodes.lower_bound(qi, NodePtCompare());
    // lpos = nodes.lower_bound(pz, NodePtCompare());
    iLower = (lpos == nodes.end()) ? NotFound : lpos->index();
    upos = nodes.upper_bound(qi, NodePtCompare());
    // upos = nodes.upper_bound(pz, NodePtCompare());
    iUpper = (upos == nodes.end()) ? NotFound : upos->index();
    return (iLower != NotFound) or (iUpper != NotFound);
  }

  /// search lower bound
  const_iterator lowerBound(const Vct2 & p) const {
    QiPoint qi( quant(p) );
    // uint pz = encodeMorton(qi[0], qi[1]);
    // return nodes.lower_bound( pz, NodePtCompare() );
    return nodes.lower_bound( qi, NodePtCompare() );
  }

  /// search for upper bound
  const_iterator upperBound(const Vct2 & p) const {
    QiPoint qi( quant(p) );
    // uint pz = encodeMorton(qi[0], qi[1]);
    // return nodes.upper_bound( pz, NodePtCompare() );
    return nodes.upper_bound( qi, NodePtCompare() );
  }

  /// iterator access
  const_iterator begin() const { return nodes.begin(); }

  /// iterator access
  const_iterator end() const { return nodes.end(); }

  /// retrieve triangle index from iterator
  uint triangle(const_iterator itr) const {
    return itr->index();
  }

  /// visualize ordering for testing
  void toMx(MxMesh & mx) const;

  /// clear set
  void clear();

private:

  /// construct a node
  Node *construct(const PointList<2> & vtx, const uint v[], uint idx) {
    Node *ptr = (Node *) nodePool.malloc();
    assert(ptr != 0);
    QiPoint ctr = triangleCenter(vtx, v);
    return (new(ptr) Node(ctr, idx));
  }

  /// point quantization
  QiPoint quant(const Vct2 & p) const {
    QiPoint q;
    q[0] = (int) ((p[0] - qoff) * qscal);
    q[1] = (int) ((p[1] - qoff) * qscal);
    return q;
  }

  /// reverse point quantization
  Vct2 rquant(const QiPoint & q) const {
    Vct2 p;
    p[0] = Real(q[0]) / qscal + qoff;
    p[1] = Real(q[1]) / qscal + qoff;
    return p;
  }

  /// triangle center
  QiPoint triangleCenter(const PointList<2> & vtx, const uint v[]) const
  {
    Vct2 p;
    for (int k=0; k<3; ++k)
      p += vtx[v[k]];
    return quant(p * 0.333333333333333);
  }

private:

  /// node allocator
  boost::pool<> nodePool;

  /// sorted container for nodes
  NodeSet nodes;

  /// quantization offset and scaling
  Real qoff, qscal;
};

#endif // TRISET_H
