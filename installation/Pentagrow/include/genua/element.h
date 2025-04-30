
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
 
#ifndef GENUA_ELEMENT_H
#define GENUA_ELEMENT_H

#include <cstring>
#include <boost/shared_ptr.hpp>

#include "defines.h"
#include "hashfunctions.h"

class MeshFields;

/** Base class for mesh elements.
 *
 * Class Element and childs have been used to implement support for object-
 * oriented mesh interfaces such as the one for NASTRAN interfacing and for
 * structural mesh generation. The OO design turned out not to be suitable for
 * this problem, as it introduces indirection and additional complexity.
 *
 * Prefer to use MxMesh for new code.
 *
 * \deprecated
 * \ingroup mesh
 */
class Element
{
  public:
    
    /// constructs an undefined element 
    Element() : bvi(0), elemid(NotFound) {}
    
    /// construct with pointer to actual data storage
    Element(uint *p) : bvi(p), elemid(NotFound) {}
    
    /// destructor 
    virtual ~Element() {}
    
    /// maximum number of edges in any one element 
    static uint maxedges() {return 24;} 
    
    /// maximum number of faces in any one element 
    static uint maxfaces() {return 6;} 
    
    /// maximum number of edges in any one element 
    static uint maxvertices() {return 20;} 
    
    /// access element id number 
    uint id() const {return elemid;}
    
    /// access element id number 
    void id(uint i) {elemid = i;}
    
    /// access vertices 
    const uint *vertices() const {
      assert(bvi != 0);
      return &bvi[1];
    }
    
    /// access vertices 
    uint *vertices() {
      assert(bvi != 0);
      return &bvi[1];
    }
    
    /// algorithm interface 
    const uint *begin() const {
      assert(bvi != 0);
      return &bvi[1];
    }
    
    /// algorithm interface 
    uint *begin() {
      assert(bvi != 0);
      return &bvi[1];
    }
    
    /// algorithm interface 
    const uint *end() const {
      assert(bvi != 0);
      return &(bvi[ bvi[0]+1 ]);
    }
    
    /// algorithm interface 
    uint *end() {
      assert(bvi != 0);
      return &(bvi[ bvi[0]+1 ]);
    }
    
    /// number of vertices 
    uint nvertices() const {
      assert(bvi != 0);
      return bvi[0];
    }
    
    /// change number of vertices (below nmax) 
    void nvertices(uint nv) const {
      assert(bvi != 0);
      bvi[0] = nv;
    }
    
    /// is element defined or not
    bool valid() const {return (bvi != 0);} 
    
    /// copy edges into ep (default implementation does nothing) 
    virtual uint edges(uint ep[]) const;
    
    /// copy faces into ep (default implementation does nothing) 
    virtual uint faces(uint ep[]) const;
    
    /// rotates indices so that smallest index comes first 
    void irotate() {
      assert(bvi != 0);
      uint *mi = std::min_element(begin(), end());
      std::rotate(begin(), mi, end());
    }
    
    /// apply permutation to vertex indices
    void translate(const Indices &perm) {
      const int n = nvertices();
      uint *v = vertices();
      for (int i=0; i<n; ++i)
        v[i] = perm[v[i]];
    }

    /// apply constant offset to vertex indices
    void offset(int off) {
      const int n = nvertices();
      uint *v = vertices();
      for (int i=0; i<n; ++i)
        v[i] += off;
    }

    /// compute hash value 
    uint32_t hash() const {
      assert(bvi != 0);
      return jenkins_hash((uint32_t *) bvi, (uint32_t) bvi[0]+1, (uint32_t) 0x89ba4fc7);
    }
    
    /// comparison by vertex indices 
    bool vless(const Element & a) const {
      const uint n(nvertices());
      const uint na(a.nvertices());
      if (n < na)
        return true;
      else if (n > na)
        return false;
      
      const uint *v(vertices());
      const uint *va(a.vertices());
      for (uint i=0; i<n; ++i) {
        if (v[i] < va[i])
          return true;
        else if (v[i] > va[i])
          return false;
      }
      
      // elements are equal
      return false;
    }
    
    /// equivalence by vertex indices 
    bool vequal(const Element & a) const {
      const uint n(nvertices());
      const uint na(a.nvertices());
      if (n != na)
        return false;
      
      const uint *v(vertices());
      const uint *va(a.vertices());
      for (uint i=0; i<n; ++i) {
        if (v[i] != va[i])
          return false;
      }
      return true;
    }
    
    /// return an ordering id (needed for sorting)
    virtual uint idtype() const;
    
    /// add entry to visualization object
    virtual uint add2viz(MeshFields &) const {return NotFound;}
    
    /// write to file (nastran)
    virtual void nstwrite(std::ostream &) const {}
    
    /// write to file (abaqus/calculix)
    virtual void abqwrite(std::ostream &) const {}
    
  protected:
    
    /// set vertex array pointer 
    void changeBase(uint *p) {bvi = p;}
    
  private:
    
    /// pointer to vertex indices 
    uint *bvi;
    
    /// element id for sorting 
    uint elemid;
};

typedef boost::shared_ptr<Element> HybElementPtr;
typedef std::vector<HybElementPtr> HybElementArray;

inline bool operator< (const HybElementPtr & a, const HybElementPtr & b)
{
  uint ida = a->idtype();
  uint idb = b->idtype();
  if (ida < idb)
    return true;
  else if (ida > idb)
    return false;
  
  return (a->id() < b->id());
}

/** Edge of an element.
 *
 * \deprecated
 * \ingroup mesh
 */
class ElementEdge
{
  public:
    
    /// construct undefined edge 
    ElementEdge() {vi[0] = vi[1] = NotFound;}
    
    /// define edge 
    ElementEdge(uint a, uint b) {
      assign(a,b);
    }
    
    /// assign vertices 
    void assign(uint a, uint b) {
       if (a < b) {
        vi[0] = a;
        vi[1] = b;
      } else {
        vi[0] = b;
        vi[1] = a;
      }
    }
    
    /// access source vertex 
    uint source() const {return vi[0];}
    
    /// access target vertex 
    uint target() const {return vi[1];}
    
    /// sorting criterion
    bool operator< (const ElementEdge & a) const {
      if (vi[0] < a.vi[0])
        return true;
      else if (vi[0] > a.vi[0])
        return false;
      else
        return (vi[1] < a.vi[1]);
    }
    
    /// equivalence
    bool operator== (const ElementEdge & a) const {
      if (vi[0] != a.vi[0])
        return false;
      else if (vi[1] != a.vi[1])
        return false;
      else
        return true;
    }
    
    /// difference
    bool operator!= (const ElementEdge & a) const {
      return !(*this == a);
    }
    
    /// geometrically valid edge?
    bool valid() const {
      return ((vi[0] != vi[1]) and (vi[0] != NotFound) and (vi[1] != NotFound));  
    }
    
    /// the opposite
    bool invalid() const {return (not valid());}
  
  private:
    
    /// vertex indices  
    uint vi[2];
};

typedef std::vector<ElementEdge> ElementEdgeArray;

/** Point element with a single vertex 
 * \deprecated
 * \ingroup mesh
 */
class PointElement : public Element
{
  public:
    
    /// construct undefined element 
    PointElement() : Element() {}
    
    /// construct defined element at vertex i 
    PointElement(uint i) : Element(vi) {
      vi[0] = 1; 
      vi[1] = i;
    } 
    
    /// destructor 
    virtual ~PointElement() {}
    
    /// return an ordering id (needed for sorting)
    virtual uint idtype() const;
    
    /// add entry to visualization object
    virtual uint add2viz(MeshFields & m) const;
    
  protected:
    
    /// vertex index 
    uint vi[2];
};

/** Line element with two vertices 
 * \deprecated
 * \ingroup mesh
 */
class Line2Element : public Element
{
  public:
    
    /// construct undefined element 
    Line2Element() : Element() {}
    
    /// construct defined element 
    Line2Element(uint a, uint b) : Element(vi) {
      vi[0] = 2;
      vi[1] = a;
      vi[2] = b;
    }
    
    /// destructor 
    virtual ~Line2Element() {}
    
    /// collect edges 
    virtual uint edges(uint ep[]) const;
    
    /// return an ordering id (needed for sorting)
    virtual uint idtype() const;
    
    /// add entry to visualization object
    virtual uint add2viz(MeshFields & m) const;
  
  protected:
    
    /// vertex indices 
    uint vi[3];
};

/** Line element with three vertices 
  *
  * End points of the line are 0,1; midpoint vertex is 2.
  *
  * \deprecated
  * \ingroup mesh
  */
class Line3Element : public Element
{
  public:
    
    /// construct undefined element 
    Line3Element() : Element() {}
    
    /// construct defined element 
    Line3Element(uint a, uint b, uint c) : Element(vi) {
      vi[0] = 3;
      vi[1] = a;
      vi[2] = b;
      vi[3] = c;
    }
    
    /// destructor 
    virtual ~Line3Element() {}
    
    /// return an ordering id (needed for sorting)
    virtual uint idtype() const;
    
    /// collect edges 
    virtual uint edges(uint ep[]) const;
    
    /// add entry to visualization object
    virtual uint add2viz(MeshFields & m) const;
  
  protected:
    
    /// vertex indices 
    uint vi[4];
};

/** Triangle element with three vertices 
 * \deprecated
 * \ingroup mesh
 */
class Tri3Element : public Element
{
  public:
    
    /// construct undefined element 
    Tri3Element() : Element() {}
    
    /// construct defined element 
    Tri3Element(uint a, uint b, uint c) : Element(vi) {
      vi[0] = 3;
      vi[1] = a;
      vi[2] = b;
      vi[3] = c;
      irotate();
    }
    
    /// destructor 
    virtual ~Tri3Element() {}
    
    /// collect edges 
    virtual uint edges(uint ep[]) const;
    
    /// return an ordering id (needed for sorting)
    virtual uint idtype() const;
    
    /// add entry to visualization object
    virtual uint add2viz(MeshFields & m) const;
    
  protected:
    
    /// vertex indices 
    uint vi[4];
};

/** Triangle element with six vertices 

  Corner vertices are 0,1,2; midpoint vertices are 3,4,5.

 * \deprecated
 * \ingroup mesh
 * \sa Element
 */
class Tri6Element : public Element
{
  public:
    
    /// construct undefined element 
    Tri6Element() : Element() {}
    
    /// construct defined element 
    Tri6Element(const uint a[6]) : Element(vi) {
      vi[0] = 6;
      memcpy(vertices(), a, 6*sizeof(uint));
    }
    
    /// destructor 
    virtual ~Tri6Element() {}
    
    /// collect edges 
    virtual uint edges(uint ep[]) const;
    
    /// return an ordering id (needed for sorting)
    virtual uint idtype() const;
    
    /// add entry to visualization object
    virtual uint add2viz(MeshFields & m) const;
    
  protected:
    
    /// vertex indices 
    uint vi[7];
};

/** Quadrilateral element with four vertices 
 * \deprecated
 * \ingroup mesh
 * \sa Element
 */
class Quad4Element : public Element
{
  public:
    
    /// construct undefined element 
    Quad4Element() : Element() {}
    
    /// construct defined element 
    Quad4Element(uint a, uint b, uint c, uint d) : Element(vi) {
      vi[0] = 4;
      vi[1] = a;
      vi[2] = b;
      vi[3] = c;
      vi[4] = d;
      irotate();
    }
    
    /// destructor 
    virtual ~Quad4Element() {}
    
    /// collect edges 
    virtual uint edges(uint ep[]) const;
    
    /// return an ordering id (needed for sorting)
    virtual uint idtype() const;
    
    /// add entry to visualization object
    virtual uint add2viz(MeshFields & m) const;
  
  protected:
    
    /// vertex indices 
    uint vi[5];
};

/** Quadrilateral element with eight vertices 
 * \deprecated
 * \ingroup mesh
 * \sa Element
 */
class Quad8Element : public Element
{
  public:
    
    /// construct undefined element 
    Quad8Element() : Element() {}
    
    /// construct defined element 
    Quad8Element(const uint a[8]) : Element(vi) {
      vi[0] = 8;
      memcpy(vertices(), a, 8*sizeof(uint));
    }
    
    /// destructor 
    virtual ~Quad8Element() {}
    
    /// collect edges 
    virtual uint edges(uint ep[]) const;
    
    /// return an ordering id (needed for sorting)
    virtual uint idtype() const;
    
    /// add entry to visualization object
    virtual uint add2viz(MeshFields & m) const;
  
  protected:
    
    /// vertex indices 
    uint vi[9];
};

/** Quadrilateral element with nine vertices 
 * \deprecated
 * \ingroup mesh
 * \sa Element
 */
class Quad9Element : public Element
{
  public:
    
    /// construct undefined element 
    Quad9Element() : Element() {}
    
    /// construct defined element 
    Quad9Element(const uint a[9]) : Element(vi) {
      vi[0] = 9;
      memcpy(vertices(), a, 9*sizeof(uint));
    }
    
    /// destructor 
    virtual ~Quad9Element() {}
    
    /// collect edges 
    virtual uint edges(uint ep[]) const;
    
    /// return an ordering id (needed for sorting)
    virtual uint idtype() const;
    
    /// add entry to visualization object
    virtual uint add2viz(MeshFields & m) const;
  
  protected:
    
    /// vertex indices 
    uint vi[10];
};

/** Hexahedral element with up to 20 nodes 
 * \deprecated
 * \ingroup mesh
 * \sa Element
 */
class HexElement : public Element
{
  public:
    
    /// construct undefined element 
    HexElement() : Element() {}
    
    /// construct element with all vertices defined 
    HexElement(const uint a[], int nv) : Element(vi) {
      assert(nv == 8 or nv == 20);
      vi[0] = nv;
      memcpy(vertices(), a, nv*sizeof(uint));
    }
    
    /// destructor 
    virtual ~HexElement() {}
    
    /// collect edges 
    virtual uint edges(uint ep[]) const;
    
    /// return an ordering id (needed for sorting)
    virtual uint idtype() const;
    
    /// add entry to visualization object (faces only)
    virtual uint add2viz(MeshFields & m) const;
  
  protected:
    
    /// vertex indices 
    uint vi[21];
};

/** Tetrahedral element with up to 10 nodes
 * \deprecated
 * \ingroup mesh
 * \sa Element
 */
class TetraElement : public Element
{
  public:

    /// construct undefined element
    TetraElement() : Element() {}

    /// construct element with all vertices defined
    TetraElement(const uint a[], int nv) : Element(vi) {
      assert(nv == 4 or nv == 10);
      vi[0] = nv;
      memcpy(vertices(), a, nv*sizeof(uint));
    }

    /// destructor
    virtual ~TetraElement() {}

    /// collect edges
    virtual uint edges(uint ep[]) const;

    /// return an ordering id (needed for sorting)
    virtual uint idtype() const;

    /// add entry to visualization object (faces only)
    virtual uint add2viz(MeshFields & m) const;

  protected:

    /// vertex indices
    uint vi[11];
};

#endif
