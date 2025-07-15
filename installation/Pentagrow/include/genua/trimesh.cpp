
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
 
// #ifdef HAVE_CGNS
#include "cgnsfile.h"
#include "cgnszone.h"
#include "cgnssection.h"
// #endif // HAVE_CGNS

#include "flagset.h"
#include "boxsearchtree.h"
#include "trimesh.h"

// for porting functions
#include "triangulation.h"
#include "sparse.h"

#include "dbprint.h"
#include "ioglue.h"
#include <sstream>

using std::string;

TriMesh::TriMesh(const TriMesh & msh) : vtx(msh.vtx), nrm(msh.nrm), 
  faces(msh.faces), edges(msh.edges), v2f(msh.v2f), v2e(msh.v2e),
  e2f(msh.e2f), f2e(msh.f2e), tagnames(msh.tagnames)
{
  bind();
}

TriMesh & TriMesh::operator= (const TriMesh & msh)
{
  if (&msh != this) {
    vtx = msh.vtx;
    nrm = msh.nrm;
    faces = msh.faces;
    edges = msh.edges;
    v2f = msh.v2f;
    v2e = msh.v2e;
    e2f = msh.e2f;
    f2e = msh.f2e;
    tagnames = msh.tagnames;
    bind();
  }
  return *this;
}

void TriMesh::bind()
{
  const uint nf(faces.size());
  for (uint i=0; i<nf; ++i)
    faces[i].bind(this);
  const uint ne(edges.size());
  for (uint i=0; i<ne; ++i)
    edges[i].bind(this);
}

void TriMesh::swap(TriMesh & a)
{
  vtx.swap(a.vtx);
  nrm.swap(a.nrm);
  faces.swap(a.faces);
  edges.swap(a.edges);
  v2f.swap(a.v2f);
  v2e.swap(a.v2e);
  e2f.swap(a.e2f);
  f2e.swap(a.f2e);
  tagnames.swap(a.tagnames);
  bind();
  a.bind();
}

void TriMesh::importMesh(const PointList<3> & pts, const Indices & tri, 
                         bool udrop)
{
  clear();
  vtx = pts;
  const uint nf(tri.size()/3);
  faces.resize(nf);
  for (uint i=0; i<nf; ++i) {
    const uint *vi(&tri[3*i]);
    faces[i].assign(this, vi[0], vi[1], vi[2]);
  }
  fixate(udrop);
}

void TriMesh::importMesh(const PointList<3> & pts, const PointList<3> & nmv, 
                         const Indices & tri, bool udrop)
{
  nrm = nmv;
  importMesh(pts, tri, udrop);
}

void TriMesh::exportMesh(PointList<3> & pts, Indices & tri) const
{
  pts = vtx;
  const uint nf(faces.size());
  tri.resize(3*nf);
  for (uint i=0; i<nf; ++i)
    faces[i].getVertices(&tri[3*i]);
}

void TriMesh::exportMesh(PointList<3> & pts, PointList<3> & nmv, 
                         Indices & tri) const
{
  nmv = nrm;
  exportMesh(pts, tri);
}

void TriMesh::clear()
{
  vtx.clear();
  nrm.clear();
  faces.clear();
  edges.clear();
  v2e.clear();
  v2f.clear();
  e2f.clear();
  f2e.clear();
  tagnames.clear();
}

void TriMesh::triangulate(const PointGrid<3> & pg, GridPattern gpt)
{
  clear();

  // copy vertices
  const uint nr(pg.nrows());
  const uint nc(pg.ncols());
  const uint nv(nr*nc);
  vtx.resize(nv);
  memcpy(&(vtx[0]), &(pg(0,0)), 3*nv*sizeof(Real));

  const uint nf( 2*(nr-1)*(nc-1) );
  faces.resize(nf);
  uint p1, p2, p3, p4, fi1, fi2;
  uint rhalf, chalf;
  switch (gpt) {

  case XPattern:
    for (uint i=0; i<nr-1; ++i) {
      for (uint j=0; j<nc-1; ++j) {
        p1 = i + j*nr;
        p2 = i+1 + j*nr;
        p3 = i+1 + (j+1)*nr;
        p4 = i + (j+1)*nr;
        fi1 = 2*(nc-1)*i + 2*j;
        fi2 = fi1 + 1;
        if (i%2 == j%2) {
          faces[fi1].assign(this, p1, p2, p3);
          faces[fi2].assign(this, p1, p3, p4);
        } else {
          faces[fi1].assign(this, p1, p2, p4);
          faces[fi2].assign(this, p2, p3, p4);
        }
      }
    }
    break;

  case QuadPattern:

    rhalf = nr/2;
    chalf = nc/2;
    for (uint i=0; i<rhalf; ++i) {
      for (uint j=0; j<chalf; ++j) {
        p1 = j*nr + i;
        p2 = j*nr + i+1;
        p3 = (j+1)*nr + i+1;
        p4 = (j+1)*nr + i;
        fi1 = 2*(nc-1)*i + 2*j;
        fi2 = fi1 + 1;
        faces[fi1].assign(this, p1, p2, p4);
        faces[fi2].assign(this, p2, p3, p4);
      }
      for (uint j=chalf; j<nc-1; ++j) {
        p1 = j*nr + i;
        p2 = j*nr + i+1;
        p3 = (j+1)*nr + i+1;
        p4 = (j+1)*nr + i;
        fi1 = 2*(nc-1)*i + 2*j;
        fi2 = fi1 + 1;
        faces[fi1].assign(this, p1, p2, p3);
        faces[fi2].assign(this, p1, p3, p4);
      }
    }
    for (uint i=rhalf; i<nr-1; ++i) {
      for (uint j=0; j<chalf; ++j) {
        p1 = j*nr + i;
        p2 = j*nr + i+1;
        p3 = (j+1)*nr + i+1;
        p4 = (j+1)*nr + i;
        fi1 = 2*(nc-1)*i + 2*j;
        fi2 = fi1 + 1;
        faces[fi1].assign(this, p1, p2, p3);
        faces[fi2].assign(this, p1, p3, p4);
      }
      for (uint j=chalf; j<nc-1; ++j) {
        p1 = j*nr + i;
        p2 = j*nr + i+1;
        p3 = (j+1)*nr + i+1;
        p4 = (j+1)*nr + i;
        fi1 = 2*(nc-1)*i + 2*j;
        fi2 = fi1 + 1;
        faces[fi1].assign(this, p1, p2, p4);
        faces[fi2].assign(this, p2, p3, p4);
      }
    }
    break;

  case BiasedPattern:
    for (uint i=0; i<nr-1; ++i) {
      for (uint j=0; j<nc-1; ++j) {
        p1 = i + j*nr;
        p2 = i+1 + j*nr;
        p3 = i+1 + (j+1)*nr;
        p4 = i + (j+1)*nr;
        fi1 = 2*(nc-1)*i + 2*j;
        fi2 = fi1 + 1;
        faces[fi1].assign(this, p1, p2, p3);
        faces[fi2].assign(this, p1, p3, p4);
      }
    }
    break;
  }
  
}

void TriMesh::merge(const TriMesh & msh)
{
  if (msh.nvertices() == 0)
    return;

  uint voff = vtx.size();
  uint foff = faces.size();
  vtx.insert(vtx.end(), msh.vtx.begin(), msh.vtx.end());
  nrm.insert(nrm.end(), msh.nrm.begin(), msh.nrm.end());
  
  // copy faces and attach to this surface
  faces.insert(faces.end(), msh.faces.begin(), msh.faces.end());
  uint nf = faces.size();
  for (uint i=foff; i<nf; ++i)
    faces[i].bind(this, voff);
  
  // delete old edges and connectivity, these are outdated now
  edges.clear();
  v2e.clear();
  v2f.clear();
  e2f.clear();
  f2e.clear();
}

void TriMesh::merge(const Triangulation & t)
{
  uint voff = vtx.size();
  const PointList<3> & tv(t.vertices());
  const PointList<3> & tn(t.normals());
  vtx.insert(vtx.end(), tv.begin(), tv.end());
  nrm.insert(nrm.end(), tn.begin(), tn.end());
  
  // copy faces and attach to this surface
  uint vi[3];
  Triangulation::face_iterator itf, first, last;
  first = t.face_begin();
  last = t.face_end();
  for (itf = first; itf != last; ++itf) {
    itf->getVertices(vi);
    vi[0] += voff;
    vi[1] += voff;
    vi[2] += voff;
    faces.push_back( TriFace(this, vi[0], vi[1], vi[2]) );
  }
  
  // delete old edges and connectivity, these are outdated now
  edges.clear();
  v2e.clear();
  v2f.clear();
  e2f.clear();
  f2e.clear();
}

void TriMesh::buildConnectivity(bool udrop)
{
  uint nv(vtx.size());
  uint nf(faces.size());

  // drop illegal faces
  {
    TriFaceArray ftmp;
    for (uint i=0; i<nf; ++i) {
      if (faces[i].isValid() and faces[i].inRange())
        ftmp.push_back(faces[i]);
    }

    // make sure 'faces' is not larger than necessary
    TriFaceArray(ftmp).swap(faces);
    nf = faces.size();
  }

  if (udrop) {

    // identify vertices in use
    Indices iused(3*nf);
    for (uint i=0; i<nf; ++i)
      faces[i].getVertices(&iused[3*i]);
    sort_unique(iused);

    if (iused.size() < nv) {

      // copy used vertices/normals only
      const uint nu(iused.size());
      if (vtx.size() == nrm.size()) {
        PointList<3> tv(nu), tn(nu);
        for (uint i=0; i<nu; ++i) {
          tv[i] = vtx[iused[i]];
          tn[i] = nrm[iused[i]];
        }
        tv.swap(vtx);
        tn.swap(nrm);
      } else {
        PointList<3> tv(nu);
        for (uint i=0; i<nu; ++i)
          tv[i] = vtx[iused[i]];
        tv.swap(vtx);
      }

      // compute inverse permutation
      Indices iperm(nv);
      std::fill(iperm.begin(), iperm.end(), NotFound);
      for (uint i=0; i<nu; ++i) {
        iperm[iused[i]] = i;
      }

      // adapt vertex index names in faces
      uint vn[3];
      for (uint i=0; i<nf; ++i) {
        const uint *vi(faces[i].vertices());
        for (uint k=0; k<3; ++k) {
          vn[k] = iperm[vi[k]];
          assert(vn[k] != NotFound);
        }
        faces[i].assign(this, vn[0], vn[1], vn[2]);
      }
      nv = nu;

    }
  }

  // count vertex-face connections and generate edges
  {
    Indices tmp(6*nf);
    uint off(0), k(0);
    edges.clear();
    edges.resize(3*nf);
    for (uint i=0; i<nf; ++i) {
      const uint *vi(faces[i].vertices());
      tmp[k+0] = vi[0];
      tmp[k+1] = i;
      tmp[k+2] = vi[1];
      tmp[k+3] = i;
      tmp[k+4] = vi[2];
      tmp[k+5] = i;
      k += 6;
      edges[off+0].assign(this, vi[0], vi[1]);
      edges[off+1].assign(this, vi[1], vi[2]);
      edges[off+2].assign(this, vi[2], vi[0]);
      off += 3;
    }
    v2f.assign(nv, tmp);
  }

  // sort edge array and shrink to required size
  {
    TriEdgeArray tmp;
    TriEdgeArray::iterator last;
    std::sort(edges.begin(), edges.end());
    last = std::unique(edges.begin(), edges.end());
    tmp.insert(tmp.end(), edges.begin(), last);
    tmp.swap(edges);
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

  // connect faces and edges
  {
    uint ei, t[3];
    Indices tmp;
    tmp.reserve(4*ne);
    f2e.allocate(nf, 3);
    for (uint i=0; i<nf; ++i) {
      const uint *vi(faces[i].vertices());
      t[0] = vi[1];
      t[1] = vi[2];
      t[2] = vi[0];
      for (uint k=0; k<3; ++k) {
        ei = tsearchEdge(vi[k], t[k]);
        assert(ei != NotFound);
        f2e.append(i, ei);
        tmp.push_back(ei);
        tmp.push_back(i);
      }
    }
    f2e.close();
    e2f.assign(ne, tmp);
  }
}

void TriMesh::fixate(bool udrop)
{
  buildConnectivity(udrop);
  
  // compute normal vectors if necessary
  if (nrm.size() != vtx.size())
    estimateNormals();
}

void TriMesh::estimateNormals()
{
  const uint nv(vtx.size());
  assert(v2f.size() == nv);
  nrm.resize(nv);
  
  Vct3 fn;
  Real angle;
  nb_face_iterator itf, first, last;
  for (uint i=0; i<nv; ++i) {
    nrm[i] = 0.0;
    first = v2fBegin(i);
    last = v2fEnd(i);
    for (itf = first; itf != last; ++itf) {
      angle = itf->corner(i);
      if (angle > 0) {
        itf->normal(fn);
        nrm[i] += angle * fn;
      }
    }
    normalize(nrm[i]);
  }
}

Real TriMesh::area() const
{
  // sum of face areas
  Real sum(0);
  face_iterator itf;
  for (itf = faceBegin(); itf != faceEnd(); ++itf)
    sum += itf->area();
  return sum;
}

Real TriMesh::volume() const
{
  Real sum(0);
  face_iterator itf;
  for (itf = faceBegin(); itf != faceEnd(); ++itf) {
    const uint *vi(itf->vertices());
    const Vct3 & a( vtx[vi[0]] );
    const Vct3 & b( vtx[vi[1]] );
    const Vct3 & c( vtx[vi[2]] );
    sum += dot(cross(a,b),c);
  }
  return 0.5*sum;
}

Vct3 TriMesh::volumeCenter() const
{
  Real vol, sum(0);
  Vct3 ctr;
  face_iterator itf;
  for (itf = faceBegin(); itf != faceEnd(); ++itf) {
    const uint *vi(itf->vertices());
    const Vct3 & a( vtx[vi[0]] );
    const Vct3 & b( vtx[vi[1]] );
    const Vct3 & c( vtx[vi[2]] );
    vol = dot(cross(a,b),c);
    ctr += vol*0.25*(a + b + c);  // fourth tet node is (0,0,0)
    sum += vol;
  }
  return ctr/sum;
}

uint TriMesh::findFlippedFaces(Indices & fflip, Real maxphi) const
{
  const Real mincphi = cos(maxphi);
  
  Indices fed;
  const int ne(edges.size());
  for (int i=0; i<ne; ++i) {
    if (e2f.size(i) != 2)
      continue;
    const uint *nbf = e2f.first(i);
    Real cphi = cosarg( face(nbf[0]).normal(), face(nbf[1]).normal() );
    if (cphi < mincphi)
      fed.push_back(i);
  }
  
  if (fed.empty())
    return 0;
  
  fflip.clear();
  const int nf(faces.size());
  for (int i=0; i<nf; ++i) {
    // const TriFace & f(face(i));
    // Vct3 fn = f.normal();
    
    // count folding edges
    if (f2e.size(i) != 3)
      continue;
    int nfe(0);
    const uint *nbe = f2e.first(i);
    for (int k=0; k<3; ++k)
      if (binary_search(fed.begin(), fed.end(), nbe[k]))
        ++nfe;
    if (nfe > 1)
      fflip.push_back(i);
  }
  return fflip.size();
}

Real TriMesh::shortestEdgeLength() const
{
  // find sortest edge and return its length
  Real elen, slen(huge);
  if (not edges.empty()) {
    edge_iterator ite;
    for (ite = edgeBegin(); ite != edgeEnd(); ++ite) {
      elen = norm(vertex(ite->source()) - vertex(ite->target()));
      slen = std::min(slen,elen);
    }
  } else {
    
    // fallback code for uninitialized mesh
    Real len1, len2, len3;
    const uint nt(faces.size());
    for (uint i=0; i<nt; ++i) {
      const uint *vi(faces[i].vertices());
      const Vct3 & p1(vtx[vi[0]]);
      const Vct3 & p2(vtx[vi[1]]);
      const Vct3 & p3(vtx[vi[2]]);
      len1 = norm(p1-p2);
      len2 = norm(p1-p3);
      len3 = norm(p3-p2);
      if ( std::isfinite(len1) and len1 > 0 )
        slen = std::min(slen, len1);
      if ( std::isfinite(len2) and len2 > 0 )
        slen = std::min(slen, len2);
      if ( std::isfinite(len3) and len3 > 0 )
        slen = std::min(slen, len3);
    }
  }
  return slen;
}

Real TriMesh::solidAngle(uint i) const
{
  // compute solid angle at vertex idx
  Real sum(0.0);
  nb_face_iterator itf, first, last;
  first = v2fBegin(i);
  last = v2fEnd(i);
  for (itf = first; itf != last; ++itf)
    sum += itf->solidAngle(i);

  return (sum > 0) ? sum : 4*PI+sum;
}

void TriMesh::gradient(uint i, SpMatrix & gmx) const
{
  assert(i < vtx.size());
  gmx = SpMatrix(3, vtx.size());
  nb_face_iterator itf, first, last;
  first = v2fBegin(i);
  last = v2fEnd(i);
  Real wsum(0), wf;
  Mtx33 fgm;
  for (itf = first; itf != last; ++itf) {
    const uint *vi(itf->vertices());
    wf = itf->corner(i);
    itf->gradient(fgm);
    for (uint j=0; j<3; ++j)
      for (uint k=0; k<3; ++k)
        gmx(k, vi[j]) += wf*fgm(k,j);
    wsum += wf;
  }
  wsum = 1./wsum;
  gmx *= wsum;
}

Vct3 TriMesh::gradient(uint i, const Vector & x) const
{
  assert(i < vtx.size());
  Vct3 gradx;
  nb_face_iterator itf, first, last;
  first = v2fBegin(i);
  last = v2fEnd(i);
  Real wsum(0), wf;
  for (itf = first; itf != last; ++itf) {
    wf = itf->corner(i);
    wsum += wf;
    gradx += wf*itf->gradient(x);
  }
  gradx *= (1.0/wsum);
  return gradx;
}

CpxVct3 TriMesh::gradient(uint i, const CpxVector & x) const
{
  assert(i < vtx.size());
  CpxVct3 gradx;
  nb_face_iterator itf, first, last;
  first = v2fBegin(i);
  last = v2fEnd(i);
  Real wsum(0), wf;
  for (itf = first; itf != last; ++itf) {
    wf = itf->corner(i);
    wsum += wf;
    gradx += Complex(wf,0.0)*itf->gradient(x);
  }
  gradx *= Complex(1.0/wsum, 0.0);
  return gradx;
}

bool TriMesh::isClosedManifold() const
{
  const uint ne(e2f.size());
  for (uint i=0; i<ne; ++i) {
    if (e2f.size(i) != 2) {
#ifndef NDEBUG
      cerr << "Edge " << "[ " << edges[i].source();
      cerr << ", " << edges[i].target();
      cerr << "] degree " << e2f.size(i);
      cerr << " at " << vtx[edges[i].source()] << endl;
#endif
      return false;
    }
  }
  return true;
}

uint TriMesh::mergeNodes(Real threshold, Real dphimax)
{
  // coordinate search tree
  uint nv(vtx.size()), ndpl;
  BSearchTree btree(vtx);

  // find (nearly) identical vertices
  PointList<3> kept;
  Indices repl(nv, NotFound), idt;
  const Real cphimin = std::cos(dphimax);
  bool ignoreDirection = (dphimax < 0.0);
  uint count(0);
  bool useNormals = (nrm.size() == vtx.size()) and (dphimax < M_PI);
  for (uint i=0; i<nv; ++i) {

    // for each vertex which is not yet marked as duplicate
    if (repl[i] == NotFound) {

      // mark as a vertex to keep
      repl[i] = count;

      // locate vertices within radius of threshold
      idt.clear();
      btree.find(vtx[i], threshold, idt);

      // mark duplicates with indices beyond i
      for (uint j=0; j<idt.size(); ++j) {
        if (idt[j] > i) {
          if (not useNormals)
            repl[idt[j]] = count;
          else {
            Real cphi = cosarg(nrm[idt[j]], nrm[i]);
            if (ignoreDirection)
              cphi = std::fabs(cphi);
            if (cphi > cphimin)
              repl[idt[j]] = count;
          }
        }
      }

      // store vertex as kept
      ++count;
      kept.push_back(vtx[i]);
    }

    // skip vertices marked as duplicates
  }

  // eliminate duplicate vertices
  nrm.clear();
  ndpl = vtx.size() - kept.size();
  vtx.swap(kept);

  // apply node index translation to triangles
  if (ndpl > 0) {
    const uint nf(faces.size());
    for (uint i=0; i<nf; ++i)
      faces[i].itranslate(repl);
  }

  // recompute connectivity, will remove invalid faces
  fixate(true);

  return ndpl;
}

uint TriMesh::cleanup(Real threshold)
{
  return mergeNodes(threshold, M_PI);
}

void TriMesh::detectEdges(Real ridgeLimitAngle, Real mergeThreshold)
{
  if (nfaces() == 0 or nvertices() == 0)
    return;
  if (ridgeLimitAngle >= M_PI)
    return;

  mergeNodes(mergeThreshold);

  // dbprint("Post merging vertices:", nvertices());

  // determine ridge edges
  const Real cosRidgeAngle = cos(ridgeLimitAngle);
  const size_t ne = nedges();
  const size_t nf = nfaces();
  std::vector<bool> isridge(ne, false);
  for (size_t i=0; i<ne; ++i) {
    if (edegree(i) != 2) {
      isridge[i] = true;
    } else {
      const uint *nbf = e2f.first(i);
      Real cphi = cosarg( face(nbf[0]).normal(), face(nbf[1]).normal() );
      isridge[i] = (cphi < cosRidgeAngle);
    }
  }

  // gather patches of faces
  std::vector<Indices> patches;
  {
    Indices cpatch, stack;
    FlagSet visited(nf, false);
    stack.push_back(0);
    visited.set(0, true);
    size_t lastNotUsed(0);
    while (not stack.empty()) {

      uint f = stack.back();
      stack.pop_back();
      cpatch.push_back(f);
      const uint *nbe = f2e.first(f);
      assert(f2e.size(f) == 3);
      for (int k=0; k<3; ++k) {
        if (not isridge[nbe[k]]) {  // not a ridge, edge degree must be 2
          assert(edegree(nbe[k]) == 2);
          const uint *nbf = e2f.first(nbe[k]);
          uint fnext = (nbf[0] == f) ? nbf[1] : nbf[0];
          if (not visited[fnext]) {
            visited.set(fnext, true);
            stack.push_back(fnext);
          }
        }
      }

      // if stack exhausted, pick next face not yet marked
      if (stack.empty()) {
        patches.push_back(cpatch);
        cpatch.clear();
        if (visited.nset() < nf) {
          for (size_t i=lastNotUsed; i<nf; ++i) {
            if (not visited[i]) {
              visited.set(i, true);
              stack.push_back(i);
              lastNotUsed = i;
              break;
            }
          }
        }
      } // if stack empty

    }

    // add last patch
    if (not cpatch.empty())
      patches.push_back(cpatch);

  } // end patch gathering

  // dbprint("Patches: ",patches.size(), " faces: ",nfaces());

  // generate mesh subsets
  Indices vix;
  PointList<3> vtmp;
  const size_t nsub = patches.size();
  size_t nchanged = 0;
  for (size_t i=0; i<nsub; ++i) {

    // collect all vertices in this patch
    const Indices & ipatch( patches[i] );
    const size_t ntri = ipatch.size();
    vix.clear();
    vix.resize(3*ntri);
    for (size_t j=0; j<ntri; ++j) {
      const uint *vi = face(ipatch[j]).vertices();
      for (int k=0; k<3; ++k) {
        // cout << ipatch[j] << " Append " << vi[k] << endl;
        vix[3*j+k] = vi[k];
      }
    }

    // generate a unique set
    std::sort(vix.begin(), vix.end());
    vix.erase( std::unique(vix.begin(), vix.end()), vix.end() );
    const size_t nv = vix.size();

    // dbprint("Patch ",i," faces: ", ntri, " vertices: ", vix.size());

    // copy vertices in set to the end of vtmp, translate vertex indices
    // in faces of this patch to indices into vtmp
    size_t voff = vtmp.size();
    for (size_t j=0; j<nv; ++j)
      vtmp.push_back( vtx[vix[j]] );

    uint vt[3];
    for (size_t j=0; j<ntri; ++j) {
      const uint *vi = face(ipatch[j]).vertices();
      for (int k=0; k<3; ++k) {
        uint relidx = sorted_index(vix, vi[k]);
        assert(relidx != NotFound);
        vt[k] = voff + relidx;
        assert( sq(vtx[vi[k]] - vtmp[vt[k]]) == 0.0 );
      }
      face(ipatch[j]).assign(this, vt[0], vt[1], vt[2]);
      ++nchanged;
    }
  }

  // dbprint(nchanged, "faces re-indexed.");

  vtx.swap(vtmp);
  nrm.clear();
  fixate();
}

void TriMesh::reverse()
{
  const uint nf(faces.size());
  for (uint i=0; i<nf; ++i)
    faces[i].reverse();

  // flip all normal vectors
  const uint nv(vtx.size());
  if (nrm.size() == nv) {
    for (uint i=0; i<nv; ++i) {
      nrm[i][0] = -nrm[i][0];
      nrm[i][1] = -nrm[i][1];
      nrm[i][2] = -nrm[i][2];
    }
  } else {
    nrm.clear();
  }
}

void TriMesh::reorder(const Indices & perm)
{
  const uint nv(vtx.size());
  if (perm.size() != nv)
    throw Error("TriMesh::reorder() - Permutation set must have have"
                " nvertices() entries.");

  if (nrm.size() == nv) {
    PointList<3> vtmp(vtx), ntmp(nrm);
    for (uint i=0; i<nv; ++i) {
      vtx[i] = vtmp[perm[i]];
      nrm[i] = ntmp[perm[i]];
    }
  } else {
    PointList<3> tmp(vtx);
    for (uint i=0; i<nv; ++i)
      vtx[i] = tmp[perm[i]];
  }

  // compute inverse permutation
  Indices iperm(nv);
  for (uint i=0; i<nv; ++i)
    iperm[perm[i]] = i;

  // change face indices
  const uint nf(faces.size());
  for (uint i=0; i<nf; ++i)
    faces[i].itranslate(iperm);

  // it is certainly easier to call fixate() at this point and
  // just recompute all connectivity data, but it is certainly
  // more efficient to translate indices explicitly
  //fixate();

  // change edge indices
  const uint ne(edges.size());
  for (uint i=0; i<ne; ++i)
    edges[i].itranslate(iperm);

  v2f.rowpermute(perm);
  v2e.rowpermute(perm);
}

void TriMesh::faceTag(int t)
{
  const int nf = faces.size();
  for (int i=0; i<nf; ++i)
    faces[i].tag(t);
}

void TriMesh::allTags(Indices & tgs) const
{
  const int nf = faces.size();
  for (int i=0; i<nf; ++i)
    insert_once(tgs, uint(faces[i].tag()));
}

void TriMesh::dropDuplicates()
{
  Indices idrop;
  const int nv = v2f.size();
  for (int i=0; i<nv; ++i) {
    const uint *nbf = v2f.first(i);
    const int nf = v2f.size(i);
    for (int j=0; j<nf; ++j) {
      for (int k=j+1; k<nf; ++k) {
        if ( face(nbf[j]).equivalent( face(nbf[k]) ) ) {
          uint jdrop = std::max(nbf[j], nbf[k]);
          insert_once(idrop, jdrop);
        }
      }
    }
  }
  if (idrop.empty())
    return;

  TriFaceArray keep;
  const int nf = faces.size();
  keep.reserve(nf);
  for (int i=0; i<nf; ++i) {
    if (not binary_search(idrop.begin(), idrop.end(), uint(i))) {
      keep.push_back( faces[i] );
    }
  }
  keep.swap(faces);
  fixate();
}

uint TriMesh::dropInternalTriangles(uint itx, bool usetags)
{
  Indices idx(1);
  idx[0] = itx;
  return dropInternalTriangles(idx, usetags);
}

uint TriMesh::dropInternalTriangles(const Indices & idx, bool usetags)
{
  if (faces.empty())
    return 0;

  Indices ixternal;
  Indices::iterator ipos;
  std::deque<uint> queue(idx.begin(), idx.end());

  while (not queue.empty()) {

    uint fcur = queue.front();
    ipos = lower_bound(ixternal.begin(), ixternal.end(), fcur);
    if (ipos == ixternal.end() or *ipos != fcur) {
      ixternal.insert(ipos, fcur);
      nb_edge_iterator ite, first, last;
      first = f2eBegin(fcur);
      last = f2eEnd(fcur);
      for (ite = first; ite != last; ++ite) {
        uint fnext(NotFound);
        uint ei = ite.index();
        uint edeg = e2f.size(ei);
        if (edeg == 2) {
          const uint *nbf(e2f.first(ei));
          assert(fcur == nbf[0] or fcur == nbf[1]);
          // do not walk around the trailing edge
          // this trick solves the t-tail problems
          Vct3 n0( faces[nbf[0]].normal() );
          Vct3 n1( faces[nbf[1]].normal() );
          if (cosarg(n0,n1) > -0.7) {
            if (fcur == nbf[0])
              fnext = nbf[1];
            else
              fnext = nbf[0];
          }

        } else {
          fnext = nextExternalTriangle(fcur, ei, usetags);
        }
        if (fnext != NotFound) {
          if (not binary_search(ixternal.begin(), ixternal.end(), fnext))
            queue.push_back(fnext);
        }
      }
    }
    queue.pop_front();
  }

  // keep only triangles marked as external
  uint nkeep(ixternal.size());
  if (nkeep < faces.size()) {
    TriFaceArray tmp(nkeep);
    for (uint i=0; i<nkeep; ++i)
      tmp[i] = faces[ixternal[i]];
    faces.swap(tmp);
    fixate(true);
  }

  return faces.size();
}

uint TriMesh::nextExternalTriangle(uint fcur, uint ei, bool usetags) const
{
  Vct3 ept, edir, xax, yax, t;
  ept = vtx[edges[ei].target()];
  edir = ept - vtx[edges[ei].source()];
  normalize(edir);
  uint iopp = faces[fcur].opposed(edges[ei]);
  xax = vtx[iopp] - ept;
  xax -= dot(xax,edir)*edir;
  normalize(xax);
  faces[fcur].normal(yax);

  uint fnext(NotFound);

  int edeg = e2f.size(ei);
  const uint *nbf = e2f.first(ei);

  if (usetags and edeg == 4) {

    Real phi[4], minphi, maxphi;
    int tf[4], tcur = faces[fcur].tag();
    for (int k=0; k<4; ++k) {
      tf[k] = faces[nbf[k]].tag();
      if (nbf[k] == fcur) {
        phi[k] = 0.0;
      } else {
        t = vtx[faces[nbf[k]].opposed(edges[ei])] - ept;
        t -= dot(t,edir)*edir;
        Real x = dot(t, xax);
        Real y = dot(t, yax);
        phi[k] = atan2(y, x);
        if (phi[k] < 0)
          phi[k] += 2*PI;
      }
    }

    minphi = 4*PI;
    maxphi = -2*PI;
    int kmaxphi(0), kminphi(0); //, kmid(0);
    for (int k=0; k<4; ++k) {
      if (nbf[k] != fcur) {
        if (phi[k] > maxphi) {
          maxphi = phi[k];
          kmaxphi = k;
        }
        if (phi[k] < minphi) {
          minphi = phi[k];
          kminphi = k;
        }
      }
    }

//    for (int k=0; k<4; ++k)
//      if (nbf[k] != fcur and k != kminphi and k != kmaxphi)
//        kmid = k;

    if ( tf[kmaxphi] != tcur and tf[kminphi] != tcur ) {

      //       // standard case, coming from outside as we should
      //       minphi = 2*PI;
      //       for (int k=0; k<4; ++k) {
      //         if (nbf[k] != fcur and tf[k] != tcur and phi[k] < minphi) {
      //           fnext = nbf[k];
      //           minphi = phi[k];
      //         }
      //       }

      // standard case, coming from outside as we should
      minphi = 2*PI;
      for (int k=0; k<4; ++k) {
        if (nbf[k] != fcur and phi[k] < minphi) {
          fnext = nbf[k];
          minphi = phi[k];
        }
      }

      //       cout << "edeg 4 standard case " << endl;
      //       uint iadd = face(fnext).opposed(edge(ei));
      //       uint src = edge(ei).source();
      //       uint trg = edge(ei).target();
      //       cout << "Added " << iadd << " coming from " << iopp << endl;
      //       cout << "across " << src << " to " << trg << endl;

    } else {

      // inverted case: rely on that the truely external triangle is
      // reachable from the other side.
      fnext = NotFound;

      //       cout << "edeg 4 inverted case " << endl;
      //       uint src = edge(ei).source();
      //       uint trg = edge(ei).target();
      //       cout << "Skipping " << src << " to " << trg << endl;

    }

  } else {

    // standard configuration : never mind component tags
    Real minphi(2*PI);
    for (int k=0; k<edeg; ++k) {
      if (nbf[k] == fcur)
        continue;
      t = vtx[faces[nbf[k]].opposed(edges[ei])] - ept;
      t -= dot(t,edir)*edir;
      Real x = dot(t, xax);
      Real y = dot(t, yax);
      Real phi = atan2(y, x);
      if (phi < 0)
        phi = 2*PI + phi;
      if (phi < minphi) {
        minphi = phi;
        fnext = nbf[k];
      }
    }

    //     cout << "edeg 3 standard case " << endl;
    //     uint iadd = face(fnext).opposed(edge(ei));
    //     uint src = edge(ei).source();
    //     uint trg = edge(ei).target();
    //     cout << "Added " << iadd << " coming from " << iopp << endl;
    //     cout << "across " << src << " to " << trg << endl;

  }

  return fnext;
}

void TriMesh::findEnclosedGroup(uint fcur, Indices & ftri) const
{
  std::deque<uint> qtri(1);
  qtri[0] = fcur;
  while (not qtri.empty()) {
    fcur = qtri.front();
    qtri.pop_front();
    insert_once(ftri, fcur);
    const uint *nbe = f2e.first(fcur);
    assert(f2e.size(fcur) == 3);
    for (int k=0; k<3; ++k) {
      const uint ei = nbe[k];
      const uint *nbf = e2f.first(ei);
      const uint edeg = e2f.size(ei);
      if (edeg == 2) {
        uint f;
        if (nbf[0] == fcur)
          f = nbf[1];
        else
          f = nbf[0];
        if (not binary_search(ftri.begin(), ftri.end(), f))
          qtri.push_back(f);
      }
    }
  }
}

uint TriMesh::countMultipleEdges(uint fcur) const
{
  uint nm(0);
  const int ne = f2e.size(fcur);
  const uint *nbe = f2e.first(fcur);
  for (int k=0; k<ne; ++k) {
    if ( e2f.size( nbe[k] ) > 2 )
      ++nm;
  }
  return nm;
}

uint TriMesh::dropOrphanRidges(const Indices & killtags)
{
  if (faces.empty())
    return 0;

  // find singly connected edges
  Indices fdrop;
  const int ne = edges.size();
  for (int i=0; i<ne; ++i) {
    if (e2f.size(i) < 2) {
      marchOrphanFront( *(e2f.begin(i)), killtags, fdrop );
    }
  }

  //  // debug
  //  cout << "tags from which to peel triangles: " << endl;
  //  for (uint i=0; i<killtags.size(); ++i)
  //    cout << killtags[i] << " ";
  //  cout << endl;
  //  cout << fdrop.size() << " targets." << endl;


  // keep only triangles marked as external
  uint nkeep = faces.size() - fdrop.size();
  if (nkeep > 0) {
    TriFaceArray tmp;
    tmp.reserve(nkeep);
    const int nf = faces.size();
    for (int i=0; i<nf; ++i) {
      if (not binary_search(fdrop.begin(), fdrop.end(), uint(i))) {
        tmp.push_back(faces[i]);
      }
    }
    faces.swap(tmp);
    fixate(true);
  }

  return nkeep;
}

void TriMesh::marchOrphanFront(uint f, const Indices & killtags,
                               Indices & forphan) const
{
  if ( not binary_search(killtags.begin(),
                         killtags.end(),
                         uint(face(f).tag())) )
  {
    return;
  }

  if (not insert_once(forphan, f))
    return;

  ConnectMap::const_iterator itr, elast;
  elast = f2e.end(f);
  for (itr = f2e.begin(f); itr != elast; ++itr) {
    if (e2f.size(*itr) == 2) {
      ConnectMap::const_iterator itf, flast;
      flast = e2f.end(*itr);
      for (itf = e2f.begin(*itr); itf != flast; ++itf) {
        if (*itf != f)
          marchOrphanFront(*itf, killtags, forphan);
      }
    }
  }
}

XmlElement TriMesh::toXml(bool share) const
{
  const uint nv(vtx.size());
  const uint nf(faces.size());

  XmlElement xv("Vertices");
  xv["count"] = str(nv);
  xv.asBinary(3*nv, vtx.pointer(), share);

  XmlElement xf("Faces");
  xf["count"] = str(nf);
  Indices idx(3*nf), tags(nf);
  for (uint i=0; i<nf; ++i) {
    const TriFace & f(faces[i]);
    tags[i] = f.tag();
    const uint *vi(f.vertices());
    for (int k=0; k<3; ++k)
      idx[3*i+k] = vi[k];
  }

  // idx is a local temporary, must copy to xml object
  xf.asBinary(idx.size(), &idx[0], false);

  XmlElement xe("Triangulation");
  xe.append(std::move(xv));
  xe.append(std::move(xf));

  XmlElement xt("Tags");
  xt["count"] = str(tags.size());
  xt.asBinary(tags.size(), &tags[0], false);
  xe.append(std::move(xt));

  if (not tagnames.empty()) {
    XmlElement xtn("TagNameMap");
    TagMap::const_iterator itm;
    for (itm = tagnames.begin(); itm != tagnames.end(); ++itm) {
      XmlElement xti("TagName");
      xti["tag"] = str(itm->first);
      xti["name"] = itm->second;
      xtn.append(xti);
    }
    xe.append(std::move(xtn));
  }

  return xe;
}

void TriMesh::fromXml(const XmlElement & xe)
{
  if (xe.name() != "Triangulation")
    throw Error( "TriMesh::fromXml() - Incompatible xml representation: '"
                 + xe.name() + "', expected 'Triangulation'." );

  clear();
  Indices tags;
  XmlElement::const_iterator ite, its;
  for (ite = xe.begin(); ite != xe.end(); ++ite) {
    if (ite->name() == "Vertices") {
      uint n = ite->attr2int("count", 0);
      vtx.resize(n);
      ite->fetch(3*n, vtx.pointer());
    } else if (ite->name() == "Faces") {

      int n = Int( ite->attribute("count") );
      Indices idx(3*n);
      ite->fetch(3*n, &idx[0]);
      faces.resize(n);
      for (int i=0; i<n; ++i)
        faces[i].assign(this, idx[3*i], idx[3*i+1], idx[3*i+2]);

    } else if (ite->name() == "Tags") {
      uint n = Int( ite->attribute("count") );
      tags.resize(n);
      ite->fetch(n, &tags[0]);
    } else if (ite->name() == "TagNameMap") {
      for (its = ite->begin(); its != ite->end(); ++its) {
        if (its->name() == "TagName")
          tagnames[ Int(its->attribute("tag")) ] = its->attribute("name");
      }
    }
  }

  if (tags.size() == faces.size()) {
    const int n = faces.size();
    for (int i=0; i<n; ++i)
      faces[i].tag(tags[i]);
  }

  fixate(false);
}

void TriMesh::writeBin(std::ostream & os) const
{
  // write sizes to binary stream
  const uint nv(vtx.size());
  const uint nf(faces.size());
  os.write((const char*) &nv, sizeof(uint));
  os.write((const char*) &nf, sizeof(uint));

  // write vertex coordinates
  os.write((const char*) &vtx[0], 3*nv*sizeof(Real));

  // write vertex indices
  Indices tri(3*nf);
  for (uint i=0; i<nf; ++i)
    faces[i].getVertices(&tri[3*i]);

  os.write((const char*) &tri[0], 3*nf*sizeof(uint));
}

void TriMesh::readBin(std::istream & is)
{
  // read from binary stream
  uint nv, nf;
  is.read((char*) &nv, sizeof(uint));
  is.read((char*) &nf, sizeof(uint));

  clear();
  vtx.resize(nv);
  is.read((char *) &vtx[0], 3*nv*sizeof(double));

  faces.resize(nf);
  Indices tri(3*nf);
  is.read((char *) &tri[0], 3*nf*sizeof(uint));
  for (uint i=0; i<nf; ++i)
    faces[i] = TriFace(this, tri[3*i], tri[3*i+1], tri[3*i+2]);

  fixate(false);
}

// #ifdef HAVE_CGNS

void TriMesh::toCgns(CgnsFile & file) const
{
  const int nf = faces.size();
  CgnsZone zone = file.newZone("TriMesh", vtx.size(), 0);
  zone.writeNodes(vtx);

  std::map<int, std::vector<int> > tmap;
  for (int i=0; i<nf; ++i) {
    const int t = faces[i].tag();
    const uint *vi = faces[i].vertices();
    tmap[t].insert(tmap[t].end(), vi, vi+3);
  }

  CgnsIntMatrix ielm;
  CgnsSection section(file.index(), file.base(), zone.index(), 1);

  section.elementType(cgns::TRI_3);
  std::map<int, std::vector<int> >::const_iterator itm, last;
  last = tmap.end();
  for (itm = tmap.begin(); itm != last; ++itm) {
    int t = itm->first;
    const std::vector<int> & ivec(itm->second);
    ielm.resize(3, ivec.size()/3);
    memcpy(&ielm[0], &ivec[0], ivec.size()*sizeof(int));
    ielm += 1;
    section.rename("Tag "+str(t));
    section.writeElements(ielm);
  }
}

void TriMesh::fromCgns(CgnsZone & zone)
{
  clear();
  zone.readNodes(vtx);

  CgnsIntMatrix ielm;
  const int nsec = zone.nsections();
  for (int i=0; i<nsec; ++i) {
    CgnsSection s = zone.readSection(i+1);
    if (s.elementType() == cgns::TRI_3) {
      s.readElements(ielm);
      const int nf = ielm.ncols();
      for (int j=0; j<nf; ++j) {
        TriFace f(this, ielm(0,j)-1, ielm(1,j)-1, ielm(2,j)-1);
        f.tag(i);
        faces.push_back(f);
      }
    }
  }
  fixate(false);
}

void TriMesh::writeCgns(const std::string & fname) const
{
  CgnsFile file;
  file.wopen(fname);
  toCgns(file);
}

void TriMesh::readCgns(const std::string & fname)
{
  CgnsFile file;
  file.ropen(fname);
  CgnsZone zone = file.readZone(1);
  fromCgns(zone);
}

// #endif // HAVE_CGNS

Real TriMesh::megabytes() const
{
  Real mb;
  mb  = sizeof(TriEdgeArray) + sizeof(TriFaceArray);
  mb += faces.capacity() * sizeof(TriFace);
  mb += edges.capacity() * sizeof(TriEdge);
  mb += 2*sizeof(PointList<3>);
  mb += (vtx.capacity() + nrm.capacity())*sizeof(Vct3);
  mb *= 1e-6;
  mb += v2f.megabytes();
  mb += v2e.megabytes();
  mb += e2f.megabytes();
  mb += f2e.megabytes();
  return mb;
}

bool TriMesh::enclosedTriangles(const Indices & vloop, Indices & t) const
{
  if (vloop.empty()) {
    cerr << "Empty vertex loop" << endl;
    return false;
  }

  if (vloop.front() != vloop.back()) {
    cerr << "Vertex loop not closed." << endl;
    return false;
  }

  // identify edge loop and center of loop
  Vct3 ctr;
  const int nv(vloop.size());
  Indices eloop(nv-1);
  Real elen, lsum(0.0);
  uint e;
  for (int i=0; i<nv-1; ++i) {
    e = tsearchEdge(vloop[i], vloop[i+1]);
    if (e == NotFound) {
      // cerr << "Edge " << vloop[i] << " to " << vloop[i+1]
      //      << " not found" << endl;
      return false;
    }
    eloop[i] = e;

    const Vct3 & p1( vertex(vloop[i]) );
    const Vct3 & p2( vertex(vloop[i+1]) );
    elen = norm(p1 - p2);
    lsum += elen;
    ctr += 0.5*elen*(p1 + p2);
  }
  ctr /= lsum;
  sort_unique(eloop);

  // identify first triangle which is inside loop
  uint f(NotFound);
  e = eloop.front();
  Vct3 ectr = 0.5*( vertex(edge(e).source())
                    + vertex(edge(e).target()) );
  nb_face_iterator itf;
  for (itf = e2fBegin(e); itf != e2fEnd(e); ++itf) {
    Vct3 fc = itf->center();
    if (dot(fc-ectr, ctr-ectr) > 0.0) {
      f = itf.index();
      break;
    }
  }

  if (f == NotFound) {
    cerr << "Could not identify first triangle in loop." << endl;
    return false;
  }

  // start with the first triangle identified above, put into queue
  // for each triangle in queue
  // - check each edge which is not in loop
  // - add triangles across edge to queue, if not tagged
  // - pop from queue
  // - tag triangle
  Indices ftag, queue;
  queue.push_back(f);
  nb_edge_iterator ite, elast;
  while (not queue.empty()) {
    f = queue.back();
    queue.pop_back();
    for (ite = f2eBegin(f); ite != f2eEnd(f); ++ite) {
      e = ite.index();
      if (binary_search(eloop.begin(), eloop.end(), e))
        continue;
      for (itf = e2fBegin(e); itf != e2fEnd(e); ++itf) {
        uint fnext = itf.index();
        if (not binary_search(ftag.begin(), ftag.end(), fnext))
          queue.push_back(fnext);
      }
    }
    insert_once(ftag, f);
  }

  // return internal triangles
  ftag.swap(t);
  return true;
}

void TriMesh::icosahedron(const Vct3 & ctr, Real r)
{
  clear();
  const Real c = 0.4*sqrt(5.);

  // compute vertices
  Real z1 = 0.5*r*c;
  Real r1 = r*c;
  Real sphi, cphi;
  vtx.resize(12);
  vtx[0] = ctr + vct(0.0, 0.0, r);
  for (int i=0; i<5; ++i) {
    sincosine(0.4*i*PI, sphi, cphi);
    vtx[1+i] = ctr + vct(r1*sphi, r1*cphi, z1);
  }
  for (int i=0; i<5; ++i) {
    sincosine(0.2*PI + 0.4*i*PI, sphi, cphi);
    vtx[6+i] = ctr + vct(r1*sphi, r1*cphi, -z1);
  }
  vtx[11] = ctr + vct(0.0, 0.0, -r);

  // construct triangles
  faces.clear();

  // top cap
  addFace(0, 1, 2);
  addFace(0, 2, 3);
  addFace(0, 3, 4);
  addFace(0, 4, 5);
  addFace(0, 5, 1);

  // central ring
  addFace(1, 6, 2);
  addFace(2, 6, 7);
  addFace(7, 3, 2);
  addFace(3, 7, 8);
  addFace(8, 4, 3);
  addFace(4, 8, 9);
  addFace(4, 9, 5);
  addFace(5, 9, 10);
  addFace(1, 5, 10);
  addFace(1, 10, 6);

  // bottom cap
  addFace(11, 7, 6);
  addFace(11, 8, 7);
  addFace(11, 9, 8);
  addFace(11, 10, 9);
  addFace(11, 6, 10);

  // hmm. managed to get all directions wrong.
  reverse();

  // connectivity
  fixate();
}

void TriMesh::tetrahedron(const Vct3 & ctr, Real r)
{
  clear();

  vtx.resize(4);
  Real a = r * sqrt(8./3.);
  Real cphi = 0.577350269189626;
  Real sphi = 0.816496580927726;
  Real d = a*cphi;
  Real zb = r - a*sphi;
  vtx[0] = ctr + vct(0.0, 0.0, r);
  vtx[1] = ctr + vct(d, 0.0, zb);
  vtx[2] = ctr + vct(-0.5*d,  0.5*d*sqrt(3.), zb);
  vtx[3] = ctr + vct(-0.5*d, -0.5*d*sqrt(3.), zb);

  addFace(0,2,1);
  addFace(0,1,3);
  addFace(0,3,2);
  addFace(1,2,3);

  fixate();
}

void TriMesh::quadSplit(int npass)
{
  uint vo[3], vn[3];
  for (int ip=0; ip<npass; ++ip) {

    // generate new vertices
    const int off(nvertices());
    const int ne(nedges());
    for (int i=0; i<ne; ++i) {
      uint s = edge(i).source();
      uint t = edge(i).target();
      addVertex( 0.5*(vtx[s] + vtx[t]) );
    }

    const int nf(nfaces());
    for (int i=0; i<nf; ++i) {

      // copy old vertex indices
      TriFace & f(face(i));
      f.getVertices( vo );

      // locate new vertices
      const uint *ef = f2e.first(i);
      vn[0] = off + ef[0];
      vn[1] = off + ef[1];
      vn[2] = off + ef[2];

      // change original face and add three new triangles
      f.assign(this, vo[0], vn[0], vn[2]);
      addFace(vo[1], vn[1], vn[0]);
      addFace(vo[2], vn[2], vn[1]);
      addFace(vn[0], vn[1], vn[2]);
    }
    fixate();
  }
}

void TriMesh::sphere(const Vct3 & ctr, Real r, int nrefp)
{
  icosahedron( ctr, r );
  quadSplit( nrefp );

  // project vertices onto sphere
  Vct3 rad;
  const int nv(nvertices());
  for (int i=0; i<nv; ++i) {
    rad = vtx[i] - ctr;
    rad *= r/norm(rad);
    vtx[i] = ctr + rad;
  }
}

void TriMesh::tsphere(const Vct3 & ctr, Real r, int nrefp)
{
  tetrahedron( ctr, r );
  quadSplit(1);
  dropTriStars();

  // project vertices onto sphere
  Vct3 rad;
  int nv = nvertices();
  for (int i=0; i<nv; ++i) {
    rad = vtx[i] - ctr;
    rad *= r/norm(rad);
    vtx[i] = ctr + rad;
  }

  for (int j=1; j<nrefp; ++j) {
    quadSplit(1);
    nv = nvertices();
    for (int i=0; i<nv; ++i) {
      rad = vtx[i] - ctr;
      rad *= r/norm(rad);
      vtx[i] = ctr + rad;
    }
  }
}

uint TriMesh::dropStretchedTriangles(Real maxstretch, Real maxphi)
{
  // keep track of modified faces and edges
  Indices vmod;
  int nmod(0);
  Indices fmod, emod;
  const int ne(edges.size());
  const Real mincphi = cos(maxphi);

  nb_face_iterator itf, flast;
  for (int i=0; i<ne; ++i) {

    const TriEdge & ei(edge(i));
    const uint s = ei.source();
    const uint t = ei.target();

    if ( binary_search(vmod.begin(), vmod.end(), s) or
         binary_search(vmod.begin(), vmod.end(), t) )
      continue;

    // don't touch edges which sit across large curvature
    if (cosarg(normal(s),normal(t)) < mincphi) {
      continue;
    }

    // never collapse boundary edges
    if (e2f.size(i) < 2)
      continue;

    // check stretch condition
    Vct3 midp = 0.5*(vertex(s) + vertex(t));
    Real elen = norm(vertex(s) - vertex(t));
    Real strmax(0.0), strmin(huge);
    flast = e2fEnd(i);
    for (itf = e2fBegin(i); itf != flast; ++itf) {
      uint vop = itf->opposed(ei);
      if (vop == NotFound)
        continue;
      Real rlen = norm(midp - vertex(vop)) / elen;
      strmax = std::max(strmax, rlen);
      strmin = std::min(strmin, rlen);
    }

    // check for slivers or needles
    if (strmax > maxstretch) {

      // eliminate needles by merging vertices
      // change vertex position and connect neighbors of t to s
      insert_once(vmod, s);
      insert_once(vmod, t);
      vtx[s] = vtx[t] = midp;
      nrm[s] = nrm[t] = 0.5*(nrm[s] + nrm[t]);
      ++nmod;

    } else if ((maxstretch*strmin) < 1.0) {

      // eliminate slivers by edge flip, whenever possible
      // this may (intentionally) generate needles
      if (flipEdge(i, mincphi, vmod))
        ++nmod;
    }
  }

  // update connectivity data
  cleanup(gmepsilon);

  return nmod;
}

bool TriMesh::flipEdge(uint ei, Real mincphi, Indices & vmod)
{
  // collect surrounding edges
  if (e2f.size(ei) != 2)
    return false;

  const uint *nbf = e2f.first(ei);
  if (nbf[0] == NotFound or nbf[1] == NotFound)
    return false;

  uint nbi(0), opv[2]; // nbe[6];
  for (int i=0; i<2; ++i) {
    const uint *ip = f2e.first(nbf[i]);
    opv[i] = face(nbf[i]).opposed(edge(ei));
    for (int k=0; k<3; ++k) {
      if (ip[k] != ei) {
        // nbe[nbi] = ip[k];
        ++nbi;
      }
    }
  }
  if (nbi != 4)
    return false;

  // abort if one of the opposing nodes is already touched
  if ( binary_search(vmod.begin(), vmod.end(), opv[0]) or
       binary_search(vmod.begin(), vmod.end(), opv[1]) ) {
    return false;
  }

  // check if the flipped triangle pair would have better properties
  uint s = edge(ei).source();
  uint t = edge(ei).target();
  Real elen1 = norm(vertex(s) - vertex(t));
  Vct3 mp1 = 0.5*(vertex(s) + vertex(t));
  Real s11 = norm(mp1 - vertex(opv[0])) / elen1;
  Real s12 = norm(mp1 - vertex(opv[1])) / elen1;
  if (s11 > s12)
    std::swap(s11,s12);

  Real elen2 = norm(vertex(opv[0]) - vertex(opv[1]));
  Vct3 mp2 = 0.5*(vertex(opv[0]) + vertex(opv[1]));
  Real s21 = norm(mp2 - vertex(s)) / elen2;
  Real s22 = norm(mp2 - vertex(t)) / elen2;
  if (s21 > s22)
    std::swap(s21,s22);

  if (s21 < s11)
    return false;

  // check if the flip would violate the fold angle condition
  Real ocsphi = cosarg(normal(s), normal(t));
  Real ncsphi = cosarg(normal(opv[0]), normal(opv[1]));
  if (ncsphi < ocsphi and ncsphi < mincphi) {
    // cout << "fold angle too large: " << deg(acos(ncsphi)) << endl;
    return false;
  }

  //   // check if the flipped edge would cross any of the surrounding edges
  //   Line<3> oline(vertex(opv[0]), vertex(opv[1]));
  //   for (int k=0; k<4; ++k) {
  //     const TriEdge & se(edges[nbe[k]]);
  //     Line<3> sline(vertex(se.source()), vertex(se.target()));
  //     LnIts<3> its = oline.intersection(sline);
  //     if (its.internal(-1e-3))
  //       return false;
  //   }

  // finally, if all this is ok, flip the edge and mark the 4
  // surrounding vertices as modified
  Vct3 nref;
  TriFace & f0(face(nbf[0]));
  nref = f0.normal();
  f0.assign(this, s, opv[0], opv[1]);
  if ( dot(nref, f0.normal()) < 0 )
    f0.reverse();

  TriFace & f1(face(nbf[1]));
  nref = f1.normal();
  f1.assign(this, t, opv[0], opv[1]);
  if ( dot(nref, f1.normal()) < 0 )
    f1.reverse();

  insert_once(vmod, s);
  insert_once(vmod, t);
  insert_once(vmod, opv[0]);
  insert_once(vmod, opv[1]);

  return true;
}

uint TriMesh::dropTriStars()
{
  Indices fkill;
  const uint *iptr;
  const int nv(nvertices());
  nb_edge_iterator ite, elast;
  for (int i=0; i<nv; ++i) {

    if (v2f.size(i) != 3)
      continue;
    if (v2e.size(i) != 3)
      continue;

    // retrieve vertices of the surrounding triangle
    uint vxt[3];
    iptr = v2e.first(i);
    for (int k=0; k<3; ++k)
      vxt[k] = edge(iptr[k]).opposed(i);

    // reassign external triangle to No 1
    // kill No 2 and 3 of the internal triangles
    // compare new with previous normal direction
    // and reverse triangle if necessary
    iptr = v2f.first(i);
    Vct3 nsave = face(iptr[0]).normal();
    face(iptr[0]).assign(this, vxt[0], vxt[1], vxt[2]);
    if ( dot(nsave, face(iptr[0]).normal()) < 0 )
      face(iptr[0]).reverse();
    insert_once(fkill, iptr[1]);
    insert_once(fkill, iptr[2]);
  }

  const int nf(faces.size());
  TriFaceArray tmp;
  for (int i=0; i<nf; ++i) {
    if (not binary_search(fkill.begin(), fkill.end(), uint(i)))
      tmp.push_back(faces[i]);
  }
  faces.swap(tmp);

  fixate(true);

  return fkill.size()/2;
}

bool TriMesh::mergeAndDrop(uint itx, Real thrstart, Real thrend)
{
  Real threshold = 0.5*thrstart;
  uint nmerged;
  bool manif = false;
  while (not manif) {

    // increase merge limit until we actually did something
    nmerged = 0;
    while (nmerged == 0 and threshold <= thrend) {
      threshold *= 2.0;
      nmerged = cleanup(threshold);
    };

    // could not merge with acceptable threshold
    if (nmerged == 0)
      return false;

    // drop triangles
    dropInternalTriangles( itx );

    // count non-manifold edges
    manif = true;
    const uint ne = edges.size();
    for (uint i=0; i<ne; ++i) {
      if (e2f.size(i) > 2) {
        manif = false;
        break;
      }
    }

    if (manif)
      return true;
  }

  return false;
}

void TriMesh::joinSingleEdges(Real threshold)
{
  // identify vertices on singly connected edges
  Indices sev;
  const uint ne = edges.size();
  for (uint i=0; i<ne; ++i) {
    if (e2f.size(i) == 1) {
      insert_once(sev, edges[i].source());
      insert_once(sev, edges[i].target());
    }
  }
  const uint nsv = sev.size();
  PointList<3> sep(nsv);
  for (uint i=0; i<nsv; ++i)
    sep[i] = vtx[sev[i]];

  // prepare replacement table
  const uint nv = vtx.size();
  Indices repl(nv);
  for (uint i=0; i<nv; ++i)
    repl[i] = i;

  // try to merge single-edge nodes only
  Indices idt;
  uint ndupl(0);
  BSearchTree btree(sep);
  for (uint i=0; i<nsv; ++i) {
    idt.clear();
    btree.find(sep[i], threshold, idt);
    const uint ndf = idt.size();
    for (uint j=0; j<ndf; ++j) {
      uint idup = sev[idt[j]];
      if (idup > sev[i]) {
        repl[idup] = sev[i];
        vtx[idup] = sep[i];
        ++ndupl;
      }
    }
  }

  if (ndupl > 0) {
    const uint nf(faces.size());
    for (uint i=0; i<nf; ++i)
      faces[i].itranslate(repl);

    // recompute connectivity, will remove invalid faces
    fixate(true);
  }
}

std::string TriMesh::tagName(int t) const
{
  TagMap::const_iterator itm;
  itm = tagnames.find(t);
  if (itm == tagnames.end())
    return string("Component ")+str(t);
  else
    return itm->second;
}

void TriMesh::tagName(int t, const std::string & s)
{
  tagnames[t] = s;
}

void TriMesh::submesh(int t, TriMesh & sub) const
{
  sub.clear();
  sub.vtx = vtx;

  const int nf = nfaces();
  for (int i=0; i<nf; ++i) {
    if (face(i).tag() == t)
      sub.addFace(face(i).vertices());
  }

  sub.fixate(true);
}

void TriMesh::writeAsciiSTL(const std::string & fname, const std::string & sname) const
{
  Indices tags;
  allTags(tags);
  const int ntags = tags.size();

  ofstream os(asPath(fname).c_str());
  os << std::scientific;
  Vct3 fn;
  const int nf = nfaces();
  for (int j=0; j<ntags; ++j) {
    int jtag = tags[j];
    TagMap::const_iterator itm;
    itm = tagnames.find(jtag);
    if (itm != tagnames.end())
      os << "solid " << itm->second << endl;
    else if (not sname.empty() and ntags < 2)
      os << "solid " << sname << endl;
    else
      os << "solid" << endl;
    for (int i=0; i<nf; ++i) {
      const TriFace & f(face(i));
      if (f.tag() != jtag)
        continue;
      const uint *vi = f.vertices();
      f.normal(fn);
      const Vct3 & p1( vertex(vi[0]) );
      const Vct3 & p2( vertex(vi[1]) );
      const Vct3 & p3( vertex(vi[2]) );
      os << "facet normal " << fn << endl;
      os << "  outer loop" << endl;
      os << "    vertex " << p1 << endl;
      os << "    vertex " << p2 << endl;
      os << "    vertex " << p3 << endl;
      os << "  endloop" << endl;
      os << "endfacet" << endl;
    }
    os << "endsolid" << endl;
  }
}

void TriMesh::writeBinarySTL(const std::string & fname) const
{
  if (is_bigendian())
    throw Error("TriMesh: Binary STL output not yet supported "
                "on big endian machines.");

  const char header[80] = "STL little endian binary";

  ofstream os;
  os.open(asPath(fname).c_str(), std::ios::binary);
  os.write(header, sizeof(header));

  float fcrd[12];
  char buf[12*sizeof(float) + 2];
  memset(buf, 0, sizeof(buf));

  Vct3 fn;
  const int nf = nfaces();
  uint32_t unf = (uint32_t) nf;
  os.write((const char *) &unf, 4);

  for (int i=0; i<nf; ++i) {
    const TriFace & f(face(i));
    const uint *vi = f.vertices();
    f.normal(fn);
    for (int k=0; k<3; ++k)
      fcrd[k] = (float) fn[k];
    for (int j=0; j<3; ++j)
      for (int k=0; k<3; ++k)
        fcrd[3+3*j+k] = (float) vtx[vi[j]][k];
    memcpy(buf, fcrd, 12*sizeof(float));
    os.write(buf, sizeof(buf));
  }
}

void TriMesh::readSTL(const std::string & fname)
{
  ifstream in(asPath(fname).c_str());
  string word;
  in >> word;
  if (word == "solid") {
    readAsciiSTL(fname);

    // some binary STL files may start with 'solid' as well, so,
    // if the above did not work, try as binary
    if (nfaces() == 0)
      readBinarySTL(fname);

  } else {
    readBinarySTL(fname);
  }
}

void TriMesh::readAsciiSTL(const std::string & fname)
{
  ifstream in(asPath(fname).c_str());

  clear();
  string line;
  Vct3 fv, fn;
  const char *pos;
  char *tail;
  uint k(0), vi[3], iline(0);

  int solid = 0;
  const char bsep[] = "solid";
  while (getline(in, line)) {

    ++iline;

    pos = strstr(line.c_str(), bsep);
    if (pos != 0) {
      ++solid;
      pos += 5; // length of 'solid'
      string solidname = strip(string(pos));
      if (solidname.empty())
        solidname = string("Solid ") + str(solid);
      tagnames[solid] = solidname;
    }

    if (k == 0) {
      pos = strstr(line.c_str(), "normal");
      if (pos != 0) {
        pos += 6; // length of 'normal'
        for (int j=0; j<3; ++j) {
          fn[j] = genua_strtod(pos, &tail);
          if (tail == pos)
            throw Error("TriMesh: Syntax error in "
                        "line "+str(iline)+" of ASCII STL file"+fname);
          pos = tail;
        }
      }
    }

    pos = strstr(line.c_str(), "vertex");
    if (pos == 0)
      continue;

    pos += 6; // length of 'vertex'
    for (int j=0; j<3; ++j) {
      fv[j] = genua_strtod(pos, &tail);
      if (tail == pos)
        throw Error("TriMesh: Syntax error in "
                    "line "+str(iline)+" of ASCII STL file"+fname);
      pos = tail;
      vi[k] = addVertex(fv);
    }
    ++k;

    if (k == 3) {
      uint jf = addFace(vi[0], vi[1], vi[2]);
      k = 0;

      // check normal
      if (sq(fn) > gmepsilon) {
        TriFace & f(face(jf));
        if (dot(fn, f.normal()) < 0.0)
          f.reverse();
        f.tag( solid );
      }
    }
  }
}

void TriMesh::readBinarySTL(const std::string & fname)
{
  if (is_bigendian())
    throw Error("TriMesh: Binary STL output not yet supported "
                "on big endian machines.");

  char header[80];
  memset(header, '\0', sizeof(header));

  // read header (currently not used)
  ifstream in;
  in.open(asPath(fname).c_str(), std::ios::binary);
  if (not in)
    throw Error("TriMesh:: Cannot open binary STL file: "+fname);

  in.read(header, sizeof(header));
  if (not in)
    throw Error("TriMesh:: Cannot read STL header in binary STL file: "+fname);

  // read number of triangles
  uint32_t unf = 0;
  in.read((char *) &unf, 4);

  // be careful when allocating
  try {
    vtx.resize(3*unf);
    faces.resize(unf);
  } catch (std::bad_alloc &) {
    throw Error("TriMesh: Not a binary STL file: "+fname);
  }

  float fcrd[12];
  char buf[12*sizeof(float) + 2];
  memset(buf, 0, sizeof(buf));

  const int nf(unf);
  for (int i=0; i<nf; ++i) {
    if (not in.read(buf, sizeof(buf))) {
      std::stringstream ss;
      ss << "TriMesh: Encountered premature end of STL file: " << fname << endl;
      ss << " Expected " << nf << " faces, failed to read face " << i << endl;
      throw Error(ss.str());
    }
    memcpy(fcrd, buf, 12*sizeof(float));
    for (int j=0; j<3; ++j)
      for (int k=0; k<3; ++k)
        vtx[3*i+j][k] = (double) fcrd[3+3*j+k];

    face(i).assign(this, 3*i, 3*i+1, 3*i+2);
  }
}

void TriMesh::boundaries(Indices & bde) const
{
  bde.clear();
  const int ne = nedges();
  for (int i=0; i<ne; ++i) {
    if (edegree(i) != 2) {
      bde.push_back(i);
    }
  }
}

void TriMesh::splitRidges(Indices & ridges, Real cosphi)
{
  // precompute all face normals
  const int nf = nfaces();
  PointList<3> fn( nf );
#pragma omp parallel for
  for (int i=0; i<nf; ++i)
    face(i).normal( fn[i] );

  ridges.clear();
  const int ne = nedges();
#pragma omp parallel for
  for (int i=0; i<ne; ++i) {
    if ( edegree(i) != 2 )
      continue;
    const uint *nbf = firstFaceIndex(i);
    if (cosarg( fn[nbf[0]], fn[nbf[1]] ) > cosphi)
      continue;
#pragma omp critical
    ridges.push_back( i );
  }

  // collect vertices along ridges
  std::set<uint> vrids;
  const int nrid = ridges.size();
  for (int i=0; i<nrid; ++i) {
    const TriEdge & e( edge(ridges[i]) );
    vrids.insert( e.source() );
    vrids.insert( e.target() );
  }
  Indices vrid(vrids.begin(), vrids.end());

  // duplicate ridge vertices
  uint offset = vtx.size();
  const int nvr = vrid.size();
  for (int i=0; i<nvr; ++i)
    vtx.push_back( vtx[vrid[i]] );

  // reconnect faces along ridge edges
  for (int i=0; i<nrid; ++i) {
    assert( edegree(ridges[i]) == 2 );
    const uint *nbf = firstFaceIndex(i);
    const uint *vi = face( nbf[1] ).vertices();
    uint vk[3];
    for (int k=0; k<3; ++k) {
      uint pos = sorted_index(vrid, vi[k]);
      if (pos != NotFound)
        vk[k] = offset + pos;
      else
        vk[k] = vi[k];
    }
    face(nbf[1]).assign(this, vk[0], vk[1], vk[2]);
  }

  // convert ridges from edge indices to vertex indices
  Indices lns( 2*nrid );
  for (int i=0; i<nrid; ++i) {
    const TriEdge & e( edge(ridges[i]) );
    lns[2*i+0] = e.source();
    lns[2*i+1] = e.target();
  }
  ridges.swap(lns);

  if (nrid > 0)
    fixate();
}

bool TriMesh::findInternalPoints(PointList<3> & holes) const
{
  // typedef std::pair<std::set<uint>::const_iterator, bool> InsertResult;

  const int nf = nfaces();
  FlagSet reached(nf, false);
  // std::set<uint> reached;
  Indices tag;
  while (reached.nset() != size_t(nf)) {

    Vct3 hole;
    tag.clear();
    for (int i=0; i<nf; ++i) {
      if (reached[i])
        continue;
      if (triInternalPoint(i, hole)) {
        holes.push_back(hole);
        tag.push_back(i);
        break;
      }
    }

    // if no suitable continuation was found, exit with failure
    if (tag.empty())
      return false;

    // starting from the newly identified triangle, walk the topological
    // neighborhood and mark faces which can be reached from there
    while (not tag.empty()) {
      uint fix = tag.back();
      tag.pop_back();
      const uint *v = face(fix).vertices();
      for (int k=0; k<3; ++k) {
        TriMesh::nb_face_iterator itf, last = v2fEnd(v[k]);
        for (itf = v2fBegin(v[k]); itf != last; ++itf) {
          size_t idx = itf.index();
          if ( reached.set(idx) ) // if not reached before but now,
            tag.push_back(idx);
        }
      }
    } // tag queue not empty

  } // repeat while not all reached

  return true;
}

bool TriMesh::triInternalPoint(uint fix, Vct3 & hole) const
{
  const Real csamin = 0.866;
  const uint *v = face(fix).vertices();
  Vct3 fn = face(fix).normal();
  for (uint k=0; k<3; ++k) {
    TriMesh::nb_face_iterator itf, last = v2fEnd(v[k]);
    for (itf = v2fBegin(v[k]); itf != last; ++itf) {
      Real csa = cosarg(fn, itf->normal());
      if (csa < csamin)
        return false;
    }
  }

  Real nfm = normalize(fn);
  Real dst = 1e-3 * sqrt(nfm);
  hole = face(fix).center() - fn * dst;

  return true;
}
