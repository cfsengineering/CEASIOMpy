
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
 
#ifndef GENUA_EDGEFACE_H
#define GENUA_EDGEFACE_H

#include "defines.h"
#include "svector.h"
#include "smatrix.h"
#include "bounds.h"

enum VertexId {v_red=1, v_green=2, v_blue=3};

class Triangulation;
class Face;
typedef std::pair<Face,Face> FacePair;

/** Triangle edge.

  An Edge connects two vertices and is part of its parent Triangulation.
  Every Edge object knows which Triangulation instance it belongs to
  (the latter can be retrieved using Edge::surface()).

  This is a fairly light class, which basically only provides access
  to the vertex indices via Edge::source() and Edge::target(). Object
  size should be 12 bytes.

  Because sorted edge lists are used by some algorithms, Edge provides
  comparison and equality operators, which compare by source (first) and
  target (second) index value.

  */
class Edge
{
  public:

    /// default (empty) construction
    Edge() : srf(0), src(0), trg(0) {}

    /// defined construction
    Edge(const Triangulation *parent, uint from, uint to)
          : srf(parent), src(from), trg(to) {}

    /// virtual destruction
    virtual ~Edge() {}

    /// equality
    bool operator== (const Edge & e) const
      { return ((src == e.src) and (trg == e.trg)); }

    /// inequality
    bool operator!= (const Edge & e) const
      { return !(*this == e);}

    /// comparison
    bool operator< (const Edge & e) const {
      if (src != e.src)
        return (src < e.src);
      else
        return (trg < e.trg);
    }

    /// access
    uint source() const
      {return src;}

    /// access
    uint target() const
      {return trg;}

    /// return the opposed vertex index
    uint opposed(uint i) const {
      assert(i == src or i == trg);
      if (i == src)
        return trg;
      else
        return src;
    }

    /// connected to a?
    bool touches(const Edge & a) const {
      if ( a.source() == src or a.source() == trg
           or a.target() == src or a.target() == trg )
        return true;
      else
        return false;
    }

    /// defined with these two vertices?
    bool hasVertices(uint a, uint b) const
      { return ((a == trg and b == src) or (a == src and b == trg));}

    /// compute direction vector
    Vct3 direction() const;
    
    /// compute edge length
    Real length() const;

    /// the number of faces connected at this edge
    uint degree() const;

    /** find left and right neighbor face, cast exception if edge
      has either one or more than two neighbor faces */
    FacePair neighbors() const;

    /// compute maximum stretch ratio (max height of neighbor faces / edge length)
    Real maxStretch() const;

    /// test if edge intersects bounding box
    bool intersects(const BndBox & bb) const;

    /// access
    const Triangulation *surface() const
      {return srf;}

  private:

    /// parent object
    const Triangulation *srf;

    /// vertex indices
    uint src, trg;
};

// struct global_edge_less
// {
//   bool operator() (const Edge & a, const Edge & b) const
//   {
//     const Triangulation *sa(a.surface());
//     const Triangulation *sb(b.surface());
// 
//     // compare by pointer value (arbitrary) if on different surfaces
//     if (sa < sb)
//       return true;
//     else if (sa > sb)
//       return false;
//     else
//       return (a < b);
//   }
// };


/** Triangular face.

  A Face always belongs to a Triangulation (which can be retrieved from
  any Face object by Face::surface()), to which it stores a pointer. When
  copying collections of Faces, remember that their parent triangulation
  must exist, otherwise, calls to some member functions of Face will lead
  to assertion failures.

  Face provides access to the indices of its vertices by Face::vertex(),
  which you might call with integers of using the  VertexId enum.
  \verbatim
    uint vr, vg, vb;
    Face f;
    vr = f.vertex(1);
    vr = f.vertex(v_red);    // equivalent
    vg = f.vertex(2);
    vg = f.vertex(v_green);  // equivalent
  \endverbatim

  For each set of three vertices, only two different vertex orderings
  (red,green,blue) are possible, allowing two different normal directions.
  This restriction is necessary to define a unique face ordering. Thus,
  if you define a Face(&tg, 45, 61, 2), it is exactly the same as
  Face(&tg, 2, 45, 61). (Actually, the second variant is stored in both
  cases.) Normal direction is never changed by this reordering.

  Face has moderate size, normally 16 bytes.

  */
class Face
{
  public:

    /// empty construction
    Face() : srf(0) {}

    /// definition by vertices
    Face(const Triangulation *parent, uint p1, uint p2, uint p3);

    /// definition by edges
    Face(const Triangulation *parent,
        const Edge & ed1, const Edge & ed2, const Edge & ed3);

    /// virtual destruction
    virtual ~Face() {}

    /// check validity 
    bool valid() const {return srf != 0;}
    
    /// equality
    bool operator== (const Face & a) const;

    /// inequality
    bool operator!= (const Face & a) const {return !(*this == a);}

    /// comparison
    bool operator< (const Face & a) const {
      if (v[0] == a.v[0] and v[1] == a.v[1])
        return (v[2] < a.v[2]);
      else if (v[0] == a.v[0])
        return (v[1] < a.v[1]);
      else
        return (v[0] < a.v[0]);
    }

    bool operator> (const Face & a) const {
      if (a == *this or *this < a)
        return false;
      else
        return true;
    }

    /// access
    uint vertex(uint i) const {
      assert(i < 4 and i > 0);
      return v[i-1];
    }

    /// copy vertex indices into array
    void getVertices(uint vi[3]) const {
      vi[0] = v[0]; vi[1] = v[1]; vi[2] = v[2];
    }

    /// access vertex index pointer
    const uint* vertices() const {return v;}
    
    /// access vertex index pointer
    uint* vertices() {return v;}
    
    /// copies edges into array
    void getEdges(Edge edg[3]) const;

    /// access edge
    Edge edge(uint i) const;

    /// check if edge is present in this face
    bool hasEdge(const Edge & e) const;
    
    /// find vertex opposed to edge e
    uint opposed(const Edge & e) const;

    /// find edge opposed to vertex i
    Edge opposed(uint i) const;

    /// find the neighbor faces connected to edges
    uint neighbors(Face f[3]) const;
    
    /// access
    const Triangulation *surface() const
      {assert(srf != 0); return srf;}

    /// change reference
    void setSurface(const Triangulation *parent)
      {srf = parent;}

    /// evaluate parameters
    Vct3 eval(Real xi, Real eta) const;

    /// evaluate scalar field over triangle
    Real eval(const Vector & u, Real xi, Real eta) const {
      Real theta = 1-xi-eta;
      return theta*u[v[0]] + xi*u[v[1]] + eta*u[v[2]];
    }

    /// compute normal
    Vct3 normal() const;

    /// compute center
    Vct3 center() const;

    /// project, return parameters and signed distance to projection
    Vct3 project(const Vct3 & pt) const;

    /** Find the point where an edge would pierce this face, return the
      projection parameter (u,v,t). The point is inside the face if
      0<u,v,w<1 where w = 1-u-v. (t) is the edge parameter. */
    Vct3 pierce(const Edge & e) const;

    /// return transformation matrix for local coordinate system
    SMatrix<3,3> trafo() const;
    
    /** Gradient. Computes the matrix relating a scalar property associated 
    to the vertices to its gradient in global 3D coordinates. */
    void gradient(Mtx33 & gm) const;
    
    /// computes the gradient of global x on this triangle
    Vct3 gradient(const Vector & x) const;

    /// computes the gradient of global x on this triangle
    CpxVct3 gradient(const CpxVector & x) const;

    /// compute corner angle for (global) vertex gv
    Real corner(uint gv) const;

    /// compute solid angle associated with vertex idx
    Real solidAngle(uint idx) const;

    /// compute solid angle associated with vertex idx, for normal a
    Real solidAngle(uint idx, const Vct3 & a) const;

    /// triangle quality
    Real quality() const;

    /// make ordering canonical
    void orderCanonical();

    /// reverse normal
    void reverse();

    /// replace index
    void replace(uint vold, uint vnew);
    
    /// return how many of this face's vertices are inside the box
    uint inside(const BndBox & bb) const;
    
    /// return minimum signed distance of pt to this triangle, set foot point parameter
    Real minDistance(const Vct3 & pt, Vct2 & foot) const;

  protected:

    /// parent object
    const Triangulation *srf;

    /// vertex indices
    uint v[3];
};

// struct global_face_less
// {
//   bool operator() (const Face & a, const Face & b) const
//   {
//     const Triangulation *sa(a.surface());
//     const Triangulation *sb(b.surface());
// 
//     // compare by pointer value (arbitrary) if on different surfaces
//     if (sa < sb)
//       return true;
//     else if (sa > sb)
//       return false;
//     else
//       return (a < b);
//   }
// };

#endif

