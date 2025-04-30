
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
 
// #include <fpu_control.h>
#include <genua/meshfields.h>
#include <genua/synchron.h>
#include <genua/dimsearchtree.h>
#include <genua/dbprint.h>
#include "cascademesh.h"
#include "sides.h"
#include "dnrefine.h"
#include "dnmesh.h"

#include <deque>

using namespace std;

typedef enum {DnRegular, DnNeedle, DnHat} DnShape;

struct DnTriangleShape
{
  Real stretch;
  DnShape shape;
  uint elong, eshort;
};

static inline bool insert_once(Indices & idx, uint i)
{
  Indices::iterator pos;
  pos = lower_bound(idx.begin(), idx.end(), i);
  if (pos == idx.end() or *pos != i) {
    idx.insert(pos, i);
    return true;
  } else {
    return false;
  }
}

// --------------------------------------------------------------------------

// number of DnMesh instances
static bool jrsIsInitialized(false);

// mutex which protects object count
static Mutex DnObjectCountMutex;

// --------------------------------------------------------------------------

DnMesh::DnMesh(SurfacePtr s, DnType t) : 
  type(t), psf(s), depinsert(false), nowrefining(false)
{
  if (not jrsIsInitialized) {
    DnObjectCountMutex.lock();
    if (not jrsIsInitialized) {
      
      // modify i387 FPU control word to use 64 bit precision, not 80 bit
      // this does not work - just generates FP exceptions
      //    fpu_control_t cword = _FPU_DOUBLE;
      //    _FPU_SETCW(cword);
      
      // initialize Shewchuk's robust predicates
      jrsExactInit();
      jrsIsInitialized = true;
    }
    DnObjectCountMutex.unlock();
  }

  // decide if surface is wrapped in u-direction
  Vct3 p0( psf->eval(0.0, 0.5) );
  Vct3 p1( psf->eval(1.0, 0.5) );
  if (norm(p1-p0) < gmepsilon)
    uwrap = true;
  else
    uwrap = false;
  
  bAbort = false;
}

void DnMesh::init(uint nu, uint nv)
{
  Real u, v;
  PointGrid<2> pg(nu,nv);
  for (uint j=0; j<nv; ++j) {
    v = Real(j)/(nv-1);
    for (uint i=0; i<nu; ++i) {
      u = Real(i)/(nu-1);
      pg(i,j) = vct(u,v);
    }
  }
  init(pg);
}

void DnMesh::init(const Vector & up, const Vector & vp)
{
  const uint nu(up.size());
  const uint nv(vp.size());
  PointGrid<2> pg(nu,nv);
  for (uint j=0; j<nv; ++j) {
    for (uint i=0; i<nu; ++i) {
      pg(i,j) = vct(up[i],vp[j]);
    }
  }
  init(pg);
}

void DnMesh::init(const PointGrid<2> & pg)
{
  // delete current mesh
  clear();

  // add vertices
  const uint nv(pg.size());
  PointList<2> pts(nv);
  vertices.reserve(nv);
  for (uint i=0; i<nv; ++i) {
    vertices.push_back( DnVertex(*psf, pg[i]) );
    pts[i] = vertices.back().parpos();
  }

  // create vertex search tree
  btree = RSearchTree(pts);

  // construct triangles
  uint nr = pg.nrows();
  uint nc = pg.ncols();

  uint a, b, c, d;
  triangles.reserve((nr-1)*(nc-1));

  for (uint i=0; i<nr-1; ++i) {
    for (uint j=0; j<nc-1; ++j) {
      a = j*nr + i;
      b = j*nr + i+1;
      c = (j+1)*nr + i+1;
      d = (j+1)*nr + i;
      addQuad(a, b, c, d);
    }
  }

  // compute all connectivity data
  fixate();
}

void DnMesh::init(const PointGrid<2> & pg, Real maxstretch, uint kins)
{
  // delete current mesh
  clear();

  CascadeMesh csm(psf.get(), pg);
  csm.generate(maxstretch, kins);
  
  Indices itri;
  PointList<2> qts;
  csm.exportMesh(qts, itri);
  importMesh(qts, itri);
}


bool DnMesh::initPolygon(const PointList<2> & pts)
{
  clear();
  
  // add vertices
  const int nv(pts.size());
  vertices.resize(nv);
  Indices idx(nv);
  for (int i=0; i<nv; ++i) {
    vertices[i] = DnVertex(*psf, pts[i]);
    idx[i] = i;
  }
  
  // create vertex search tree
  btree = RSearchTree(pts);

  // generate first edge
  uint ei = addEdge(0, 1);
  
  // fill polygonal hole
  idx.erase(idx.begin(), idx.begin()+2);
  if (not triangulatePolygon(ei, idx))
    return false;

  fixate();
  return true;
}

void DnMesh::disableBoundarySplit()
{
  const int ne = edges.size();
  for (int i=0; i<ne; ++i) {
    const DnEdge & e(edges[i]);
    if (not e.isValid())
      continue;
    if (e.nNeighbors() < 2)
      insert_once(iNoSplit, uint(i));
  }
}

void DnMesh::enableBoundarySplit()
{
  Indices::iterator pos;
  const int ne = edges.size();
  for (int i=0; i<ne; ++i) {
    const DnEdge & e(edges[i]);
    if (not e.isValid())
      continue;
    if (e.nNeighbors() < 2) {
      pos = lower_bound(iNoSplit.begin(), iNoSplit.end(), uint(i));
      if (pos != iNoSplit.end() and int(*pos) == i)
        iNoSplit.erase(pos);
    }
  }
}

void DnMesh::addQuad(uint a, uint b, uint c, uint d)
{
  const Vct3 & pa( vertices[a].eval() );
  const Vct3 & pb( vertices[b].eval() );
  const Vct3 & pc( vertices[c].eval() );
  const Vct3 & pd( vertices[d].eval() );

  // option 1
  // addTriangle(a, b, c);
  // addTriangle(a, c, d);
  Vct3 n_abc( cross(pb-pa, pc-pa) );
  Vct3 n_acd( cross(pc-pa, pd-pa) );
  Real c1 = cosarg(n_abc, n_acd);
  
  // option 2
  // addTriangle(a, b, d);
  // addTriangle(b, c, d);
  Vct3 n_abd( cross(pb-pa, pd-pa) );
  Vct3 n_bcd( cross(pc-pb, pd-pb) );
  Real c2 = cosarg(n_abd, n_bcd);

  if ( fabs(c1-c2) > 0.05 ) {
    if (c1 > c2) {
      // if (norm(n_abc) > 0)
      addTriangle(a, b, c);
      // if (norm(n_acd) > 0)
      addTriangle(a, c, d);
    } else {
      // if (norm(n_abd) > 0)
      addTriangle(a, b, d);
      // if (norm(n_bcd) > 0)
      addTriangle(b, c, d);
    }
  } else {
    if (norm(pa-pc) < norm(pb-pd)) {
      // if (norm(n_abc) > 0)
      addTriangle(a, b, c);
      // if (norm(n_acd) > 0)
      addTriangle(a, c, d);
    } else {
      // if (norm(n_abd) > 0)
      addTriangle(a, b, d);
      // if (norm(n_bcd) > 0)
      addTriangle(b, c, d);
    }
  }
}

void DnMesh::cleanup(Real xyzt, Real uvt)
{
  // coordinate search tree
  uint nv(vertices.size());
  
  // map DnVertices to 3D points
  PointList<3> vtx(nv);
  for (uint i=0; i<nv; ++i)
    vtx[i] = vertices[i].eval();
  BSearchTree b3tree(vtx);
  
  // find (nearly) identical vertices
  Indices repl(nv), idt;
  fill(repl.begin(), repl.end(), NotFound);
  uint count(0);
  DnVertexArray kept;
  for (uint i=0; i<nv; ++i) {
    Vct2 iq = vertices[i].parpos();
    // for each vertex which is not yet marked as duplicate
    if (repl[i] == NotFound) {
      
      // mark as a vertex to keep
      repl[i] = count;
      
      // locate vertices within radius of threshold
      idt.clear();
      b3tree.find(vtx[i], xyzt, idt);
      
      // mark duplicates with indices beyond i
      for (uint j=0; j<idt.size(); ++j) {
        Real uvd = norm(iq - vertices[idt[j]].parpos());
        if (idt[j] > i and uvd < uvt)
          repl[idt[j]] = count;
      }
      
      // store vertex as kept
      ++count;
      kept.push_back( vertices[i] );
    }
    
    // skip vertices marked as duplicates
  }

  // eliminate duplicate vertices
  uint ndpl = nv - kept.size();
  kept.swap(vertices);
  
  // rebuild search tree
  nv = vertices.size();
  {
    PointList<2> uvp(nv);
    for (uint i=0; i<nv; ++i)
      uvp[i] = vertices[i].parpos();
    btree = RSearchTree(uvp);
  }
  
  // apply node index translation to triangles
  if (ndpl > 0) {
    const int nf(triangles.size());
    for (int i=0; i<nf; ++i) {
      DnTriangle & t(triangles[i]);
      if (not t.isValid())
        continue;
      
      t.itranslate(repl);
      if (t.hasDuplicates())
        t.invalidate();
      else
        t.computeSphere(*psf, vertices, (type == DnSpatial));
    }
    fixate();
  }
}

bool DnMesh::initBoundary(const PointList<2> & pts)
{
  // delete all current geometry
  clear();
  
  // can only do this in plane mode
  type = DnPlane;
  
  // start with two triangles which bound all of pts
  Vct2 plo, phi;
  plo = huge;
  phi = -huge;
  const uint np(pts.size());
  for (uint i=0; i<np; ++i) {
    for (uint k=0; k<2; ++k) {
      plo[k] = min(plo[k], pts[i][k]);
      phi[k] = max(phi[k], pts[i][k]);
    }
  }
  vertices.resize(4);
  vertices[0] = DnVertex(*psf, plo);
  vertices[1] = DnVertex(*psf, vct(phi[0], plo[1]));
  vertices[2] = DnVertex(*psf, phi);
  vertices[3] = DnVertex(*psf, vct(plo[0], phi[1]));
  addTriangle(0, 1, 2);
  addTriangle(2, 3, 0);
  
  // construct initial search tree
  PointList<2> sp(4);
  sp[0] = plo;
  sp[1] = vct(phi[0], plo[1]);
  sp[2] = phi;
  sp[3] = vct(plo[0], phi[1]);
  btree = RSearchTree(sp);
  
  fixate();
  
  // now, insert constrained edges
  Indices idx = addConstraint(pts);
  if (idx.size() != pts.size())
    return false;
  
  // finally, remove all triangles connected to the four initial vertices
  Indices tkill;
  sort_unique(idx);
  for (uint k=0; k<4; ++k) {
    if (not binary_search(idx.begin(), idx.end(), k)) {
      const Indices & nbf(vertices[k].nbTriangles());
      tkill.insert(tkill.end(), nbf.begin(), nbf.end());
    }
  }
  
  // If degenerate triangles are removed here, we end up with triangle location
  // failures later when inserting additional vertices - no good
  
  //   // test if any of the present triangles is degenerate
  //   const uint n(triangles.size());
  //   for (uint i=0; i<n; ++i) {
  //     const DnTriangle & t(triangles[i]);
  //     if (t.isValid() and norm(t.normal(vertices)) < gmepsilon)
  //       tkill.push_back(i);
  //   }
  
  sort_unique(tkill);
  const uint nt(tkill.size());
  for (uint i=0; i<nt; ++i) {
    uint ti = tkill[i];
    const uint *nbe(triangles[ti].nbEdges());
    for (uint k=0; k<3; ++k) {
      assert(nbe[k] != NotFound);
      assert(edges[nbe[k]].isValid());
      edges[nbe[k]].detachTriangle(ti);
    }
    killTriangle(ti);
  }

  return true;
}

uint DnMesh::importMesh(const PointList<2> & pts, const Indices & qtri)
{
  vertices.clear();
  const uint nv(pts.size());
  vertices.resize(nv);
  PointList<2> vtx(nv);
  for (uint i=0; i<nv; ++i) {
    vertices[i] = DnVertex(*psf, pts[i]);
    vtx[i] = vertices[i].parpos();
  }
  btree = RSearchTree(vtx);
  
  uint k;
  triangles.clear();
  const uint nt(qtri.size()/3);
  for (uint i=0; i<nt; ++i) {
    k = 3*i;
    addTriangle(qtri[k], qtri[k+1], qtri[k+2]);
  }
  
  // generate edges and connectivity
  fixate();
  
  return nt;
}

uint DnMesh::exportMesh(PointList<2> & pts, Indices & qtri) const
{
  const uint nv(vertices.size());
  const uint nt(triangles.size() - iDeadTriangles.size() );
  pts.resize(nv);
  for (uint i=0; i<nv; ++i)
    pts[i] = vertices[i].parpos();
  
  uint k(0);
  qtri.resize(3*nt);
  const uint nta(triangles.size());
  for (uint i=0; i<nta; ++i) {
    const DnTriangle & t(triangles[i]);
    if (t.isValid()) {
      const uint *vi(t.vertices());
      assert(k+2 < qtri.size());
      qtri[k] = vi[0];
      qtri[k+1] = vi[1];
      qtri[k+2] = vi[2];
      k += 3;
    }
  }
  
  return k/3;
}

uint DnMesh::exportMesh(PointList<2> & pp, PointList<3> & vtx, 
                        PointList<3> & nrm, Indices & qtri) const
{
  const uint nv(vertices.size());
  const uint nt(triangles.size() - iDeadTriangles.size() );
  pp.resize(nv);
  vtx.resize(nv);
  nrm.resize(nv);
  for (uint i=0; i<nv; ++i) {
    pp[i] = vertices[i].parpos();
    vtx[i] = vertices[i].eval();
    nrm[i] = vertices[i].normal();
  }
  
  uint k(0);
  qtri.resize(3*nt);
  const uint nta(triangles.size());
  for (uint i=0; i<nta; ++i) {
    const DnTriangle & t(triangles[i]);
    if (t.isValid()) {
      const uint *vi(t.vertices());
      assert(k+2 < qtri.size());
      qtri[k] = vi[0];
      qtri[k+1] = vi[1];
      qtri[k+2] = vi[2];
      k += 3;
    }
  }
  
  return k/3;
}

uint DnMesh::addEdge(uint a, uint b)
{  
  DnEdge e(a,b);
  if (iDeadEdges.empty()) {
    edges.push_back(e);
    return edges.size()-1;
  } else {
    uint i = iDeadEdges.back();
    edges[i] = e;
    iDeadEdges.pop_back();
    return i;
  }
}

uint DnMesh::addTriangle(uint a, uint b, uint c)
{
  DnTriangle t(a, b, c);
  fixDirection(t);
  t.computeSphere(*psf, vertices, (type == DnSpatial));
  
  uint ti;
  if (iDeadTriangles.empty()) {
    triangles.push_back(t);
    ti = triangles.size()-1;
  } else {
    ti = iDeadTriangles.back();
    triangles[ti] = t;
    iDeadTriangles.pop_back();
  }

  const uint *vi(triangles[ti].vertices());
  vertices[vi[0]].attachTriangle(ti);
  vertices[vi[1]].attachTriangle(ti);
  vertices[vi[2]].attachTriangle(ti);
  
  return ti;
}

void DnMesh::killTriangle(uint ti)
{
  if (ti == NotFound)
    return;

  assert(ti < triangles.size());
  assert(triangles[ti].isValid());

  const uint *vi(triangles[ti].vertices());
  vertices[vi[0]].detachTriangle(ti);
  vertices[vi[1]].detachTriangle(ti);
  vertices[vi[2]].detachTriangle(ti);
  
  triangles[ti].invalidate();
  iDeadTriangles.push_back(ti);
}

void DnMesh::killEdge(uint ei)
{
  if (ei == NotFound)
    return;
  
  edges[ei].invalidate();
  iDeadEdges.push_back(ei);
}

uint DnMesh::elimNeedles(Real maxstretch, Real maxphi)
{
  // this does not work at all, for the moment
  return 0;
  
  Real mincphi = cos(maxphi);
  uint nmod(0), nkill;
  do {

    nkill = 0;
    const int ne(nedges());
    Indices vmod;
    for (int i=0; i<ne; ++i) {
      
      DnEdge & e(edges[i]);
      if ((not e.isValid()) or (e.nNeighbors() != 2))
        continue;
      
      if (binary_search(vmod.begin(), vmod.end(), e.source()))
        continue;
      if (binary_search(vmod.begin(), vmod.end(), e.target()))
        continue;
      
      uint nnb, v[4], nbf[2];
      v[0] = e.source();
      v[2] = e.target();
      Real cphi = cosarg(normal(v[0]), normal(v[2]));
      if (cphi < mincphi)
        continue;
      
      nnb = e.nNeighbors();
      if (nnb != 2)
        continue;
      
      nbf[0] = e.nbTriangle(0);
      nbf[1] = e.nbTriangle(1);
      if (nbf[0] == NotFound or nbf[1] == NotFound)
        continue;
      
      v[1] = triangles[nbf[0]].opposedVertex(e);
      v[3] = triangles[nbf[1]].opposedVertex(e);
      if (v[1] == NotFound or v[3] == NotFound)
        continue;
      
      const Vct3 & ps( position(v[0]) );
      const Vct3 & pt( position(v[2]) );
      Real elen = norm(ps - pt);
      Vct3 midp = 0.5*(ps + pt);
      Real s1 = norm(position(v[1]) - midp) / elen;
      Real s2 = norm(position(v[3]) - midp) / elen;
      if (max(s1,s2) < maxstretch)
        continue;
      
      // collapse edge to midpoint by connecting all triangles
      // hanging on t to s instead and moving s to midpoint
      // find f2 and f3, replace edge and vertex connections
      killTriangle( nbf[0] );
      killTriangle( nbf[1] );
      killEdge(i);
      const Indices & vnf(vertices[v[2]].nbTriangles());
      const int nf(vnf.size());
      for (int j=0; j<nf; ++j)
        if (vnf[j] != NotFound)
          triangles[vnf[j]].replaceVertex(v[2], v[0]);
      vertices[v[0]] = DnVertex(*psf, 0.5*(parpos(v[0]) + parpos(v[1])));
      
      for (int k=0; k<4; ++k)
        insert_once(vmod, v[k]);
      
      ++nkill;
    }
    nmod += nkill;
    fixate();
  } while (nkill > 0);
  
  return nmod;
}

Indices DnMesh::addConstraint(const PointList<2> & pts, bool allowSplit)
{
  const uint np(pts.size());
  Indices idx(np), opbv(np);
  uint ilast, inext, ei;

  // list of opposing boundary vertices
  for (uint i=0; i<np; ++i)
    opbv[i] = NotFound;
  
  // insert first vertex
  bool boundaryInsert = false;
  ilast = insertVertex(pts[0], boundaryInsert);
  if (ilast == NotFound) {
    stringstream ers;
    ers << "Failed to insert first vertex at " << pts[0] << endl;
    errmsg = ers.str();
    return Indices();
  }
  idx[0] = inext = ilast;
  
  // if this vertex is on a wrapped boundary, insert the opposing
  // vertex as well
  if (uwrap) {
    if (pts[0][0] < 0.001 and boundaryInsert) {
      uint nins = insertVertex(vct(1.0, pts[0][1]), boundaryInsert);
      if (nins == NotFound) {
        stringstream ers;
        ers << "Failed to insert opposed vertex of " << pts[0] << endl;
        errmsg = ers.str();
        return Indices();
      }
      opbv[0] = nins;
    } else if (pts[0][0] > 0.999 and boundaryInsert) {
      uint nins = insertVertex(vct(0.0, pts[0][1]), boundaryInsert);
      if (nins == NotFound) {
        stringstream ers;
        ers << "Failed to insert opposed vertex of " << pts[0] << endl;
        errmsg = ers.str();
        return Indices();
      }
      opbv[0] = nins;
    }
  }
  
  // insert all vertices first, make mesh conforming
  
  for (uint i=1; i<np; ++i) {
    ilast = inext;
    
    inext = insertVertex(pts[i], boundaryInsert);
    assert(inext != ilast);
    if (inext == NotFound) {
      stringstream ers;
      ers << "Failed to insert vertex " << i << '/' << np
          << " at " << pts[i] << endl;
      ers << "Previous vertex was " << pts[i-1] << endl;
      errmsg = ers.str();
      return Indices();
    }
    idx[i] = inext;
    
    // if this vertex is on a wrapped boundary, insert the opposing
    // vertex as well
    if (uwrap) {
      if (pts[i][0] < 0.001 and boundaryInsert) {
        uint nins = insertVertex(vct(1.0, pts[i][1]), boundaryInsert);
        if (nins == NotFound) {
          stringstream ers;
          ers << "Failed to insert opposed vertex of " << pts[i] << endl;
          errmsg = ers.str();
          return Indices();
        }
        opbv[i] = nins;
      } else if (pts[i][0] > 0.999 and boundaryInsert) {
        uint nins = insertVertex(vct(0.0, pts[i][1]), boundaryInsert);
        if (nins == NotFound) {
          stringstream ers;
          ers << "Failed to insert opposed vertex of " << pts[i] << endl;
          errmsg = ers.str();
          return Indices();
        }
        opbv[i] = nins;
      }
    }
  }
  
  // connect segments
  ilast = idx[0];
  for (uint i=1; i<np; ++i) {

    inext = idx[i];

    if (uwrap) {
      // constraint lines cannot cross the parameter seam u=0/1, so
      // that we need to consider the opposed vertices for those cases
      const Vct2 & plast( vertices[ilast].parpos() );
      const Vct2 & pnext( vertices[inext].parpos() );
      Real du = fabs(pnext[0] - plast[0]);
      uint irep;
      if (du > 0.5) {
        if (opbv[i-1] != NotFound) {
          irep = opbv[i-1];
          if (irep == ilast)
            irep = idx[i-1];
          dbprint("ilast: Replace ", ilast, " at ", vertices[ilast].parpos() );
          dbprint("with ", irep, " at ", vertices[irep].parpos() );
          dbprint("to connect to ", inext, " at ", vertices[inext].parpos() );
          ilast = irep;
        } else if (opbv[i] != NotFound) {
          irep = opbv[i];
          if (irep == inext)
            irep = idx[i];
          dbprint("inext: Replace ", inext, " at ", vertices[inext].parpos() );
          dbprint("with ", irep, " at ", vertices[irep].parpos() );
          dbprint("to connect to ", ilast, " at ", vertices[ilast].parpos() );
          inext = irep;
        } else {
          dbprint("Warning: Constraint appears to cross parameter boundary: " );
          dbprint("From ", ilast, " at ", vertices[ilast].parpos() );
          dbprint("to ", inext, " at ", vertices[inext].parpos() );
        }

        // after this modification, we may have generated the case
        // inext == ilast which, of course, does not require edge manipulations
        if (inext == ilast)
          continue;
      }
    }
    
    // enforce constraint edge if the two points are distinct
    Real dst;
    if (type == DnSpatial)
      dst = norm(vertices[inext].eval() - vertices[ilast].eval());
    else
      dst = norm(vertices[inext].parpos() - vertices[ilast].parpos());

    if (dst > gmepsilon) {
      ei = enforceEdge(ilast, inext);
      if (ei != NotFound) {
        assert(edges[ei].find(ilast) != NotFound);
        assert(edges[ei].find(inext) != NotFound);
        forbidFlip(ei);
        if (not allowSplit)
          forbidSplit(ei);
      } else {
        
        // TODO: Implement constraint splitting if permissible
        ei = insertSegment(ilast, inext);
        if (ei == NotFound)
          return Indices();
      }
      assert(findEdgeTopo(ilast, inext) != NotFound);
      assert(not canFlip(findEdgeTopo(ilast, inext)));
    }
    
    ilast = inext;
  }
  
  return idx;
}

uint DnMesh::insertVertex(const Vct2 & p, bool &onBoundary)
{
  onBoundary = false;

  // debug : treat boundary vertex differently
  if (whichside(p) != none) {
    onBoundary = true;
    return insertBoundaryVertex(p);
  }

  // create vertex, compute its position
  DnVertex vnew(*psf, p);

  // locate nearest old vertex
  uint vnear = btree.nearest(p);
  
  // if the new and the nearest old vertex are identical,
  // return immediately
  if (norm(p - vertices[vnear].parpos()) < gmepsilon)
    return vnear;
  
  // find the triangle containing the new vertex (in the plane)
  uint ni, ti;
  int inside;
  
  ni = vertices.size();
  vertices.push_back(vnew);
  inside = locateTriangle(ni, vnear, ti);
  
  // split triangle or edge
  if (inside == -1) {
    btree.insert(p);
    splitTriangle(ti, ni);
  } else if (inside >= 0 and inside < 3) {
    btree.insert(p);
    const uint *nbe(triangles[ti].nbEdges());
    assert(nbe[inside] != NotFound);
    onBoundary = ( edges[nbe[inside]].nNeighbors() == 1 );
    splitEdge(nbe[inside], ni);
  } else {
    
    // not inside any triangle and not on an edge
    vertices.pop_back();
    return NotFound;
  }
  
  return ni;
}

uint DnMesh::insertBoundaryVertex(const Vct2 & p, Real ptol)
{
  // create vertex, compute its position
  DnVertex vnew(*psf, p);

  // locate nearest old vertex
  uint vnear = btree.nearest(p);

  // if the new and the nearest old vertex are identical, return immediately
  if (sq(p - vertices[vnear].parpos()) < sq(ptol))
    return vnear;

  // identify the boundary/boundaries which p is on
  int pBoundary = BoundaryFlag::eval(p, ptol);

  // debug
  //dbprint("***", p, "p boundary:", pBoundary);

  // Algorithm
  // Pick a vertex (start with the one nearest to p) and walk through all
  // of the ring-1 edges around that vertex. If one of the edges is on a
  // boundary, try to project p onto that edge. If that succeeds, split that
  // edge and return the inserted point, otherwise, continue the search with
  // the end points of the processed edge.

  // keep track of all edges/vertices already tested
  std::vector<bool> vtouched( vertices.size(), false );
  std::vector<bool> etouched( edges.size(), false );

  // vertex queue for processing
  std::deque<uint> vqueue;
  vqueue.push_back(vnear);

  Indices etmp;
  uint ixe = NotFound;
  while (not vqueue.empty()) {

    // collect edges in the ring-1 of current vertex
    uint vcur = vqueue.front();
    vqueue.pop_front();
    collectNbEdges(vcur, etmp, true);
    vtouched[vcur] = true;

    const int ne = etmp.size();
    for (int i=0; i<ne; ++i) {

      // ignore edges already processed earlier
      if (etouched[etmp[i]])
        continue;

      // mark edge as processed
      etouched[etmp[i]] = true;

      const DnEdge & e( edges[etmp[i]] );
      uint src = e.source();
      uint trg = e.target();

      // check whether p is close enough to one of the end points
      const Vct2 & vs( vertices[src].parpos() );
      const Vct2 & vt( vertices[trg].parpos() );
      if (sq(p-vs) < sq(ptol))
        return src;
      if (sq(p-vt) < sq(ptol))
        return trg;

      // ignore edge if one of the end points is not on p's boundary
      int sBoundary = BoundaryFlag::eval( vs, ptol );
      int tBoundary = BoundaryFlag::eval( vt, ptol );
      bool sp = BoundaryFlag::share(pBoundary, sBoundary);
      bool tp = BoundaryFlag::share(pBoundary, tBoundary);
      if ( sp and (not tp) ) {
        // dbprint(vt, "t boundary: ", tBoundary);
        if (not vtouched[src])
          vqueue.push_back(src);
        continue;
      } else if ( tp and (not sp) ) {
        // dbprint(vs, "s boundary: ", sBoundary);
        if (not vtouched[trg])
          vqueue.push_back(trg);
        continue;
      } else if (not (sp or tp)) {

        // this is not particularly logical, but necesary because there may
        // be the case that none of the edges in etmp touches the same boundary
        // as p, which would lead to an early termination of the search
        if (not vtouched[src])
          vqueue.push_back(src);
        if (not vtouched[trg])
          vqueue.push_back(trg);
        continue;
      }

      // project point on edge, use only one coordinate
      int c = BoundaryFlag::onU(pBoundary) ? 1 : 0;
      Real t = (p[c] - vs[c]) / (vt[c] - vs[c]);
      if (t > 0.0 and t < 1.0) {
        ixe = etmp[i];
        break;
      } else {
        // dbprint(vs, p, vt);
        // dbprint("Projection foot:", t);
      }

      // edge is on the right boundary, but point projection is outside
      // continue the search with the end points of this edge
      if (not vtouched[src])
        vqueue.push_back(src);
      if (not vtouched[trg])
        vqueue.push_back(trg);

    } // edge loop

  } // while (not vqueue.empty())

  if (ixe == NotFound) {
    abort();
    return NotFound;
  }

  // found edge ixe into which p is to be inserted
  uint ni = vertices.size();
  vertices.push_back(vnew);
  btree.insert(p);
  splitEdge(ixe, ni);

  return ni;

  //  // create vertex, compute its position
  //  DnVertex vnew(*psf, p);

  //  // locate nearest old vertex
  //  uint vnear = btree.nearest(p);
  
  //  // if the new and the nearest old vertex are identical,
  //  // return immediately
  //  if (norm(p - vertices[vnear].parpos()) < gmepsilon)
  //    return vnear;
  
  //  // locate edge on which to force insertion
  //  uint ixe = NotFound;
  //  const Indices & nbf = vertices[vnear].nbTriangles();
  //  const int nf = nbf.size();
  //  for (int i=0; i<nf; ++i) {
  //    const DnTriangle & t( triangles[nbf[i]] );
  //    const uint *nbe = t.nbEdges();
  //    for (int k=0; k<3; ++k) {
  //      assert(nbe[k] != NotFound);
  //      const DnEdge & e( edges[nbe[k]] );
  //      assert(e.isValid());
  //      const Vct2 & src( vertices[e.source()].parpos() );
  //      const Vct2 & trg( vertices[e.target()].parpos() );

  //      if (whichside(src) != none and whichside(trg) != none) {

  //        if (norm(p-src) < ptol)
  //          return e.source();
  //        else if (norm(p-trg) < ptol)
  //          return e.target();

  //        Real tfoot = dot( p-src, trg-src ) / dot(trg-src, trg-src);
  //        Real ldst = norm( p - ( (1.-tfoot)*src + tfoot*trg ) );
  //        if (ldst < gmepsilon) {
  //          if (tfoot == 0.0)
  //            return e.source();
  //          else if (tfoot == 1.0)
  //            return e.target();
  //          else if (tfoot > 0.0 and tfoot < 1.0) {
  //            ixe = nbe[k];
  //            break;
  //          } else {
  //            dbprint(src, p, trg);
  //            dbprint("foot ", tfoot, " ldst ", ldst);
  //          }
  //        }
  //      } else {
  //        dbprint("Edge not on boundary ", src, trg);
  //      }
  //    }
  //    if (ixe != NotFound)
  //      break;
  //  }
  
  //  if (ixe == NotFound) {
  //    abort();
  //    return NotFound;
  //  }
  
  //  uint ni = vertices.size();
  //  vertices.push_back(vnew);
  //  btree.insert(p);
  //  splitEdge(ixe, ni);
  
  //  return ni;
}

uint DnMesh::addHole(const Vct2 & p)
{
  // create vertex, compute its position
  DnVertex vnew(*psf, p);
  
  // locate nearest old vertex
  uint ti, nk;
  uint vnear = btree.nearest(p);
  int inside;
  inside = locateTriangle(p, vnear, ti);
  
  if (inside == -1) {
    // nk = recursiveErase(ti);
    nk = carveHole(ti);
  } else if (inside > -1 and inside < 3) {

    // hole point managed to end up on an edge
    assert(ti != NotFound);
    assert(inside < 3);
    const uint *nbe(triangles[ti].nbEdges());
    uint ei = nbe[inside];

    // check if this edge is constrained
    if (not canFlip(ei))
      return 0;

    // otherwise, simply start at its first neighbor
    // nk = recursiveErase(edges[ei].nbTriangle(0));
    nk = carveHole(edges[ei].nbTriangle(0));
  } else {
    return 0;
  }

  return nk;
}

int DnMesh::locateTriangle(const Vct2 & p, uint vnear, uint & ti) const
{
  int inside(-2);
  Indices fc(vertices[vnear].nbTriangles());
  Indices fout, fnb;

  while (not fc.empty()) {
    
    fnb.clear();
    const uint n(fc.size());
    for (uint i=0; i<n; ++i) {
      inside = triangles[fc[i]].isInside(edges, vertices, p);
      if (inside > -2) {
        ti = fc[i];
        return inside;
      } else {
        fout.push_back(fc[i]);
        const uint *vi(triangles[fc[i]].vertices());
        for (uint k=0; k<3; ++k) {
          const Indices & nbf(vertices[vi[k]].nbTriangles());
          fnb.insert(fnb.end(), nbf.begin(), nbf.end());
        }
      }
    }

    // Still no triangle found in this neighborhood. Expand search.
    fc.clear();
    sort_unique(fnb);
    sort_unique(fout);
    set_difference( fnb.begin(), fnb.end(),
                    fout.begin(), fout.end(),
                    back_inserter(fc) );
  }
  
  return inside;
}

int DnMesh::locateTriangle(uint ni, uint vnear, uint & ti) const
{
  int inside(-2);
  Indices bde;
  Indices fout, fnb;
  Indices fc(vertices[vnear].nbTriangles());
  while (not fc.empty()) {

    fnb.clear();
    const uint n(fc.size());
    for (uint i=0; i<n; ++i) {
      inside = isInside(fc[i], ni);
      if (inside > -2) {
        ti = fc[i];
        return inside;
      } else {
        fout.push_back(fc[i]);
        const uint *vi(triangles[fc[i]].vertices());
        const uint *nbe( triangles[fc[i]].nbEdges() );
        for (uint k=0; k<3; ++k) {
          const Indices & nbf(vertices[vi[k]].nbTriangles());
          fnb.insert(fnb.end(), nbf.begin(), nbf.end());

          // collect boundary edges for backup search
          assert(nbe[k] != NotFound);
          if (nbe[k] != NotFound) {
            const DnEdge & e( edges[nbe[k]] );
            if (e.nNeighbors() == 1)
              bde.push_back(nbe[k]);
          }
        }
      }
    }

    // Still no triangle found in this neighborhood. Expand search.
    fc.clear();
    sort_unique(fnb);
    sort_unique(fout);
    set_difference( fnb.begin(), fnb.end(),
                    fout.begin(), fout.end(),
                    back_inserter(fc) );
  }

  // we end up at this point if the location test failed for all triangles,
  // which may happen for points which are extremely close to the parametric
  // boundary but not exactly on it, in spatial mode
  const Vct2 & qni = vertices[ni].parpos();
  const int bflag = BoundaryFlag::eval( qni, 0.001 );
  const int c = BoundaryFlag::onU(bflag) ? 1 : 0;
  if (bflag != 0) {
    const int ne = bde.size();
    for (int i=0; i<ne; ++i) {
      const DnEdge & e( edges[bde[i]] );
      assert(e.nNeighbors() == 1);
      const Vct2 & ps( vertices[e.source()].parpos() );
      const Vct2 & pt( vertices[e.target()].parpos() );
      Real t = (qni[c] - ps[c]) / (pt[c] - ps[c]);
      if (t >= 0.0 and t <= 1.0) {
        ti = e.nbTriangle(0);
        assert(ti != NotFound);
        uint teix = triangles[ti].findEdge(bde[i]);
        assert(teix != NotFound);
        return teix;
      }
    }
  }
  
  // abort on location failure in debugging mode
#ifndef NDEBUG
  if (inside == -2) {
    clog << "Triangle location failed." << endl;
    if (type == DnPlane)
      pToXml().write("locationfailure.zml", XmlElement::ZippedXml);
    else
      toXml().write("locationfailure.zml", XmlElement::ZippedXml);
    abort();
  }
#endif  
  
  return inside;
}

void DnMesh::splitTriangle(uint ti, uint ni)
{
  // copy connectivity data of old triangle
  uint v[3];
  uint nbe[3];
  memcpy(nbe, triangles[ti].nbEdges(), 3*sizeof(uint));

  // vertices v are ordered so that v[i] is opposed edge nbe[i]
  for (uint k=0; k<3; ++k) {
    assert(nbe[k] != NotFound);
    v[k] = triangles[ti].opposedVertex( edges[nbe[k]] );
    assert(v[k] != NotFound);
  }

  // delete old triangle
  killTriangle(ti);

  // create new edges and triangles
  uint ne[3], nt[3];
  for (uint k=0; k<3; ++k) {
    ne[k] = addEdge(v[k], ni);
    const DnEdge & e(edges[nbe[k]]);
    nt[k] = addTriangle(e.source(), e.target(), ni);
  }

  // store new edge and triangle indices
  newEdges.insert(newEdges.end(), ne, ne+3);
  newTriangles.insert(newTriangles.end(), nt, nt+3);
  
  // connect new triangles with edges
  static const uint ie1[] = {1, 2, 0};
  static const uint ie2[] = {2, 0, 1};
  for (uint k=0; k<3; ++k) {
    DnEdge & e(edges[nbe[k]]);
    e.replaceTriangle(ti, nt[k]);
    edges[ne[ie1[k]]].attachTriangle(nt[k]);
    edges[ne[ie2[k]]].attachTriangle(nt[k]);
    triangles[nt[k]].attachEdge(nbe[k]);
    triangles[nt[k]].attachEdge(ne[ie1[k]]);
    triangles[nt[k]].attachEdge(ne[ie2[k]]);
  }

  // establish Delaunay property by recursive edge flips
  for (uint k=0; k<3; ++k)
    legalizeEdge(nbe[k], ni);
}

bool DnMesh::splitEdge(uint ei, uint ni)
{
  if (not canSplit(ei))
    return false;

  // need to mark new edges unflippable if we split constrained edges
  bool canflip = canFlip(ei);
  bool iskink = isKink(ei);
  uint nnb, v[4], e[4], f[2];
  nnb = findNeighborhood(ei, v, e, f);
  assert(nnb > 0);
  
  // remove old edge and triangles
  killEdge(ei);
  for (uint k=0; k<2; ++k)
    if (f[k] != NotFound)
      killTriangle(f[k]);

  // create new edges
  uint ne[4];
  ne[0] = addEdge(v[0], ni);
  ne[1] = addEdge(v[2], ni);
  if (not canflip) {
    forbidFlip(ne[0]);
    forbidFlip(ne[1]);
  }
  
  if (iskink) {
    insert_once(iKinkEdge, ne[0]);
    insert_once(iKinkEdge, ne[1]);
  }
  
  if (v[1] != NotFound)
    ne[2] = addEdge(v[1], ni);
  else
    ne[2] = NotFound;
  if (v[3] != NotFound)
    ne[3] = addEdge(v[3], ni);
  else
    ne[3] = NotFound;

  // create new triangle
  uint nt[4];
  for (uint k=0; k<4; ++k) {
    if (e[k] != NotFound) {
      const DnEdge & eroot(edges[e[k]]);
      nt[k] = addTriangle(eroot.source(), eroot.target(), ni);
    } else {
      nt[k] = NotFound;
    }
  }

  // store new triangle indices
  newEdges.insert(newEdges.end(), ne, ne+4);
  newTriangles.insert(newTriangles.end(), nt, nt+4);

  // connect new triangles with edges
  static const uint oldf[] = {1, 1, 0, 0};
  static const uint ie1[] = {1, 3, 0, 2};
  static const uint ie2[] = {3, 0, 2, 1};
  for (uint k=0; k<4; ++k) {
    if (e[k] != NotFound) {
      assert(f[oldf[k]] != NotFound);
      DnEdge & eroot(edges[e[k]]);
      DnTriangle & t(triangles[nt[k]]);
      eroot.replaceTriangle(f[oldf[k]], nt[k]);
      assert(ne[ie1[k]] != NotFound);
      assert(ne[ie2[k]] != NotFound);
      edges[ne[ie1[k]]].attachTriangle(nt[k]);
      edges[ne[ie2[k]]].attachTriangle(nt[k]);
      t.attachEdge(e[k]);
      t.attachEdge(ne[ie1[k]]);
      t.attachEdge(ne[ie2[k]]);
    }
  }

  // establish Delaunay property by recursive edge flips
  for (uint k=0; k<4; ++k)
    legalizeEdge(e[k], ni);

  //#ifndef NDEBUG
  //  {
  //    Indices nbv, dmy;
  //    checkConnectivity(ni, nbv);
  //    for (uint i=0; i<4; ++i) {
  //      if (v[i] != NotFound) {
  //        checkConnectivity(v[i], nbv);
  //      }
  //    }
  //    for (uint i=0; i<nbv.size(); ++i)
  //      checkConnectivity(nbv[i], dmy);
  //  }
  //#endif
  
  return true;
}

bool DnMesh::flipEdge(uint ei)
{
  if (ei == NotFound)
    return false;
  
  if (not canFlip(ei))
    return false;
  
  if (nowrefining and isKink(ei))
    return false;
  
  uint nnb, v[4], e[4], f[2];
  nnb = findNeighborhood(ei, v, e, f);

  // cannot flip if neighborhood is incomplete
  if (nnb != 2)
    return false;

  // never flip an edge if its immediate neighborhood is not convex
  if (not isConvexSet(v))
    return false;
  
  // do not flip if the flipped edge exists...
  if (findEdgeTopo(v[1], v[3]) != NotFound)
    return false;
  
  // do not flip if the new end points end up on different
  // sides of the surface (avoid edges with cut through wing leading edge)
  Real dn1 = dot(vertices[v[0]].normal(), vertices[v[2]].normal());
  Real dn2 = dot(vertices[v[1]].normal(), vertices[v[3]].normal());
  if (dn2 < 0.0 and dn2 < dn1)
    return false;
  
  // change central edge connections
  edges[ei].reconnect(v[1], v[3]);
  edges[ei].attachTriangle(f[0]);
  edges[ei].attachTriangle(f[1]);
  
  // reconnect central faces
  triangles[f[0]].reconnect(v[1], v[2], v[3]);
  triangles[f[1]].reconnect(v[1], v[3], v[0]);

  // recompute information which depends on vertex indices
  fixDirection(triangles[f[0]]);
  fixDirection(triangles[f[1]]);
  triangles[f[0]].computeSphere(*psf, vertices, (type == DnSpatial));
  triangles[f[1]].computeSphere(*psf, vertices, (type == DnSpatial));

  // change vertex-face connections
  vertices[v[0]].detachTriangle(f[0]);
  vertices[v[2]].detachTriangle(f[1]);
  vertices[v[1]].attachTriangle(f[1]);
  vertices[v[3]].attachTriangle(f[0]);

  // connect new triangles to edges
  triangles[f[0]].attachEdge(ei);
  triangles[f[0]].attachEdge(e[0]);
  triangles[f[0]].attachEdge(e[3]);
  triangles[f[1]].attachEdge(ei);
  triangles[f[1]].attachEdge(e[1]);
  triangles[f[1]].attachEdge(e[2]);

  // connect outer edges to triangles
  edges[e[0]].replaceTriangle(f[1], f[0]);
  edges[e[2]].replaceTriangle(f[0], f[1]);
  
  newTriangles.push_back(f[0]);
  newTriangles.push_back(f[1]);
  
  return true;
}

bool DnMesh::legalizeEdge(uint ei, uint v)
{
  if (ei == NotFound)
    return false;

  // cannot flip constrained edge
  if (not canFlip(ei))
    return false;
  
  // cannot flip if edge is on boundary
  if (edges[ei].nNeighbors() < 2)
    return false;

  // identify triangle to test with
  uint tf, f[2];
  f[0] = edges[ei].nbTriangle(0);
  f[1] = edges[ei].nbTriangle(1);
  assert(f[0] != NotFound);
  assert(f[1] != NotFound);
  if (triangles[f[0]].find(v) == NotFound)
    tf = f[0];
  else
    tf = f[1];
  assert(triangles[tf].isValid());

  // store the two other edges of tf, they are candidates
  // for further edge flips in case ei is illegal
  uint ec[2], nbi(0);
  const uint *nbe(triangles[tf].nbEdges());
  for (uint k=0; k<3; ++k) {
    if (nbe[k] != ei) {
      ec[nbi] = nbe[k];
      ++nbi;
    }
  }
  assert(nbi == 2);
  
  // test if edge is locally Delaunay
  bool isLegal(false);
  switch (type) {
  case DnPlane:
    isLegal = (triangles[tf].inCircle(vertices, v) <= 0);
    break;
  case DnSpatial:
    isLegal = (triangles[tf].inSphere(vertices, v) <= 0);
    break;
  }

  // flip recursively if illegal
  if (not isLegal) {

    // flip offending edge
    bool flipped = flipEdge(ei);
    if (not flipped)
      return false;

    // test adjacent edges for legality
    legalizeEdge(ec[0], v);
    legalizeEdge(ec[1], v);
    return true;
  }
  
  return false;
}

void DnMesh::collectNbEdges(uint v, Indices & edg, bool allEdges) const
{
  edg.clear();
  if (v == NotFound)
    return;
  
  const Indices & nbf(vertices[v].nbTriangles());
  const uint nf(nbf.size());
  for (uint i=0; i<nf; ++i) {
    if (nbf[i] == NotFound)
      continue;
    const uint *nbe(triangles[nbf[i]].nbEdges());
    for (uint k=0; k<3; ++k) {
      assert(nbe[k] != NotFound);
      const DnEdge & e(edges[nbe[k]]);
      if (allEdges or e.source() == v or e.target() == v)
        edg.push_back(nbe[k]);
    }
  }
  sort_unique(edg);
}

uint DnMesh::findNeighborhood(uint ei, uint v[4], uint nbe[4], uint nbf[2]) const
{
  assert(ei != NotFound);
  assert(ei < edges.size());
  const DnEdge & e(edges[ei]);

  // initialize v, nbe, and nbf with NotFound
  for (uint i=0; i<4; ++i) {
    v[i] = NotFound;
    nbe[i] = NotFound;
  }

  nbf[0] = e.nbTriangle(0);
  nbf[1] = e.nbTriangle(1);

  v[0] = e.source();
  v[2] = e.target();
  
  if (nbf[0] != NotFound) {
    const DnTriangle & t(triangles[nbf[0]]);
    
    // locate v1
    v[1] = t.opposedVertex(e);
    assert(v[1] != NotFound);

    // locate e2 and e3
    const uint *nb(t.nbEdges());
    for (uint k=0; k<3; ++k) {
      assert(nb[k] != NotFound);
      if (nb[k] != ei) {
        const DnEdge & ne(edges[nb[k]]);
        uint ov = t.opposedVertex(ne);
        assert(ov == v[0] or ov == v[2]);
        if (ov == v[0])
          nbe[3] = nb[k];
        else
          nbe[2] = nb[k];
      }
    }
  }
  
  if (nbf[1] != NotFound) {
    const DnTriangle & t(triangles[nbf[1]]);
    v[3] = t.opposedVertex(e);
    assert(v[3] != NotFound);
    const uint *nb(t.nbEdges());
    for (uint k=0; k<3; ++k) {
      assert(nb[k] != NotFound);
      if (nb[k] != ei) {
        const DnEdge & ne(edges[nb[k]]);
        uint ov = t.opposedVertex(ne);
        assert(ov == v[0] or ov == v[2]);
        if (ov == v[0])
          nbe[0] = nb[k];
        else
          nbe[1] = nb[k];
      }
    }
  }

  return e.nNeighbors();
}

uint DnMesh::enforceEdge(uint a, uint b)
{
  // make sure that a < b
  if (a > b)
    swap(a,b);
  
  // first, check if edge is already present
  uint edexist = findEdgeTopo(a, b);

  if (edexist != NotFound) {
    assert(edges[edexist].find(a) != NotFound);
    assert(edges[edexist].find(b) != NotFound);
    return edexist;
  }

  // Hmm, not there. Our edge may be a flipped new edge.
  uint ov0, ov1;
  uint nne = nnedges();
  for (uint i=0; i<nne; ++i) {
    if (newEdges[i] == NotFound)
      continue;

    // see if we can find a candidate for edge flip
    const DnEdge & e(edges[newEdges[i]]);
    if ( (not canFlip(newEdges[i])) or e.nNeighbors() < 2)
      continue;
    if (e.find(a) == NotFound and e.find(b) == NotFound) {
      const DnTriangle & f0(triangles[e.nbTriangle(0)]);
      const DnTriangle & f1(triangles[e.nbTriangle(1)]);
      ov0 = f0.opposedVertex(e);
      ov1 = f1.opposedVertex(e);
      if ( (ov0 == a and ov1 == b) or (ov0 == b and ov1 == a) ) {
        if (flipEdge(newEdges[i]))
          return newEdges[i];
      }
    }
  }

  // none of the new edges fits, and none can be flipped.
  // search through the triangles incident on the two vertices
  const Indices & anbf(vertices[a].nbTriangles());
  const Indices & bnbf(vertices[b].nbTriangles());
  
  Indices nbf, nbe;
  nbf.insert(nbf.end(), anbf.begin(), anbf.end());
  nbf.insert(nbf.end(), bnbf.begin(), bnbf.end());
  sort_unique(nbf);

  const uint nf(nbf.size());
  for (uint i=0; i<nf; ++i) {
    const DnTriangle & f(triangles[nbf[i]]);
    const uint *ve(f.nbEdges());
    nbe.insert(nbe.end(), ve, ve+3);
  }
  sort_unique(nbe);

  // let's see if one of these edges fits
  const uint ne(nbe.size());
  vector<bool> isSwapCand(ne);
  for (uint i=0; i<ne; ++i) {
    if (not canFlip(nbe[i]))
      continue;
    const DnEdge & e(edges[nbe[i]]);
    if (e.nNeighbors() < 2)
      continue;
    uint s = e.source();
    uint t = e.target();
    if (s == a and t == b)
      return nbe[i];
    else if (s != a and t != b)
      isSwapCand[i] = true;
    else
      isSwapCand[i] = false;
  }

  // last chance: it may be possible to swap one of these
  for (uint i=0; i<ne; ++i) {
    if (isSwapCand[i]) {
      const DnEdge & e(edges[nbe[i]]);
      const DnTriangle & f0(triangles[e.nbTriangle(0)]);
      const DnTriangle & f1(triangles[e.nbTriangle(1)]);
      ov0 = f0.opposedVertex(e);
      ov1 = f1.opposedVertex(e);
      if ( (ov0 == a and ov1 == b) or (ov0 == b and ov1 == a) ) {
        if (flipEdge(nbe[i]))
          return nbe[i];
      }
    }
  }
  
  // could not find a candidate for flip, either
  return NotFound;
}

uint DnMesh::recursiveErase(uint ti)
{
  if (ti == NotFound)
    return 0;

  // catch triangles which are already killed
  DnTriangle & t(triangles[ti]);
  if (not t.isValid())
    return 0;

  // collect max three neighbor triangles
  uint nbt[3];
  for (uint i=0; i<3; ++i)
    nbt[i] = NotFound;
  
  const uint *nbe(t.nbEdges());
  for (uint k=0; k<3; ++k) {
    uint ei = nbe[k];
    if (ei == NotFound)
      continue;
    
    // if this edge is not constrained, kill triangle across the edge, too
    if (canFlip(ei)) {
      nbt[k] = edges[ei].opposed(ti);
      if (edges[ei].isValid())
        killEdge(ei);
    } else {
      edges[ei].detachTriangle(ti);
    }
  }

  // kill this triangle
  killTriangle(ti);

  // kill neighbors if permissible
  uint nk(1);
  for (uint k=0; k<3; ++k)
    nk += recursiveErase(nbt[k]);
  
  return nk;
}

uint DnMesh::carveHole(uint ti)
{
  if (ti == NotFound)
    return 0;

  std::set<uint> blacktri, blackedge;
  std::vector<uint> stack;
  stack.push_back(ti);

  while (not stack.empty()) {

    ti = stack.back();
    stack.pop_back();

    assert(ti < triangles.size());
    DnTriangle & t(triangles[ti]);
    if (not t.isValid())
      continue;

    blacktri.insert(ti);
    const uint *nbe(t.nbEdges());
    for (uint k=0; k<3; ++k) {

      uint optri(NotFound), ei = nbe[k];
      if (ei == NotFound)
        continue;

      DnEdge & e(edges[ei]);
      if (not e.isValid())
        continue;

      // if this edge is not constrained, kill triangle across the edge, too
      if ( canFlip(ei) ) {
        optri = e.opposed(ti);
        blackedge.insert(ei);
      } else {
        e.detachTriangle(ti);
      }

      // put only those candidate triangles on the
      // stack which have not already been marked
      if (optri != NotFound and blacktri.find(optri) == blacktri.end())
        stack.push_back(optri);
    }

    // hole ate the full mesh
    if (blacktri.size() >= nfaces()) {
      clear();
      return blacktri.size();
    }
  }

  std::set<uint>::const_iterator itr, last;
  last = blacktri.end();
  for (itr = blacktri.begin(); itr != last; ++itr)
    killTriangle( *itr );
  last = blackedge.end();
  for (itr = blackedge.begin(); itr != last; ++itr)
    killEdge( *itr );

  return blacktri.size();
}

uint DnMesh::insertSegment(uint a, uint b)
{
  // identify first edge which intersects segment (a,b)
  bool collision;
  const Indices & nbf(vertices[a].nbTriangles());
  const uint nf(nbf.size());
  uint ise(NotFound), isf(NotFound);
  for (uint i=0; i<nf; ++i) {
    assert(nbf[i] != NotFound);
    const uint *nbe(triangles[nbf[i]].nbEdges());
    for (uint k=0; k<3; ++k) {
      assert(nbe[k] != NotFound);
      const DnEdge & e(edges[nbe[k]]);
      assert(e.isValid());
      
      // if edge contains a or b, it cannot be intersected
      // by the intended line a-b
      if (e.find(a) != NotFound or e.find(b) != NotFound)
        continue;
      
      // check for intersection
      collision = intersects(nbe[k], a, b);
      if (collision) {
        ise = nbe[k];
        isf = nbf[i];
        if (not canFlip(nbe[k])) {
          stringstream ers;
          ers << "DnMesh::insertSegment(): ";
          ers << "Cannot flip first intersected segment ";
          ers << edges[ise].source() << " to " << edges[ise].target() << " ";
          ers << " at " << vertices[edges[ise].source()].eval()
              << " on surface: " << psf->name();
          return NotFound;
        }
        break;
      }
    }
    if (isf != NotFound)
      break;
  }

  // FIXME : Special case of constrained segment which lies exactly
  // on one *or several* existing edges is not covered yet.
  if (ise == NotFound) {
    stringstream ers;
    ers << "DnMesh::insertSegment(): No edge intersects ("
        << a << ", " << b << ").";
    errmsg = ers.str();
    return NotFound;
  }

  Indices pleft, pright;
  Indices cre, crf;
  cre.push_back(ise);
  crf.push_back(isf);

  do {
    
    // store vertices to the left/right of constraint
    uint src = edges[ise].source();
    uint trg = edges[ise].target();
    assert(src != a and src != b);
    assert(trg != a and trg != b);
    Real oris = orientation(a, b, src);
    Real orit = orientation(a, b, trg);
    
    if (oris < 0 and orit > 0) {
      if (pleft.empty() or pleft.back() != src)
        pleft.push_back(src);
      if (pright.empty() or pright.back() != trg)
        pright.push_back(trg);
    } else if (oris > 0 and orit < 0) {
      if (pleft.empty() or pleft.back() != trg)
        pleft.push_back(trg);
      if (pright.empty() or pright.back() != src)
        pright.push_back(src);
    } else {

      // one of the end points is on the constraint
      if (oris < 0) {
        if (pleft.empty() or pleft.back() != src)
          pleft.push_back(src);
      } else if (oris > 0) {
        if (pright.empty() or pright.back() != src)
          pright.push_back(src);
      }
      
      if (orit < 0) {
        if (pleft.empty() or pleft.back() != trg)
          pleft.push_back(trg);
      } else if (orit > 0) {
        if (pright.empty() or pright.back() != trg)
          pright.push_back(trg);
      }
    }
    
    // check if we need to proceed further
    if (triangles[isf].opposedVertex(edges[ise]) == b)
      break;
    
    // switch to next triangle across
    isf = edges[ise].opposed(isf);
    if (isf == NotFound)
      break;

    crf.push_back(isf);
    
    // find the next edge crossing (a,b)
    uint inext = NotFound;
    const uint *nbe(triangles[isf].nbEdges());
    for (uint k=0; k<3; ++k) {
      assert(nbe[k] != NotFound);
      if (nbe[k] == ise)
        continue;
      const DnEdge & e(edges[nbe[k]]);
      assert(e.isValid());
      if (e.find(a) != NotFound or e.find(b) != NotFound)
        continue;
      collision = intersects(nbe[k], a, b);
      if (collision) {
        inext = nbe[k];
        if (not canFlip(nbe[k]))
          return NotFound;
        break;
      }
    }
    ise = inext;
    if (ise != NotFound)
      cre.push_back(ise);
    
  } while (isf != NotFound and ise != NotFound);

  // kill marked triangles
  for (uint i=0; i<crf.size(); ++i) {
    
    // disconnect triangle from its edges
    uint ti = crf[i];
    const uint *nbe(triangles[ti].nbEdges());
    for (uint k=0; k<3; ++k) {
      if (nbe[k] != NotFound)
        edges[nbe[k]].detachTriangle(ti);
    }
    
    // remove from triangulation
    killTriangle(ti);
  }

  // kill marked edges
  for (uint i=0; i<cre.size(); ++i) {
    // disconnect edge from triangles
    uint ei = cre[i];
    assert(canFlip(ei));
    uint f0 = edges[ei].nbTriangle(0);
    if (f0 != NotFound)
      triangles[f0].detachEdge(ei);
    uint f1 = edges[ei].nbTriangle(1);
    if (f1 != NotFound)
      triangles[f1].detachEdge(ei);
    killEdge(ei);
  }
  
  // create new edge officially
  uint ei = addEdge(a,b);
  forbidFlip(ei);

  // this algorithm gets only called if splitting is not allowed
  forbidSplit(ei);
  
  // triangulate left and right polygons (recursively)
  bool ok(true);
  if (not pleft.empty())
    ok &= triangulatePolygon(ei, pleft);
  if (not pright.empty())
    ok &= triangulatePolygon(ei, pright);
  if (not ok) {
    stringstream ers;
    ers << "Failed to triangulate cavity to connect vertex " << a;
    ers << " at [" << vertices[a].parpos() << "] to ";
    ers << b << " at [" << vertices[b].parpos() << "] ";
    ers << "on surface " << psf->name() << ".";
    errmsg = ers.str();
    return NotFound;
  }

  return ei;
}

bool DnMesh::sIntersects(uint ei, uint a, uint b) const
{
  assert(ei != NotFound);
  const DnEdge & e(edges[ei]);
  assert(e.isValid());
  uint s = e.source();
  uint t = e.target();
  
  if (a > b)
    swap(a,b);
  
  // cannot test for intersection with self
  assert(s != a and t != b);
  
  // if the edge runs into one of a,b, there
  // cannot be an intersection
  if (s == a or t == b)
    return false;
  
  // determine on which side of e are a and b
  Real sa = sOrientation(s, t, a);
  Real sb = sOrientation(s, t, b);
  
  // no intersection if both are on the same side
  if ( (sa > 0.0 and sb > 0.0) or (sa < 0.0 and sb < 0.0))
    return false;
  
  // determine on which side of e are a and b
  Real ss = sOrientation(a, b, s);
  Real st = sOrientation(a, b, t);
  
  // no intersection if both are on the same side
  if ( (ss > 0.0 and st > 0.0) or (ss < 0.0 and st < 0.0))
    return false;
  else
    return true;
}

Real DnMesh::pOrientation(uint a, uint b, uint c) const
{
  assert(a < vertices.size());
  assert(b < vertices.size());
  assert(c < vertices.size());
  
  // plane version
  const Vct2 & p1(vertices[a].parpos());
  const Vct2 & p2(vertices[b].parpos());
  const Vct2 & p3(vertices[c].parpos());
  return jrsOrient2d(p1.pointer(), p2.pointer(), p3.pointer());
}

Real DnMesh::sOrientation(uint a, uint b, uint c) const
{
  assert(a < vertices.size());
  assert(b < vertices.size());
  assert(c < vertices.size());

  // check if the test points are exactly on the parametric
  // boundary. in that case, use the parametric criterion
  const Vct2 & qa(vertices[a].parpos());
  const Vct2 & qb(vertices[b].parpos());
  const Vct2 & qc(vertices[c].parpos());
  if (qa[0] == qb[0] and qb[0] == qc[0])
    return 0.0;
  else if (qa[1] == qb[1] and qb[1] == qc[1])
    return 0.0;
  
  const Vct3 & p1(vertices[a].eval());
  const Vct3 & n1(vertices[a].normal());
  const Vct3 & p2(vertices[b].eval());
  const Vct3 & n2(vertices[b].normal());
  const Vct3 & p4(vertices[c].eval());
  
  // test orientation with respect to a plane through
  // a and b and normal to the surface
  // Returns positive if c is below the plane spanned
  // by a,b and the point above the edge
  Real elen = norm(p2-p1);
  Vct3 p3( 0.5*(p1+p2) + 0.5*elen*(n1+n2) );
  
  Real s = jrsOrient3d( p1.pointer(), p2.pointer(),
                        p3.pointer(), p4.pointer() );
  return s;
}

int DnMesh::pIsInside(uint ti, uint ni) const
{
  assert(ti != NotFound);
  const DnTriangle & t(triangles[ti]);
  assert(t.isValid());
  
  double po;
  uint v1, v2;
  const uint *nbe(t.nbEdges());
  const uint *vi(t.vertices());
  for (uint k=0; k<3; ++k) {
    assert(nbe[k] != NotFound);
    const DnEdge & e(edges[nbe[k]]);
    v1 = t.find(e.source());
    v2 = t.find(e.target());
    assert(v1 != NotFound and v2 != NotFound);
    if (v1 == 1 and v2 == 0)
      std::swap(v1,v2);
    else if (v1 == 2 and v2 == 1)
      std::swap(v1,v2);
    else if (v1 == 0 and v2 == 2)
      std::swap(v1,v2);
    
    po = pOrientation(vi[v1], vi[v2], ni);
    
    // point is outside triangle in parameter space
    if (po < 0)
      return -2;
    else if (po == 0) {
      
      const Vct2 & p( vertices[ni].parpos() );
      const Vct2 & q1( vertices[vi[v1]].parpos() );
      const Vct2 & q2( vertices[vi[v2]].parpos() );
      Vct2 tmp = q2 - q1;
      Real lpar = dot(p-q1, tmp) / dot(tmp,tmp);
      
      if (lpar >= 0.0 and lpar <= 1.0)
        return k;
      else
        return -2;
    }
  }
  
  // point is inside
  return -1;
}

int DnMesh::sIsInside(uint ti, uint ni) const
{
  assert(ti != NotFound);
  const DnTriangle & t(triangles[ti]);
  assert(t.isValid());
  
  // the approach below fails for points which are located
  // exactly on the wrapped boundary (u = 0 or 1), so that
  // this case must be handled separately
  const Vct2 & qni( vertices[ni].parpos() );
  // if (uwrap and (qni[0] == 0.0 or qni[0] == 1.0))
  //   return sIsOnBoundaryEdge(ti, ni);

  // change to allow handling of all edge cases
  if (whichside(qni, 0.0) != none)
    return sIsOnBoundaryEdge(ti, ni);
  
  // check if point ni is exactly on any of the edges
  Real eso[3];
  uint v1, v2;
  const uint *vi(t.vertices());
  const uint *nbe(t.nbEdges());
  for (uint k=0; k<3; ++k) {
    assert(nbe[k] != NotFound);
    const DnEdge & e(edges[nbe[k]]);
    v1 = t.find(e.source());
    v2 = t.find(e.target());
    assert(v1 != NotFound and v2 != NotFound);
    
    // fix ordering so that the plane through this edge as
    // constructed in sOrientation() has its normal pointing
    // inside the triangle
    if (v1 == 0 and v2 == 1)
      std::swap(v1,v2);
    else if (v1 == 1 and v2 == 2)
      std::swap(v1,v2);
    else if (v1 == 2 and v2 == 0)
      std::swap(v1,v2);
    
    // so positive means that ni is below the edge plane, i.e.
    // outside of the prism above the triangle
    eso[k] = sOrientation(vi[v1], vi[v2], ni);
    if (eso[k] > 0) {
      return -2;
    }
    
    // zero means that ni is exactly on the plane, but not
    // necessarily inside the region assigned to this triangle.
    // hence, continue testing the other edges - if one of
    // them yields 'outside', we bail out early
  }
  
  // if we get here, we may have ni exactly above an edge, in
  // which case at least one of eso[k] == 0, otherwise, ni is
  // above ti but not exactly on an edge
  for (uint k=0; k<3; ++k) {
    assert(eso[k] <= 0);
    if (eso[k] == 0)
      return k;
  }
  
  // point is inside
  return -1;
}

int DnMesh::sIsOnBoundaryEdge(uint ti, uint ni) const
{
  // TODO
  // Determine whether this is correct even for !uwrap

  assert(ti != NotFound);
  const DnTriangle & t(triangles[ti]);
  assert(t.isValid());
  
  const Vct2 & qni( vertices[ni].parpos() );
  Real uni = qni[0];
  Real vni = qni[1];
  // assert(uni == 0.0 or uni == 1.0);
  const uint *nbe(t.nbEdges());

  // if (uwrap) {

  for (uint k=0; k<3; ++k) {
    assert(nbe[k] != NotFound);
    const DnEdge & e(edges[nbe[k]]);
    const Vct2 & ps( vertices[e.source()].parpos() );
    const Vct2 & pt( vertices[e.target()].parpos() );
    if (ps[0] == uni and pt[0] == uni) {
      Real vlo = min(ps[1], pt[1]);
      Real vhi = max(ps[1], pt[1]);
      if (vlo < vni and vni < vhi)
        return k;
    }
  }

  // } else {

  if (uni == 0.0 or uni == 1.0) {
    for (uint k=0; k<3; ++k) {
      assert(nbe[k] != NotFound);
      const DnEdge & e(edges[nbe[k]]);
      const Vct2 & ps( vertices[e.source()].parpos() );
      const Vct2 & pt( vertices[e.target()].parpos() );
      if (ps[0] == uni and pt[0] == uni) {
        Real vlo = min(ps[1], pt[1]);
        Real vhi = max(ps[1], pt[1]);
        if (vlo < vni and vni < vhi)
          return k;
      }
    }
  } else if (vni == 0.0 or vni == 1.0) {
    for (uint k=0; k<3; ++k) {
      assert(nbe[k] != NotFound);
      const DnEdge & e(edges[nbe[k]]);
      const Vct2 & ps( vertices[e.source()].parpos() );
      const Vct2 & pt( vertices[e.target()].parpos() );
      if (ps[1] == vni and pt[1] == vni) {
        Real ulo = min(ps[0], pt[0]);
        Real uhi = max(ps[0], pt[0]);
        if (ulo < uni and uni < uhi)
          return k;
      }
    }
  }
  // }
  
  // not on any edge, cannot be inside, is therefore outside
  return -2;
}

bool DnMesh::triangulatePolygon(uint ei, const Indices & v)
{
  if (ei == NotFound or v.empty())
    return false;

  uint a = edges[ei].source();
  uint b = edges[ei].target();
  const uint ni = v.size();

  if (ni == 1) {
    
    // single-triangle case is purely topological
    // should work fine in plane and spatial mode
    uint e1 = findEdgeTopo(a, v[0]);
    if (e1 == NotFound)
      e1 = addEdge(a, v[0]);
    uint e2 = findEdgeTopo(b, v[0]);
    if (e2 == NotFound)
      e2 = addEdge(b, v[0]);
    uint nt = addTriangle(a, b, v[0]);
    DnTriangle & t(triangles[nt]);
    t.attachEdge(ei);
    t.attachEdge(e1);
    t.attachEdge(e2);
    edges[ei].attachTriangle(nt);
    edges[e1].attachTriangle(nt);
    edges[e2].attachTriangle(nt);

  } else {

    // selection of the first vertex is critical - uses encroachment criterion
    uint ibreak(0), c = v[0];
    DnTriangle ttest(a, b, c);
    fixDirection(ttest);
    ttest.computeSphere(*psf, vertices, (type == DnSpatial));
    for (uint i=1; i<ni; ++i) {
      int ici;
      if (type == DnSpatial)
        ici = ttest.inSphere(vertices, v[i]);
      else
        ici = ttest.inCircle(vertices, v[i]);
      if (ici > 0) {
        c = v[i];
        ibreak = i;
        ttest.reconnect(a, b, c);
        fixDirection(ttest);
        ttest.computeSphere(*psf, vertices, (type == DnSpatial));
      }
    }

    // create first triangle (topological)
    // uint e1 = addEdge(a, c);
    // uint e2 = addEdge(b, c);
    
    uint e1 = findEdgeTopo(a,c);
    if (e1 == NotFound)
      e1 = addEdge(a, c);
    uint e2 = findEdgeTopo(b, c);
    if (e2 == NotFound)
      e2 = addEdge(b, c);
    uint nt = addTriangle(a, b, c);
    DnTriangle & t(triangles[nt]);
    t.attachEdge(ei);
    t.attachEdge(e1);
    t.attachEdge(e2);
    edges[ei].attachTriangle(nt);
    edges[e1].attachTriangle(nt);
    edges[e2].attachTriangle(nt);

    // recursively process remaining vertices
    Indices pa, pb;
    std::copy(v.begin(), v.begin()+ibreak, back_inserter(pa));
    std::copy(v.begin()+ibreak+1, v.end(), back_inserter(pb));

    // decide how to assign remaining point sets to base edges
    // by comparing the angles through which the edges are seen from
    // points in the sets pa,pb.
    Real a1phi(0.0), a2phi(0.0);
    if (not pa.empty()) {
      uint ta = pa[ pa.size()/2 ];
      if (type == DnSpatial) {
        const Vct3 & ptref(vertices[ta].eval());
        const Vct3 & pta( vertices[a].eval() );
        const Vct3 & ptb( vertices[b].eval() );
        const Vct3 & ptc( vertices[c].eval() );
        a1phi = arg( pta-ptref, ptc-ptref );
        a2phi = arg( ptb-ptref, ptc-ptref );
      } else {
        const Vct2 & ptref(vertices[ta].parpos());
        const Vct2 & pta( vertices[a].parpos() );
        const Vct2 & ptb( vertices[b].parpos() );
        const Vct2 & ptc( vertices[c].parpos() );
        a1phi = arg( pta-ptref, ptc-ptref );
        a2phi = arg( ptb-ptref, ptc-ptref );
      }
    }
    
    Real b1phi(0.0), b2phi(0.0);
    if (not pb.empty()) {
      uint tb = pb[ pb.size()/2 ];
      if (type == DnSpatial) {
        const Vct3 & ptref(vertices[tb].eval());
        const Vct3 & pta( vertices[a].eval() );
        const Vct3 & ptb( vertices[b].eval() );
        const Vct3 & ptc( vertices[c].eval() );
        b1phi = arg( pta-ptref, ptc-ptref );
        b2phi = arg( ptb-ptref, ptc-ptref );
      } else {
        const Vct2 & ptref(vertices[tb].parpos());
        const Vct2 & pta( vertices[a].parpos() );
        const Vct2 & ptb( vertices[b].parpos() );
        const Vct2 & ptc( vertices[c].parpos() );
        b1phi = arg( pta-ptref, ptc-ptref );
        b2phi = arg( ptb-ptref, ptc-ptref );
      }
    }

    // should be impossible except in degenerate cases
    if (fabs(a1phi-a2phi) == 0 and fabs(b1phi-b2phi) == 0)
      return false;
    
    // determine which pair of angles decides assignment
    bool ok(true);
    if ( fabs(a1phi-a2phi) > fabs(b1phi-b2phi) ) {
      if (a1phi > a2phi) {
        if (not pa.empty())
          ok &= triangulatePolygon(e1, pa);
        if (not pb.empty())
          ok &= triangulatePolygon(e2, pb);
      } else {
        if (not pa.empty())
          ok &= triangulatePolygon(e2, pa);
        if (not pb.empty())
          ok &= triangulatePolygon(e1, pb);
      }
    } else {
      if (b2phi > b1phi) {
        if (not pa.empty())
          ok &= triangulatePolygon(e1, pa);
        if (not pb.empty())
          ok &= triangulatePolygon(e2, pb);
      } else {
        if (not pa.empty())
          ok &= triangulatePolygon(e2, pa);
        if (not pb.empty())
          ok &= triangulatePolygon(e1, pb);
      }
    }
    return ok;
  }

  return true;
}

void DnMesh::fixate()
{  
  // collect referenced vertices and swap invalid elements
  // to the end of the triangle array
  // TODO: Test for case with many invalid triangles

  // this will create new edge indices etc - old indices are void
  iNoFlip.clear();
  iNoSplit.clear();
  iKinkEdge.clear();
  iDeadTriangles.clear();
  iDeadEdges.clear();

  Indices refv;
  const uint nta(triangles.size());
  uint last = nta - 1;
  for (uint i=0; i<nta; ++i) {
    DnTriangle & t(triangles[i]);
    if (t.isValid()) {
      const uint *vi(t.vertices());
      refv.insert(refv.end(), vi, vi+3);
    } else {
      
      // make last the last valid triangle
      while (not triangles[last].isValid())
        --last;
      
      // swap current with last
      if (last > i) {
        swap(t, triangles[last]);
        const uint *vi(t.vertices());
        refv.insert(refv.end(), vi, vi+3);
      }
    }
  }
  iDeadTriangles.clear();
  
  // make last the last valid triangle
  while (not triangles[last].isValid())
    --last;
  
  // adjust element array size
  if (last < nta-1)
    triangles.erase(triangles.begin()+last+1, triangles.end());
  
  // create a vertex index mapping for renaming
  sort_unique(refv);
  const uint nv(refv.size());
  Indices iperm(vertices.size());
  for (uint i=0; i<nv; ++i) {
    iperm[refv[i]] = i;
  }
  
  // delete stored connectivity
  for (uint i=0; i<vertices.size(); ++i)
    vertices[i].clearNeighbors();
  
  // construct edges and vertex - face connectivity
  edges.clear();
  const uint nt(triangles.size());
  edges.reserve(3*nt);
  for (uint i=0; i<nt; ++i) {
    
    // translate indices
    triangles[i].itranslate(iperm);
    
    // construct edges
    const uint *vi = triangles[i].vertices();
    edges.push_back( DnEdge(vi[0], vi[1]) );
    edges.push_back( DnEdge(vi[1], vi[2]) );
    edges.push_back( DnEdge(vi[0], vi[2]) );
    
    // connect vertices to triangles
    vertices[vi[0]].attachTriangle(i);
    vertices[vi[1]].attachTriangle(i);
    vertices[vi[2]].attachTriangle(i);
  }
  sort_unique(edges);

  // register connectivity: triangles - edges
  for (uint i=0; i<nt; ++i) {
    DnTriangle & t(triangles[i]);
    const uint *vi(t.vertices());
    uint *ve(t.nbEdges());
    ve[0] = findEdgeSorted(vi[1], vi[2]);
    ve[1] = findEdgeSorted(vi[0], vi[2]);
    ve[2] = findEdgeSorted(vi[0], vi[1]);
    for (uint k=0; k<3; ++k) {
      assert(ve[k] != NotFound);
      edges[ve[k]].attachTriangle(i);
    }
  }
}

uint DnMesh::findEdgeTopo(uint a, uint b) const
{
  assert(a < vertices.size());
  assert(b < vertices.size());
  if (a > b)
    swap(a,b);

  const Indices & nbf(vertices[a].nbTriangles());
  const uint nf(nbf.size());
  for (uint i=0; i<nf; ++i) {
    assert(nbf[i] != NotFound);
    if (not triangles[nbf[i]].isValid())
      continue;
    const uint *nbe(triangles[nbf[i]].nbEdges());
    for (uint k=0; k<3; ++k) {
      assert(nbe[k] != NotFound);
      const DnEdge & e(edges[nbe[k]]);
      if (e.source() == a and e.target() == b)
        return nbe[k];
    }
  }
  return NotFound;
}

void DnMesh::clear()
{
  vertices.clear();
  triangles.clear();
  edges.clear();
  iDeadEdges.clear();
  iDeadTriangles.clear();
}

XmlElement DnMesh::toXml() const
{
  MeshFields m;
  const uint nv(vertices.size());
  for (uint i=0; i<nv; ++i) {
    m.addVertex(vertices[i].eval());
    m.addNormal(vertices[i].normal());
  }
  const uint nf(triangles.size());
  for (uint i=0; i<nf; ++i) {
    if (triangles[i].isValid())
      m.addTri3(triangles[i].vertices());
  }
  
  return m.toXml();
}

XmlElement DnMesh::pToXml() const
{
  MeshFields m;
  
  const uint nv(vertices.size());
  for (uint i=0; i<nv; ++i) {
    const Vct2 & p(vertices[i].parpos());
    m.addVertex(vct(p[0], p[1], 0.0));
  }
  const uint nf(triangles.size());
  for (uint i=0; i<nf; ++i) {
    if (triangles[i].isValid())
      m.addTri3(triangles[i].vertices());
  }
  
  return m.toXml();
}

void DnMesh::iterativeRefine(const DnRefineCriterion & c)
{
  bAbort = false;
  nowrefining = true;
  c.bind(this);
  
  uint ipass(0);
  const uint nmax(c.nmax());
  while ( vertices.size() < nmax ) {

    // number of triangles refined in this pass
    uint nref(0);
    
    const int nf = triangles.size();
    for (int i=0; i<nf; ++i) {
      
      const DnTriangle & t(triangles[i]);
      if (not t.isValid())
        continue;
      
      // refine i if criteria not satisfied
      Real cv = c.eval(t.vertices());
      if (cv <= 1.0) {
        continue;
      } else if (refineTriangle(i, c.maxStretch(), c.minLength())) {
        ++nref;
      }
    }
    ++ipass;
    
    // if few refined, stop here
    if (nref < 2 or bAbort)
      break;
  }
  
  nowrefining = false;
}

void DnMesh::refineAround(const Indices & vlist, const DnRefineCriterion & c)
{
  bAbort = false;
  nowrefining = true;
  c.bind(this);
  
  const int nvl = vlist.size();
  for (int iv=0; iv<nvl; ++iv) {
    assert(vlist[iv] < vertices.size());
    Indices vnf( vertices[vlist[iv]].nbTriangles() );
    const int nf = vnf.size();
    for (int j=0; j<nf; ++j) {
      if (vnf[j] == NotFound)
        continue;
      if (not triangles[vnf[j]].isValid())
        continue;
      refineTriangle(vnf[j], c.maxStretch(), c.minLength());
    }
  }
  
  nowrefining = false;
}

bool DnMesh::refineTriangle(uint tix, Real mxs, Real minlen)
{
  const DnTriangle & t(triangles[tix]);
  const uint *nbe = t.nbEdges();
  
  // compute edge lengths and check
  Real elen[3];
  bool econ[3];
  for (int k=0; k<3; ++k) {
    assert(nbe[k] != NotFound);
    elen[k] = edges[nbe[k]].sLength(vertices);
    econ[k] = !canFlip(nbe[k]);
  }
  
  // longest and shortest edge
  uint elong[3];
  elong[0] = distance(elen, max_element(elen, elen+3));
  elong[2] = distance(elen, min_element(elen, elen+3));
  elong[1] = 3 - elong[0] - elong[2];
  
  Real s1 = elen[elong[1]] / elen[elong[2]];  // mid/short
  Real s2 = elen[elong[0]] / elen[elong[2]];  // long/short
  
  // if we have a flat hat shaped triangle, i.e. the two
  // shorter edges are about equally long, we must split the
  // longest edge unless that is forbidden
  if (s2 > mxs and s1 < 1.5) {
    if (econ[elong[0]])
      return false;
    else
      return refineEdge(nbe[elong[0]], minlen);
  }
  
  // at this point, it's not a hat-shaped triangle at least
  // split the longest edge, or, if that is not permitted,
  // the second longest one, even the shortest if that's OK
  if ( not econ[elong[0]] )
    return refineEdge(nbe[elong[0]], minlen);
  else if ( not econ[elong[1]] )
    return refineEdge(nbe[elong[1]], minlen);
  else if ( s2 < 0.5*mxs and (not econ[elong[2]]) )
    return refineEdge(nbe[elong[2]], minlen);
  
  // no way to split this triangle
  return false;
}

uint DnMesh::refine(const DnRefineCriterion & c)
{
  bAbort = false;
  nowrefining = true;
  c.bind(this);
  
  const uint nmax(c.nmax());
  Real maxstretch = c.maxStretch();
  Real minlen = 2*c.minLength();
  DnTriangleShape shp;
  uint iter(0), rfcount, rftotal(0);

  DnTriangleQueue irq(c, triangles);
  do {
    
    // count refinements in this iteration
    rfcount = 0;
    dbprint("Refinement pass ", iter+1, ", queue: ", irq.size());
    if (irq.empty()) {
      nowrefining = false;
      return rftotal;
    }
    
    // fetch worst triangle
    Real worst(0.0);
    uint iworst = irq.next(worst);
    if (worst <= 1.0) {
      nowrefining = false;
      return rftotal;
    }
    
    while (worst > 1.0) {
      
      bool refined(false);
      classify(iworst, maxstretch, shp);
      
      // check if elong is constrained. if so, never try to split
      if (canSplit(shp.elong)) {

        refined = refineEdge(shp.elong, minlen);

        // if refinement of elong failed, try another edge
        // unless iworst is a hat, which would deteriorate horribly
        // if we would split one of the short edges
        if ((not refined) and (shp.shape != DnHat)) {
          uint enext(NotFound);
          const uint *nbe(triangles[iworst].nbEdges());
          for (uint k=0; k<3; ++k) {
            if (nbe[k] != shp.elong and nbe[k] != shp.eshort)
              enext = nbe[k];
          }
          if ( enext != NotFound
               and edges[enext].sLength(vertices) > minlen
               and canSplit(enext) )
            refined = refineEdge(enext, minlen);
        }
      }
      
      if (refined)
        ++rfcount;
      
      iworst = irq.next(worst);
    }
    rftotal += rfcount;
    ++iter;

    // exit if abort flag was set
    if (bAbort) {
      bAbort = false;
      nowrefining = false;
      return rftotal;
    }
    dbprint(rfcount, " edges split.");
    irq.refill();
  } while (nvertices() < nmax and rfcount > 2 and (not irq.empty()));
  
  nowrefining = false;
  return rftotal;
}

bool DnMesh::refineEdge(uint ei, Real minlen)
{
  assert(ei != NotFound);
  assert(edges[ei].isValid());
  
  // locate point to insert
  uint ni = findDivider(ei, minlen);
  if (ni == NotFound)
    return false;
  
  // register vertex only if it could be inserted
  const Vct2 & pin( vertices[ni].parpos() );
  if (splitEdge(ei, ni)) {
    btree.insert(pin);
  } else {
    vertices.pop_back();
    return false;
  }
  
  // handle boundary cases
  bool boundaryInsert = false;
  if (type == DnSpatial and uwrap) {
    if (pin[0] == 0.0) {
      depinsert = true;
      insertVertex( vct(1.0, pin[1]), boundaryInsert );
      depinsert = false;
    } else if (pin[0] == 1.0) {
      depinsert = true;
      insertVertex( vct(0.0, pin[1]), boundaryInsert );
      depinsert = false;
    }
  }
  
  return true;
}

uint DnMesh::findDivider(uint ei, Real minlen)
{
  // compute neighborhood first
  uint nnb, v[4], e[4], f[2];
  nnb = findNeighborhood(ei, v, e, f);
  
  // refuse to split the short edge of a hat triangle
  for (uint k=0; k<2; ++k) {
    if (f[k] == NotFound)
      continue;
    DnTriangleShape shp;
    classify(f[k], 10.0, shp);
    if (shp.shape == DnHat and shp.elong != ei)
      return NotFound;
  }
  
  const Vct2 & q0(vertices[v[0]].parpos());
  const Vct2 & q2(vertices[v[2]].parpos());

  const Vct3 & p0(vertices[v[0]].eval());
  const Vct3 & p2(vertices[v[2]].eval());

  bool eiOnBound(false);
  if (uwrap) {
    if (q0[0] < gmepsilon and q2[0] < gmepsilon)
      eiOnBound = true;
    else if (q0[1] < gmepsilon and q2[1] < gmepsilon)
      eiOnBound = true;
    else if (q0[0] > 1.0-gmepsilon and q2[0] > 1.0-gmepsilon)
      eiOnBound = true;
    else if (q0[1] > 1.0-gmepsilon and q2[1] > 1.0-gmepsilon)
      eiOnBound = true;
  }
  
  bool canflip = canFlip(ei);
  bool nokink = (not isKink(ei));
  
  Vct2 qdiv;
  uint ni(NotFound);
  if (nnb == 2 and canflip and nokink and isConvexSet(v)) {

    const Vct2 & q1(vertices[v[1]].parpos());
    const Vct2 & q3(vertices[v[3]].parpos());

    const Vct3 & p1(vertices[v[1]].eval());
    const Vct3 & p3(vertices[v[3]].eval());
    
    qdiv = 0.25*(q0 + q1 + q2 + q3);
    if (type == DnSpatial) {
      
      // determine tolerances for projection
      Real l1, l2, l3, l4, dpmin, stol;
      l1 = norm(p0-p1);
      l2 = norm(p2-p1);
      l3 = norm(p0-p3);
      l4 = norm(p2-p3);
      stol = 0.01*min(min(l1, l2), min(l3,l4));
      
      l1 = norm(q0-q1);
      l2 = norm(q2-q1);
      l3 = norm(q0-q3);
      l4 = norm(q2-q3);
      dpmin = 0.01*min(min(l1, l2), min(l3,l4));
      
      Vct3 ptarget( 0.25*(p0 + p1 + p2 + p3) );
      Vct2 qj( qdiv );
      bool pok;
      pok = psf->project(ptarget, qj,
                         min(1e-6, stol), min(1e-6, dpmin) );
      
      // check if projection ok
      Real d1 = norm(ptarget - psf->eval(qdiv[0], qdiv[1]) );
      Real d2 = norm(ptarget - psf->eval(qj[0], qj[1]) );
      if (pok and (d2 < d1))
        qdiv = qj;
    }
    
    DnVertex vnew(*psf, qdiv);
    ni = vertices.size();
    vertices.push_back( vnew );
    
    // test if divider point is inside at least one triangle
    assert(nnb > 1);
    assert(f[0] != NotFound);
    assert(f[1] != NotFound);
    int inside[2];
    for (uint k=0; k<2; ++k) {
      inside[k] = isInside(f[k], ni);
      if (inside[k] > -1) {
        const uint *nbe(triangles[f[k]].nbEdges());
        if (nbe[inside[k]] == ei)
          inside[k] = -1;
        else
          inside[k] = -2;
      }
    }
    
    // ok if barycenter inside one triangle
    if (inside[0] == -2 and inside[1] == -2) {
      vertices.pop_back();
      ni = NotFound;
    }
  }
  
  // fallback option is edge midpoint
  if (ni == NotFound) {
    qdiv = 0.5*(q0 + q2);
    if (type == DnSpatial and (not eiOnBound) and nokink)
      psf->project(0.5*(p0 + p2), qdiv);

    DnVertex vnew(*psf, qdiv);
    ni = vertices.size();
    vertices.push_back( vnew );
  }
  
  // if ni is too close to nearest vertex, refuse to split
  uint vnear = btree.nearest(vertices[ni].parpos());
  Real dst = norm(vertices[ni].eval() - vertices[vnear].eval());
  if (dst < 0.25*minlen) {
    vertices.pop_back();
    return NotFound;
  }
  
  // test if this vertex yields acceptable triangles
  const Vct3 & pnew(vertices.back().eval());
  const Vct3 & sn(vertices.back().normal());
  for (uint k=0; k<4; ++k) {
    if (e[k] == NotFound or e[k] == ei)
      continue;
    const DnEdge & ebase(edges[e[k]]);
    if (not ebase.isValid())
      continue;
    
    uint s = ebase.source();
    uint t = ebase.target();
    if (type == DnSpatial) {
      Vct3 r1( vertices[s].eval() - pnew );
      Vct3 r2( vertices[t].eval() - pnew );
      Vct3 tn( cross(r1,r2) );
      if ( fabs(dot(sn,tn)) < gmepsilon ) {
        vertices.pop_back();
        return NotFound;
      }
    }
    
    if (orientation(s, t, ni) == 0.0) {
      vertices.pop_back();
      return NotFound;
    }
  }
  
  // passed all tests
  return ni;
}

void DnMesh::smoothVertex(uint v)
{
  // check if v can be moved in the first place
  const Indices & nbf(vertices[v].nbTriangles());
  const uint nf(nbf.size());
  for (uint i=0; i<nf; ++i) {
    assert(nbf[i] != NotFound);
    assert(triangles[nbf[i]].isValid());
    const uint *nbe(triangles[nbf[i]].nbEdges());
    for (uint k=0; k<3; ++k) {
      assert(nbe[k] != NotFound);
      assert(edges[nbe[k]].isValid());
      uint src = edges[nbe[k]].source();
      uint trg = edges[nbe[k]].target();
      if (src == v or trg == v) {
        if (not canFlip(nbe[k]))
          return;
        if (edges[nbe[k]].nNeighbors() < 2)
          return;
      }
    }
  }
  
  // try to move v closer to its barycenter, if possible
  centerVertex(v, 1.0);
}

void DnMesh::classify(uint ti, Real maxstretch, DnTriangleShape & shp) const
{
  assert(ti != NotFound);
  assert(triangles[ti].isValid());

  // compute edge lengths
  Real elen[3];
  const uint *nbe(triangles[ti].nbEdges());
  for (uint k=0; k<3; ++k) {
    assert(nbe[k] != NotFound);
    const DnEdge & e(edges[nbe[k]]);
    const Vct3 & p1(vertices[e.source()].eval());
    const Vct3 & p2(vertices[e.target()].eval());
    elen[k] = norm(p2-p1);
  }

  // find longest and shortest edge
  uint imx, imn;
  imx = std::distance(elen, std::max_element(elen, elen+3));
  imn = std::distance(elen, std::min_element(elen, elen+3));
  
  shp.elong = nbe[imx];
  shp.eshort = nbe[imn];

  Real maxlen = elen[imx];
  Real minlen = elen[imn];
  Real area = 0.5*norm(triangles[ti].normal(vertices));
  Real stretch = 0.25*sqrt(3.)*sq(maxlen)/area;
  shp.stretch = stretch;

  if (stretch > maxstretch) {
    if (maxlen/minlen > maxstretch)
      shp.shape = DnNeedle;
    else
      shp.shape = DnHat;
  } else {
    shp.shape = DnRegular;
  }
}

bool DnMesh::collapseEdge(uint eshort)
{
  // if flipping or splitting is not allowed, we cannot collapse either
  if (not canFlip(eshort))
    return false;
  if (not canSplit(eshort))
    return false;
  
  // remove one vertex, two triangles and three edges in order to
  // get rid of a very short edge (in a needle-shaped triangle)
  uint nnb, v[4], nbe[4], nbf[2];
  nnb = findNeighborhood(eshort, v, nbe, nbf);
  
  // let's see if we can kill nbe[0] and nbe[3], and drop v[2]
  // or otherwise, kill nbe[1] and nbe[2] and drop v[0]
  bool dropv2(true), dropv0(true);
  
  // length of eshort
  Real lshort = norm(vertices[v[0]].eval() - vertices[v[2]].eval());
  
  // check if any edge which runs into v[2] is forbidden to flip
  // furthermore, refuse to collapse any edge where the vertex to
  // be disconnected has a neighbor edge which is shorter than eshort,
  // because that will yield inverted triangles in some cases
  Indices edg;
  collectNbEdges(v[2], edg);
  uint ne = edg.size();
  for (uint i=0; i<ne; ++i) {
    if (edg[i] == NotFound)
      continue;
    if (not canFlip(edg[i])) {
      dropv2 = false;
      break;
    }
    
    // if eshort has two neighbors (is fully internal) and v2 has any
    // neighbor edge on the boundary (nnb=1), we cannot delete v2,
    // otherwise we would damage the boundary contour
    if (nnb == 2 and edges[edg[i]].nNeighbors() < 2) {
      dropv2 = false;
      break;
    }
    if (edges[edg[i]].sLength(vertices) < lshort) {
      dropv2 = false;
      break;
    }
  }
  
  // We cannot drop v[2], but perhaps v[0]?
  if (not dropv2) {
    collectNbEdges(v[0], edg);
    ne = edg.size();
    for (uint i=0; i<ne; ++i) {
      if (edg[i] == NotFound)
        continue;
      if (not canFlip(edg[i])) {
        dropv0 = false;
        break;
      }
      if (nnb == 2 and edges[edg[i]].nNeighbors() < 2) {
        dropv0 = false;
        break;
      }
      if (edges[edg[i]].sLength(vertices) < lshort) {
        dropv2 = false;
        break;
      }
    }
  }
  
  // finally, check if dropping one vertex would tangle the mesh
  if (not vertexCanMove(v[0], vertices[v[2]].parpos()))
    dropv0 = false;
  if (not vertexCanMove(v[2], vertices[v[0]].parpos()))
    dropv2 = false;
  
  // bail out if neither vertex can be erased
  if ((not dropv2) and (not dropv0)) {
    return false;
  }
  
  if (dropv2) {
    
    // find f2 and f3, replace edge and vertex connections
    if (nbe[3] != NotFound and nbf[0] != NotFound) {
      uint f2 = edges[nbe[3]].opposed(nbf[0]);
      if (f2 != NotFound) {
        triangles[f2].replaceEdge(nbe[3], nbe[2]);
        edges[nbe[2]].replaceTriangle(nbf[0], f2);
      }
    }
    if (nbe[0] != NotFound and nbf[1] != NotFound) {
      uint f3 = edges[nbe[0]].opposed(nbf[1]);
      if (f3 != NotFound) {
        triangles[f3].replaceEdge(nbe[0], nbe[1]);
        edges[nbe[1]].replaceTriangle(nbf[1], f3);
      }
    }
    
    // exchange v[2] for v[0] in faces and edges incident in v[2]
    fuseVertices(v[2], v[0]);
    
    killEdge(nbe[0]);
    killEdge(nbe[3]);
    btree.erase(v[2]);
    
  } else if (dropv0) {
    
    if (nbe[2] != NotFound and nbf[0] != NotFound) {
      uint f2 = edges[nbe[2]].opposed(nbf[0]);
      if (f2 != NotFound) {
        triangles[f2].replaceEdge(nbe[2], nbe[3]);
        edges[nbe[3]].replaceTriangle(nbf[0], f2);
      }
    }
    if (nbe[1] != NotFound and nbf[1] != NotFound) {
      uint f3 = edges[nbe[1]].opposed(nbf[1]);
      if (f3 != NotFound) {
        triangles[f3].replaceEdge(nbe[1], nbe[0]);
        edges[nbe[0]].replaceTriangle(nbf[1], f3);
      }
    }
    
    // exchange v[0] for v[2] in faces and edges incident in v[0]
    fuseVertices(v[0], v[2]);
    
    killEdge(nbe[1]);
    killEdge(nbe[2]);
    btree.erase(v[0]);
    
  } else {
    assert(!"Should never be here.");
  }
  
  // kill old triangles and edge
  killTriangle(nbf[0]);
  killTriangle(nbf[1]);
  killEdge(eshort);
  
#if defined(DELAUNAY_VERBOSE)
  
  // expensive connectivity check - ring-1
  uint ncf[4];
  memset(ncf, 0, sizeof(ncf));
  Indices nbv;
  for (uint i=0; i<4; ++i) {
    if (v[i] != NotFound)
      ncf[i] = checkConnectivity(v[i], nbv);
  }
  assert(*min_element(ncf, ncf+4) == 0);
  
  // ring-2 check
  Indices tmp;
  for (uint i=0; i<nbv.size(); ++i) {
    tmp.clear();
    checkConnectivity(nbv[i], tmp);
  }
  
#endif
  
  return true;
}

void DnMesh::fuseVertices(uint vdrop, uint vkeep)
{
  // collect faces which are connected to vdrop and
  // move them over to vkeep
  Indices edg;
  Indices f(vertices[vdrop].nbTriangles());
  const uint nf(f.size());
  for (uint i=0; i<nf; ++i) {
    if (f[i] != NotFound and triangles[f[i]].isValid()) {
      triangles[f[i]].replaceVertex(vdrop, vkeep);
      vertices[vdrop].detachTriangle(f[i]);
      vertices[vkeep].attachTriangle(f[i]);
      const uint *nbe(triangles[f[i]].nbEdges());
      edg.insert(edg.end(), nbe, nbe+3);
      
      // recompute the circumsphere center of the modified triangle
      triangles[f[i]].computeSphere(*psf, vertices, (type == DnSpatial));
    }
  }
  sort_unique(edg);
  
  // move edge endpoints from vdrop to vkeep
#if !defined(NDEBUG)  
  uint nid(0);
#endif
  const uint ne(edg.size());
  for (uint i=0; i<ne; ++i) {
    if (edg[i] == NotFound)
      continue;
    DnEdge & e(edges[edg[i]]);
    uint f1 = e.nbTriangle(0);
    uint f2 = e.nbTriangle(1);
    uint src = e.source();
    uint trg = e.target();
    assert(src != trg);
    if (src == vdrop) {
      e.reconnect(vkeep, trg);
      e.attachTriangle(f1);
      e.attachTriangle(f2);
    } else if (trg == vdrop) {
      e.reconnect(src, vkeep);
      e.attachTriangle(f1);
      e.attachTriangle(f2);
    }
    
#if !defined(NDEBUG)    
    // count collapsed edges
    if (e.source() == e.target()) {
      ++nid;
      if (nid > 1)
        this->toXml().write("collapse_failure.xml", XmlElement::ZippedXml);
      assert(nid < 2);
    }
#endif  
  }
}

bool DnMesh::destroyHat(uint ti, uint elong)
{
  assert(ti != NotFound);
  assert(triangles[ti].isValid());
  assert(elong != NotFound);
  
  // vertex with large internal angle:
  uint vtop = triangles[ti].opposedVertex(edges[elong]);
  
  // first, flip edge if illegal
  bool flipped = legalizeEdge(elong, vtop);
  if (flipped) {
#if !defined(NDEBUG)
    Indices tmp;
    checkConnectivity(vtop, tmp);
#endif
    return true;
  }
  
  // else, apply local laplacian smoothing if possible
  Vct2 ra, rb, bc, pos;
  Real ta, area(0.0);
  DnVertex & v(vertices[vtop]);
  const Indices & nbf(v.nbTriangles());
  const uint nf(nbf.size());
  for (uint k=0; k<nf; ++k) {
    
    // check if any edge of nbf[k] is either nonflippable
    // or a boundary edge - cannot move vtop in that case
    const uint *nbe(triangles[nbf[k]].nbEdges());
    for (uint j=0; j<3; ++j) {
      assert(nbe[j] != NotFound);
      assert(edges[nbe[j]].isValid());
      if (not canFlip(nbe[j]))
        return false;
      const DnEdge & e(edges[nbe[j]]);
      if (e.nNeighbors() < 2)
        return false;
    }
    
    // compute contribution to barycenter
    const uint *vi(triangles[nbf[k]].vertices());
    const Vct2 & p1(vertices[vi[0]].parpos());
    const Vct2 & p2(vertices[vi[1]].parpos());
    const Vct2 & p3(vertices[vi[2]].parpos());
    ra = p2-p1;
    rb = p3-p1;
    ta = ra[0]*rb[1] - ra[1]*rb[0];
    area += fabs(ta);
    bc += ta*(p1 + p2 + p3);
  }
  bc /= 3*area;
  
  // try damped laplacian smoothing
  Real omega = 1.0;
  while (omega > 0.01) {
    pos = (1.0 -omega) * v.parpos() + omega*bc;
    if (vertexCanMove(vtop, pos)) {
      v.displace(*psf, pos);
      
      // recompute the circumsphere center of the modified triangle
      for (uint k=0; k<nf; ++k)
        triangles[nbf[k]].computeSphere(*psf, vertices, (type == DnSpatial));
      
#if !defined(NDEBUG)
      Indices tmp;
      checkConnectivity(vtop, tmp);
#endif      
      return true;
    }
    omega *= 0.5;
  }
  
  // failed to move vertex because of topological collision
  return false;
}

bool DnMesh::isConvexSet(uint v[4]) const
{
  Real t0, t2;
  t0 = orientation(v[1], v[3], v[0]);
  if (t0 == 0)
    return false;
  t2 = orientation(v[1], v[3], v[2]);
  if (t2 == 0)
    return false;
  if ( (t0*t2) >= 0.0)
    return false;
  
  Real t1, t3;
  t1 = orientation(v[0], v[2], v[1]);
  if (t1 == 0)
    return false;
  t3 = orientation(v[0], v[2], v[3]);
  if (t3 == 0)
    return false;
  if ( (t1*t3) >= 0.0)
    return false;
  
  return true;
}

void DnMesh::destretch(uint nmax, Real maxstretch)
{
  // maintain a heap sorted by stretch ratio
  DnStretchCriterion c(this);
  DnTriangleHeap heap(c, triangles);
  if (heap.empty())
    return;
  
  // refine until all criteria are met
  DnTriangleShape shp;
  Indices that, ehat;
  uint nt, iworst = heap.top();
  while (c.eval(triangles[iworst].vertices()) > maxstretch
         and vertices.size() < nmax) {
    
    // clear new triangle list
    newTriangles.clear();
    
    // try to improve triangle
    classify(iworst, maxstretch, shp);
    switch (shp.shape) {
    case DnRegular:
      return;
    case DnNeedle:
      collapseEdge(shp.eshort);
      break;
    case DnHat:
      destroyHat(iworst, shp.elong);
      break;
    }
    
    // remove top element from heap after triangles
    // have been processed - to make sure that the heap ordering
    // reflects their (possibly) changed shape
    heap.pop();
    
    // in case we created new triangles, add them to heap
    uint nnt = nntriangles();
    for (uint i=0; i<nnt; ++i) {
      nt = newTriangles[i];
      if (nt != NotFound)
        heap.push(nt);
    }
    
    // fetch new 'worst' triangle
    iworst = heap.top();
    
    // if the top element is uncritical, we may need to initialize
    // the heap again
    if (c.eval(triangles[iworst].vertices()) < maxstretch) {
      heap.append(Indices());
      iworst = heap.top();
    }
  }
}

void DnMesh::smooth(uint niter, Real omega)
{
  if (niter == 0 or omega == 0.0)
    return;

  // find vertices which cannot be moved
  Indices ifix;
  uint ne(edges.size());
  for (uint i=0; i<ne; ++i) {
    const DnEdge & e(edges[i]);
    if (e.isValid()) {
      uint src = e.source();
      uint trg = e.target();
      if (e.nNeighbors() < 2 or (not canFlip(i)) or isKink(i)) {
        ifix.push_back(src);
        ifix.push_back(trg);
      }
    }
  }
  sort_unique(ifix);
  
  // vertices which can theoretically be moved
  Indices idx;
  const uint nvo(vertices.size());
  for (uint i=0; i<nvo; ++i) {
    if (binary_search(ifix.begin(), ifix.end(), i))
      continue;
    uint nnb = vertices[i].nbTriangles().size();
    if (nnb > 2)
      idx.push_back(i);
  }
  
  smooth(idx, niter, omega);
}

void DnMesh::smooth(const Indices & idx, uint niter, Real omega)
{
  if (niter == 0 or omega == 0.0)
    return;

  // collect indices of surrounding polygons
  const uint nv(idx.size());
  
  // smoothing iteration
  Vct2 pos, ra, rb, bc;
  for (uint iter=0; iter<niter; ++iter) {
    for (uint i=0; i<nv; ++i) {
      centerVertex(idx[i], omega);
    }
  }
  
  // recompute circumsphere centers after smoothing
  // these are not used inside the loop but must be computed
  // once all vertices have moved to their final position
  const uint nt(triangles.size());
  for (uint i=0; i<nt; ++i) {
    DnTriangle & t(triangles[i]);
    if (t.isValid())
      t.computeSphere(*psf, vertices, (type == DnSpatial));
  }
}

void DnMesh::smoothStretched(Real maxstretch)
{
  // collect candidates for smoothing
  Indices ism;
  DnTriangleShape shp;
  const uint nt(triangles.size());
  for (uint i=0; i<nt; ++i) {
    const DnTriangle & t(triangles[i]);
    if (not t.isValid())
      continue;
    classify(i, maxstretch, shp);
    if (shp.shape == DnNeedle or shp.shape == DnHat) {
      const uint *vi(t.vertices());
      for (int k=0; k<3; ++k) {
        insert_once(ism, vi[k]);
        const Indices & nbf(vertices[vi[k]].nbTriangles());
        const int nf = nbf.size();
        for (int j=0; j<nf; ++j) {
          if (nbf[j] == NotFound)
            continue;
          const DnTriangle & tj(triangles[nbf[j]]);
          if (not tj.isValid())
            continue;
          const uint *vj(tj.vertices());
          for (int kj=0; kj<3; ++kj)
            insert_once(ism, vj[kj]);
        }
      }
    }
  }
  
  // find vertices which cannot be moved
  Indices ifix;
  uint ne(edges.size());
  for (uint i=0; i<ne; ++i) {
    const DnEdge & e(edges[i]);
    if (e.isValid()) {
      uint src = e.source();
      uint trg = e.target();
      if (e.nNeighbors() < 2 or (not canFlip(i)) ) {
        ifix.push_back(src);
        ifix.push_back(trg);
      }
    }
  }
  sort_unique(ifix);
  
  Indices imv;
  std::set_difference(ism.begin(), ism.end(),
                      ifix.begin(), ifix.end(),
                      back_inserter(imv) );
  
  // must do at least 2 iterations to handle difficult cases
  // near constraints (some beneficial destretching occurs only in 2nd pass)
  smooth(imv, 3, 0.8);
}

void DnMesh::smoothStretched(Real maxstretch, std::vector<BndRect> & bxs)
{
  // collect candidates for smoothing
  Indices ism;
  DnTriangleShape shp;
  const uint nt(triangles.size());
  for (uint i=0; i<nt; ++i) {
    const DnTriangle & t(triangles[i]);
    if (t.isValid()) {
      classify(i, maxstretch, shp);
      if (shp.shape == DnNeedle or shp.shape == DnHat) {
        const uint *vi(t.vertices());
        ism.insert(ism.end(), vi, vi+3);
      }
    }
  }
  sort_unique(ism);
  
  // find vertices which cannot be moved
  Indices ifix;
  uint ne(edges.size());
  for (uint i=0; i<ne; ++i) {
    const DnEdge & e(edges[i]);
    if (e.isValid()) {
      uint src = e.source();
      uint trg = e.target();
      if (e.nNeighbors() < 2 or (not canFlip(i)) ) {
        ifix.push_back(src);
        ifix.push_back(trg);
      }
    }
  }
  sort_unique(ifix);
  
  Indices imv;
  std::set_difference(ism.begin(), ism.end(),
                      ifix.begin(), ifix.end(),
                      back_inserter(imv) );
  
  // use vertices in boxes only
  Indices tmp;
  const uint nb(bxs.size());
  const uint ni(imv.size());
  for (uint i=0; i<ni; ++i) {
    const Vct2 p(parpos(imv[i]));
    for (uint k=0; k<nb; ++k) {
      if (bxs[k].isInside(p)) {
        tmp.push_back(imv[i]);
        break;
      }
    }
  }
  sort_unique(tmp);
  imv.swap(tmp);
  
  smooth(imv, 1, 1.0);
}

void DnMesh::centerVertex(uint i, Real omega)
{
  if (type == DnSpatial) {
    
    Vct3 bc;
    Real ta, area(0.0);
    DnVertex & v(vertices[i]);
    const Indices & nbf(v.nbTriangles());
    const uint nf(nbf.size());
    for (uint k=0; k<nf; ++k) {
      const uint *vi(triangles[nbf[k]].vertices());
      const Vct3 & p1(vertices[vi[0]].eval());
      const Vct3 & p2(vertices[vi[1]].eval());
      const Vct3 & p3(vertices[vi[2]].eval());
      ta = norm(cross(p2-p1, p3-p1));
      area += ta;
      bc += ta*(p1 + p2 + p3);
    }
    bc *= omega/(3*area);
    bc += (1.0 - omega) * v.eval();
    
    // compute projection for 3-space point on surface
    Vct2 qbest( vertices[i].parpos() );
    psf->project(bc, qbest);
    
    // TODO: Fallback if projection fails
    
    if (vertexCanMove(i, qbest))
      v.displace(*psf, qbest);
    
  } else {
    
    Vct2 bc, ra, rb, pos;
    Real ta, area(0.0);
    DnVertex & v(vertices[i]);
    const Indices & nbf(v.nbTriangles());
    const uint nf(nbf.size());
    for (uint k=0; k<nf; ++k) {
      const uint *vi(triangles[nbf[k]].vertices());
      const Vct2 & p1(vertices[vi[0]].parpos());
      const Vct2 & p2(vertices[vi[1]].parpos());
      const Vct2 & p3(vertices[vi[2]].parpos());
      ra = p2-p1;
      rb = p3-p1;
      ta = ra[0]*rb[1] - ra[1]*rb[0];
      area += fabs(ta);
      bc += fabs(ta)*(p1 + p2 + p3);
    }
    bc /= 3*area;
    pos = (1.0 -omega) * v.parpos() + omega*bc;

    if (vertexCanMove(i, pos))
      v.displace(*psf, pos);
    
  }
}

bool DnMesh::vertexCanMove(uint v, const Vct2 & pt) const
{
  Real a;
  const Indices & nbf(vertices[v].nbTriangles());
  const uint nf(nbf.size());
  if (type == DnPlane) {
    Vct2 ra, rb;
    for (uint i=0; i<nf; ++i) {
      assert(nbf[i] != NotFound);
      assert(triangles[nbf[i]].isValid());
      const uint *vi(triangles[nbf[i]].vertices());
      const Vct2 & p1(vertices[vi[0]].parpos());
      const Vct2 & p2(vertices[vi[1]].parpos());
      const Vct2 & p3(vertices[vi[2]].parpos());
      
      if (v == vi[0]) {
        ra = p2-pt;
        rb = p3-pt;
      } else if (v == vi[1]) {
        ra = pt-p1;
        rb = p3-p1;
      } else if (v == vi[2]) {
        ra = p2-p1;
        rb = pt-p1;
      } else {
        assert(!"Huh? Point is not in its own triangle?");
      }
      a = ra[0]*rb[1] - ra[1]*rb[0];
      if (a < gmepsilon)
        return false;
    }
    return true;
    
  } else {
    
    Vct3 nprev, ra, rb, ept(psf->eval(pt[0], pt[1]));
    for (uint i=0; i<nf; ++i) {
      assert(nbf[i] != NotFound);
      assert(triangles[nbf[i]].isValid());
      const uint *vi(triangles[nbf[i]].vertices());
      const Vct3 & p1(vertices[vi[0]].eval());
      const Vct3 & p2(vertices[vi[1]].eval());
      const Vct3 & p3(vertices[vi[2]].eval());
      
      if (v == vi[0]) {
        ra = p2-ept;
        rb = p3-ept;
      } else if (v == vi[1]) {
        ra = ept-p1;
        rb = p3-p1;
      } else if (v == vi[2]) {
        ra = p2-p1;
        rb = ept-p1;
      } else {
        assert(!"Huh? Point is not in its own triangle?");
      }
      a = dot(cross(ra,rb), vertices[v].normal());
      if (a < gmepsilon)
        return false;
    }
    return true;
  }
}  

void DnMesh::constructPolygon(uint v, Indices & ip) const
{
  // collect circumferential edges for interior point
  assert(v < vertices.size());
  Indices cfe;
  uint src, trg;
  const Indices & nbf(vertices[v].nbTriangles());
  const uint nf(nbf.size());
  for (uint k=0; k<nf; ++k) {
    assert(nbf[k] != NotFound);
    assert(triangles[nbf[k]].isValid());
    const uint *nbe(triangles[nbf[k]].nbEdges());
    for (uint j=0; j<3; ++j) {
      assert(nbe[j] != NotFound);
      assert(edges[nbe[j]].isValid());
      src = edges[nbe[j]].source();
      trg = edges[nbe[j]].target();
      if (src != v and trg != v) {
        cfe.push_back(nbe[j]);
        break;
      }
    }
  }
  
  // bail out for fewer than three edges - no polygon
  ip.clear();
  if (cfe.size() < 3)
    return;
  
  // insert first edge (ordering does not matter yet)
  ip.push_back( edges[cfe.back()].source() );
  ip.push_back( edges[cfe.back()].target() );
  cfe.pop_back();
  
  // insert remaining edges
  Indices::iterator pos;
  while (not cfe.empty()) {
    const uint ne(cfe.size());
    uint last = ip.back();
    for (uint i=0; i<ne; ++i) {
      pos = cfe.begin()+i;
      src = edges[cfe[i]].source();
      trg = edges[cfe[i]].target();
      if (src == last) {
        ip.push_back(trg);
        break;
      } else if (trg == last) {
        ip.push_back(src);
        break;
      }
    }
    cfe.erase(pos);
  }
  
  if (ip.back() != ip.front())
    ip.push_back(ip.front());
}

bool DnMesh::ptInPolygon(const Vct2 & pt, const Indices & ip) const
{
  assert(ip.front() == ip.back());
  uint ninters(0);
  const uint ne(ip.size()-1);
  Real s, x, y;
  x = pt[0];
  y = pt[1];
  for (uint i=0; i<ne; ++i) {
    const Vct2 & p1(vertices[ip[i]].parpos());
    const Vct2 & p2(vertices[ip[i+1]].parpos());

    // count how often a ray from pt to (pt[0], infty) would intersect
    // the edges of the polygon
    if (x < min(p1[0], p2[0]))
      continue;
    else if (x > max(p1[0],p2[0]))
      continue;
    
    if (y > max(p1[1], p2[1]))
      continue;
    
    s = (x - p1[0]) / (p2[0] - p1[0]);
    if (s >= 0.0 and s < 1.0) {
      ++ninters;
    }
  }
  return ((ninters%2) == 1);
}

void DnMesh::markKinks(Real dphi)
{
  iKinkEdge.clear();
  
  Vct3 nr, nl;
  Real dcosphi = cos(dphi);
  const uint ne(edges.size());
  uint fr, fl;
  for (uint i=0; i<ne; ++i) {
    const DnEdge & e(edges[i]);
    if (not e.isValid())
      continue;
    else if (e.nNeighbors() < 2)
      continue;
    
    fr = e.nbTriangle(0);
    fl = e.nbTriangle(1);
    
    assert(triangles[fr].isValid());
    assert(triangles[fl].isValid());
    
    nr = triangles[fr].normal(vertices);
    nl = triangles[fl].normal(vertices);
    
    if ( cosarg(nr,nl) < dcosphi ) {
      iKinkEdge.push_back(i);
    }
  }
  
  //#ifndef NDEBUG
  //  clog << "Marked " << iKinkEdge.size() << " edges as kinks. " << endl;
  //#endif
  
  //   const Real tdist(2e-4);
  //   Vct3 nmid, nr, nl;
  //   Vct2 qmid, qdir, qtrans, ql, qr;
  //   Real dcosphi = cos(dphi);
  //   const uint ne(edges.size());
  //   for (uint i=0; i<ne; ++i) {
  //     const DnEdge & e(edges[i]);
  //     if (not e.isValid())
  //       continue;
  //     else if (e.nNeighbors() < 2)
  //       continue;
  //
  //     uint src = e.source();
  //     uint trg = e.target();
  //
  //     // construct two points left and right of edge midpoint
  //     qmid = 0.5*(vertices[src].parpos() + vertices[trg].parpos());
  //     qdir = (vertices[trg].parpos() - vertices[src].parpos());
  //     normalize(qdir);
  //     qtrans[0] =  qdir[1];
  //     qtrans[1] = -qdir[0];
  //     qr = qmid + tdist*qtrans;
  //     ql = qmid - tdist*qtrans;
  //
  //     // cannot use this method near the boundary
  //     if (qr[0] < 0 or qr[0] > 1)
  //       continue;
  //     if (qr[1] < 0 or qr[1] > 1)
  //       continue;
  //     if (ql[0] < 0 or ql[0] > 1)
  //       continue;
  //     if (ql[1] < 0 or ql[1] > 1)
  //       continue;
  //
  //     // evaluate normals at these points
  //     nr = psf->normal(qr[0], qr[1]);
  //     nl = psf->normal(ql[0], ql[1]);
  //
  //     if ( cosarg(nr,nl) < dcosphi ) {
  //       iKinkEdge.push_back(i);
  // #ifndef NDEBUG
  //       clog << "Marked kink at " << qmid << endl;
  //     } else if ( fabs(qmid[1] - 0.5) < gmepsilon) {
  //       clog << "Center edge: " << deg(arg(nr,nl)) << endl;
  // #endif
  //     }
  //   }
}

#if !defined(NDEBUG)

uint DnMesh::checkConnectivity(uint v, Indices & nbv) const
{
  assert(v != NotFound);
  // check if any affected entities are connected
  // to dead triangle or edges
  const Indices & vnbf(vertices[v].nbTriangles());
  const uint nf(vnbf.size());
  for (uint j=0; j<nf; ++j) {
    
    // check that all nb triangles are valid
    assert(vnbf[j] != NotFound);
    const DnTriangle & t(triangles[vnbf[j]]);
    assert(t.isValid());
    
    // nb triangle of v must be connected to v
    assert(t.find(v) != NotFound);
    
    // compute 3D normal vector of triangle
    const uint *vi(t.vertices());
    //     if (type == DnSpatial) {
    //       const Vct3 & p1(vertices[vi[0]].eval());
    //       const Vct3 & p2(vertices[vi[1]].eval());
    //       const Vct3 & p3(vertices[vi[2]].eval());
    //       Vct3 fn = cross(p2-p1, p3-p1);
    //       assert(dot(fn, vertices[v].normal()) > 0);
    //     }
    
    nbv.insert(nbv.end(), vi, vi+3);
    const uint *fnbe(t.nbEdges());
    for (uint k=0; k<3; ++k) {
      
      // check if edge is valid
      assert(fnbe[k] != NotFound);
      const DnEdge & e(edges[fnbe[k]]);
      assert(e.isValid());
      assert(e.source() != e.target());
      
      // edge itself must be connected to triangle as well
      assert(e.nbTriangle(0) == vnbf[j] or e.nbTriangle(1) == vnbf[j]);
    }
  }
  sort_unique(nbv);
  
  return nf;
}

#else

uint DnMesh::checkConnectivity(uint, Indices &) const
{
  return 0;
}

#endif
