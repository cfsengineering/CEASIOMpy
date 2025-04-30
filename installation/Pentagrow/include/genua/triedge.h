
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
 
#ifndef GENUA_TRIEDGE_H
#define GENUA_TRIEDGE_H

#include "defines.h"
#include "svector.h"
#include "hashfunctions.h"

class TriMesh;

class TriEdge
{
  public:
    
    /// construct unconnected edge
    TriEdge() : msh(0) {}
    
    /// define connected edge
    TriEdge(const TriMesh *m, uint s, uint t) : msh(m) {
      assert(s != t);
      if (s < t) {
        v[0] = s;
        v[1] = t;
      } else {
        v[0] = t;
        v[1] = s;
      }
    }
    
    /// attach to different mesh
    void bind(const TriMesh *m) {msh = m;}
    
    /// assign mesh and vertices
    void assign(const TriMesh *m, uint s, uint t) {
      assert(s != t);
      if (s < t) {
        v[0] = s;
        v[1] = t;
      } else {
        v[0] = t;
        v[1] = s;
      }
      msh = m;
    }
    
    /// access source vertex index
    uint source() const {return v[0];}
    
    /// access target vertex index
    uint target() const {return v[1];}
    
    /// return the 'other' vertex
    uint opposed(uint i) const {
      if (i == v[0])
        return v[1];
      else if (i == v[1])
        return v[0];
      else
        return NotFound;
    }
    
    /// access mesh pointer
    const TriMesh *mesh() const {return msh;}
    
    /// sorting criterion
    bool operator< (const TriEdge & a) const {
      if (v[0] < a.v[0])
        return true;
      else if (v[0] > a.v[0])
        return false;
      else
        return (v[1] < a.v[1]);
    }
    
    /// equivalence
    bool operator== (const TriEdge & a) const {
      if (v[0] != a.v[0])
        return false;
      else if (v[1] != a.v[1])
        return false;
      else
        return true;
    }
    
    /// difference
    bool operator!= (const TriEdge & a) const {
      return !(*this == a);
    }
    
    /// translate vertex indices
    void itranslate(const Indices & repl) {
      v[0] = repl[v[0]];
      v[1] = repl[v[1]];
      if (v[1] < v[0])
        std::swap(v[0], v[1]);
    }
    
    /// compute length
    Real length() const;
    
    /// compute normalized direction vector and length
    Real direction(Vct3 & dv) const;
    
    /// compute a hash value 
    uint64_t hash() const {
      uint64_t a = uint64_t(v[0]);
      uint64_t b = uint64_t(v[1]);
      uint64_t c = uint64_t( ptrdiff_t(msh) );
      return jenkins_hash(a, b, c);
    }
    
  protected:
    
    /// vertices
    uint v[2];
    
    /// connected mesh
    const TriMesh *msh;
};

struct global_edge_less 
{
  bool operator()(const TriEdge & a, const TriEdge & b) const
  {
    const TriMesh *ma( a.mesh() );
    const TriMesh *mb( b.mesh() );
    if (ma == mb) {
      return (a < b);
    } else {
      return ma < mb;
    }
  }
};

struct global_edge_equal
{
  bool operator()(const TriEdge & a, const TriEdge & b) const
  {
    const TriMesh *ma( a.mesh() );
    const TriMesh *mb( b.mesh() );
    if (ma != mb) {
      return false;
    } else {
      return a == b;
    }
  }
};

struct edge_hash
{
  size_t operator() (const TriEdge & a) const {return a.hash();}
};

#endif

