#include "jrsmeshgenerator.h"
#include <surf/dcmeshcrit.h>
#include <surf/dcedge.h>
#include <surf/surface.h>
#include <genua/pattern.h>
#include <genua/timing.h>
#include <genua/dbprint.h>
#include <genua/smallqr.h>
#include <predicates/predicates.h>
#ifdef HAVE_TBB
#include <tbb/parallel_for.h>
#endif
#include <iostream>

using namespace std;

void JrsMeshGenerator::initMap(SurfacePtr psf)
{
  PatchMeshGenerator::initMap(psf);
  PatchMeshGenerator::initUvMap(psf, m_uvmap);
}

inline bool llisec(const Vct2 &a1, const Vct2 &a2,
                   const Vct2 &b1, const Vct2 &b2, Vct2 &r)
{
  SMatrix<2,2> A;
  A.assignColumn(0, a2-a1);
  A.assignColumn(1, b1-b2);
  r = b1 - a1;
  bool notparl = qrlls<2,2>(A.pointer(), r.pointer());
  return !notparl;
}

size_t JrsMeshGenerator::enforceConstraint(const Indices &cvi, int tag)
{
  size_t soff = m_segmark.size();
  assert(m_segments.size() == 2*soff);
  size_t nns = cvi.size() - 1;

  // generate new segments
  soff = m_segmark.size();
  assert(m_segments.size() == 2*soff);
  m_segmark.reserve(soff + nns);
  m_segments.reserve(2*soff + 2*nns);
  for (size_t i=0; i<nns; ++i) {
    if (cvi[i] != cvi[i+1]) {
      m_segments.push_back(cvi[i]);
      m_segments.push_back(cvi[i+1]);
      m_segmark.push_back(tag);
    }
  }
  nns = m_segmark.size() - soff;

  bool allowSplit = (tag & DcEdge::NeverSplit) == DcEdge::NeverSplit;
  if ((soff > 0) and allowSplit) {
    // check new constraints for intersections with old constraints;
    // when intersection found, insert point into uvi and slash the intersected
    // old segment into two pieces
    RadialOrdering porder = radiusOrder();
    for (size_t jseg=0; jseg < nns; ++jseg) {
      for (size_t iseg=0; iseg<soff; ++iseg) {
        uint inew = combineSegments(porder, iseg, soff+jseg);
        if (inew != NotFound) {
          ++nns;
          ++soff;
          m_segisec.push_back(inew);
        }
      }
    }

  }

  assert(m_segments.size() == 2*m_segmark.size());

  return cvi.size();
}

uint JrsMeshGenerator::combineSegments(RadialOrdering &porder,
                                       uint iseg, uint jseg)
{
  const uint isrc = m_segments[2*iseg+0];
  const uint itrg = m_segments[2*iseg+1];

  const uint jsrc = m_segments[2*jseg+0];
  const uint jtrg = m_segments[2*jseg+1];

  // skip forward if the old segment shares a vertex with the
  // new segment - that would always trigger an intersection
  if ( (isrc == jsrc) or (isrc == jtrg) )
    return NotFound;
  else if ( (itrg == jtrg) or (itrg == jsrc) )
    return NotFound;

  const Vct2 &js = m_uvp[jsrc];
  const Vct2 &jt = m_uvp[jtrg];             // must be here because jtrg changes
  const Vct2 &is = m_uvp[isrc];
  const Vct2 &it = m_uvp[itrg];

  Vct2 lp;
  bool lparl = llisec(js, jt, is, it, lp);                   // true if parallel

  if (not lparl) {

    // intersection point is outside segments
    if ((lp[0] < 0.0) or (lp[0] > 1) or (lp[1] < 0) or (lp[1] > 1))
      return NotFound;

    // inject intersection point
    Vct2 pis = (1-lp[0])*js + lp[0]*jt;
    uint inew = insertSegmentPoint(porder, pis);

    cerr << "New segment " << js << " --> " << jt
         << " (" << jsrc << "," << jtrg << ") intersects " << endl;
    cerr << "old segment " << is << " --> " << it
         << " (" << isrc << "," << itrg << ")"<< endl;
    cerr << "Parameter " << lp[0] << " at " << pis << endl;

    // modify both segments
    m_segments[2*iseg+1] = m_segments[2*jseg+1] = inew;

    // create two new ones
    m_segments.push_back(inew);
    m_segments.push_back(itrg);
    m_segmark.push_back( m_segmark[iseg] );
    m_segments.push_back(inew);
    m_segments.push_back(jtrg);
    m_segmark.push_back( m_segmark[jseg] );

    assert(m_segments.size() == 2*m_segmark.size());

    // return new vertex
    return inew;

  } else {

    Vct2 ed = (it - is).normalized();
    Vct2 jsfoot = is + dot(ed, js - is)*ed;

    // segments are parallel but far apart
    if ( sq(jsfoot - js) > gmepsilon )
      return NotFound;

    // compute coordinates along the shared direction
    Real a1 = dot(ed, is);
    Real a2 = dot(ed, it);
    Real b1 = dot(ed, js);
    Real b2 = dot(ed, jt);

    // segments do not overlap if ranges do not
    if (std::min(a1,a2) > std::max(b1,b2))
      return NotFound;
    else if (std::min(b1,b2) > std::max(a1,a2))
      return NotFound;

    // TODO : parallel segments - need to handle overlap
    stringstream ss;
    ss << "JrsMeshGenerator: New constraint segment overlaps old one:";
    ss << endl << is << " --> " << it
       << " (" << isrc << "," << itrg << ")" << endl;
    ss << endl << js << " --> " << jt
       << " (" << jsrc << "," << jtrg << ")" << endl;
    ss << endl << "on surface: " << m_psf->name();
    throw Error(ss.str());
  }

  return NotFound;
}

size_t JrsMeshGenerator::refineBoundaries()
{
  assert(m_pmc);
  m_pmc->assign(m_psf.get(), &m_uvp, &m_stp, &vtx, &nrm);
  const int npass = m_pmc->npass();
  size_t nref = 0;
  for (int j=0; j<npass; ++j) {
    uint nsplit = 0;
    const int nseg = m_segmark.size();
    for (int i=0; i<nseg; ++i) {
      uint s = m_segments[2*i+0];
      uint t = m_segments[2*i+1];
      if (m_pmc->splitEdge(s,t)) {
        uint imid = m_uvp.size();
        m_uvp.push_back( 0.5*(m_uvp[s] + m_uvp[t]) );
        m_stp.push_back( m_uvmap.eval(m_uvp.back()) );
        m_segments.push_back(imid);
        m_segments.push_back(t);
        m_segments[2*i+1] = imid;
        m_segmark.push_back(m_segmark[i]);
        ++nsplit;
      }
    }

    nref += nsplit;
    if (nsplit < 1)
      break;

  } // j-pass

  return nref;
}

size_t JrsMeshGenerator::generate(const PointList2d &uvini)
{
  assert(m_pmc);
  m_pmc->assign(m_psf.get(), &m_uvp, &m_stp, &vtx, &nrm);
  firstpass(uvini);

  // never do more than 3 sweeps with triangle -
  const size_t npass = std::min(m_pmc->npass(), 3u);
  size_t vxoffset = 0;
  for (size_t i=0; i<npass; ++i) {
    smooth(2, 0.5, vxoffset, m_uvp.size());
    vxoffset = nvertices();
    size_t newfaces = refine();
    if (nvertices() >= m_pmc->maxNodes() or newfaces == 0)
      break;
  }

  // final balancing pass
  this->smooth();

  clog << "[t] Time in delaunay : " << m_tjrs << endl;
  clog << "[t] Time in smoothing: " << m_tsmooth << endl;

  return nfaces();
}

size_t JrsMeshGenerator::firstpass(const PointList2d &uvini)
{
  assert(m_pmc != nullptr);
  m_pmc->assign(m_psf.get(), &m_uvp, &m_stp, &vtx, &nrm);
  bool splitBoundaries = stTransfer(uvini);

  Real starea = -1.0;

  // desired triangle area in (x,y,z) space
  DcMeshCritPtr mcp = boost::dynamic_pointer_cast<DcMeshCrit>(m_pmc);
  if (mcp) {

    Real sqedgelen = mcp->sqMaxLengthXyz();
    Real xarea = 0.25*std::sqrt(3.0)*sqedgelen;

    // determine mean area factor by averaging over surface
    const int nu = 4;
    const int nv = 4;
    const Real du = 1.0 / (nu+1);
    const Real dv = 1.0 / (nv+1);

    // mean area in (x,y,z) space of a unit square in (s,t) space
    Real staf = 0.0;
    for (int j=0; j<nv; ++j) {
      Real v = (j+1)*dv;
      for (int i=0; i<nu; ++i) {
        Real u = (i+1)*du;
        staf += areaRatio(u, v);
      }
    }
    staf /= (nu*nv);

    // desired mean area in (s,t) space
    starea = xarea / staf;
    dbprint("xarea",xarea,"starea",starea);
  }

  const Real minAngle = rad(15.0);

  Wallclock clk;
  clk.start();
  m_wrp.generate(minAngle, starea, splitBoundaries, m_pmc->maxNodes());
  extractMesh();
  m_tjrs += clk.stop();
  return TriMesh::nfaces();
}

size_t JrsMeshGenerator::refine()
{
  assert(m_pmc);
  m_pmc->assign(m_psf.get(), &m_uvp, &m_stp, &vtx, &nrm);

  // don't refine if there are already too many nodes
  if (nvertices() >= m_pmc->maxNodes())
    return 0;

  const size_t nf = nfaces();
  Vector area(nf);
  Indices tri(3*nf);

  Real maxarea = 1e6;
  Real minarea = std::numeric_limits<Real>::epsilon();
  Real minbeta = rad(15.);
  Real maxphi = rad(30);
  DcMeshCritPtr mcp = boost::dynamic_pointer_cast<DcMeshCrit>(m_pmc);
  if (mcp) {
    maxarea = 0.25*std::sqrt(3.0)*mcp->sqMaxLengthXyz();     // area in 3d space
    minarea = 0.25*std::sqrt(3.0)*mcp->sqMinLengthXyz();
    minbeta = std::max(minbeta, std::acos(mcp->maxCosApexAngle()));
    maxphi = std::acos(mcp->minCosNormalAngle());
  }

  auto f = [&](size_t i) {
    const uint *v = face(i).vertices();
    memcpy(&tri[3*i], v, 3*sizeof(uint));
    area[i] = targetArea(v, maxphi, maxarea, minarea);
  };

#ifdef HAVE_TBB
  tbb::parallel_for(size_t(0), nf, f);
#else
#pragma omp parallel for schedule(static,256)
  for (intptr_t i=0; i < intptr_t(nf); ++i)
    f(i);
#endif

  Wallclock clk;
  clk.start();
  // don't use holes with -r switch - must be done earlier
  m_wrp.allocate(m_stp, m_segments, m_segmark, PointList2d(), tri, area);
  m_wrp.refine(minbeta, false, nvertices() - m_pmc->maxNodes());
  extractMesh();
  m_tjrs += clk.stop();
  return nfaces() - nf;
}

Real JrsMeshGenerator::areaRatio(Real u, Real v) const
{
  Vct3 Ss, St;
  m_uvmap.plane(*m_psf, u, v, Ss, St);
  return norm(cross(Ss, St));
}

bool JrsMeshGenerator::stTransfer(const PointList2d &uvini)
{
  bool splitBoundaries = false;

  // for debugging - create enclosing segments
  if (uvini.empty()) {
    Vector up, vp;
    m_psf->initGridPattern(up, vp);
    const size_t nu = up.size();
    const size_t nv = vp.size();
    const size_t voff = m_uvp.size();

    bool gensegm = m_segments.empty();
    m_uvp.reserve(m_uvp.size() + nu*nv);
    for (size_t j=0; j<nv; ++j) {
      for (size_t i=0; i<nu; ++i) {
        size_t idx = m_uvp.size();
        Vct2 uv(up[i], vp[j]);
        if (j > 0 and j < nv-1 and i > 0 and i < nu-1) {
          Real sgn = 1.0 - 2.0*(i & 0x1);
          Real dv = 0.25*std::min( vp[j] - vp[j-1], vp[j+1] - vp[j] );
          uv[1] += sgn * dv;
        }
        m_uvp.push_back(uv);
        if (gensegm and i > 0 and (j == 0 or j == nv-1)) {
          m_segments.push_back(idx-1);
          m_segments.push_back(idx);
        }
      }
      if (gensegm and j > 0) {
        m_segments.push_back( voff + (j-1)*nu );
        m_segments.push_back( voff + j*nu );
        m_segments.push_back( voff + j*nu - 1);
        m_segments.push_back( voff + (j+1)*nu - 1);
      }
    }
    splitBoundaries = gensegm;
  } else {
    m_uvp.insert(m_uvp.end(), uvini.begin(), uvini.end());
  }

  // compute points in (s,t) plane - parallel?
  const size_t np = m_uvp.size();
  m_stp.resize(np);
  std::transform( m_uvp.begin(), m_uvp.end(),
                  m_stp.begin(),
                  [&](const Vct2 &uv){ return m_uvmap.eval(uv); });

  m_wrp.allocate(m_stp, m_segments, m_segmark, m_holes);
  return splitBoundaries;
}

void JrsMeshGenerator::extractMesh()
{
  TriMesh::clear();

  // accuracy of (uv)-(st) inversion
  const Real inv_tol = 1e-9;

  Indices tri;
  m_wrp.extract(m_stp, tri, m_segments, m_segmark);

  // map (s,t) nodes back to (u,v) - first nodes are identical
  // NOTE: During refinement, each pass may add only a small fraction of
  // the original nodes
  const size_t noff = m_uvp.size();
  const size_t nnodes = m_stp.size();
  const size_t nt = tri.size() / 3;
  m_uvp.resize(nnodes);

  TriMesh::reserve(nnodes, nt);
  vtx.resize(nnodes);
  nrm.resize(nnodes);

#ifdef HAVE_TBB
  auto f = [&](size_t i) {
    Vct3 Su, Sv;
    if (i >= noff)
      m_uvp[i] = m_uvmap.invert(m_stp[i], inv_tol);
    m_psf->plane(m_uvp[i][0], m_uvp[i][1], vtx[i], Su, Sv);
    nrm[i] = cross(Su, Sv);
  };
  tbb::parallel_for(size_t(0), nnodes, f);
#else
#pragma omp parallel for schedule(static,256)
  for (intptr_t i=0; i<intptr_t(nnodes); ++i) {
    Vct3 Su, Sv;
    if (i >= noff)
      m_uvp[i] = m_uvmap.invert(m_stp[i], inv_tol);
    m_psf->plane(m_uvp[i][0], m_uvp[i][1], vtx[i], Su, Sv);
    nrm[i] = cross(Su, Sv);
  }
#endif

  for (size_t i=0; i<nt; ++i)
    TriMesh::addFace( &tri[3*i] );
}

Real JrsMeshGenerator::targetArea(const uint *v, Real maxPhi,
                                  Real maxXArea, Real minXArea) const
{
  Real phi = arg(normal(v[0]), normal(v[1]));
  phi = std::max(phi, arg(normal(v[1]), normal(v[2])));
  phi = std::max(phi, arg(normal(v[2]), normal(v[0])));

  Vct2 rst1 = m_stp[v[1]] - m_stp[v[0]];
  Vct2 rst2 = m_stp[v[2]] - m_stp[v[0]];
  Real starea = 0.5*fabs(rst1[0]*rst2[1] - rst1[1]*rst2[0]);

  Vct2 uvm = (m_uvp[v[0]] + m_uvp[v[1]] + m_uvp[v[2]]) / 3.0;
  if (m_mcp) {
    Real bf = m_mcp->biasReduction(uvm);
    maxXArea *= sq(bf);
    minXArea *= sq(bf);
  }

  Real target;
  Real iar = 1.0 / areaRatio(uvm[0], uvm[1]);
  target = starea * std::min(1.0, sq(maxPhi/phi));
  target = std::max(std::min(target, maxXArea*iar), minXArea*iar);
  target = std::max(target, m_maxAreaReduction*starea);

  // TODO : Check if calling m_mcp directly works better
  // (doesn't yield a factor)

  return target;
}

void JrsMeshGenerator::smooth()
{
  const uint niter = m_pmc->nSmooth();
  const Real omega = m_pmc->wSmooth();
  this->smooth(niter, omega);
}

void JrsMeshGenerator::importMesh(const PointList2d &uvp,
                                  const Indices &tri, int tag)
{
  PatchMeshGenerator::importMesh(uvp, tri, tag);

  const size_t np = uvp.size();
  m_stp.resize(np);
  for (size_t i=0; i<np; ++i)
    m_stp[i] = m_uvmap.eval(uvp[i]);
}


void JrsMeshGenerator::smooth(uint niter, Real omega, size_t vbegin, size_t vend)
{
  Wallclock clk;
  clk.start();

  // needs vertex-to-face connectivity
  TriMesh::fixate(false);

  const size_t nvx = TriMesh::nvertices();
  vend = std::min(vend, nvx);
  const size_t nsm = vend - vbegin;

  // generate vertex ordering
  Indices smv(nsm);
  std::iota(smv.begin(), smv.end(), vbegin);
  dbprint("Smoothing ",nsm,"nodes");

  // mark vertices on segments, which may not move
  const size_t nsv = m_segments.size();
  std::vector<bool> constrained(nvx, false);
  for (size_t i=0; i<nsv; ++i)
    constrained[m_segments[i]] = true;

  for (uint iter=0; iter<niter; ++iter) {
    // avoid bias by using a new ordering in each iteration
    std::random_shuffle(smv.begin(), smv.end());
    for (size_t i=0; i<nsm; ++i) {
      size_t ki = smv[i];
      if (not constrained[ki])
        smoothVertex(ki, TriMesh::v2f.size(ki),
                     TriMesh::v2f.first(ki), omega);
    }
  }

  m_tsmooth += clk.stop();
}

void JrsMeshGenerator::smoothVertex(uint iv, uint nnb,
                                    const uint *nbf, Real omega)
{
  if (nnb == 0 or omega <= 0.0)
    return;

  // determine barycenter bcu in (u,v)-space and bcx in (x,y,z)-space
  Vct3 bcx;
  Vct2 bcu;
  Real area(0);
  const PointList3d &pxy = TriMesh::vtx;
  for (uint i=0; i<nnb; ++i) {
    const uint *vi = face( nbf[i] ).vertices();
    const Vct3 & p0( pxy[vi[0]] );
    const Vct3 & p1( pxy[vi[1]] );
    const Vct3 & p2( pxy[vi[2]] );
    Real ar = 0.5*norm(cross(p1-p0, p2-p0));
    assert(ar > 0);
    bcx += ar/3. * (p0 + p1 + p2);
    area += ar;
    const Vct2 & q0( m_uvp[vi[0]] );
    const Vct2 & q1( m_uvp[vi[1]] );
    const Vct2 & q2( m_uvp[vi[2]] );
    bcu += ar/3. * (q0 + q1 + q2);
  }

  assert(area > 0);
  bcu /= area;
  bcx /= area;

  Vct2 uv, st;
  bool legalMove = true;
  do {

    Vct3 pnew = (1.0 - omega)*pxy[iv] + omega*bcx;

    // project barycenter onto surface to find (u,v)
    uv = clamp((1.0 - omega)*m_uvp[iv] + omega*bcu, 0.0, 1.0);
    m_psf->project( pnew, uv );
    st = m_uvmap.eval(uv);

    // determine if all the triangles to be modified will remain legal
    legalMove = true;
    for (uint i=0; i<nnb; ++i) {
      const uint *vi = face( nbf[i] ).vertices();
      legalMove &= (orientChanged(vi, iv, st) == CounterClockwise);
    }

    // reduce smoothing parameter, abort smoothing operation if omega
    // becomes too small to be worthwhile
    omega *= 0.5;
    if (omega < 0.125)
      return;

  } while (not legalMove);

  assert(legalMove);

  Vct3 S, Su, Sv;
  m_psf->plane(uv[0], uv[1], S, Su, Sv);
  TriMesh::vtx[iv] = S;
  TriMesh::nrm[iv] = cross(Su,Sv);
  m_uvp[iv]= uv;
  m_stp[iv] = st;
}

int JrsMeshGenerator::orientationPlanar(const Vct2 &pa, const Vct2 &pb,
                                        const Vct2 &pc) const
{
  double ori = jrsOrient2d(pa, pb, pc);
  int flag = (ori < 0.0) ? Clockwise :
                           ( (ori > 0.0) ? CounterClockwise : Colinear );
  return flag;
}

int JrsMeshGenerator::orientChanged(const uint vi[],
                                    uint a, const Vct2 &pa) const
{
  if (vi[0] == a)
    return orientationPlanar(pa, m_stp[vi[1]], m_stp[vi[2]]);
  else if (vi[1] == a)
    return orientationPlanar(m_stp[vi[0]], pa, m_stp[vi[2]]);
  else if (vi[2] == a)
    return orientationPlanar(m_stp[vi[0]], m_stp[vi[1]], pa);
  else
    return orientationPlanar(m_stp[vi[0]], m_stp[vi[1]], m_stp[vi[2]]);
}





