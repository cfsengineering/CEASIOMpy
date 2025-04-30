
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
 
#include "trimesh.h"
#include "meshfields.h"
#include "trafo.h"
#include "hybridmesh.h"

void HybridMesh::merge(const TriMesh & m)
{
  const uint off(vtx.size());
  const PointList<3> & mv(m.vertices());
  vtx.insert(vtx.end(), mv.begin(), mv.end());
  
  const uint nf(m.nfaces());
  for (uint i=0; i<nf; ++i) {
    const uint *vi( m.face(i).vertices() );
    addElement( new Tri3Element(off+vi[0], off+vi[1], off+vi[2]) );
  }
  
  // invalidate topology data 
  f2e.clear();
  v2e.clear();
  v2f.clear();
  e2f.clear();
}

void HybridMesh::esort()
{
  std::sort(elements.begin(), elements.end());
  
  // invalidate topology data 
  f2e.clear();
  v2f.clear();
  e2f.clear();
}

void HybridMesh::fixate()
{
  uint nv(vtx.size());
  uint nf(elements.size());
  
  // setup vertex-face connections and generate edges
  {
    Indices vacc;
    vacc.reserve(4*nf);
    edges.clear();
    edges.reserve(3*nf);
    Indices etmp(2*Element::maxedges());
    Indices vtmp(2*Element::maxvertices());
    for (uint i=0; i<nf; ++i) {
      const uint ne( elements[i]->edges(&etmp[0]) );
      for (uint j=0; j<ne; ++j)
        edges.push_back( ElementEdge(etmp[2*j], etmp[2*j+1]) );
      
      // construct vertex-face connections
      const uint  n(elements[i]->nvertices());
      const uint *v(elements[i]->vertices());
      for (uint j=0; j<n; ++j) {
        vtmp[2*j]   = v[j];
        vtmp[2*j+1] = i;
      }
      vacc.insert(vacc.end(), &vtmp[0], &vtmp[2*n]);
    }
    v2f.assign(nv, vacc);
    
    // sort edge array and shrink to required size
    ElementEdgeArray se;
    std::sort(edges.begin(), edges.end());
    ElementEdgeArray::iterator last;
    last = std::unique(edges.begin(), edges.end());
    se.insert(se.end(), edges.begin(), last);
    se.swap(edges);
  }
  
  // connect edges and vertices  
  const uint ne(edges.size());
  {
    uint k(0);
    Indices tmp(4*ne);
    for (uint i=0; i<ne; ++i) {
      tmp[k+0] = edges[i].source();
      tmp[k+1] = i;
      tmp[k+2] = edges[i].target();
      tmp[k+3] = i;
      k += 4;
    }
    v2e.assign(nv, tmp);
  }
  
  // construct connections between faces and edges 
  {
    Indices tmp(2*Element::maxedges());
    f2e.clear();
    f2e.beginCount(nf);
    for (uint i=0; i<nf; ++i) {
      uint nfe = elements[i]->edges(&tmp[0]);
      f2e.incCount(i, nfe);
    }
    f2e.endCount();
    
    Indices eacc;
    Indices etmp(2*Element::maxedges());
    for (uint i=0; i<nf; ++i) {
      uint nfe = elements[i]->edges(&tmp[0]);
      for (uint j=0; j<nfe; ++j) {
        uint ei = tsearchEdge( tmp[2*j], tmp[2*j+1] );
        f2e.append(i, ei);
        etmp[2*j] = ei;
        etmp[2*j+1] = i;
      }
      eacc.insert(eacc.end(), &etmp[0], &etmp[2*nfe]);
    }
    f2e.close();
    e2f.assign(ne, eacc);
  }
  
  // reduce point array sizes if necessary
  if (vtx.capacity() > vtx.size())
    PointList<3>(vtx).swap(vtx);
}
       
void HybridMesh::clear()
{
  vtx.clear();
  elements.clear();
  f2e.clear();
  v2e.clear();
  v2f.clear();
  e2f.clear();
}

void HybridMesh::transform(const Transformer & t)
{ 
  const uint nv(vtx.size());
  for (uint i=0; i<nv; ++i)
    vtx[i] = t.forward(vtx[i]);
}

void HybridMesh::add2viz(MeshFields & mf) const
{
  mf.clear();
  mf.addVertices( vtx );
  const uint nf(nelements());
  for (uint i=0; i<nf; ++i)
    elements[i]->add2viz(mf);
}

