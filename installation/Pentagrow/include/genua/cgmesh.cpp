
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
 
#include "defines.h"
#include "cgmesh.h"
#include "xcept.h"
#include "trimesh.h"
#include "ndpointtree.h"
#include "basictriangle.h"
#include "basicedge.h"
#include <set>
#include <deque>

#ifdef _MSC_VER
#pragma warning( disable : 4100 )
#endif

using namespace std;

// ------------------------ local scope

static inline bool parse_vertex(const char *s, char **tail, Vct3f & p)
{
  p[0] = (float) genua_strtod(s, tail);
  if (*tail != s)
    s = *tail;
  else
    return false;
  p[1] = (float) genua_strtod(s, tail);
  if (*tail != s)
    s = *tail;
  else
    return false;
  p[2] = (float) genua_strtod(s, tail);
  if (*tail != s)
    s = *tail;
  else
    return false;

  if (**tail == ',')
    ++(*tail);

  return true;
}

static inline void parse_indices(const string & s, Indices & idx)
{
  const char *pos = s.c_str();
  char *tail;
  uint v;
  do {
    
    v = genua_strtol(pos, &tail, 10);
    if (pos == tail)
      break;
    idx.push_back(v);
    pos = tail;
    
  } while (pos != 0 and *pos != 0);
}

static inline void ptrafo(const SMatrix<4,4,float> & t, 
                          PointList<3,float> & pts)
{
  Vct4f pw;
  float iw;
  const int n = pts.size();
  for (int i=0; i<n; ++i) {
    for (int k=0; k<3; ++k)
      pw[k] = pts[i][k];
    pw[3] = 1.0f;
    pw = t*pw;
    iw = 1.0f / pw[3];
    for (int k=0; k<3; ++k)
      pts[i][k] = iw*pw[k];
  }
}

static inline void ntrafo(const SMatrix<4,4,float> & t, 
                          PointList<3,float> & pts)
{
  // version for normal vector transformation
  Mtx33f t3;
  for (int j=0; j<3; ++j)
    for (int i=0; i<3; ++i)
      t3(i,j) = t(i,j);
  
  const int n = pts.size();
  for (int i=0; i<n; ++i) {
    pts[i] = t3 * pts[i];
    normalize(pts[i]);
  }
}

// ------------------------ CgMesh

// color which indicates that surface is to be excluded/included
Color CgMesh::s_sigcolor;

// signal color excluded or included?
CgMesh::ColorImportMode CgMesh::s_sigcolormode = CgMesh::IgnoreColor;

uint CgMesh::ntriangles() const
{
  uint n = m_triangles.size() / 3;
  if (m_tristrips.nstrip() > 0)
    n += m_tristrips.ntriangles();
  if (m_trifans.nstrip() > 0)
    n += m_trifans.ntriangles();
  return n;
}

uint CgMesh::nlines() const
{
  uint n = m_lines.size() / 2;
  if (m_lnstrips.nstrip() > 0)
    n += m_lnstrips.ntriangles();

  return n;
}

float CgMesh::megabytes() const
{
  float bytes = sizeof(CgMesh);
  bytes += m_vtx.capacity() * sizeof(Vct3f);
  bytes += m_nrm.capacity() * sizeof(Vct3f);
  bytes += m_lvx.capacity() * sizeof(Vct3f);
  bytes += m_triangles.size() * sizeof(Indices::value_type);
  bytes += m_lines.size() * sizeof(Indices::value_type);
  return 1e-6f*bytes + m_tristrips.megabytes()
      + m_trifans.megabytes() + m_lnstrips.megabytes();
}

void CgMesh::fitColorBuffer(const Color & dfc)
{
  m_vtxcol.resize( m_vtx.size() );
  fill(m_vtxcol.begin(), m_vtxcol.end(), dfc );
}

void CgMesh::merge(const CgMesh & msub, const Mtx44f & tsub)
{
  const int voff = m_vtx.size();
  const int loff = m_lvx.size();

  // extend normal array if necessary
  if (m_nrm.size() != m_vtx.size()) {
    size_t nn = std::max( m_vtx.size(), m_nrm.size() );
    PointList<3,float> tmp(nn);
    if (not m_nrm.empty())
      memcpy( tmp.pointer(), m_nrm.pointer(), m_nrm.size()*3*sizeof(float) );
    tmp.swap(m_nrm);
  }
  
  m_vtx.insert(m_vtx.end(), msub.m_vtx.begin(), msub.m_vtx.end());
  m_nrm.insert(m_nrm.end(), msub.m_nrm.begin(), msub.m_nrm.end());
  m_lvx.insert(m_lvx.end(), msub.m_lvx.begin(), msub.m_lvx.end());

  // extend normal array if necessary
  if (m_nrm.size() != m_vtx.size()) {
    size_t nn = std::max( m_vtx.size(), m_nrm.size() );
    PointList<3,float> tmp(nn);
    if (not m_nrm.empty())
      memcpy( tmp.pointer(), m_nrm.pointer(), m_nrm.size()*3*sizeof(float) );
    tmp.swap(m_nrm);
  }

  // transform vertices
  if (tsub != Mtx44f::identity()) {
    const int nv = m_vtx.size();
    assert(m_nrm.size() == uint(nv));
    for (int i=voff; i<nv; ++i) {
      Vct3f tp = m_vtx[i];
      Vct3f tn = m_nrm[i];
      for (int k=0; k<3; ++k) {
        m_vtx[i][k] = tsub(k,0)*tp[0] + tsub(k,1)*tp[1]
            + tsub(k,2)*tp[2] + tsub(k,3);
        m_nrm[i][k] = tsub(k,0)*tn[0] + tsub(k,1)*tn[1] + tsub(k,2)*tn[2];
      }
    }
    const int nlv = m_lvx.size();
    for (int i=loff; i<nlv; ++i) {
      Vct3f tp = m_lvx[i];
      for (int k=0; k<3; ++k)
        m_lvx[i][k] = tsub(k,0)*tp[0] + tsub(k,1)*tp[1]
            + tsub(k,2)*tp[2] + tsub(k,3);
    }
  }
  
  // merge triangle strips and fans
  m_tristrips.merge( msub.m_tristrips, voff );
  m_trifans.merge( msub.m_trifans, voff );
  m_lnstrips.merge( msub.m_lnstrips, loff );
  
  // translate indices of plain triangles
  const int nt = msub.m_triangles.size();
  const int toff = m_triangles.size();
  m_triangles.resize(toff + nt);
  for (int i=0; i<nt; ++i)
    m_triangles[toff+i] = msub.m_triangles[i] + voff;

  // translate line indices
  const int nl = msub.m_lines.size();
  const int lnoff = m_lines.size();
  m_lines.resize(lnoff + nl);
  for (int i=0; i<nl; ++i)
    m_lines[lnoff+i] = msub.m_lines[i] + voff;
}

void CgMesh::mergeTriangles(size_t nm,
                            const PointList3f mv[], const Indices mt[])
{
  m_nrm.clear();

  const uint voff = m_vtx.size();
  const uint toff = m_triangles.size();

  intptr_t ntv(0), niv(0);
  for (size_t j=0; j<nm; ++j) {
    ntv += mt[j].size();
    niv += mv[j].size();
  }

  m_vtx.reserve(voff + niv);
  m_triangles.resize(toff + ntv);
  uint triOffset = toff;
  uint vtxOffset = voff;
  for (size_t j=0; j<nm; ++j) {
    vtxOffset = m_vtx.size();
    m_vtx.insert(m_vtx.end(), mv[j].begin(), mv[j].end());
    ntv = mt[j].size();
    uint *tmesh = &m_triangles[triOffset];
    const uint *tbase = &(mt[j][0]);
    // TODO: vectorize
    for (intptr_t i=0; i<ntv; ++i)
      tmesh[i] = tbase[i] + vtxOffset;
    triOffset += ntv;
  }
}

void CgMesh::mergeTriangles(const CgMesh &msub)
{
  const PointList3f &mv = msub.vertices();
  const Indices &mt = msub.m_triangles;
  mergeTriangles(1, &mv, &mt);
}

void CgMesh::appendCircle(const Vct3f & ctr, const Vct3f & cn, 
                          float r, int nt)
{
  Vct3f xax, yax;
  float nx = fabs(cn[0]);
  float ny = fabs(cn[1]);
  float nz = fabs(cn[2]);
  if (nx < ny and nx < nz)
    xax[0] = 1.0f;
  else if (ny < nx and ny < nz)
    xax[1] = 1.0f;
  else
    xax[2] = 1.0f;
  xax -= dot(xax,cn) * cn;
  yax = cross(cn, xax);
  xax *= r/norm(xax);
  yax *= r/norm(yax);
  
  Indices tfan(nt+1);
  
  Vct3f pt;
  tfan[0] = m_vtx.size();
  m_vtx.push_back(ctr);
  m_nrm.push_back(cn);
  float sphi, cphi, dphi;
  dphi = static_cast<float>( 2*M_PI / (nt-1) );
  for (int i=0; i<nt; ++i) {
    sincosine(i*dphi, sphi, cphi);
    pt = ctr + cphi*xax + sphi*yax;
    tfan[1+i] = m_vtx.size();
    m_vtx.push_back(pt);
    m_nrm.push_back(cn);
  }
  m_trifans.append(tfan.begin(), tfan.end());
}

void CgMesh::appendCross(const Vct3f & ctr, float s)
{
  Vct3f p1(ctr), p2(ctr);
  for (int k=0; k<3; ++k) {
    p1[k] -= s;
    p2[k] += s;
    appendLine(p1, p2);
    p1[k] = p2[k] = ctr[k];
  }
}

void CgMesh::appendLine(const Vct3f & p1, const Vct3f & p2)
{
  //  lvx.push_back(p1);
  //  lvx.push_back(p2);
  //  lnstrips.append(lvx.size());

  uint a = m_vtx.size();
  m_vtx.push_back(p1);
  m_vtx.push_back(p2);
  m_lines.push_back(a);
  m_lines.push_back(a+1);
}

void CgMesh::appendLine(const PointList<3,float> & pts)
{
  // append polyline
  const uint voff = m_vtx.size();
  const uint loff = m_lines.size();
  m_vtx.insert(m_vtx.end(), pts.begin(), pts.end());

  const uint np = pts.size();
  const uint nl = (np-1);
  m_lines.resize(loff + 2*nl);
  for (uint i=0; i<nl; ++i) {
    m_lines[loff + 2*i+0] = voff+i;
    m_lines[loff + 2*i+1] = voff+i+1;
  }
}

void CgMesh::appendLines(const PointList<3, float> &pts)
{
  // append multiple line segments with two vertices each
  assert((pts.size() & 1) == 0);
  const uint voff = m_vtx.size();
  m_vtx.insert(m_vtx.end(), pts.begin(), pts.end());
  const uint np = pts.size();
  const uint ilxoff = m_lines.size();
  m_lines.resize( ilxoff + np );
  std::iota(m_lines.begin()+ilxoff, m_lines.end(), voff);
}

void CgMesh::removeLines(size_t lbegin, size_t lend)
{
  if (lend > lbegin and 2*lend <= m_lines.size()) {
    m_lines.erase( m_lines.begin()+2*lbegin,
                   m_lines.begin()+2*lend );
  }
}

void CgMesh::boundingBox(float plo[], float phi[]) const
{
  const int nv = m_vtx.size();
  for (int i=0; i<nv; ++i) {
    for (int k=0; k<3; ++k) {
      plo[k] = std::min(plo[k], m_vtx[i][k]);
      phi[k] = std::max(phi[k], m_vtx[i][k]);
    }
  }
}

float CgMesh::meanEdgeLength() const 
{
  float sum(0.0f);
  const size_t nf = m_triangles.size() / 3;
  for (size_t i=0; i<nf; ++i) {
    const uint *v = &m_triangles[3*i];
    sum += norm( m_vtx[v[1]] - m_vtx[v[0]] );
    sum += norm( m_vtx[v[2]] - m_vtx[v[1]] );
    sum += norm( m_vtx[v[2]] - m_vtx[v[0]] );
  }
  return sum/(3.0f*nf);
}

float CgMesh::meanTriangleArea() const
{
  float sum(0.0f);
  const size_t nf = m_triangles.size() / 3;
  for (size_t i=0; i<nf; ++i) {
    const uint *v = &m_triangles[3*i];
    sum += 0.5f*norm( cross(m_vtx[v[1]] - m_vtx[v[0]], m_vtx[v[2]] - m_vtx[v[0]]) );
  }
  return sum/nf;
}

void CgMesh::transform(const SMatrix<4,4,float> & t)
{
  ptrafo(t, m_vtx);
  ntrafo(t, m_nrm);
  ptrafo(t, m_lvx);
}

void CgMesh::importMesh(const TriMesh & tm)
{
  m_tristrips = CgStrip(true);
  m_trifans = CgStrip(true);
  m_lnstrips = CgStrip(false);

  // copy triangle vertices
  const int nf = tm.nfaces();
  m_triangles.resize(3*nf);
  for (int i=0; i<nf; ++i) {
    const uint *vi = tm.face(i).vertices();
    for (int k=0; k<3; ++k)
      m_triangles[3*i+k] = vi[k];
  }

  // copy vertices and normals, or estimate if not present
  const PointList<3> & tv( tm.vertices() );
  const PointList<3> & tn( tm.normals() );
  bool hasNormals = (tv.size() == tn.size());
  m_vtx = PointList3f(tv);
  if (hasNormals)
    m_nrm = PointList3f(tn);
  else
    estimateNormals();

  // mark boundary edges as lines
  Indices bde;
  tm.boundaries(bde);
  const int nb = bde.size();
  m_lines.resize( 2*nb );
  for (int i=0; i<nb; ++i) {
    const TriEdge & e( tm.edge(bde[i]) );
    m_lines[2*i+0] = e.source();
    m_lines[2*i+1] = e.target();
  }
}

void CgMesh::splitTriangles()
{
  const int nt = m_triangles.size() / 3;
  const int nlv = m_lines.size();
  PointList<3,float> vtmp(3*nt+nlv), ntmp(3*nt);
  // ColorArray ctmp(3*nt);
  Indices ttmp(3*nt);
  m_vtxcol.clear();

  //#pragma omp parallel for
  for (int i=0; i<3*nt; ++i) {
    vtmp[i] = m_vtx[m_triangles[i]];
    ttmp[i] = i;
  }

  //#pragma omp parallel for
  for (int i=0; i<nt; ++i) {
    const Vct3f & p1 = vtmp[3*i+0];
    const Vct3f & p2 = vtmp[3*i+1];
    const Vct3f & p3 = vtmp[3*i+2];
    Vct3f fn = cross(p2-p1, p3-p1).normalized();
    ntmp[3*i+0] = ntmp[3*i+1] = ntmp[3*i+2] = fn;
  }

  //#pragma omp parallel for
  for (int i=0; i<nlv; ++i) {
    vtmp[3*nt+i] = m_vtx[m_lines[i]];
    m_lines[i] = 3*nt+i;
  }

  m_triangles.swap(ttmp);
  m_vtx.swap(vtmp);
  m_nrm.swap(ntmp);
  // vtxcol.swap(ctmp);
}

void CgMesh::freeLines(PointList3f &plines) const
{
  plines.clear();

  Indices triv(m_triangles);
  std::sort(triv.begin(), triv.end());
  triv.erase( std::unique(triv.begin(), triv.end()), triv.end() );

  const size_t nl = m_lines.size() / 2;
  for (size_t i=0; i<nl; ++i) {
    uint s = m_lines[2*i+0];
    uint t = m_lines[2*i+1];
    if ( (not binary_search(triv.begin(), triv.end(), s)) and
         (not binary_search(triv.begin(), triv.end(), t)) ) {
      plines.push_back( m_vtx[s] );
      plines.push_back( m_vtx[t] );
    }
  }
}

void CgMesh::reorderElements(const Indices &perm)
{
  // reordering acts on separate elements only
  assert(m_lvx.empty());
  assert(m_tristrips.nstrip() == 0);
  assert(m_trifans.nstrip() == 0);

  // determine inverse permutation
  const size_t n = perm.size();
  assert(n == m_vtx.size());
  Indices iperm(n);
  for (size_t i=0; i<n; ++i) {
    assert(perm[i] < n);
    iperm[perm[i]] = i;
  }

  // apply permutation
  const size_t ntv = m_triangles.size();
  for (size_t i=0; i<ntv; ++i)
    m_triangles[i] = iperm[m_triangles[i]];
  const size_t nlv = m_lines.size();
  for (size_t i=0; i<nlv; ++i)
    m_lines[i] = iperm[m_lines[i]];
}

void CgMesh::detectEdges(float mergeTol, float minAngle)
{
  // don't do anything with nonsensical criteria
  if (minAngle >= M_PI)
    return;

  splitTriangles();

  // keep lines that do not reference triangle vertices
  PointList3f plines;
  freeLines(plines);

  TriMesh tm;
  this->exportMesh(tm);
  tm.detectEdges(minAngle, mergeTol);
  tm.estimateNormals();
  this->importMesh(tm);

  // re-introduce free lines
  this->appendLines(plines);
}

void CgMesh::repairNormals()
{
  // use TriMesh for this since that already generates the required
  // topology information
  TriMesh tm;
  this->exportMesh(tm);

  // do not drop any vertices because that would destroy the indexing of
  // line elements in *this
  tm.fixate(false);
  const uint nf = tm.nfaces();

  uint nfixed = 1;
  std::vector<bool> ifixed(nf, false);
  std::vector<uint> stack;

  // use the first triangle as a reference
  stack.push_back(0);
  ifixed[0] = true;
  while (not stack.empty()) {

    uint ti = stack.back();
    stack.pop_back();
    Vct3 nref = tm.face(ti).normal();

    // iterate over all vertices of ti
    const uint *vi = tm.face(ti).vertices();
    for (uint k=0; k<3; ++k) {

      // iterate over all triangles which use vi[k]
      TriMesh::nb_face_iterator itf, last = tm.v2fEnd(vi[k]);
      for (itf = tm.v2fBegin(vi[k]); itf != last; ++itf) {

        // ignore this neighbor triangle if it is already fixed
        uint tj = itf.index();
        if (ifixed[tj])
          continue;

        Vct3 nk = itf->normal();
        if ( dot(nref,nk) < 0.0 )
          tm.face(tj).reverse();
        ifixed[tj] = true;
        stack.push_back(tj);
        ++nfixed;

      } // neighbors of vi[k]
    } // vertices vi of ti

    // if we have multiple, disjoint surfaces, then the stack will empty
    // before all faces are processed - continue with the first triangle
    // not yet touched and put it on the stack to restart on the next surface
    if (stack.empty() and nfixed != nf) {
      for (uint i=0; i<nf; ++i) {
        if (not ifixed[i]) {
          stack.push_back(i);
          ifixed[i] = true;
          ++nfixed;
        }
      }
    }

  } // while stack not empty

  tm.estimateNormals();
  this->importMesh(tm);
}

Vct3f CgMesh::areaCenter() const
{
  const int nf = m_triangles.size() / 3;
  Vct3f ctr;
  float area(0), k(1.0f/3.0f);
  for (int i=0; i<nf; ++i) {
    const uint *v = &m_triangles[3*i];
    const Vct3f &p0(m_vtx[v[0]]);
    const Vct3f &p1(m_vtx[v[1]]);
    const Vct3f &p2(m_vtx[v[2]]);
    float a = norm(cross(p1-p0, p2-p0));
    area += a;
    ctr += a*(p0 + p1 + p2)*k;
  }
  ctr /= area;
  return ctr;
}

uint CgMesh::dropUnusedVertices(Indices *pvm)
{
  expandStrips();

  Indices map;
  const int nv = m_vtx.size();
  {
    map = m_triangles;
    map.insert(map.end(), m_lines.begin(), m_lines.end());
    std::sort(map.begin(), map.end());
    map.erase( std::unique(map.begin(), map.end()), map.end() );
  }

  const int np = map.size();
  if (np == nv)
    return 0;

  PointList<3,float> pmap(np);
  for (int i=0; i<np; ++i)
    pmap[i] = m_vtx[map[i]];
  m_vtx.swap(pmap);
  pmap.resize(np);
  for (int i=0; i<np; ++i)
    pmap[i] = m_nrm[map[i]];
  m_nrm.swap(pmap);

  Indices iperm(nv, NotFound);
  for (int i=0; i<np; ++i)
    iperm[map[i]] = i;

  const int ntv = m_triangles.size();
  for (int i=0; i<ntv; ++i)
    m_triangles[i] = iperm[m_triangles[i]];
  const int nlv = m_lines.size();
  for (int i=0; i<nlv; ++i)
    m_lines[i] = iperm[m_lines[i]];

  if (pvm != 0)
    pvm->assign(map.begin(), map.end());

  return nv-np;
}

void CgMesh::dropInvalidTriangles(float mergetol)
{
  Indices repl, keep;
  {
    NDPointTree<3,float> btree;
    btree.allocate(m_vtx, true, 4);
    btree.sort();
    btree.repldup(mergetol, repl, keep);

    const int nkeep = keep.size();
    PointList<3,float> tv(nkeep), tn;
    if (m_nrm.size() == m_vtx.size()) {
      tn.resize(nkeep);
      for (int i=0; i<nkeep; ++i) {
        tv[i] = m_vtx[keep[i]];
        tn[i] = m_nrm[keep[i]];
      }
    } else {
      for (int i=0; i<nkeep; ++i)
        tv[i] = m_vtx[keep[i]];
    }

    tv.swap(m_vtx);
    tn.swap(m_nrm);
  }

  // convert strips/fans to plain triangles
  expandStrips();

  // generate unique set of regular triangles
  std::vector<BasicTriangle> tset;
  const int n = m_triangles.size() / 3;
  tset.reserve( n );

  // just a safeguard against triangles with size (almost) zero
  const float min_sqa( 4.0f*sq(mergetol) );
  for (int i=0; i<n; ++i) {

    uint a = repl[m_triangles[3*i+0]];
    uint b = repl[m_triangles[3*i+1]];
    uint c = repl[m_triangles[3*i+2]];

    Vct3f fn = cross( m_vtx[b] - m_vtx[a],
                      m_vtx[c] - m_vtx[a] );
    if (sq(fn) < min_sqa)
      continue;

    BasicTriangle t(a, b, c);

    // ignore ill-defined triangles
    if (t.regular())
      tset.push_back( t );
  }

  std::vector<BasicTriangle>::iterator last;
  std::sort(tset.begin(), tset.end());
  last = std::unique(tset.begin(), tset.end());
  tset.erase(last, tset.end());

  const int nu = tset.size();
  m_triangles.resize( 3*nu );
  for (int k=0; k<nu; ++k) {
    const uint *v = tset[k].vertices();
    for (int j=0; j<3; ++j)
      m_triangles[3*k+j] = v[j];
  }

  // index translation for lines
  const int nlv = m_lines.size();
  for (int i=0; i<nlv; ++i)
    m_lines[i] = repl[m_lines[i]];
}

void CgMesh::quadRefine()
{
  // unique edge set needed to generate points
  const size_t nv = m_triangles.size();
  const size_t nf = m_triangles.size() / 3;
  BasicEdgeArray edges(nv);
  for (size_t i=0; i<nv; i+=3)
    BasicEdge::createEdges( &m_triangles[i], &edges[i] );

  std::sort(edges.begin(), edges.end());
  edges.erase( std::unique(edges.begin(), edges.end()), edges.end() );

  const size_t ne = edges.size();
  const size_t voff = m_vtx.size();
  m_vtx.reserve( voff + ne );
  for (size_t i=0; i<ne; ++i) {
    const Vct3f & src = m_vtx[ edges[i].source() ];
    const Vct3f & trg = m_vtx[ edges[i].target() ];
    appendVertex( 0.5f*(src + trg) );
  }

  Indices tri(12*nf);
  const int map[12] = { 0,3,5, 1,4,3, 2,5,4, 3,4,5 };
  for (size_t i=0; i<nf; ++i) {
    uint ve[6];
    const uint *vn = &m_triangles[3*i];
    for (int k=0; k<3; ++k) {
      uint eix = sorted_index(edges, BasicEdge( vn[k], vn[(k+1)%3] ));
      assert(eix != NotFound);
      ve[3+k] = voff + eix;
      ve[k] = vn[k];
    }

    for (int k=0; k<12; ++k)
      tri[12*i+k] = ve[map[k]];
  }

  m_triangles.swap(tri);
}

void CgMesh::exportMesh(TriMesh & tm) const
{
  PointList<3> pts(m_vtx.size());
  convert(m_vtx, pts);
  Indices itri;
  toTriangles(itri);
  tm.importMesh(pts, itri, true);
}

void CgMesh::merge(const CgMesh &msub)
{
  merge(msub, Mtx44f::identity());
}

void CgMesh::toTriangles(Indices & tri) const
{
  tri.insert(tri.end(), m_triangles.begin(), m_triangles.end());
  m_tristrips.strips2triangles(tri);
  m_trifans.fans2triangles(tri);
}

void CgMesh::toLines(Indices & lns) const
{
  lns.insert(lns.end(), m_lines.begin(), m_lines.end());
}

void CgMesh::expandStrips()
{
  if (m_tristrips.nstrip() == 0 and m_trifans.nstrip() == 0
      and m_lnstrips.nstrip() == 0)
    return;

  m_tristrips.strips2triangles(m_triangles);
  m_trifans.fans2triangles(m_triangles);

  m_tristrips.clear();
  m_trifans.clear();

  // do the same for polylines
  const uint voff = m_vtx.size();
  m_vtx.insert(m_vtx.end(), m_lvx.begin(), m_lvx.end());
  m_lvx.clear();

  m_lnstrips.poly2lines(m_lines, voff);
  m_lnstrips.clear();
}

CPHINT_HOTSPOT_BEGIN

void CgMesh::estimateNormals()
{
  const int nv = m_vtx.size();
  m_nrm.resize(nv);

  Indices tri;
  toTriangles(tri);
  const int nt = tri.size() / 3;

  DVector<float> wgt(nv);

  CPHINT_SIMD_LOOP
  for (int i=0; i<nt; ++i) {
    const uint *v = &tri[3*i];
    Vct3f fn = cross(m_vtx[v[1]]-m_vtx[v[0]], m_vtx[v[2]]-m_vtx[v[0]]);
    normalize(fn);
    for (int k=0; k<3; ++k) {
      const Vct3f & pa( m_vtx[v[k]] );
      const Vct3f & pb( m_vtx[v[(k+1)%3]] );
      const Vct3f & pc( m_vtx[v[(k+2)%3]] );
      float w = arg(pb-pa, pc-pa);
      m_nrm[v[k]] += w*fn;
      wgt[v[k]] += w;
    }
  }

  // avoid square root in normalize()
  for (int i=0; i<nv; ++i) {
    if (wgt[i] != 0.0f)
      m_nrm[i] /= wgt[i];
  }
}

CPHINT_HOTSPOT_END

int CgMesh::checkValidity() const
{
  int stat = CgMesh::Valid;
  const int ntv = m_triangles.size();
  for (int i=0; i<ntv; ++i) {
    uint tv = m_triangles[i];
    if (tv >= m_vtx.size())
      stat |= RefInvalidVertex;
    if (tv >= m_nrm.size())
      stat |= RefInvalidNormal;
  }
  const int nlv = m_lines.size();
  for (int i=0; i<nlv; ++i) {
    uint tv = m_lines[i];
    if (tv >= m_vtx.size())
      stat |= RefInvalidVertex;
  }
  return stat;
}

void CgMesh::clearMesh()
{
  m_vtx.clear();
  m_nrm.clear();
  m_lvx.clear();
  m_tristrips.clear();
  m_trifans.clear();
  m_triangles.clear();
  m_lines.clear();
  m_lnstrips.clear();
  m_vtxcol.clear();
}

XmlElement CgMesh::toXml(bool share) const
{
  XmlElement xe("CgMesh");
  
  if (not m_vtx.empty()) {
    XmlElement xv("Vertices");
    xv["count"] = str(m_vtx.size());
    xv.asBinary(3*m_vtx.size(), m_vtx.pointer(), share);
    xe.append(std::move(xv));
  }
  
  if (not m_nrm.empty()) {
    XmlElement xv("Normals");
    xv["count"] = str(m_nrm.size());
    xv.asBinary(3*m_nrm.size(), m_nrm.pointer(), share);
    xe.append(std::move(xv));
  }
  
  if (not m_lvx.empty()) {
    XmlElement xv("PolylineVertices");
    xv["count"] = str(m_lvx.size());
    xv.asBinary(3*m_lvx.size(), m_lvx.pointer(), share);
    xe.append(std::move(xv));
  }
  
  if (m_tristrips.nstrip() > 0) {
    XmlElement xs( m_tristrips.toXml(share) );
    xs["name"] = "tristrips";
    xe.append(std::move(xs));
  }
  
  if (m_trifans.nstrip() > 0) {
    XmlElement xs( m_trifans.toXml(share) );
    xs["name"] = "trifans";
    xe.append(std::move(xs));
  }
  
  if (m_lnstrips.nstrip() > 0) {
    XmlElement xs( m_lnstrips.toXml(share) );
    xs["name"] = "linestrips";
    xe.append(std::move(xs));
  }
  
  if (not m_triangles.empty()) {
    XmlElement xi("Indices");
    xi["name"] = "triangles";
    xi["count"] = str(m_triangles.size());
    xi.asBinary(m_triangles.size(), &m_triangles[0], share);
    xe.append(std::move(xi));
  }
  
  if (not m_lines.empty()) {
    XmlElement xi("Indices");
    xi["name"] = "lines";
    xi["count"] = str(m_lines.size());
    xi.asBinary(m_lines.size(), &m_lines[0], share);
    xe.append(std::move(xi));
  }

  if (m_vtxcol.size() == m_vtx.size() and m_vtxcol.size() > 0) {
    XmlElement xc("VertexColor");
    xc["count"] = m_vtxcol.size();
    xc.asBinary(3*m_vtxcol.size(), m_vtxcol[0].pointer(), share);
    xe.append(std::move(xc));
  }
  
  return xe;
}

void CgMesh::fromXml(const XmlElement & xe)
{
  if (xe.name() != "CgMesh")
    throw Error("Incompatible XML representation for CgMesh");
  
  XmlElement::const_iterator itr, last(xe.end());
  for (itr = xe.begin(); itr != last; ++itr) {
    const string &n = itr->name();
    if (n == "Vertices") {
      const int nv = Int(itr->attribute("count"));
      m_vtx.resize(nv);
      if (nv > 0)
        itr->fetch(3*nv, m_vtx.pointer());
    } else if (n == "Normals") {
      const int nv = Int(itr->attribute("count"));
      m_nrm.resize(nv);
      if (nv > 0)
        itr->fetch(3*nv, m_nrm.pointer());
    } else if (n == "CgStrip") {
      string s = itr->attribute("name");
      if (s == "tristrips")
        m_tristrips.fromXml(*itr);
      else if (s == "trifans")
        m_trifans.fromXml(*itr);
      else if (s == "linestrips")
        m_lnstrips.fromXml(*itr);
    } else if (n == "Indices") {
      string s = itr->attribute("name");
      if (s == "triangles") {
        const uint ni = Int(itr->attribute("count"));
        m_triangles.resize(ni);
        if (ni > 0)
          itr->fetch(ni, &m_triangles[0]);
      } else if (s == "lines") {
        const uint ni = Int(itr->attribute("count"));
        m_lines.resize(ni);
        if (ni > 0)
          itr->fetch(ni, &m_lines[0]);
      }
    } else if (n == "PolylineVertices") {
      const int nv = Int(itr->attribute("count"));
      m_lvx.resize(nv);
      if (nv > 0)
        itr->fetch(3*nv, m_lvx.pointer());
    } else if (n == "VertexColor") {
      const int nv = Int(itr->attribute("count"));
      m_vtxcol.resize(nv);
      if (nv > 0)
        itr->fetch(size_t(4*nv), (uint8_t*) &m_vtxcol[0]);
    }
  }
}

void CgMesh::importNode3Dxml(const XmlElement & xe)
{
  // clear first
  m_vtx.clear();
  m_nrm.clear();
  m_lvx.clear();
  m_vtxcol.clear();

  m_tristrips = CgStrip(true);
  m_trifans = CgStrip(true);
  m_lnstrips = CgStrip(false);
  m_triangles = Indices();
  m_lines = Indices();

  // set tag if present
  m_itag = xe.attr2int("id", 0);
  
  // search for xml nodes containing vertex and face data
  XmlElement::const_iterator itr, last(xe.end());
  XmlElement::const_iterator ivbuf(last), ifaces(last), iedges(last);
  for (itr = xe.begin(); itr != last; ++itr) {
    const string &s = itr->name();
    if (s == "VertexBuffer")
      ivbuf = itr;
    else if (s == "Faces")
      ifaces = itr;
    else if (s == "Edges")
      iedges = itr;
  }
  
  // ignore geometry nodes without faces or vertices
  if (ivbuf == last)
    return;
  if (ifaces == last)
    return;
  
  // retrieve vertex data
  itr = ivbuf->findChild("Positions");
  if (itr == ivbuf->end())
    throw Error("CgMesh::import3dxml() : No vertices in buffer.");
  
  Vct3f p;
  const char *s = itr->text().c_str();
  char *tail;
  while (parse_vertex(s, &tail, p)) {
    m_vtx.push_back(p);
    if (*tail == 0)
      break;
    s = tail;
  }
  
  // retrieve normal data, complain about missing normals
  itr = ivbuf->findChild("Normals");
  if (itr == ivbuf->end())
    throw Error("CgMesh::import3dxml() : No normals in buffer.");
  
  s = itr->text().c_str();
  while (parse_vertex(s, &tail, p)) {
    m_nrm.push_back(p);
    if (*tail == 0)
      break;
    s = tail;
  }

  // allocate vertex colors
  if (s_sigcolormode == CgMesh::ImportColor) {

    m_vtxcol.resize(m_vtx.size());

    // collect triangle data
    last = ifaces->end();
    Indices uix;
    for (itr = ifaces->begin(); itr != last; ++itr) {
      Color faceCol;
      if (itr->name() == "Face" and testColorNode3Dxml(*itr, faceCol)) {
        XmlElement::attr_iterator ita, alast(itr->attrEnd());
        for (ita = itr->attrBegin(); ita != alast; ++ita) {
          const string & key = ita->first;
          const string & val = ita->second;
          if (key == "strips") {
            uint ibegin = m_tristrips.nindices();
            m_tristrips.append(val);
            uint iend = m_tristrips.nindices();
            m_tristrips.uniqueIndices(uix, ibegin, iend);
            setVertexColor(faceCol, uix);
          } else if (key == "fans") {
            uint ibegin = m_tristrips.nindices();
            m_trifans.append(val);
            uint iend = m_tristrips.nindices();
            m_trifans.uniqueIndices(uix, ibegin, iend);
            setVertexColor(faceCol, uix);
          } else if (key == "triangles") {
            uint ntpre = m_triangles.size();
            parse_indices(val, m_triangles);
            uint ntpost = m_triangles.size();
            uix.clear();
            uix.insert(uix.end(), m_triangles.begin()+ntpre, m_triangles.begin()+ntpost);
            std::sort(uix.begin(), uix.end());
            uix.erase(std::unique(uix.begin(), uix.end()), uix.end());
            setVertexColor(faceCol, uix);
          }
        }
      }
    }

  } else {

    // don't import colors, but use them as exclusion/inclusion flags
    last = ifaces->end();
    for (itr = ifaces->begin(); itr != last; ++itr) {
      Color faceCol;
      if (itr->name() == "Face" and testColorNode3Dxml(*itr, faceCol)) {
        XmlElement::attr_iterator ita, alast(itr->attrEnd());
        for (ita = itr->attrBegin(); ita != alast; ++ita) {
          const string & key = ita->first;
          const string & val = ita->second;
          if (key == "strips") {
            m_tristrips.append(val);
          } else if (key == "fans") {
            m_trifans.append(val);
          } else if (key == "triangles") {
            parse_indices(val, m_triangles);
          }
        }
      }
    }

  }
  
  // look for polylines (optional)
  if (iedges != xe.end()) {
    last = iedges->end();
    for (itr = iedges->begin(); itr != last; ++itr) {
      if (itr->name() == "Polyline") {
        XmlElement::attr_iterator ita, alast;
        alast = itr->attrEnd();
        for (ita = itr->attrBegin(); ita != alast; ++ita) {
          const string & key = ita->first;
          const string & val = ita->second;
          if (key == "vertices") {
            s = val.c_str();
            while (parse_vertex(s, &tail, p)) {
              m_lvx.push_back(p);
              if (*tail == 0)
                break;
              s = tail;
            }
            m_lnstrips.append(m_lvx.size());
          }
        }
      }
    }
  }
}

bool CgMesh::testColorNode3Dxml(const XmlElement & xe, Color & faceCol) const
{
  if (s_sigcolormode == CgMesh::IgnoreColor)
    return true;

  // set default color
  faceCol = Color();

  // always accept faces without surface attributes
  XmlElement::const_iterator sfattr = xe.findChild("SurfaceAttributes");
  if (sfattr == xe.end())
    return true;

  // always accept faces without color attributes
  XmlElement::const_iterator xcolor = sfattr->findChild("Color");
  if (xcolor == sfattr->end())
    return true;

  float rgb[3] = {0.5f, 0.5f, 0.5f};
  XmlElement::attr_iterator ita, alast(xcolor->attrEnd());
  for (ita =  xcolor->attrBegin(); ita != alast; ++ita) {
    const string & key = ita->first;
    const string & val = ita->second;
    if (key == "red")
      rgb[0] = (float) genua_strtod(val.c_str(), 0);
    else if (key == "green")
      rgb[1] = (float) genua_strtod(val.c_str(), 0);
    else if (key == "blue")
      rgb[2] = (float) genua_strtod(val.c_str(), 0);
  }
  faceCol = Color(rgb);

  // jump out here if we just need to extract the face color
  if (s_sigcolormode == CgMesh::ImportColor)
    return true;

  // determine whether the color matches, ignoring the alpha channel
  bool cmatch = true;
  for (int k=0; k<3; ++k)
    cmatch &= (faceCol[k] == s_sigcolor[k]);

  if (s_sigcolormode == CgMesh::ExcludeSigColor)
    return (not cmatch);
  else
    return cmatch;
}

void CgMesh::importFile3Dxml(const XmlElement & xe)
{
  typedef XmlElement::const_iterator NodeIterator;
  typedef std::deque<NodeIterator> NodeQueue;

  clearMesh();
  
  CgMesh surf;
  NodeQueue queue;
  queue.push_back( xe.begin() );
  while (not queue.empty()) {
    // process breadth-first and in file ordering
    NodeIterator itr = queue.front();
    queue.pop_front();
    string s = itr->name();
    if ((s == "Rep" or s == "Root") and itr->hasAttribute("xsi:type")) {
      string t = itr->attribute("xsi:type");
      if (t == "PolygonalRepType") {
        surf.importNode3Dxml(*itr);
        merge(surf);
      } else if (t == "BagRepType") {
        // put all child nodes of a bag into queue
        NodeIterator cit(itr->begin()), clast(itr->end());
        size_t offset = queue.size();
        queue.resize(offset + std::distance(cit, clast));
        while (cit != clast)
          queue[offset++] = cit++;
      }
    }
    // if not a 'Rep', just skip to the next node in queue
  }
}

void CgMesh::setVertexColor(const Color & fc, const Indices & idx)
{
  const int nvs = idx.size();
  for (int i=0; i<nvs; ++i)
    m_vtxcol[idx[i]] = fc;
}



