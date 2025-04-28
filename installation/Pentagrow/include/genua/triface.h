
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
 
#ifndef GENUA_TRIFACE_H
#define GENUA_TRIFACE_H

#include "smatrix.h"
#include "dvector.h"
#include "point.h"
#include "triedge.h"

class TriMesh;
class Plane;

/** Triangular face of a TriMesh.

  TriFace objects represent the linear triangular faces used by class TriMesh.

  \sa TriMesh, TriEdge
  */
class TriFace
{
  public:
    
    /// construct unconnected face
    TriFace() : ftag(0), msh(0) {}
    
    /// construct connected face
    TriFace(const TriMesh *m, uint a, uint b, uint c)
      : ftag(0), msh(m) {order(a,b,c);}
  
    /// set mesh and vertices
    void assign(const TriMesh *m, uint a, uint b, uint c) {
      order(a, b, c);
      msh = m;
    }
    
    /// check if all three vertices are distinct
    bool isValid() const {
      if (v[0] == v[1] or v[0] == v[2] or v[1] == v[2])
        return false;
      else
        return true;
    }

    /// check if vertex indices are in range
    bool inRange() const;
    
    /// make triangle invalid, to force elimination by TriMesh::fixate()
    void invalidate() { v[0]=v[1]=v[2] = NotFound; }
    
    /// access mesh
    const TriMesh *mesh() const {return msh;}
    
    /// access vertices
    const uint *vertices() const {return v;}
    
    /// access vertices
    uint *vertices() {return v;}
    
    /// copy vertex indices
    void getVertices(uint *vi) const {
      vi[0] = v[0];
      vi[1] = v[1];
      vi[2] = v[2];
    }
    
    /// find vertex opposed to edge ei
    uint opposed(const TriEdge & e) const {
      uint s = e.source();
      uint t = e.target();
      for (uint k=0; k<3; ++k) {
        uint vk = v[k];
        if (vk != s and vk != t)
          return vk;
      }
      return NotFound;
    }
    
    /// rebind to different mesh and offset vertex indices
    void bind(const TriMesh *m, uint off = 0) {
      msh = m;
      v[0] += off;
      v[1] += off;
      v[2] += off;
    }
    
    /// flip normal direction
    void reverse() {std::swap(v[1], v[2]);}
    
    /// translate vertex indices
    void itranslate(const Indices & repl) {
      order(repl[v[0]], repl[v[1]], repl[v[2]]);
    }
    
    /// replace a single vertex index, fix ordering
    uint replace(uint iold, uint inew) {
      for (uint k=0; k<3; ++k) {
        if (v[k] == iold) {
          v[k] = inew;
          order(v[0], v[1], v[2]);
          return k;
        }
      }
      return NotFound;
    }
    
    /// compute point on triangle 
    Vct3 eval(Real up, Real vp) const;
    
    /// compute triangle center
    Vct3 center() const;
    
    /// compute normal vector (not normalized)
    Vct3 normal() const;
    
    /// compute area
    Real area() const;
    
    /// compute normalized normal, return area
    Real normal(Vct3 & nrm) const;
    
    /// compute the internal angle at vertex i
    Real corner(uint i) const;
    
    /// compute solid angle with respect to vertex idx
    Real solidAngle(uint idx) const;
    
    /// compute the length of all three edges
    void edgeLengths(Vct3 & elen) const;
    
    /// project, return parameters and signed distance to projection
    Vct3 project(const Vct3 & pt) const;

    /** Find the point where a line (a-b) would pierce this face, return the
    projection parameter (u,v,t). The point is inside the face if
    u,v,w are within (0,1) where w = 1-u-v. (t) is the line parameter. */
    Vct3 pierce(const Vct3 & a, const Vct3 & b) const;
    
    /// return minimum signed distance of pt to this triangle, set foot point parameter
    Real minDistance(const Vct3 & pt, Vct2 & foot) const;
    
    /// Determine intersection segment with plane pln
    bool intersect(const Plane & pln, Vct3 & src, Vct3 & trg) const;

    /** Gradient. Computes the matrix relating a scalar property associated 
    to the vertices to its gradient in global 3D coordinates. */
    void gradient(Mtx33 & gm) const;
    
    /// Computes the surface gradient of the scalar property in x. 
    Vct3 gradient(const Vector & x) const;
    
    /// Computes the surface gradient of the scalar property in x. 
    CpxVct3 gradient(const CpxVector & x) const;
    
    /// surface integration, add int(p*n dA) and int(r x pn dA) to sums 
    void xIntegrate(const Vector & p, const Vct3 & ref, Vct3 & pn, Vct3 & rxpn) const;
    
    /// surface integration, return int( dot(pn,z) dA  )
    Real dotIntegrate(const Vector & p, const PointList<3> & z) const;
    
    /// sorting criterion
    bool operator< (const TriFace & a) const {
      if (v[0] < a.v[0])
        return true;
      else if (v[0] > a.v[0])
        return false;
      else if (v[1] < a.v[1])
        return true;
      else if (v[1] > a.v[1])
        return false;
      else
        return (v[2] < a.v[2]);
    }
    
    /// equivalence
    bool operator== (const TriFace & a) const {
      if (v[0] != a.v[0])
        return false;
      else if (v[1] != a.v[1])
        return false;
      else if (v[2] != a.v[2])
        return false;
      else
        return true;
    }
    
    /// equivalent, but possibly flipped
    bool equivalent(const TriFace & a) const {
      if (v[0] != a.v[0])
        return false;
      else if (v[1] == a.v[1] and v[2] == a.v[2])
        return true;
      else if (v[2] == a.v[1] and v[1] == a.v[2])
        return true;
      else
        return false;
    }
    
    /// difference
    bool operator!= (const TriFace & a) const {
      return !(*this == a);
    }

    /// access tag value
    int tag() const {return ftag;}

    /// change tag value
    void tag(int t) {ftag = t;}
    
    /// compute a hash value 
    uint64_t hash() const {
      uint64_t a = uint64_t(v[0]);
      uint64_t b = uint64_t(v[1]);
      uint64_t c = uint64_t(v[2]);
      uint64_t d = uint64_t(ptrdiff_t(msh));
      return jenkins_hash(a, b, c, d);
    }
    
  protected:
    
    /// set vertices in correct order
    void order(uint a, uint b, uint c) {
      if (a < b and a < c) {
        v[0] = a;
        v[1] = b;
        v[2] = c;
      } else if (b < a and b < c) {
        v[0] = b;
        v[1] = c;
        v[2] = a;
      } else {
        v[0] = c;
        v[1] = a;
        v[2] = b;
      }
    }
    
  protected:
    
    /// vertex indices
    uint v[3];
    
    /// marker tag
    int ftag;
    
    /// connected mesh
    const TriMesh *msh;
};

struct global_face_less 
{
  bool operator()(const TriFace & a, const TriFace & b) const
  {
    const TriMesh *am(a.mesh());
    const TriMesh *bm(b.mesh());
    if (am == bm) 
      return a < b;
    else
      return am < bm;
  }
};

struct global_face_equal
{
  bool operator()(const TriFace & a, const TriFace & b) const
  {
    const TriMesh *am(a.mesh());
    const TriMesh *bm(b.mesh());
    if (am != bm) 
      return false;
    else
      return a == b;
  }
};

struct face_hash 
{
  size_t operator() (const TriFace & a) const {return a.hash();}
};

#endif

