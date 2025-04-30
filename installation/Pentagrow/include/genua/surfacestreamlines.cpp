#include "surfacestreamlines.h"
#include "mxmesh.h"
#include "mxmeshfield.h"
#include "mxmeshsection.h"
#include "rng.h"
#include "xcept.h"
#include "smallqr.h"
#include "atomicop.h"
#include "parallel_algo.h"
#include "basictriangle.h"
#include <fstream>

typedef std::lock_guard<std::mutex> Lock;

using namespace std;

uint SurfaceStreamlines::surfacesFromMesh(const MxMesh &mx)
{
  // identify nodes in mx which will be used in trimesh
  m_pretri.clear();
  const int nsec = mx.nsections();
  for (int i=0; i<nsec; ++i) {
    const MxMeshSection &sec = mx.section(i);
    if (sec.surfaceElements())
      addSection(sec);
  }

  return fixate(mx);
}

void SurfaceStreamlines::addSection(const MxMeshSection &sec)
{
  const int *tmap;
  const int ntri = sec.triangleMap(&tmap);

  // make space at the end of pretri but keep the previous triangles
  const size_t ne = sec.nelements();
  const size_t offset = m_pretri.size();
  m_pretri.resize(offset + 3*ntri*ne);

  uint tri[64];
  assert(3*ntri <= 64);
  for (size_t j=0; j<ne; ++j) {
    const uint *v = sec.element(j);
    for (int k=0; k<3*ntri; ++k)
      tri[k] = v[tmap[k]];
    std::copy(tri, tri+3*ntri, &m_pretri[offset+j*ntri*3]);
  }
}

uint SurfaceStreamlines::fixate(const MxMesh &mx)
{
  // create a set of unique indices
  m_idxmap = m_pretri;
  parallel::sort(m_idxmap.begin(), m_idxmap.end());
  m_idxmap.erase( std::unique(m_idxmap.begin(), m_idxmap.end()),
                  m_idxmap.end() );
  m_idxmap.shrink_to_fit();

  // create a set of unique triangles which index into m_idxmap
  const intptr_t ntri = m_pretri.size() / 3;
  std::vector<BasicTriangle> tri(ntri);

#pragma omp parallel for schedule(static,512)
  for (intptr_t i=0; i<ntri; ++i) {
    uint a = sorted_index(m_idxmap, m_pretri[3*i+0]);
    uint b = sorted_index(m_idxmap, m_pretri[3*i+1]);
    uint c = sorted_index(m_idxmap, m_pretri[3*i+2]);
    tri[i].assign(a,b,c);
  }
  parallel::sort(tri.begin(), tri.end());
  tri.erase(std::unique(tri.begin(), tri.end()), tri.end());

  // release memory
  m_pretri = Indices();

  // finally, assign to TriMesh
  const uint nv = m_idxmap.size();
  const uint nf = tri.size();
  m_msh.clear();
  m_msh.reserve(nv, nf);
  for (uint i=0; i<nv; ++i)
    m_msh.addVertex(mx.node(m_idxmap[i]));
  for (uint i=0; i<nf; ++i)
    m_msh.addFace(tri[i].vertices());

  m_msh.buildConnectivity();
  clog << m_msh.nvertices() << " vertices, " << m_msh.nfaces()
       << " triangles." << endl;

  clear();
  return m_msh.nedges();
}

void SurfaceStreamlines::extractField(const MxMeshField &f)
{
  if (not f.nodal())
    throw Error("Streamlines can only be computed for nodal fields.");
  if (f.ndimension() != 3)
    throw Error("Field dimension must be 3 for streamline computation.");

  const size_t nv = m_idxmap.size();
  m_vf.resize( nv );
  for (size_t i=0; i<nv; ++i)
    f.value(m_idxmap[i], m_vf[i]);

  // new field, new crossings.
  clear();
}

uint SurfaceStreamlines::edgeSliced(uint k) const
{
  const std::atomic_uint *p;
  p = reinterpret_cast<const std::atomic_uint*>(&m_edgesliced[k]);
  return (p->load(std::memory_order_acquire));
}

PointList4d SurfaceStreamlines::computeStreamline(uint istart,
                                                  Real minSpeed)
{
  PointList4d s1, s2;
  if (forbiddenEdge(istart))
    return s1;

  // typically, there're a few hundred points/line
  s1.reserve(256);
  s2.reserve(256);

  PointOnEdge first, cur;
  first.iedge = istart;
  first.tpos = 0.5;

  // walk forward
  cur = first;
  while (cur.valid()) {
    if ( forbiddenEdge(cur.iedge) )
      break;
    Real speed = storePoint(cur, s1);
    if (speed < minSpeed or s1.size() >= m_maxpoints)
      break;
    cur = walk(cur, true);
  }

  // walk backward
  cur = first;
  cur = walk(cur, false);
  while (cur.valid()) {
    if ( forbiddenEdge(cur.iedge) )
      break;
    Real speed = storePoint(cur, s2);
    if (speed < minSpeed or s2.size() >= m_maxpoints)
      break;
    cur = walk(cur, false);
  }

  // merge point sets
  std::reverse(s2.begin(), s2.end());
  s2.insert(s2.end(), s1.begin(), s1.end());

  return s2;
}

void SurfaceStreamlines::writeRandomLines(uint n,
                                          const std::string &baseName,
                                          Real minSpeed)
{
  clear();

  IntRng rng(0, m_msh.nedges()-1);
  rng.timeSeed();
  uint k = 0;
  for (uint j=0; j<n; ++j) {
    PointList4d sline( computeStreamline( rng(), minSpeed) );
    if (sline.size() > 1) {
      ++k;
      ofstream os( baseName + str(k) + ".txt" );
      os << sline;
      os.close();
    }
  }
  clog << k << " lines written." << endl;
}

void SurfaceStreamlines::appendRandomLines(MxMesh &mx, uint n,
                                           const string &baseName,
                                           Real minSpeed)
{
  clear();

  IntRng rng(0, m_msh.nedges()-1);
  rng.timeSeed();
  uint k = 0;
  PointList3d segment;
  for (uint j=0; j<n; ++j) {
    PointList4d sline( computeStreamline( rng(), minSpeed) );
    if (sline.size() > 1) {
      ++k;
      string sname = baseName + str(k);
      const size_t np = sline.size();
      segment.resize(np);
      for (size_t i=0; i<np; ++i)
        segment[i] = Vct3(sline[i][0], sline[i][1], sline[i][2]);
      uint isec = mx.appendSection(segment);
      mx.section(isec).rename(sname);
    }
  }
}

bool SurfaceStreamlines::forbiddenEdge(uint k) const
{
  const std::atomic_uint *p;
  p = reinterpret_cast<const std::atomic_uint*>(&m_edgesliced[k]);
  return (p->load(std::memory_order_acquire) >= m_maxslice);
}

void SurfaceStreamlines::incSlice(uint k)
{
  std::atomic_uint *p = reinterpret_cast<std::atomic_uint*>(&m_edgesliced[k]);
  p->fetch_add(1, std::memory_order_release);
}

uint SurfaceStreamlines::storeStreamline(const PointList4d &sln)
{
  Lock guard(m_sline_guard);
  m_slines.push_back(sln);
  return m_slines.size()-1;
}

void SurfaceStreamlines::clear()
{
  m_slines.clear();
  m_edgesliced.clear();
  m_edgesliced.resize(m_msh.nedges(), 0);
}

uint SurfaceStreamlines::storeRandomLines(uint n, uint minLength, Real minSpeed)
{
  clear();
  if (nedges() < 3)
    return 0;

  // how often to attempt to find a better seed point
  const int maxtry = 16;

  // some lines will be discarded, loop more
  const intptr_t nloop = 2*n;

#pragma omp parallel
  {
    IntRng rng(0, m_msh.nedges()-1);
    rng.threadSeed();
    int istart, ntry = 0;

#pragma omp for schedule(dynamic,16)
    for (intptr_t i=0; i<nloop; ++i) {
      if (size() < n) {
        istart = rng();
        ntry = 0;
        while ( (edgeSliced(istart) != 0) and (ntry < maxtry) ) {
          istart = rng();
          ++ntry;
        }
        PointList4d line = computeStreamline(istart, minSpeed);
        if (line.size() >= minLength and size() < n)
          storeStreamline(line);
      }
    }
  }

  return size();
}

SurfaceStreamlines::PointOnEdge
SurfaceStreamlines::walk(const SurfaceStreamlines::PointOnEdge &cur,
                         bool forward) const
{
  PointOnEdge next;
  if (cur.iedge >= m_msh.nedges())
    return next;

  // stop walk if edge is on boundary
  if ( m_msh.edegree(cur.iedge) != 2 )
    return next;

  // collect vertices around current edge
  uint diamond[4];
  const TriEdge &e(m_msh.edge(cur.iedge));
  const uint src = e.source();
  const uint trg = e.target();
  diamond[0] = src;
  diamond[1] = trg;
  Vct3 pe = cur.location(m_msh);

  // vector on edge
  Vct3 v = (1.0-cur.tpos)*m_vf[src] + cur.tpos*m_vf[trg];
  normalize(v);
  if (not forward)
    v = -v;

  TriMesh::nb_face_iterator itf;
  itf = m_msh.e2fBegin(cur.iedge);
  diamond[2] = itf->opposed(e);
  ++itf;
  diamond[3] = itf->opposed(e);

  // check four possible edges, return the first feasible
  PointOnEdge pnext;
  const int ia[] = {0, 0, 1, 1};
  const int ib[] = {2, 3, 2, 3};
  for (int k=0; k<4; ++k) {
    pnext = candidate(pe, v, diamond[ia[k]], diamond[ib[k]]);
    if (pnext.valid())
      return pnext;
  }

  return pnext;
}

Real SurfaceStreamlines::storePoint(const SurfaceStreamlines::PointOnEdge &p,
                                    PointList4d &sln)
{
  if ( hint_unlikely(not p.valid()) )
    return 0.0;

  Real t = p.tpos;
  const TriEdge &e = m_msh.edge( p.iedge );
  Vct3 pt = p.location(m_msh);
  Real v = norm( (1.0-t)*m_vf[e.source()] + t*m_vf[e.target()] );
  sln.push_back( Vct4(pt[0], pt[1], pt[2], v) );
  incSlice( p.iedge );
  return v;
}

SurfaceStreamlines::PointOnEdge
SurfaceStreamlines::candidate(const Vct3 &pe, const Vct3 &vf,
                              uint a, uint b) const
{
  // line equations:
  // L1 = pe + s*vf
  // L2 = (1-t)*a + t*b
  // min || L1 - L2 ||^2 = | pe + s*vf - (a + t*(b - a) |^2
  // min || C*x - y ||, y = a - pe
  SMatrix<3,2> C;
  Vct3 rhs;
  const Vct3 & pa = m_msh.vertex(a);
  const Vct3 & pb = m_msh.vertex(b);
  for (int k=0; k<3; ++k) {
    C(k,0) = vf[k]; // s
    C(k,1) = pa[k] - pb[k]; // t
    rhs[k] = pa[k] - pe[k];
  }

  PointOnEdge pnext;
  bool ok = qrlls<3,2>(C.pointer(), rhs.pointer());
  if (not ok)
    return pnext;  // vf || (b-a)

  Real s = rhs[0];
  Real t = rhs[1];
  if ((s > 0) and (t >= 0) and (t <= 1)) {
    pnext.iedge = m_msh.bsearchEdge(a, b);
    pnext.tpos = (a < b) ? t : (1.0 - t);
  }
  return pnext;
}

Vct3 SurfaceStreamlines::PointOnEdge::location(const TriMesh &m) const
{
  const Vct3 &ps = m.vertex( m.edge(iedge).source() );
  const Vct3 &pt = m.vertex( m.edge(iedge).target() );
  return (1.0-tpos)*ps + tpos*pt;
}
