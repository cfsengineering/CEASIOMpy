
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
 
#ifndef GENUA_HYBRIDMESH_H
#define GENUA_HYBRIDMESH_H

#include "element.h"
#include "connectmap.h"
#include "point.h"

class TriMesh;
class MeshFields;
class Transformer;

/** Object-oriented Mesh containing different elements
  *
  * HybridMesh is the container class for meshes which make use of the
  * object-oriented element classes. Unfortunately, this approach makes
  * supporting different file formats and element properties rather
  * work-intensive. For new code, prefer to use MxMesh and relatives.
  *
  * Mainly used by NstMesh in libsurf and structural (FEM) mesh generation.
  *
  * \deprecated
  *
  * \ingroup mesh
  * \sa Element
  */
class HybridMesh
{
  public:
    
    class nb_face_iterator {
      public:
        nb_face_iterator() {}
        nb_face_iterator(const HybridMesh *m, Indices::const_iterator itr) : 
          pos(itr), msh(m) {}
        nb_face_iterator(const nb_face_iterator & a) : 
          pos(a.pos), msh(a.msh) {}
        const nb_face_iterator & operator= (const nb_face_iterator & a) {
          if (&a != this) {
            msh = a.msh;
            pos = a.pos;
          }
          return *this;
        }
        bool operator== (const nb_face_iterator & a) const {
          return (pos == a.pos); 
        }
        bool operator!= (const nb_face_iterator & a) const {
          return (pos != a.pos); 
        }
        bool operator< (const nb_face_iterator & a) const {
          return (pos < a.pos); 
        }
        const Element & operator*() const {return msh->element(*pos);}
        const Element *operator->() const {return &msh->element(*pos);}
        const nb_face_iterator & operator++ () {++pos; return *this;}
        const nb_face_iterator & operator-- () {--pos; return *this;}
        uint index() const {return *pos;}
      private:
        Indices::const_iterator pos;
        const HybridMesh *msh;
    };
    
    class nb_edge_iterator {
      public:
        nb_edge_iterator() {}
        nb_edge_iterator(const HybridMesh *m, Indices::const_iterator itr) : 
          pos(itr), msh(m) {}
        nb_edge_iterator(const nb_edge_iterator & a) : 
            pos(a.pos), msh(a.msh) {}
        const nb_edge_iterator & operator= (const nb_edge_iterator & a) {
          if (&a != this) {
            msh = a.msh;
            pos = a.pos;
          }
          return *this;
        }
        bool operator== (const nb_edge_iterator & a) const {
          return (pos == a.pos); 
        }
        bool operator!= (const nb_edge_iterator & a) const {
          return (pos != a.pos); 
        }
        bool operator< (const nb_edge_iterator & a) const {
          return (pos < a.pos); 
        }
        const ElementEdge & operator*() const {return msh->edge(*pos);}
        const ElementEdge *operator->() const {return &msh->edge(*pos);}
        const nb_edge_iterator & operator++ () {++pos; return *this;}
        const nb_edge_iterator & operator-- () {--pos; return *this;}
        uint index() const {return *pos;}
      private:
        Indices::const_iterator pos;
        const HybridMesh *msh;
    };
    
    /// empty mesh 
    HybridMesh() {}
    
    /// destroy 
    virtual ~HybridMesh() {}
    
    /// number of elements 
    uint nelements() const {return elements.size();}
    
    /// number of vertices 
    uint nvertices() const {return vtx.size();}
    
    /// access mesh node i
    const Vct3 & vertex(uint i) const {return vtx[i];}
    
    /// access all vertices
    const PointList<3> & vertices() const {return vtx;}
    
    /// access mesh node i
    Vct3 & vertex(uint i) {return vtx[i];}
    
    /// access element 
    const Element & element(uint i) const {
      assert(i < elements.size());
      return *elements[i];
    }
    
    /// access element 
    Element & element(uint i) {
      assert(i < elements.size());
      return *elements[i];
    }
    
    /// access element pointer
    HybElementPtr elementptr(uint i) const {
      assert(i < elements.size());
      return elements[i];
    }
    
    /// access edge 
    const ElementEdge & edge(uint i) const {
      assert(i < edges.size());
      return edges[i];
    }
    
    /// add vertex coordinates 
    uint addVertex(const Vct3 & p) {
      vtx.push_back(p);
      return vtx.size()-1;
    }
    
    /// add vertex coordinates 
    void insertVertex(uint ipos, const Vct3 & p) {
      vtx.insert(vtx.begin()+ipos, p);
    }
    
    /// add element and transfer ownership to mesh, return index
    uint addElement(Element *ep) {
      if (ep->id() == NotFound)
        ep->id(elements.size());
      elements.push_back(HybElementPtr(ep));
      return elements.size()-1;
    } 
    
    /// remove element (invalidates connectivity)
    void removeElement(uint i) {
      assert(i < elements.size());
      elements.erase(elements.begin()+i);
    }
    
    /// transform all vertex coordinates 
    virtual void transform(const Transformer & t);
    
    /// add a triangle mesh in one sweep (does not fixate)
    virtual void merge(const TriMesh & m);

    /// sort elements by type and element id
    virtual void esort();
    
    /// compute edges and connectivity 
    virtual void fixate();
    
    /// delete all contents 
    virtual void clear();
    
    /// iterate over neighborhood
    nb_face_iterator v2fBegin(uint i) const {
      assert(i < v2f.size());
      return nb_face_iterator(this, v2f.begin(i));
    }
    
    /// iterate over neighborhood
    nb_face_iterator v2fEnd(uint i) const {
      assert(i < v2f.size());
      return nb_face_iterator(this, v2f.end(i));
    }
    
    /// iterate over neighborhood
    nb_face_iterator e2fBegin(uint i) const {
      assert(i < e2f.size());
      return nb_face_iterator(this, e2f.begin(i));
    }
    
    /// iterate over neighborhood
    nb_face_iterator e2fEnd(uint i) const {
      assert(i < e2f.size());
      return nb_face_iterator(this, e2f.end(i));
    }
    
    /// iterate over neighborhood
    nb_edge_iterator v2eBegin(uint i) const {
      assert(i < v2e.size());
      return nb_edge_iterator(this, v2e.begin(i));
    }
    
    /// iterate over neighborhood
    nb_edge_iterator v2eEnd(uint i) const {
      assert(i < v2e.size());
      return nb_edge_iterator(this, v2e.end(i));
    }
    
    /// iterate over neighborhood
    nb_edge_iterator f2eBegin(uint i) const {
      assert(i < f2e.size());
      return nb_edge_iterator(this, f2e.begin(i));
    }
    
    /// iterate over neighborhood
    nb_edge_iterator f2eEnd(uint i) const {
      assert(i < f2e.size());
      return nb_edge_iterator(this, f2e.end(i));
    }    
    
    /// find edge by traversing connectivity 
    uint tsearchEdge(uint s, uint t) const {
      if (s > t)
        std::swap(s, t);
      assert(s < v2e.size());
      const uint ne(v2e.size(s));
      const uint *nbe(v2e.first(s));
      for (uint i=0; i<ne; ++i) {
        uint idx = nbe[i];
        const ElementEdge & e(edges[idx]);
        if (e.source() == s and e.target() == t)
          return idx;
      }
      return NotFound;
    }
    
    /// add geometry to visualization 
    virtual void add2viz(MeshFields & mf) const;

  protected:
    
    /// mesh vertices 
    PointList<3> vtx;
    
    /// shared pointers to elements
    HybElementArray elements;
    
    /// edges of the above elements 
    ElementEdgeArray edges;
    
    /// connectivity data 
    ConnectMap f2e, v2e, v2f, e2f;
};

#endif

