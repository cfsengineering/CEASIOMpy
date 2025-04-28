
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
 
#ifndef SURF_DCEDGE_H
#define SURF_DCEDGE_H

#include <genua/defines.h>
#include <boost/functional/hash.hpp>
#include <boost/unordered/unordered_set.hpp>

/** Butterfly edge for Delaunay algorithms.

  DcEdge is the main data structure for the algorithms implemented in class
  DelaunayCore. It stores source and target vertex indices along with two
  face indices which reference a face array in DelaunayCore.

  Pointers to DcEdge are stored in a hash map (boost::unordered_set), hashed
  by source and target vertex indices.

  \todo
  - Pack flags into the high bits of the face indices -> 16 byte edge size
  - Store vertex indices+1 to avoid zero key in integer table
  - Make key function return first 8 bytes as uint64_t

  \ingroup meshgen
  \sa DelaunayCore, DcFace
*/
class DcEdge
{
public:

  enum Flags { None = 0,           ///< Normal, free edge
               Constrained = 1,    ///< Edge is part of a constraint
               Feature = 2,        ///< Feature edge, should not be flipped
               NeverSplit = 4,     ///< Edge should never be split
               SurfaceIntersection = 11  ///< Edge is on a surface intersection
             };

  /// create undefined edge
  DcEdge() : flags(0) {
    vix[0] = vix[1] = NotFound;
    fix[0] = fix[1] = NotFound;
  }

  /// create edge with source and target vertex only
  explicit DcEdge(uint32_t s, uint32_t t) : flags(0) {
    assign(s,t);
    fix[0] = fix[1] = NotFound;
  }

  /// test flag
  bool checkFlag(int f) const {
    return (flags & f) == f;
  }

  /// set flag
  void setFlag(int f) {
    flags |= f;
  }

  /// unset flag
  void unsetFlag(int f) {
    flags &= (~f);
  }

  /// access flags
  int getFlags() const {return flags;}

  /// return topo edge id embedded in high bits
  int topoId() const {
    return (flags >> 16);
  }

  /// embed topo edge id in high flag bits
  void topoId(int id) {
    flags = (flags & 0x0000ffff) | (id << 16);
  }

  /// check whether edge is allowed to flip
  bool canFlip() const {
    const int noflipflag = Constrained | Feature | SurfaceIntersection;
    return (flags & noflipflag) == 0;
  }

  /// check whether edge is defined
  bool valid() const {return (vix[0] != NotFound) and (vix[1] != NotFound);}

  /// mark as invalid
  void invalidate() { vix[0] = NotFound; }

  /// access source vertex
  uint32_t source() const {return vix[0];}

  /// access target vertex
  uint32_t target() const {return vix[1];}

  /// check for equality
  bool connects(uint32_t s, uint32_t t) const {
    if (s < t)
      return (s == source()) and (t == target());
    else
      return (t == source()) and (s == target());
  }

  /// access neighbor face indices
  const uint32_t *faces() const {return fix;}

  /// number of defined face neighbors
  uint32_t nfaces() const {
    return (fix[0] != NotFound) + (fix[1] != NotFound);
  }

  /// access left neighbor face
  uint32_t left() const {return fix[0];}

  /// access left neighbor face
  uint32_t right() const {return fix[1];}

  /// face opposed to face f
  uint32_t otherFace(uint32_t f) const {
    if (f == fix[0])
      return fix[1];
    else if (f == fix[1])
      return fix[0];
    return NotFound;
  }

  /// set source and target vertices
  void assign(uint32_t s, uint32_t t) {
    assert(s != t);
    if (s < t) {
      vix[0] = s;
      vix[1] = t;
    } else {
      vix[0] = t;
      vix[1] = s;
    }
  }

  /// number of faces present
  uint32_t degree() const {
    uint32_t n(0);
    n += (fix[0] != NotFound);
    n += (fix[1] != NotFound);
    return n;
  }

  /// define sort order
  bool operator< (const DcEdge & e) const {
    if (source() < e.source())
      return true;
    else if (source() > e.source())
      return false;
    else
      return target() < e.target();
  }

  /// define equality
  bool operator== (const DcEdge & e) const {
    return (source() == e.source()) and (target() == e.target());
  }

  /// append face to neighbor set
  uint32_t appendFace(uint32_t f) {
    for (int k=0; k<2; ++k) {
      assert(fix[k] != f);
      if (fix[k] == NotFound) {
        fix[k] = f;
        return k;
      }
    }
    return NotFound;
  }

  /// assign neighbor face indices
  void assignFaces(uint32_t f1, uint32_t f2) {
    assert(f1 != f2);
    fix[0] = f1;
    fix[1] = f2;
  }

  /// replace face index k1 with k2
  bool replaceFace(uint32_t k1, uint32_t k2) {
    if (fix[0] == k1) {
      fix[0] = k2;
      return true;
    } else if (fix[1] == k1) {
      fix[1] = k2;
      return true;
    }
    return false;
  }

  /// replace face index fr or fl with k2
  bool replaceFace(uint32_t fr, uint32_t fl, uint32_t k2) {
    if (fix[0] == fr or fix[0] == fl) {
      fix[0] = k2;
      return true;
    } else if (fix[1] == fr or fix[1] == fl) {
      fix[1] = k2;
      return true;
    }
    return false;
  }

  /// Computes hash value from vertex indices
  struct Hasher
  {
    size_t operator() (const DcEdge *pe) const {
      size_t seed = 0;
      boost::hash_combine(seed, pe->source());
      boost::hash_combine(seed, pe->target());
      return seed;
    }
  };

  /// Compares two edges for equality with respect to vertex indices
  struct PtrEqual
  {
    bool operator() (const DcEdge *pa, const DcEdge *pb) const {
      if (sizeof(char*) == 8) {
        union {uint32_t u32[2]; uint64_t u64;} a = {{pa->source(), pa->target()}};
        union {uint32_t u32[2]; uint64_t u64;} b = {{pb->source(), pb->target()}};
        return (a.u64 == b.u64);
      } else {
        return ((pa->source() == pb->source()) and (pa->target() == pb->target()));
      }
    }
  };

  /// Establish ordering between two edges  with respect to vertex indices
  struct PtrLess
  {
    bool operator() (const DcEdge *pa, const DcEdge *pb) const {
      return (*pa < *pb);
    }
  };

private:

  /// source and target vertex indices, src < trg
  uint32_t vix[2];

  /// left and right faces
  uint32_t fix[2];

  /// bitmap for various edge properties
  int32_t flags;
};

typedef boost::unordered_set<DcEdge*, DcEdge::Hasher,
                             DcEdge::PtrEqual> DcEdgeHash;
typedef DcEdgeHash::iterator DcEdgeItr;

#endif // DCEDGE_H
