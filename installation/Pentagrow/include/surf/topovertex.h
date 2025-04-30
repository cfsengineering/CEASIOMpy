
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
 
#ifndef SURF_TOPOVERTEX_H
#define SURF_TOPOVERTEX_H

#include "forward.h"
#include <genua/point.h>

/** Topological vertex.
  *
 * \ingroup meshgen
 * \sa Topology, TopoEdge
 */
class TopoVertex
{
public:

  enum Corner {NoCorner, SouthWest, SouthEast, NorthEast, NorthWest};

  /// create vertex
  explicit TopoVertex(const Vct3 &p) : m_position(p) {}

  /// construct on a single face
  TopoVertex(const Topology &topo, uint iface, const Vct2 &uvp);

  /// construct on two faces (typically from intersections)
  TopoVertex(const Topology &topo, uint ifa, const Vct2 &uva,
             uint ifb, const Vct2 &uvb);

  /// append face
  uint append(uint iface, const Vct2 &uvp);

  /// merge with another vertex
  void merge(const TopoVertex &v);

  /// find local index of face iface
  uint findFace(uint iface) const {
    const int nf = m_faces.size();
    for (int i=0; i<nf; ++i)
      if (m_faces[i] == iface)
        return i;
    return NotFound;
  }

  /// access location
  const Vct3 &pos() const {return m_position;}

  /// test whether vertex is close to another one
  bool closeTo(const TopoVertex &v, Real tol = gmepsilon) const {
    return (sq(m_position - v.m_position) < sq(tol));
  }

  /// faces to which this vertex is attached
  const Indices & faces() const {return m_faces;}

  /// parameter-space location on faces
  const PointList<2> & uvpos() const {return m_uvp;}

  /// parameter-space location on face k
  const Vct2 &uvpos(uint k) const {return m_uvp[k];}

  /// classify vertex corner on *global* face index gface
  int cornerType(uint gface) const {
    uint k = findFace(gface);
    if (k != NotFound)
      return classifyCorner(m_uvp[k]);
    else
      return NoCorner;
  }

  /// plain text debugging output
  void print(uint k, std::ostream &os) const;

  /// classify a vertex according to corner description
  static int classifyCorner(const Vct2 &p) {
    Real u(p[0]), v(p[1]);
    if (u == 0 and v == 0)
      return SouthWest;
    else if (u == 1 and v == 0)
      return SouthEast;
    else if (u == 1 and v == 1)
      return NorthEast;
    else if (u == 0 and v == 1)
      return NorthWest;
    return NoCorner;
  }

private:

  /// location in 3D space
  Vct3 m_position;

  /// indices of faces on which this point lies
  Indices m_faces;

  /// parameter-space location on faces
  PointList<2> m_uvp;
};

#endif // TOPOVERTEX_H
