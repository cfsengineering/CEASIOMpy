
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       quadmesh.h
 * begin:      Oct 2004
 * copyright:  (c) 2004 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * simple datastructure for unstructured quad mesh
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */
 
#ifndef GENUA_QUADMESH
#define GENUA_QUADMESH

#include <iostream>
#include <vector>
#include <map>
#include "point.h"
#include "quad.h"

typedef std::vector<Quad> QuadArray;
typedef std::map<uint, QuadArray> VQuadMap;

class QuadMesh
{
  public:
    
    typedef QuadArray::iterator face_iterator;
    typedef QuadArray::const_iterator const_face_iterator;
    
    /// undefined construction
    QuadMesh() {}
    
    /// construct from a grid of points
    explicit QuadMesh(const PointGrid<3> & gd);
    
    /// count vertices
    uint nvertices() const {return vtx.size();}
    
    /// count elements
    uint nfaces() const {return quads.size();}
    
    /// add a vertex, return its index
    uint addVertex(const Vct3 & v);
    
    /// add an element, return its index
    uint addQuad(const Quad & q);
    
    /// recompute connectivity
    void fixate();
    
    /// access vertex (const)
    const Vct3 & vertex(uint i) const {return vtx[i];}
    
    /// access vertex (mutable)
    Vct3 & vertex(uint i) {return vtx[i];}
    
    /// access element (const)
    const Quad & quad(uint i) const {
      assert(i < quads.size());
      return quads[i];
    }
    
    /// access element (mutable)
    Quad & quad(uint i) {
      assert(i < quads.size());
      return quads[i];
    }
    
    /// iterate over faces sharing vertex i
    const_face_iterator nb_face_begin(uint i) const;
    
    /// iterate over faces sharing vertex i
    const_face_iterator nb_face_end(uint i) const;
    
    /// merge with other mesh
    void merge(const QuadMesh & a);
    
    /// remove duplicate vertices
    void cleanup(Real threshold = gmepsilon);
    
    /// flip all elements
    void reverse();
    
    /// delete everything
    void clear();
    
    /// write an OOGL representation (OFF)
    void writeOogl(std::ostream & os) const;
    
  protected:
    
    /// identify duplicate vertices and get rid of them
    void unify(Real threshold);
    
    /// change indexing 
    void rename(const Indices & idx);
    
  private:
    
    /// vertices
    PointList<3> vtx;
    
    /// quad elements
    QuadArray quads;
    
    /// map vertices to quads
    VQuadMap v2f;      
};

#endif
