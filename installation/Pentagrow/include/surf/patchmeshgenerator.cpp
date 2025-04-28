#include "patchmeshgenerator.h"
#include <surf/surface.h>
#include <surf/uvmapping.h>
#include <genua/pattern.h>
#include <genua/dbprint.h>
#ifdef HAVE_TBB
#include <tbb/parallel_for.h>
#endif
#include <iostream>

using namespace std;

void PatchMeshGenerator::criterion(DcMeshCritBasePtr pmc)
{
  m_pmc = pmc;
  m_mcp = boost::dynamic_pointer_cast<DcMeshCrit>(m_pmc);
}

void PatchMeshGenerator::initMap(SurfacePtr psf)
{
  m_psf = psf;
}

void PatchMeshGenerator::punchHole(const Vct2 &ph)
{
  m_holes.push_back(ph);
}

void PatchMeshGenerator::importMesh(const PointList2d &uvp,
                                    const Indices &tri, int tag)
{
  assert(m_psf);
  m_uvp = uvp;

  TriMesh::clear();
  reserve(uvp.size(), tri.size()/3);
  vtx.resize(uvp.size());
  nrm.resize(uvp.size());

  auto f = [&](size_t i) {
    Vct3 Su, Sv;
    m_psf->plane(uvp[i][0], uvp[i][1], vtx[i], Su, Sv);
    nrm[i] = cross(Su, Sv);
  };

#ifdef HAVE_TBB
  tbb::parallel_for(0u, uvp.size(), f);
#else
  intptr_t nv = uvp.size();
#pragma omp for schedule(static,256)
  for (intptr_t i=0; i<nv; ++i)
    f(i);
#endif

  const size_t nf = tri.size() / 3;
  for (size_t i=0; i<nf; ++i)
    addFace(&tri[3*i], tag);
}

void PatchMeshGenerator::initUvMap(SurfacePtr psf, UvMapping &uvmap)
{
  m_psf = psf;
  if (m_psf == nullptr)
    return;

  // extract patterns for mesh initialization
  Vector up, vp;
  m_psf->initGridPattern(up, vp);
  if (up.size() < 4)
    up = equi_pattern(4);
  if (vp.size() < 4)
    vp = equi_pattern(4);

  uvmap.init(*m_psf, up, vp);

#ifndef NDEBUG
  uvmap.dump(psf->name() + "-uvmap.zml");
#endif
}

size_t PatchMeshGenerator::enforceConstraint(const PointList2d &uvp, int tag)
{
  return this->enforceConstraint( insertSegmentPoints(uvp), tag );
}

RadialOrdering PatchMeshGenerator::radiusOrder() const
{
  RadialOrdering ro;
  ro.sort(m_uvp);
  return ro;
}

Indices PatchMeshGenerator::insertSegmentPoints(const PointList2d &pts)
{
  const size_t np = pts.size();
  Indices cvi(np);
  if (m_uvp.empty()) {
    m_uvp = pts;
    std::iota(cvi.begin(), cvi.end(), 0);
    return cvi;
  }

  const size_t nop = m_uvp.size();

  // ordering of existing points by radius from origin
  RadialOrdering porder = radiusOrder();

//  // debug
//  for (size_t i=0; i<nop; ++i) {
//    cerr << porder[i] << " -> " << sq(m_uvp[porder[i]]) << " p: " << m_uvp[porder[i]] << endl;
//  }

  m_uvp.reserve(m_uvp.size()+np);

  // binary search each new point in old points
  for (size_t i=0; i<np-1; ++i)
    cvi[i] = insertSegmentPoint(porder, pts[i]);

  // check if the constraint is circular, i.e. last point equals first one
  if ( sq(pts.front() - pts.back()) < gmepsilon )
    cvi[np-1] = cvi[0];
  else
    cvi[np-1] = insertSegmentPoint(porder, pts[np-1]);

  // debug - sanity check
#ifndef NDEBUG
  for (size_t i=0; i<np; ++i) {
    const size_t ki = cvi[i];
    if (ki < nop)
      continue;
    for (size_t j=0; j<nop; ++j) {
      Real sqd = sq(m_uvp[ki] - m_uvp[j]);
      assert(sqd > m_sqmergetol);
    }
  }
#endif

  return cvi;
}

uint PatchMeshGenerator::insertSegmentPoint(RadialOrdering &porder, const Vct2 &p)
{
  return porder.insert(m_uvp, p, m_sqmergetol);
//  auto cmp = [&](const size_t &a, Real r2) {return (sq(m_uvp[a]) < r2);};
//  Indices::iterator lb, ub, itr;

//  Real sqp = sq(p);
//  lb = std::lower_bound(porder.begin(), porder.end(), sqp - m_sqmergetol, cmp);

//  size_t idx = m_uvp.size();
//  if (lb == porder.end()) {
//    m_uvp.push_back(p);
//    porder.push_back(idx);
//  } else {

//    while ( lb != porder.begin() and sq(m_uvp[*lb]) >= sqp - m_sqmergetol )
//      --lb;

//    ub = std::upper_bound(lb, porder.end(), sqp + m_sqmergetol, cmp);

//    // this shouldn't be needed, but it is
//    while ( (ub != porder.end()) and (sq(m_uvp[*ub]) < sqp + m_sqmergetol) )
//      ++ub;

//    if (ub == lb) {
//      if (lb != porder.begin())
//        --lb;
//      else if (ub != porder.end())
//        ++ub;
//    }

////    // debug
////    if (sqp == 1) {
////      cerr << "Lower: " << std::distance(porder.begin(), lb) << " = " << sq(m_uvp[*lb]) << endl;
////      if (ub != porder.end())
////        cerr << "Upper: " << std::distance(porder.begin(), ub) << " = " << sq(m_uvp[*ub]) << endl;
////      else
////        cerr << "Range: " << std::distance(lb,ub) << " last: " << sq(m_uvp.back()) << endl;
////    }

//    assert( sq(m_uvp[*lb]) <= sqp );
//    assert( ub == porder.end() or sq(m_uvp[*ub]) > sqp );
//    assert( lb != ub );
//    for (itr = lb; itr != ub; ++itr) {

////      // debug
////      if (sqp == 1) {
////        cerr << *itr << " - " << m_uvp[*itr] << endl;
////      }

//      if ( sq(m_uvp[*itr] - p) <= m_sqmergetol ) {
//        return *itr;
//      }
//    }

//    // range identified, but point is not in it - insert where it fits
//    m_uvp.push_back(p);
//    ub = std::upper_bound(lb, porder.end(), sqp, cmp);
//    porder.insert(ub, idx);
//  }

//  assert(idx < m_uvp.size());
//  return idx;
}

