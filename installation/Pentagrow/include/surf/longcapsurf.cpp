
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
 
#include "longcapsurf.h"
#include "dnmesh.h"
#include "dnrefine.h"
#include <genua/pattern.h>
#include <genua/trimesh.h>

using namespace std;

LongCapSurf::LongCapSurf(const PointList<3> & pts, Real rh)
  : Surface("LongCapSurf") {init(pts, rh);}

uint LongCapSurf::init(const PointList<3> & bp, Real rh)
{
  assert(bp.size() > 3);

  // copy points, but do not use duplicated last point
  PointList<3> pts;
  if (norm(bp.front()-bp.back()) < gmepsilon)
    pts.insert(pts.end(), bp.begin(), bp.end()-1);
  else
    pts.insert(pts.end(), bp.begin(), bp.end());

  // compute segments
  PointList<3> sgm(pts.size());
  sgm[0] = pts.front() - pts.back();
  for (uint i=1; i<pts.size(); ++i)
    sgm[i] = pts[i] - pts[i-1];

  // compute midpoint
  Vct3 pmid;
  Real len(norm(sgm[0])), dl;
  pmid = 0.5*len*(pts.front() + pts.back());
  for (uint i=1; i<sgm.size(); ++i) {
    dl = norm(sgm[i]);
    len += dl;
    pmid += 0.5*dl*(pts[i] + pts[i-1]);
  }
  pmid /= len;

  // find point where angle between segments is largest
  Vector kink(pts.size());
  for (uint i=0; i<pts.size()-1; ++i)
    kink[i] = fabs(arg(sgm[i+1], sgm[i]));
  kink.back() = fabs(arg(sgm.front(), sgm.back()));

  // debug
  Real mxk = *std::max_element(kink.begin(), kink.end());
  
  // make sure that the largest angle between segments is at the first point
  if (mxk > 0.5*PI) {
    m_bKink = true;
    std::rotate(pts.begin(),
                pts.begin() + std::distance(kink.begin(),
                                            std::max_element(kink.begin(),
                                                              kink.end())),
                pts.end());
  } else {
    m_bKink = false;
  }

  // close curve again (required for splining)
  pts.push_back(pts.front());
  
  // identify the point with largest distance from the first
  uint ifar;
  if (m_bKink)
    ifar = pivotByDistance(pts);
  else
    ifar = pivotByMedian(pts);

  // find mean normal vector
  m_nmean = 0.0;
  uint np = pts.size();
  PointList<3> rmid(np);
  for (uint i=0; i<np; ++i)
    rmid[i] = pts[i] - pmid;
  for (uint i=1; i<np; ++i) 
    m_nmean += cross(rmid[i], rmid[i-1]);
  normalize(m_nmean);

  // split the line at ifar
  PointList<3> phi, plo, psp;
  for (uint i=0; i<=ifar; ++i)
    plo.push_back(pts[i]);
  for (uint i=np-1; i>=ifar; --i)
    phi.push_back(pts[i]);
  
  // reverse direction for proper parametrization
  if (rh < 0) {
    std::reverse(plo.begin(), plo.end());
    std::reverse(phi.begin(), phi.end());
  }
  
  // construct boundary splines
  m_vplo = m_clo.interpolate(plo, 1);
  m_vphi = m_chi.interpolate(phi, 1);

  // store boundary constraints for mesh
  m_bsegm.clear();
  m_bsegm.reserve(m_vplo.size()+m_vphi.size()+1);
  for (uint i=0; i<m_vplo.size(); ++i)
    m_bsegm.push_back( vct(0.0, m_vplo[i]) );
  for (uint i=0; i<m_vphi.size(); ++i) {
    uint k = m_vphi.size()-i-1;
    m_bsegm.push_back( vct(1.0, m_vphi[k]) );
  }
  m_bsegm.push_back(m_bsegm.front());

  // TODO:
  // use surface tangents instead of nrm

  // construct spine curve
  Vct3 p1, p2;
  Vector vps = cosine_pattern(np/2, 2*PI, 0.0, 0.7);
  psp.resize(vps.size());
  for (uint i=0; i<vps.size(); ++i) {
    p1 = m_clo.eval(vps[i]);
    p2 = m_chi.eval(vps[i]);
    psp[i] = 0.5*(p1+p2) + 0.5*rh*norm(p2-p1)*m_nmean;
  }
  m_cspine.interpolate(psp, 3);

  return ifar;
}


uint LongCapSurf::pivotByDistance(const PointList<3> & pts) const
{
  Real dst, mdst(0);
  uint ifar(0);
  const int np(pts.size());
  for (int i=0; i<np; ++i) {
    dst = norm(pts[i] - pts[0]);
    if (dst > mdst) {
      mdst = dst;
      ifar = i;
    }
  }
  return ifar;
}

uint LongCapSurf::pivotByMedian(const PointList<3> & pts) const
{
  const int np = pts.size();
  Vector slen(np);
  slen[0] = 0.0;
  for (int i=1; i<np; ++i)
    slen[i] = slen[i-1] + norm(pts[i] - pts[i-1]);
  
  uint ipivot(np/2);
  Real hlf = slen.back() / 2;
  Real halfdst = huge;
  for (int i=0; i<np; ++i) {
    Real hd = fabs( hlf - slen[i] );
    if (hd < halfdst) {
      ipivot = i;
      halfdst = hd;
    }
  }
  return ipivot;
}

Vct3 LongCapSurf::eval(Real u, Real v) const
{
  assert(u >= 0.0 and u <= 1.0);
  assert(v >= 0.0 and v <= 1.0);
  Vct3 plo, phi, pbase, pelv;
  plo = m_clo.eval(v);
  phi = m_chi.eval(v);
  pbase = (1-u)*plo + u*phi; 
  pelv = m_cspine.eval(v) - 0.5*(plo + phi);
  // Real arc = 2.0*sqrt(fabs(0.25 - sq(u-0.5)));
  // Real arc = 1.0 - 4*sq(u - 0.5);
  Real t1 = sq(u - 0.5);
  Real arc = 1.0 - 8*sq(t1) - 2*t1;
  return pbase + arc*pelv;
}

Vct3 LongCapSurf::derive(Real u, Real v, uint ku, uint kv) const
{
  assert(u >= 0.0 and u <= 1.0);
  assert(v >= 0.0 and v <= 1.0);
  if (ku == 0 and kv == 0)
    return eval(u,v);

  // debug
  const Real ptol(1e-6);
  if (v < ptol or v > 1.0-ptol) {
    v = max(ptol, min(1.0-ptol, v) );
    return derive(0.5, v, ku, kv);
  }
  
  if (ku == 1 and kv == 0) {
    Vct3 plo = m_clo.eval(v);
    Vct3 phi = m_chi.eval(v);
    Vct3 pelv = m_cspine.eval(v) - 0.5*(plo + phi);
    //Real darc = (1 - 2*u)/sqrt(0.25 - sq(0.5 - u));
    //Real darc = 1.0 - 8*u;
    Real darc = -32*cb(u-0.5) - 4*(u-0.5);
    return phi - plo + pelv*darc;
  } else if (ku == 0 and kv == 1) {
    
    if (fabs(v) < gmepsilon or fabs(1.0-v) < gmepsilon)
      return m_nmean;
    
    Vct3 dlo = m_clo.derive(v, 1);
    Vct3 dhi = m_chi.derive(v, 1);
    Vct3 delv = m_cspine.derive(v, 1) - 0.5*(dlo + dhi);
    //Real arc = 2.0*sqrt(fabs(0.25 - sq(u-0.5)));
    //Real arc = 1.0 - 4*sq(u - 0.5);
    Real t1 = sq(u - 0.5);
    Real arc = 1.0 - 8*sq(t1) - 2*t1;
    return (1-u)*dlo + u*dhi + arc*delv;
  } else {
    throw Error("Higher order derivatives of LongCapSurf not implemented.");
  }
}

void LongCapSurf::apply()
{
  PointGrid<3> tmp;
  tmp = m_clo.getCp();
  for (uint i=0; i<tmp.size(); ++i)
    tmp[i] = RFrame::forward(tmp[i]);
  m_clo = Spline<3>(m_clo.getKnots(), tmp,  3);
  
  tmp = m_chi.getCp();
  for (uint i=0; i<tmp.size(); ++i)
    tmp[i] = RFrame::forward(tmp[i]);
  m_chi = Spline<3>(m_chi.getKnots(), tmp,  3);
  
  tmp = m_cspine.getCp();
  for (uint i=0; i<tmp.size(); ++i)
    tmp[i] = RFrame::forward(tmp[i]);
  m_cspine = Spline<3>(m_cspine.getKnots(), tmp,  3);
  
  RFrame::clear();
}

bool LongCapSurf::merge(TriMesh & tglob) const
{
  // export and merge with global mesh
  PointList<2> dmy;
  PointList<3> tp, nrm;
  Indices tri;
  bool ok = fixedMesh(dmy, tp, nrm, tri);
  if (not ok)
    return false;

  TriMesh tmesh;
  tmesh.importMesh(tp, tri);
  tmesh.fixate();
  tmesh.cleanup(1e-6);
  
  tglob.merge(tmesh);
  return true;
}

void LongCapSurf::initMesh(const DnRefineCriterion & crit, DnMesh & gnr) const
{
  // use the old implementation for sumo 1.8
  initMeshStd(crit, gnr);
  return;
 /* 
  // manufacture a shared_ptr to this
  SurfacePtr psf((Surface *) this, null_deleter() );
  
  // try to find a good pattern for vertex insertions
  // in the v-direction, that is along the boundary curves 
  const uint nb(bsegm.size());
  Vector vplo, vphi;
  for (uint i=0; i<nb; ++i) {
    const Vct2 & pb(bsegm[i]);
    if (pb[0] < 0.5)
      vplo.push_back(pb[1]);
    else
      vphi.push_back(pb[1]);
  }
  sort_unique(vplo);
  sort_unique(vphi);
  
  cout << "vplo: " << vplo << endl;
  cout << "vphi: " << vphi << endl;
  
  // construct boundary to use for initialization
  PointList<2> pbound;
  pbound.push_back( vct(0.5, 1.0) );
  for (uint i=1; i<vphi.size()-1; ++i)
    pbound.push_back( vct(1.0, vphi[vphi.size()-1-i]) );
  pbound.push_back( vct(0.5, 0.0) );
  for (uint i=1; i<vplo.size()-1; ++i)
    pbound.push_back( vct(0.0, vplo[i]) );
  
  //pbound.push_back( vct(0.5, 0.0) );
  
  cout << name() << " boundary: " << endl;
  cout << pbound << endl;
  
  DnMesh msh(psf, DnSpatial);
  msh.initPolygon(pbound);
  //msh.switchMode(DnSpatial);
  //msh.cleanup(gmepsilon, 2.0);
  
  msh.toXml().write("capboundinit.msh");
  
  if (bKink) {
  
    // delete first and last value (0.0 and 1.0)
    vplo.pop_back();
    vplo.erase(vplo.begin());
    vphi.pop_back();
    vphi.erase(vphi.begin());
    
    // create 'mean' pattern
    uint nv = (vphi.size() + vplo.size()) / 2;
    vplo = interpolate_pattern(vplo, nv);
    vphi = interpolate_pattern(vphi, nv);
    
    // reference length along the lateral curve
    Real lref = 0.5*norm(eval(0.0,0.0) - eval(0.0,1.0))
              + 0.5*norm(eval(1.0,0.0) - eval(1.0,1.0));
    
    uint nu(5);
    for (uint j=0; j<nv; ++j) {
      
      if (not bKink) {
        Real wref = norm(eval(0.0,vplo[j]) - eval(1.0,vphi[j])); 
        nu = max(3u, uint(nv*wref/lref));
      }
      
      for (uint i=0; i<nu; ++i) {
        Real u = (i + 0.5) / nu;
        Real v = (1.-u)*vplo[j] + u*vphi[j];
        msh.insertVertex( vct(u, v) );
      }
    }
  
  }
  
  // export and merge with global mesh
  PointList<2> dmy;
  Indices tri;
  msh.exportMesh(dmy, tri);
  gnr.importMesh(dmy, tri);
  gnr.disableBoundarySplit();*/
}

bool LongCapSurf::fixedMesh(PointList2d &puv, PointList3d &pts,
                            PointList3d &nrm, Indices &tri) const
{
  // manufacture a shared_ptr to this
  SurfacePtr psf((Surface *) this, null_deleter() );

  // initialize coarse mesh
  DnMesh mgen(psf, DnPlane);
  bool binit = mgen.initBoundary(m_bsegm);
  if (not binit)
    return false;

  // try to find a good pattern for vertex insertions
  // in the v-direction, that is along the boundary curves
  const uint nb(m_bsegm.size());
  Vector vplo, vphi;
  for (uint i=0; i<nb; ++i) {
    const Vct2 & pb(m_bsegm[i]);
    if (pb[0] < 0.5)
      vplo.push_back(pb[1]);
    else
      vphi.push_back(pb[1]);
  }
  sort_unique(vplo);
  sort_unique(vphi);

  // delete first and last value (0.0 and 1.0)
  vplo.pop_back();
  vplo.erase(vplo.begin());
  vphi.pop_back();
  vphi.erase(vphi.begin());

  // create 'mean' pattern
  uint nv = (vphi.size() + vplo.size()) / 2;
  vplo = resize_pattern(vplo, nv);
  vphi = resize_pattern(vphi, nv);

  // insert internal points in grid pattern
  uint nu = max(3u, nv/7);
  bool boundaryInsert;
  for (uint i=0; i<nu; ++i) {
    Real u = (i + 0.5) / nu;
    for (uint j=0; j<nv; ++j) {
      Real v = (1.-u)*vplo[j] + u*vphi[j];
      mgen.insertVertex( vct(u, v), boundaryInsert );
    }
  }
  mgen.exportMesh(puv, pts, nrm, tri);

  return true;
}

Vct2 LongCapSurf::boundaryProjection(const Vct3 & p) const
{
  if (norm(p - m_clo.eval(0.0)) < gmepsilon)
    return vct(0.5,0.0);
  else if (norm(p - m_clo.eval(1.0)) < gmepsilon)
    return vct(0.5,1.0);
  
  Real tlo = bproject(m_clo, p);
  Real thi = bproject(m_chi, p);
  Real dlo = norm(p - m_clo.eval(tlo));
  Real dhi = norm(p - m_chi.eval(thi));
  
  if (dlo < dhi) {
    if (tlo == 0.0 or tlo == 1.0)
      return vct(0.5, tlo);
    else
      return vct(0.0, tlo);
  } else {
    if (thi == 0.0 or thi == 1.0)
      return vct(0.5, thi);
    else
      return vct(1.0, thi);
  }
}

Real LongCapSurf::bproject(const Spline<3> & spl, const Vct3 & p) const
{
  // identify starting value
  Real df, t(0.5), lo(0.0), hi(1.0);
  
  Vct3 dp, dS;
  dp = p - spl.eval(lo);
  dS = spl.derive(lo);
  Real dflo = -2*dot(dp, dS);
  dp = p - spl.eval(hi);
  dS = spl.derive(hi);
  Real dfhi = -2*dot(dp, dS);
  
  if ( (dflo*dfhi) > 0.0 ) {
    return (fabs(dflo) < fabs(dfhi)) ? lo : hi;
  } else if (dflo > 0.0) {
    swap(lo, hi);
  }
  
  const Real ttol = 1e-7;
  while ( fabs(hi-lo) > ttol ) {
    t = 0.5*(lo + hi);
    dp = p - spl.eval(t);
    if (norm(dp) < gmepsilon)
      return t;
    
    dS = spl.derive(t);
    df = -2*dot(dp, dS);
    if (df < 0.0) 
      lo = t;
    else if (df > 0.0) 
      hi = t;
    else
      return t;
  }
  
  return t;
}

XmlElement LongCapSurf::toXml(bool) const
{
  assert(not "LongCapSurf does not support XML serialization.");
  XmlElement xe;
  return xe; 
}
    
void LongCapSurf::fromXml(const XmlElement &)
{
  assert(not "LongCapSurf does not support XML serialization.");
}

void LongCapSurf::writeViz(const std::string & fname) const
{
  SurfacePtr psf((Surface *) this, null_deleter() );
  DnMesh msh(psf, DnPlane);
  msh.init(6u, 25u);
  msh.toXml().write(fname, XmlElement::ZippedXml);
}

// void LongCapSurf::initMeshKinked(const DnRefineCriterion & c, DnMesh & gnr) const
// {
//   // extract v-coordinates on boundary
//   const uint nb(bsegm.size());
//   Vector vplo, vphi;
//   for (uint i=0; i<nb; ++i) {
//     const Vct2 & pb(bsegm[i]);
//     if (pb[0] < 0.5)
//       vplo.push_back(pb[1]);
//     else
//       vphi.push_back(pb[1]);
//   }
//   sort_unique(vplo);
//   sort_unique(vphi);
//   
//   // construct boundary to use for initialization
//   PointList<2> pbound;
//   pbound.push_back( vct(0.5, 0.0) );
//   for (uint i=1; i<vplo.size()-1; ++i)
//     pbound.push_back( vct(0.0, vplo[i]) );
//   pbound.push_back( vct(0.5, 1.0) );
//   for (uint i=1; i<vphi.size()-1; ++i)
//     pbound.push_back( vct(1.0, vphi[vphi.size()-1-i]) );
//   
//   // start to create a mesh from the kink (back)
//   Indices tri;
//   uint v[3], npb = pbound.size();
//   v[0] = 0;
//   v[1] = 1;
//   v[2] = npb-1;
//   tri.insert(tri.begin(), v, v+3);
//   
//   // sweep forward by selecting the smaller edge angle to continue
//   
//   
//   // check triangle directions before import
// }

void LongCapSurf::initMeshStd(const DnRefineCriterion &, DnMesh & gnr) const
{
  // manufacture a shared_ptr to this
  SurfacePtr psf((Surface *) this, null_deleter() );
  
  DnMesh msh(psf, DnPlane);
  msh.initBoundary(m_bsegm);
  
  // try to find a good pattern for vertex insertions
  // in the v-direction, that is along the boundary curves 
  const uint nb(m_bsegm.size());
  Vector vplo, vphi;
  for (uint i=0; i<nb; ++i) {
    const Vct2 & pb(m_bsegm[i]);
    if (pb[0] < 0.5)
      vplo.push_back(pb[1]);
    else
      vphi.push_back(pb[1]);
  }
  sort_unique(vplo);
  sort_unique(vphi);
  
  // delete first and last value (0.0 and 1.0)
  vplo.pop_back();
  vplo.erase(vplo.begin());
  vphi.pop_back();
  vphi.erase(vphi.begin());
  
  // create 'mean' pattern
  uint nv = (vphi.size() + vplo.size()) / 2;
  vplo = interpolate_pattern(vplo, nv);
  vphi = interpolate_pattern(vphi, nv);
  
  // reference length along the lateral curve
  Real lref = 0.5*norm(eval(0.0,0.0) - eval(0.0,1.0))
      + 0.5*norm(eval(1.0,0.0) - eval(1.0,1.0));
   
  uint nu(5);
  bool boundaryInsert;
  for (uint j=0; j<nv; ++j) {
    
    if (not m_bKink) {
      Real wref = norm(eval(0.0,vplo[j]) - eval(1.0,vphi[j])); 
      nu = max(3u, uint(nv*wref/lref));
    }
    
    for (uint i=0; i<nu; ++i) {
      Real u = (i + 0.5) / nu;
      Real v = (1.-u)*vplo[j] + u*vphi[j];
      msh.insertVertex( vct(u, v), boundaryInsert );
    }
  }
  
  // export and merge with global mesh
  PointList<2> dmy;
  Indices tri;
  msh.exportMesh(dmy, tri);
  gnr.importMesh(dmy, tri);
  gnr.cleanup(gmepsilon, 1.0);
}

