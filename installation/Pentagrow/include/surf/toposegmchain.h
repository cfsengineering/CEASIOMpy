
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
 
#ifndef SURF_TOPOSEGMCHAIN_H
#define SURF_TOPOSEGMCHAIN_H

#include "forward.h"
#include "topoisecsegment.h"
#include <genua/connectmap.h>
#include <deque>

/** Chain of intersection segments.
 *
 * \ingroup meshgen
 * \sa TopoIsecSegment, Topology
 */
class TopoSegmChain
{
public:

  typedef std::deque<uint> IdxChain;
  typedef std::vector<IdxChain> IdxChainArray;

  /// create undefined intersection topology handler
  TopoSegmChain() {}

  /// compute connectivity
  uint extractTopology(const Topology &topo, Real threshold=gmepsilon);

  /// create an edge from chain k
  uint generateEdge(Topology &topo, uint k) const;

private:

  /// reduce number of points in chain without violating criteria
  //void reduce(uint k, Real lmax, Real lmin, Real cosphi);

  /// merge intersection vertices
  void mergeVertices(Real threshold);

  /// create a vertex-to-segment mapping
  int mapSegments();

  /// determine whether a vertex v on segment s is on a (u,v) boundary
  int onBoundary(uint s, uint v) const;

  /// determine (u,v) space point of vertex j on face f
  Vct2 uvlocation(uint j, uint f) const {
    ConnectMap::const_iterator itr, last = m_map.end(j);
    for (itr = m_map.begin(j); itr != last; ++itr) {
      const TopoIsecSegment &seg( m_segm[*itr] );
      if (seg.aface() == f) {
        if (j == seg.source())
          return seg.asource();
        else if (j == seg.target())
          return seg.atarget();
      } else if (seg.bface() == f) {
        if (j == seg.source())
          return seg.bsource();
        else if (j == seg.target())
          return seg.btarget();
      }
    }
    assert(!"Failed to locate point, topologically impossible.");
    return Vct2();
  }

private:

  /// intersection segments
  TopoIsecArray m_segm;

  /// final set of vertices in 3D space
  PointList<3> m_vtx;

  /// surface pair for chains
  IndexPairArray m_sfp;

  /// identified vertex chains
  IdxChainArray m_vchains;

  /// identified segment chains
  IdxChainArray m_schains;

  /// maps vertices to segment indices
  ConnectMap m_map;
};

#endif // TOPOSEGMCHAIN_H
