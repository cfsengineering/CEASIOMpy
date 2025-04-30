
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
 
#include <list>

#include <boost/utility.hpp>
#include <genua/pattern.h>
#include <genua/boxsearchtree.h>
#include <genua/lls.h>
#include "sides.h"
#include "surface.h"
#include "linearsurf.h"
#include "dnmesh.h"
#include "dnrefine.h"
#include "dnboxadaptor.h"
#include "intersect.h"
#include "meshpatch.h"

using namespace std;

// write to file if debugging active
#ifndef NDEBUG
static void dbStoreMesh(const DnMesh & m, const string & fname)
{
  m.toXml().write(fname, XmlElement::ZippedXml);
}
#else
static void dbStoreMesh(const DnMesh&, const string &) {}
#endif

// ----------------------------------------------------------------------------

void MeshPatch::addConstraints(const PointList<2> & c)
{
  if (stc.empty()) {
    stc.push_back(c);
    return;
  }

#ifndef NDEBUG
  // check for NaN
  for (uint i=0; i<c.size(); ++i)
    assert(norm(c[i]) == norm(c[i]));
#endif

  stc.push_back(c);
}

void MeshPatch::addIntersections(const IsecSet & isl)
{
  const uint ni(isl.size());
  
  IpointSet ips;
  convert(isl, ips);
  
  for (uint i=0; i<ni; ++i) {
    
    PointList<2> cpt;
    PointList<3> rpt;
    filterConstraint(isl[i], cpt, rpt);
    
    rpp.insert(rpp.end(), rpt.begin(), rpt.end());
    ipl.push_back(cpt);
  }
}

void MeshPatch::premesh(const DnRefineCriterion & crit, bool psm)
{
  // use custom initialization
  DnMesh gnr(srf, DnSpatial);
  srf->initMesh(crit, gnr);
  dbStoreMesh(gnr, srf->name()+"Init.msh");
  
  // refine and smooth
  gnr.refine(crit);
  if (psm)
    gnr.smooth(2, 0.25);
  dbStoreMesh(gnr, srf->name()+"Premesh.msh");
  
  // copy mesh vertices
  clear();
  Indices tri;
  gnr.exportMesh(ppt, vtx, nrm, tri);
  
  // generate triangles
  const uint nf(tri.size()/3);
  for (uint i=0; i<nf; ++i) {
    uint k = 3*i;
    TriMesh::addFace(tri[k], tri[k+1], tri[k+2]);
  }
  fixate();
}

MgError MeshPatch::mesh(const DnRefineCriterion & crit, bool psm, bool pir)
{
  DnMesh gnr(srf, DnSpatial);
  srf->initMesh(crit, gnr);
  
  // refine  first, before constraint insertion
  gnr.refine(crit);
  dbStoreMesh(gnr, srf->name()+"PreInsert.msh");
  
  // introduce intersection constraints
  Indices csi, idx;
  for (uint i=0; i<ipl.size(); ++i) {
    idx = gnr.addConstraint( ipl[i] );
    if (idx.empty()) {
      dbStoreMesh(gnr, srf->name()+"InsertionFailed.msh");
      return MgCollidingIntersections;
    }
    assert(idx.size() == ipl[i].size());
    csi.insert(csi.end(), idx.begin(), idx.end());
  }
  
  // introduce structural constraints 
  for (uint i=0; i<stc.size(); ++i) {
    idx = gnr.addConstraint( stc[i] );
    if (idx.empty()) {
      dbStoreMesh(gnr, srf->name()+"InsertionFailed.msh");
      return MgCollidingIntersections;
    }
    assert(idx.size() == stc[i].size());
  }
  
  // debug: check boundary size
  if (csi.size() != rpp.size()) {
    clog << "Warning: " << rpp.size() << " replacement "
        << "points for " << csi.size() << " constrained vertices on "
        << srf->name() << endl;
    
    return MgBoundaryReplacementMismatch;
  }
  
  // eliminate stretched triangles after constraint insertion
  gnr.smoothStretched(crit.maxStretch());    
  
  // refinement after constraint insertion often fails 
  // with unnecessary radical refinements near constrained edges
  if (pir) {
    DnRefineCriterionPtr cpost(crit.clone());
    cpost->maxStretch(huge);
    gnr.refine(*cpost);
    // gnr.refine(crit);
    gnr.smoothStretched(crit.maxStretch());
    if (psm) {
      gnr.smooth(2, 0.25);
    }
  }
  dbStoreMesh(gnr, srf->name()+"PostInsert.msh");
  
  // add hole markers
  for (uint i=0; i<holes.size(); ++i) 
    gnr.addHole( holes[i] );
  
  // copy mesh vertices
  clear();
  Indices tri;
  gnr.exportMesh(ppt, vtx, nrm, tri);
  
  // perform vertex replacements
  assert(rpp.size() == csi.size());
  const uint nr(csi.size());
  for (uint i=0; i<nr; ++i) 
    vtx[csi[i]] = rpp[i];
  
  // generate triangles
  const uint nf(tri.size()/3);
  for (uint i=0; i<nf; ++i) {
    uint k = 3*i;
    TriMesh::addFace(tri[k], tri[k+1], tri[k+2]);
  }
  fixate();
  return MgSuccess;
}

MgError MeshPatch::meshCoarse(const DnRefineCriterion & crit)
{
  // merge constraints
  vector<PointList<2> > allc(ipl);
  allc.insert(allc.end(), stc.begin(), stc.end());
  
  Indices csi;
  DnMesh gnr(srf, DnSpatial);
  if (allc.empty()) {
    // simple case if no constraints
    srf->initMesh(crit, gnr);
  } else {
    // manually create an initial grid mesh
    PointGrid<2> qts;
    Real lmax = crit.maxLength();
    Real lmin = crit.minLength();
    Real phimax = min(rad(45.), crit.maxPhi());
    srf->initGrid(lmax, lmin, phimax, qts);
    gnr.init(qts);
    gnr.elimNeedles(1.5*crit.maxStretch(), 0.5*crit.maxPhi());
    const uint nr(qts.nrows());
    const uint nc(qts.ncols());
    
    // define the regions to refine - align with existing grid
    // FIXME : Will not work if several intersections overlap 
    //         in v-direction (may happen for fuselage bodies)
    Vct2 plo, phi;
    DnBoxAdaptor bxa(crit); 
    Indices ccols;
    vector<BndRect> bbs;
    for (uint i=0; i<allc.size(); ++i) {
      BndRect b;
      b.findBndRect(allc[i]);
      plo = b.lower();
      phi = b.upper();
      for (uint j=1; j<nc; ++j) {
        Real v1 = qts(0,j-1)[1];
        Real v2 = qts(0,j)[1];
        if (v1 < plo[1] and v2 > plo[1]) {
          plo[1] = v1 + 1e-5;
          ccols.push_back(j-1);
        } 
        if (v1 < phi[1] and v2 > phi[1]) {
          phi[1] = v2 - 1e-5;
          ccols.push_back(j);
        }
      }
      plo[0] = 0.0;
      phi[0] = 1.0;
      b = BndRect(plo, phi);
      bxa.addBox(b);
      bbs.push_back(b);
    }
    sort_unique(ccols);
    
    // constrain grid columns
    PointList<2> ccon(nr);
    for (uint j=0; j<ccols.size(); ++j) {
      for (uint i=0; i<nr; ++i)
        ccon[i] = qts(i,ccols[j]);
      gnr.addConstraint(ccon);
    }
    
    // refine regions affected by constraints
    gnr.refine(bxa);
    dbStoreMesh(gnr, srf->name()+"PreInsert.msh");
    
    // process actual constraints
    Indices idx;
    for (uint i=0; i<ipl.size(); ++i) {
      idx = gnr.addConstraint( ipl[i] );
      if (idx.empty()) {
        dbStoreMesh(gnr, srf->name()+"InsertionFailed.msh");
        return MgCollidingIntersections;
      }
      csi.insert(csi.end(), idx.begin(), idx.end());
    }
    for (uint i=0; i<stc.size(); ++i) {
      idx = gnr.addConstraint( stc[i] );
      if (idx.empty()) {
        dbStoreMesh(gnr, srf->name()+"InsertionFailed.msh");
        return MgCollidingIntersections;
      }
    }
    
    // no postrefinement : focus is on coarse mesh
    gnr.smoothStretched(crit.maxStretch(), bbs);
    dbStoreMesh(gnr, srf->name()+"PostInsert.msh");
  }
  
  // copy result after constraint processing
  clear();
  Indices tri;
  gnr.exportMesh(ppt, vtx, nrm, tri);
  
  // perform vertex replacements
  if (csi.size() != rpp.size()) {
    clog << "Warning: " << rpp.size() << " replacement "
        << "points for " << csi.size() << " constrained vertices on "
        << srf->name() << endl;
    return MgBoundaryReplacementMismatch;
  }
  assert(rpp.size() == csi.size());
  const uint nr(csi.size());
  for (uint i=0; i<nr; ++i) 
    vtx[csi[i]] = rpp[i];
  
  // generate triangles
  const uint nf(tri.size()/3);
  for (uint i=0; i<nf; ++i) {
    uint k = 3*i;
    TriMesh::addFace(tri[k], tri[k+1], tri[k+2]);
  }
  fixate();
  return MgSuccess;
}

void MeshPatch::convert(const IsecLine & line, PointList<2> & pts) const
{
  pts.resize(line.size());
  for (uint i=0; i<line.size(); ++i)
    pts[i] = line[i].parameter(this);
}

void MeshPatch::convert(const IsecSet & isl, IpointSet & pts) const
{
  pts.resize(isl.size());
  for (uint i=0; i<isl.size(); ++i)
    convert(isl[i], pts[i]);
}

void MeshPatch::fixate()
{
  TriMesh::fixate();
  tree = BSearchTree(vtx);
}

void MeshPatch::filterConstraint(const IsecLine & isl, 
                                 PointList<2> & cpt, PointList<3> & rpt) const
{
  cpt.clear();
  rpt.clear();
  
  PointList<2> ipt;
  convert(isl, ipt);
  
  // simplest version - boundary crossing not handled
  Real mlen(huge);
  const uint np(isl.size());
  cpt.reserve(np);
  rpt.reserve(np);
  cpt.push_back(ipt[0]);
  rpt.push_back(isl[0].midpoint());
  for (uint i=1; i<np; ++i) {
    cpt.push_back(ipt[i]);
    rpt.push_back(isl[i].midpoint());
    mlen = min(mlen, norm(rpt[i] - rpt[i-1]));
  }
  
  // replace almost-on-boundary points 
  for (uint i=0; i<np; ++i) {
    Real u = cpt[i][0];
    Real v = cpt[i][1];
    if (u < gmepsilon)
      u = 0.0;
    if (u > 1.0-gmepsilon)
      u = 1.0;  
    if (v < gmepsilon)
      v = 0.0;
    if (v > 1.0-gmepsilon)
      v = 1.0;
    cpt[i][0] = u;
    cpt[i][1] = v;  
  }
  
  // merge first and last point of loop constraints
  Real sloopgap = norm(rpt.front() - rpt.back());
  Real ploopgap = norm(cpt.front() - cpt.back());
  if (sloopgap < 0.5*mlen and ploopgap < 1e-4) {
    cpt.front() = cpt.back() = 0.5*(cpt.front() + cpt.back());
    rpt.front() = rpt.back() = 0.5*(rpt.front() + rpt.back());
    // cout << "pLoop identified, rpt at " << rpt.front() << endl;
  } else if (sloopgap < 0.125*mlen) {
    rpt.front() = rpt.back() = 0.5*(rpt.front() + rpt.back());
    // cout << "sLoop identified, rpt at " << rpt.front() << endl;
  } else {
    // cout << "Not a loop, sgap " << sloopgap << " pgap " << ploopgap;
    // cout << " mlen " << mlen << endl;
  }
}

void MeshPatch::boundaryPoints(side_t s, Indices & si) const
{
  // identify all vertices on side s 
  si.clear();
  const int nv(ppt.size());
  
  Real t;
  const Real tol(gmepsilon);
  switch (s) {
    
    case west:
      for (int i=0; i<nv; ++i) {
        t = ppt[i][0];
        if (t < tol)
          si.push_back(i);
      }
      break;
      
    case north:
      for (int i=0; i<nv; ++i) {
        t = ppt[i][1];
        if (1-t < tol)
          si.push_back(i);
      }
      break;
      
    case east:
      for (int i=0; i<nv; ++i) {
        t = ppt[i][0];
        if (1-t < tol)
          si.push_back(i);
      }
      break;
      
    case south:
      for (int i=0; i<nv; ++i) {
        t = ppt[i][1];
        if (t < tol)
          si.push_back(i);
      }
      break;
      
    default:
      break;  
  }
  
  // sort depending on side 
  if (s == south or s == north) {
    BndCompare<0> cmp(ppt);
    std::sort(si.begin(), si.end(), cmp);  
  } else {
    BndCompare<1> cmp(ppt);
    std::sort(si.begin(), si.end(), cmp);
  }
}
