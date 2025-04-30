
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
 
#include <genua/xmlelement.h>
#include <genua/xcept.h>
#include "dnmesh.h"
#include "dnwingcriterion.h"
#include "dnrefine.h"

using namespace std;

void DnRefineCriterion::bind(const DnMesh *pm) const
{
  msh = pm;
}

void DnRefineCriterion::setDefault()
{
  maxlen = huge;
  minlen = 0.0;
  maxphi = PI/6.0;
  maxstretch = 100.0;
  mincosphi = cos(maxphi);
  nvmax = 1073741824u;
}

void DnRefineCriterion::setCriteria(Real lmax, Real lmin, 
                                    Real phimax, Real stretch, uint n)
{
  maxlen = lmax;
  minlen = lmin;
  maxphi = phimax;
  maxstretch = stretch;
  mincosphi = cos(maxphi);
  nvmax = n;
}

Real DnRefineCriterion::eval(const uint *vi) const
{
  assert(msh != 0);
  
  // invalid triangles are not refined
  if (vi[0] == NotFound)
    return 0.0;
  
  // fetch vertices
  const Vct3 & p1(msh->position(vi[0]));
  const Vct3 & p2(msh->position(vi[1]));
  const Vct3 & p3(msh->position(vi[2]));

  // compute edge lengths 
  Real len[3], lmax, lmin;
  len[0] = norm(p2-p1);
  len[1] = norm(p3-p1);
  len[2] = norm(p3-p2);
  lmax = max( len[0], max(len[1], len[2]) );
  lmin = min( len[0], min(len[1], len[2]) );
  // assert(lmin > 0);
  
  // do not refine if splitting longest edge would 
  // yield too short edges
  if (lmax < 2*minlen)
    return 0.0;

  // compute triangle area and stretch
  const Real sf(0.43301270189222); // sqrt(3)/4
  Vct3 ntri( cross(p2-p1, p3-p1) );
  Real area = 0.5*norm(ntri);
  assert(area > 0);
  Real stretch = sf*sq(lmax) / area;  

  // compute normal vector difference
  const Vct3 & n1(msh->normal(vi[0]));
  const Vct3 & n2(msh->normal(vi[1]));
  const Vct3 & n3(msh->normal(vi[2]));
  Real cphi[6], cphimin, acrit;
  cphi[0] = cosarg(n1, ntri);
  cphi[1] = cosarg(n2, ntri);
  cphi[2] = cosarg(n3, ntri);
  cphi[3] = cosarg(n1, n2);
  cphi[4] = cosarg(n1, n3);
  cphi[5] = cosarg(n2, n3);
  cphimin = *min_element(cphi, cphi+6);
  acrit = (1.0 + mincosphi) / (1.0 + gmepsilon + cphimin);

  const uint ncrit(3);
  Real crit[ncrit];
  crit[0] = lmax/maxlen;
  crit[1] = stretch/maxstretch;
  crit[2] = cb(acrit);
  
  // return worst violation
  return *(max_element(crit, crit+ncrit));
}
    
void DnRefineCriterion::globalScale(Real f)
{
  maxlen *= f;
  minlen *= f;
}

void DnRefineCriterion::fromXml(const XmlElement & xe)
{
  // make sure that only defined properties are active
  setDefault();
  
  if (xe.hasAttribute("maxphi")) {
    maxphi = rad( Float(xe.attribute("maxphi")) );
    maxphi = max( 0.01*PI, min(0.45*PI, maxphi) );
    mincosphi = cos(maxphi);
  } 
  if (xe.hasAttribute("maxlen")) 
    maxlen = Float(xe.attribute("maxlen"));  
  if (xe.hasAttribute("minlen")) 
    minlen = Float(xe.attribute("minlen"));
  if (xe.hasAttribute("maxstretch")) 
    maxstretch = Float(xe.attribute("maxstretch"));
  if (xe.hasAttribute("nvmax"))
    nvmax = Int(xe.attribute("nvmax"));
}

XmlElement DnRefineCriterion::toXml() const
{
  XmlElement xe("MeshCriterion");
  xe["maxphi"] = str(deg(maxphi));
  xe["maxlen"] = str(maxlen);
  xe["minlen"] = str(minlen);
  xe["maxstretch"] = str(maxstretch);
  xe["nvmax"] = str(nvmax);
  return xe;  
}

DnRefineCriterion *DnRefineCriterion::clone() const
{
  return (new DnRefineCriterion(*this));
}

DnRefineCriterionPtr DnRefineCriterion::createFromXml(const XmlElement & xe)
{
  DnRefineCriterionPtr rfp;
  
  // for historical reasons, mesh criteria may not be saved with 
  // different xml tags, so we need to determine the type heuristically
  string s = xe.name();
  if (s == "MeshCriterion") {
    if (xe.hasAttribute("lerfactor")) {
      DnWingCriterion *wcp = new DnWingCriterion;
      wcp->fromXml(xe);
      rfp = DnRefineCriterionPtr(wcp);
    } else {
      DnRegionCriterion *rcp = new DnRegionCriterion;
      rcp->fromXml(xe);
      rfp = DnRefineCriterionPtr(rcp);
    }
  } else if (s == "RegionCriterion") {
    DnRegionCriterion *rcp = new DnRegionCriterion;
    rcp->fromXml(xe);
    rfp = DnRefineCriterionPtr(rcp);
  } else if (s == "WingCriterion") {
    DnWingCriterion *wcp = new DnWingCriterion;
    wcp->fromXml(xe);
    rfp = DnRefineCriterionPtr(wcp);
  }
  
  return rfp;
}

// --------------------------------------------------------------------------

uint DnRegionCriterion::addRegion(const DnRefineRegion & rg)
{
  regions.push_back(rg);
  return regions.size()-1;
}

uint DnRegionCriterion::addRegion(const BndRect & rg, Real f)
{
  regions.push_back( DnRefineRegion(rg.lower(), rg.upper(), f) );
  return regions.size()-1;
}

void DnRegionCriterion::removeRegions(uint first, uint last)
{
  if (first >= last)
    return;
  
  assert(first < regions.size());
  assert(last <= regions.size());
  regions.erase(regions.begin()+first, regions.begin()+last);
}

void DnRegionCriterion::removeRegions(const Indices & idx)
{
  if (idx.empty())
    return;
  else if (idx.size() == 1) 
    regions.erase(regions.begin() + idx.front());
  else {
    DnRegionArray tmp;
    const uint nr(regions.size());
    for (uint i=0; i<nr; ++i) {
      if (find(idx.begin(), idx.end(), i) == idx.end())
        tmp.push_back(regions[i]);
    }
    regions.swap(tmp);
  }
}

Real DnRegionCriterion::eval(const uint *vi) const
{
  assert(msh != 0);
  
  // invalid triangles are not refined
  if (vi[0] == NotFound)
    return 0.0;
  
  // fetch vertices
  const Vct3 & p1(msh->position(vi[0]));
  const Vct3 & p2(msh->position(vi[1]));
  const Vct3 & p3(msh->position(vi[2]));

  // compute edge lengths 
  Real len[3], lmax, lmin;
  len[0] = norm(p2-p1);
  len[1] = norm(p3-p1);
  len[2] = norm(p3-p2);
  lmax = max( len[0], max(len[1], len[2]) );
  lmin = min( len[0], min(len[1], len[2]) );  
  // assert(lmin > 0);
  if (lmax < 2*minlen)
    return 0.0;

  // compute triangle area and stretch
  const Real sf(0.43301270189222); // sqrt(3)/4
  Vct3 ntri( cross(p2-p1, p3-p1) );
  Real area = 0.5*norm(ntri);
  assert(area > 0);
  Real stretch = sf*sq(lmax) / area;  
  
  // compute squared edge length of a equilateral triangle 
  // with the same area, stop if too small
  if (area < sf*sq(minlen))
    return 0.0;

  // compute normal vector difference
  const Vct3 & n1(msh->normal(vi[0]));
  const Vct3 & n2(msh->normal(vi[1]));
  const Vct3 & n3(msh->normal(vi[2]));
  Real cphi[6], cphimin, acrit;
  cphi[0] = cosarg(n1, ntri);
  cphi[1] = cosarg(n2, ntri);
  cphi[2] = cosarg(n3, ntri);
  cphi[3] = cosarg(n1, n2);
  cphi[4] = cosarg(n1, n3);
  cphi[5] = cosarg(n2, n3);
  cphimin = *min_element(cphi, cphi+6);
  acrit = (1.0 + mincosphi) / (1.0 + gmepsilon + cphimin);

  const uint ncrit(3);
  Real crit[ncrit];
  crit[0] = lmax/maxlen;
  crit[1] = stretch/maxstretch;
  crit[2] = cb(acrit);
  
  // check if triangle is in refinement region
  Real mxrf(0.0);
  const uint nr(regions.size());
  for (uint i=0; i<nr; ++i) {
    for (uint k=0; k<3; ++k) {
      const Vct2 & q(msh->parpos(vi[k]));
      mxrf = max(mxrf, regions[i].factor(q));
//       const Vct2 & q(msh->parpos(vi[k]));
//       if (regions[i].isInside(q))
//         mxrf = max(mxrf, rff[i]);
    } 
  }
  
  if (mxrf != 0.0) {
    crit[0] *= mxrf;
    crit[2] = pow(acrit, 3.*mxrf);
  }
  
  // return worst violation
  return *(max_element(crit, crit+ncrit));
}
    
void DnRegionCriterion::fromXml(const XmlElement & xe)
{
  // set global criteria first
  DnRefineCriterion::fromXml(xe);
  
  regions.clear();
  XmlElement::const_iterator ite;
  for (ite = xe.begin(); ite != xe.end(); ++ite) {
    if (ite->name() == "RefinementRegion") 
      regions.push_back(DnRefineRegion(*ite));
  }
}

XmlElement DnRegionCriterion::toXml() const
{
  XmlElement xe( DnRefineCriterion::toXml() );
  for (uint i=0; i<regions.size(); ++i) 
    xe.append(regions[i].toXml());
  return xe;  
}

DnRegionCriterion *DnRegionCriterion::clone() const
{
  return (new DnRegionCriterion(*this));
}

// --------------------------------------------------------------------------

Real DnYKinkCriterion::eval(const uint *vi) const
{
  assert(msh != 0);
  
  // invalid triangles are not refined
  if (vi[0] == NotFound)
    return 0.0;
  
  // fetch vertices
  const Vct3 & p1(msh->position(vi[0]));
  const Vct3 & p2(msh->position(vi[1]));
  const Vct3 & p3(msh->position(vi[2]));

  // compute edge lengths 
  Real len[3], lmax, lmin;
  len[0] = norm(p2-p1);
  len[1] = norm(p3-p1);
  len[2] = norm(p3-p2);
  lmax = max( len[0], max(len[1], len[2]) );
  lmin = min( len[0], min(len[1], len[2]) );  
  // assert(lmin > 0);
  if (lmax < 2*minlen)
    return 0.0;

  // compute triangle area and stretch
  const Real sf(0.43301270189222); // sqrt(3)/4
  Vct3 ntri( cross(p2-p1, p3-p1) );
  Real area = 0.5*norm(ntri);
  assert(area > 0);
  Real stretch = sf*sq(lmax) / area;  

  // if the triangle is too small by area, stop
  if (area < sf*sq(minlen))
    return 0.0;
  
  // The only difference to the region criterion is that here,
  // we assume that the surface has kinks in y-direction which should
  // not be refined. Normal vector angles are therefore computed for
  // the projection of normals on the xz-plane
  Vct3 n1(msh->normal(vi[0]));
  Vct3 n2(msh->normal(vi[1]));
  Vct3 n3(msh->normal(vi[2]));
  
  // project normals if triangle near kink
  const Real pdv(2e-4);
  bool onKink(false);
  const Vct2 & q1(msh->parpos(vi[0]));
  const Vct2 & q2(msh->parpos(vi[1]));
  const Vct2 & q3(msh->parpos(vi[2]));
  const uint nk(vkinks.size());
  for (uint k=0; k<nk; ++k) {
    Real vk(vkinks[k]);
    Real d1 = q1[1] - vk;
    Real d2 = q2[1] - vk;
    Real d3 = q3[1] - vk;
    if (fabs(d1) < pdv or fabs(d2) < pdv or fabs(d3) < pdv) {
      // one vertex is very close to kink
      onKink = true;
      break;
    } else if ((d1*d2) <= 0 or (d2*d3) <= 0 or (d1*d3) <= 0) {
      // at least one edge straddles kink
      onKink = true;
      break;
    }
  }
  
  if (onKink) {
    ntri[1] = 0.0;
    n1[1] = 0.0;
    n2[1] = 0.0;
    n3[1] = 0.0;
    
    // we need to be a little more generous with
    // the stretch ratio near a kink
    stretch *= 0.5;
  }
  
  Real cphi[6], cphimin, acrit;
  cphi[0] = cosarg(n1, ntri);
  cphi[1] = cosarg(n2, ntri);
  cphi[2] = cosarg(n3, ntri);
  cphi[3] = cosarg(n1, n2);
  cphi[4] = cosarg(n1, n3);
  cphi[5] = cosarg(n2, n3);
  cphimin = *min_element(cphi, cphi+6);
  acrit = (1.0 + mincosphi) / (1.0 + gmepsilon + cphimin);

  const uint ncrit(3);
  Real crit[ncrit];
  crit[0] = lmax/maxlen;
  crit[1] = stretch/maxstretch;
  crit[2] = cb(acrit);
  
//   // check if triangle is in refinement region
//   Real mxrf(0.0);
//   const uint nr(regions.size());
//   for (uint i=0; i<nr; ++i) {
//     for (uint k=0; k<3; ++k) {
//       const Vct2 & q(msh->parpos(vi[k]));
//       if (regions[i].isInside(q))
//         mxrf = max(mxrf, rff[i]);
//     } 
//   }
  
  Real mxrf(0.0);
  const uint nr(regions.size());
  for (uint i=0; i<nr; ++i) {
    for (uint k=0; k<3; ++k) {
      const Vct2 & q(msh->parpos(vi[k]));
      mxrf = max(mxrf, regions[i].factor(q));
    } 
  }
  
  if (mxrf != 0.0) {
    crit[0] *= mxrf;
    crit[2] = pow(acrit, 3.*mxrf);
  }
  
  // return worst violation
  return *(max_element(crit, crit+ncrit));
}

// --------------------------------------------------------------------------

Real DnStretchCriterion::eval(const uint *vi) const
{
  // invalid triangles are not refined
  if (vi[0] == NotFound)
    return 0.0;
  
  // fetch vertices
  const Vct3 & p1(msh->position(vi[0]));
  const Vct3 & p2(msh->position(vi[1]));
  const Vct3 & p3(msh->position(vi[2]));

  // compute edge lengths and stretch  
  const Real sf(0.43301270189222); // sqrt(3)/4
  Real len[3], lmax;
  len[0] = norm(p2-p1);
  len[1] = norm(p3-p1);
  len[2] = norm(p3-p2);
  lmax = max( len[0], max(len[1], len[2]) );
  
  // compute triangle area and stretch
  Real area = 0.5*norm( cross(p2-p1, p3-p1)  );
  if (area < gmepsilon)
    return huge;
  else
    return sf*sq(lmax) / area;  
}

// --------------------------------------------------------------------------

DnTriangleHeap::DnTriangleHeap(const DnCriterion & crit, 
                               const DnTriangleArray & t) 
  : triangles(t), cmp(crit,t)
{
  refill(); 
}

DnTriangleHeap::DnTriangleHeap(const DnCriterion & crit, const DnTriangleArray & t, 
                               const Indices & idx) : triangles(t), cmp(crit,t)
{  
  const uint nt(idx.size());
  for (uint i=0; i<nt; ++i) {
    const DnTriangle & tr(triangles[idx[i]]);
    if (tr.isValid() and cmp.eval(idx[i]) > 1.0) {
      iheap.push_back(idx[i]);
    }
  }
  std::make_heap(iheap.begin(), iheap.end(), cmp);    
}

void DnTriangleHeap::refill()
{
  iheap.clear();
  const uint nt(triangles.size());
  for (uint i=0; i<nt; ++i) {
    const DnTriangle & t(triangles[i]);
    if (t.isValid() and cmp.eval(i) > 1.0) {
      iheap.push_back(i);
    }
  }
  std::make_heap(iheap.begin(), iheap.end(), cmp);
}

void DnTriangleHeap::append(const Indices & idx)
{
  Indices tmp(iheap);
  tmp.insert(tmp.end(), idx.begin(), idx.end());
  sort_unique(tmp);
  iheap.clear();
  const uint nt(tmp.size());
  for (uint i=0; i<nt; ++i) {
    const DnTriangle & t(triangles[i]);
    if (t.isValid() and cmp.eval(i) > 1.0) {
      iheap.push_back(tmp[i]);
    }
  }    
  std::make_heap(iheap.begin(), iheap.end(), cmp);  
}

void DnTriangleHeap::print()
{
  for (uint i=0; i<iheap.size(); ++i) {
    cout << "iheap[" << i << "] : " << iheap[i] <<  ", criterion: ";
    cout << cmp.eval(iheap[i]) << endl;
  }
}

// --------------------------------------------------------------------------

static inline bool tqpair_less(const TqPair & a, const TqPair & b)
{
  return a.second < b.second;
}

DnTriangleQueue::DnTriangleQueue(const DnCriterion & c, 
                                 const DnTriangleArray & t) :
    triangles(t), crit(c) 
{
  refill();
}
      
void DnTriangleQueue::refill()
{
  irf.clear();
  const uint nt(triangles.size());
  for (uint i=0; i<nt; ++i) {
    const DnTriangle & t(triangles[i]);
    if (t.isValid()) {
      Real cval = crit.eval(t.vertices());
      if (cval > 1.0) 
        irf.push_back( TqPair(i, cval) );
    }
  }
  std::sort(irf.begin(), irf.end(), tqpair_less);
}

