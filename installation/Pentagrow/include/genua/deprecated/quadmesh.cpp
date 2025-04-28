
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       quadmesh.cpp
 * begin:      Oct 2004
 * copyright:  (c) 2004 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * simple datastructure for unstructured quad mesh
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */
 
#include <set>
#include "dimsearchtree.h"
#include "quadmesh.h"

using namespace std;

QuadMesh::QuadMesh(const PointGrid<3> & gd)
{
  vtx.resize(gd.size());  
  std::copy(gd.begin(), gd.end(), vtx.begin());
  
  uint nf, a, b, ld = gd.nrows();
  nf = (gd.nrows()-1)*(gd.ncols()-1);
  quads.reserve(nf);
  for (uint i=0; i<gd.nrows()-1; ++i) {
    for (uint j=0; j<gd.ncols()-1; ++j) {
      a = j*ld + i;
      b = (j+1)*ld + i;
      Quad q(this, a, a+1, b+1, b);
      quads.push_back(q);
    }
  }
}

uint QuadMesh::addVertex(const Vct3 & v)
{
  vtx.push_back(v);
  return vtx.size()-1;    
}    
    
uint QuadMesh::addQuad(const Quad & q)
{
  quads.push_back(q);
  return quads.size()-1;  
}

void QuadMesh::fixate()
{
  v2f.clear();
  uint vi[4];
  for (uint i=0; i<quads.size(); ++i) {
    quads[i].getVertices(vi);
    for (uint k=0; k<4; ++k)
      v2f[vi[k]].push_back(quads[i]);
  }  
}
    
QuadMesh::const_face_iterator QuadMesh::nb_face_begin(uint i) const
{
  VQuadMap::const_iterator itm = v2f.find(i);
  if (itm == v2f.end())
    throw Error("No such vertex in connectivity map: "+str(i));
  return itm->second.begin();
}
    
QuadMesh::const_face_iterator QuadMesh::nb_face_end(uint i) const    
{
  VQuadMap::const_iterator itm = v2f.find(i);
  if (itm == v2f.end())
    throw Error("No such vertex in connectivity map: "+str(i));
  return itm->second.end();  
}    
 
void QuadMesh::merge(const QuadMesh & a)
{
  uint vi[4], off = vtx.size();
  for (uint i=0; i<a.nvertices(); ++i)  
    vtx.push_back(a.vertex(i));
  for (uint i=0; i<a.nfaces(); ++i) {
    a.quad(i).getVertices(vi);
    Quad nq(this, vi[0]+off, vi[1]+off, vi[2]+off, vi[3]+off);
    quads.push_back(nq);
  }
  fixate();
}

void QuadMesh::clear()
{
  vtx.clear();
  quads.clear();
  v2f.clear();  
}

void QuadMesh::reverse()
{
  for (uint i=0; i<quads.size(); ++i)  
    quads[i].reverse();
}

void QuadMesh::cleanup(Real threshold)
{
  // remove duplicates and update
  unify(threshold);

  // determine referenced vertices
  uint vi[4];
  set<uint> iset;
  for (uint i=0; i<quads.size(); ++i) {
    quads[i].getVertices(vi);
    for (uint k=0; k<4; k++)
      iset.insert(vi[k]);
  }
  Indices idx(iset.begin(), iset.end());
  
  // keep only referenced vertices
  rename(idx);
}

void QuadMesh::unify(Real threshold)
{
  // create tree for point location queries
  DimSearchTree tree(vtx);

  // find duplicate vertices
  set<uint> dupl;
  Indices repl(vtx.size()), idt;
  uint count(0);
  PointList<3> kept;
  for (uint i=0; i<vtx.size(); i++) {
    if (dupl.find(i) == dupl.end()) {
      repl[i] = count;
      idt.clear();
      tree.find(vtx[i], threshold, idt);
      // idt = tree.equal(vtx[i], threshold);
      if (idt.size() > 1) {
        for (uint j=0; j<idt.size(); j++) {
          if (idt[j] > i) {
            dupl.insert(idt[j]);
            repl[idt[j]] = count;
          }
        }
      }
      count++;
      kept.push_back(vtx[i]);
    }
  }
  vtx.swap(kept);

  // change face array
  uint vi[4];
  QuadArray ftmp;
  for (uint i=0; i<quads.size(); ++i) {
    quads[i].getVertices(vi);
    for (uint k=0; k<4; ++k)
      vi[k] = repl[vi[k]];
    ftmp.push_back( Quad(this, vi) );
  }
  quads.swap(ftmp);
}

void QuadMesh::rename(const Indices & idx)
{
  // change vertex indices
  PointList<3> tv(idx.size());
  for (uint i=0; i<idx.size(); i++)
    tv[i] = vtx[idx[i]];
  tv.swap(vtx);
  assert(vtx.size() == idx.size());

  // change element indices
  uint vi[4];
  Indices::const_iterator pos;
  for (uint i=0; i<quads.size(); ++i) {
    quads[i].getVertices(vi);
    for (uint k=0; k<4; ++k) {
      pos = lower_bound(idx.begin(), idx.end(), vi[k]);
      assert(*pos == vi[k]);
      vi[k] = distance(idx.begin(), pos);
    }
    quads[i] = Quad(this, vi);
  }
  
  // recompute connectivity map
  fixate();
}

void QuadMesh::writeOogl(std::ostream & os) const
{
  uint vi[4];
  os << "{ OFF" << endl;
  os << vtx.size() << " " << quads.size() << " 1" << endl;
  for (uint i=0; i<vtx.size(); ++i)
    os << vtx[i] << endl; 
  for (uint i=0; i<quads.size(); ++i) {
    quads[i].getVertices(vi);
    os << "  4";
    for (uint k=0; k<4; ++k)
      os << " " << vi[k];
    os << endl;
  }
  os << "}" << endl;    
}

