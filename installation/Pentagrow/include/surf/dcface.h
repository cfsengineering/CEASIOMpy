
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
 
#ifndef SURF_DCFACE_H
#define SURF_DCFACE_H

#include "dcedge.h"
#include <genua/morton.h>
#include <genua/point.h>
#include <vector>
#include <iostream>

/** Face in a plane Delaunay triangulation.

  DcFace is a simple, 'dumb' container for three vertex indices. It is used
  as a secondary data structure in DelaunayCore.

  DcEdge and DcFace use 4-byte integer indices instead of pointers to objects
  in order to keep the object size as small as possible on 64bit systems, thus
  allowing more elements to fit into the processor cache.

  \ingroup meshgen
  \sa DelaunayCore, DcEdge
*/
class DcFace
{
public:

  enum SplitConfig { NoSplit = 0,        ///< No split performed
                     SplitEdge0 = 1,     ///< First edge (v[0],v[1]) split
                     SplitEdge1 = 2,     ///< Second edge (v[1],v[2]) split
                     SplitEdge2 = 4,     ///< Third edge (v[2],v[0]) split
                     QuadSplit = 7       ///< All edges split
                   };

  /// create undefined face
  DcFace() {
    vix[0] = vix[1] = vix[2] = NotFound;
  }

  /// define face
  explicit DcFace(uint a, uint b, uint c) {
    assign(a, b, c);
  }

  /// define face
  explicit DcFace(const uint vip[]) {
    assign(vip[0], vip[1], vip[2]);
  }

  /// check whether edge is defined
  bool valid() const {return vix[0] != NotFound;}

  /// make invalid
  void invalidate() {vix[0] = NotFound;}

  /// access vertices
  const uint *vertices() const {return vix;}

  /// copy vertices
  void copyVertices(uint v[]) const {
    v[0] = vix[0]; v[1] = vix[1]; v[2] = vix[2];
  }

  /// return vertex opposing edge vertices s, t, or NotFound
  uint opposedVertex(uint s, uint t) const {
    for (int k=0; k<3; ++k) {
      uint a = vix[k];
      uint b = vix[(k+1)%3];
      uint c = vix[(k+2)%3];
      if (s == a and t == b)
        return c;
      if (s == b and t == a)
        return c;
    }
    return NotFound;
  }

  /// determine cosine of angle at node a
  Real cosApexAngle(const PointList3d &pts, uint a) const {
    const Vct3 &pa = pts[a];
    for (int k=0; k<3; ++k) {
      if (a == vix[k]) {
        uint b = vix[(k+1)%3];
        uint c = vix[(k+2)%3];
        return cosarg( pts[b]-pa, pts[c]-pa );
      }
    }
    return 1.0;
  }

  /// check whether face contains v
  uint find(uint v) const {
    for (int k=0; k<3; ++k) {
      if (vix[k] == v)
        return k;
    }
    return NotFound;
  }

  /// compute edge k
  DcEdge edge(uint k) const {
    assert(k < 3);
    return DcEdge( vix[k], vix[(k+1)%3] );
  }

  /// return source vertex of edge k
  uint esource(uint k) const {
    assert(k < 3);
    return vix[k];
  }

  /// return target vertex of edge k
  uint etarget(uint k) const {
    assert(k < 3);
    const int map[3] = {1, 2, 0};
    return vix[map[k]];
  }

  /// find edge (s,t)
  uint findEdge(uint s, uint t) {
    for (int k=0; k<3; ++k) {
      uint a = vix[k];
      uint b = vix[(k+1)%3];
      if (b < a)
        std::swap(a,b);
      if (a == s and b == t)
        return k;
    }
    return NotFound;
  }

  /// determine Morton code (or z-code) from vertex array and quantization
  size_t zcode(const PointList<2> & vtx, Real qoffset, Real qscale) const {
    assert(valid());

    // note : profile - could be vectorized if necessary (SSE2)
    const Vct2 & p1( vtx[vix[0]] );
    const Vct2 & p2( vtx[vix[1]] );
    const Vct2 & p3( vtx[vix[2]] );
    const Real third(1.0 / 3.0);
    const int nbits( sizeof(size_t)*4 );
    Real uc = (p1[0] + p2[0] + p3[0])*third;
    Real vc = (p1[1] + p2[1] + p3[1])*third;
    size_t a( (uc - qoffset)*qscale );
    size_t b( (vc - qoffset)*qscale );
    return interleave_bits<size_t, nbits>(a, b);
  }

private:

  /// set vertex indices
  void assign(uint a, uint b, uint c) {
    if (a < b and a < c) {
      vix[0] = a;
      vix[1] = b;
      vix[2] = c;
    } else if (b < a and b < c) {
      vix[0] = b;
      vix[1] = c;
      vix[2] = a;
    } else {
      vix[0] = c;
      vix[1] = a;
      vix[2] = b;
    }
  }

private:

  /// three vertices
  uint vix[3];

  // padding (found detrimental)
  // uint pad;
};

typedef std::vector<DcFace> DcFaceArray;

inline std::ostream & operator<<( std::ostream &os, const DcFace & f )
{
  const uint *vf = f.vertices();
  os << '[' << vf[0] << ' ' << vf[1] << ' ' << vf[2] << ']';
  return os;
}

#endif // DCFACE_H
