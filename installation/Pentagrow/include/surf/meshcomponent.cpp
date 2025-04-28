
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
 
#include "meshcomponent.h"
#include "dnboxadaptor.h"
#include "dnrefine.h"
#include <genua/point.h>
#include <genua/dbprint.h>

using namespace std;

MeshComponent::MeshComponent(const SurfacePtr & s) : TriMesh(),
  psf(s), mg(s, DnSpatial), pcrit(new DnRefineCriterion),
  wSmooth(0.25), rKinkLimit(0.25*PI), nSmooth(2), iTag(NotFound),
  bFreshMesh(false), bRefine(true), bStretchedMesh(false) {}

MeshComponent::MeshComponent(const SurfacePtr & s,
                             const DnRefineCriterionPtr & pc) :
    TriMesh(),psf(s), mg(s, DnSpatial), pcrit(pc),
    wSmooth(0.25), rKinkLimit(0.25*PI), nSmooth(2), iTag(NotFound),
    bFreshMesh(false), bRefine(true), bStretchedMesh(false) {}

void MeshComponent::premesh(const PointGrid<2> & pgi)
{
  assert(pcrit);
  clear();
  
  // we will make constraint node indices meaningless
  icon.clear();
  
  // use custom initialization
  if (pgi.empty()) {
    psf->initMesh(*pcrit, mg);
  } else {
    mg.init(pgi, pcrit->maxStretch());
  }
  dbStoreMesh(psf->name()+"Init.msh");
  
  // before calling refine the first time,
  // we must mark kinks
  if (rKinkLimit < PI)
    mg.markKinks(rKinkLimit);
  
  // refine and smooth
  if (bRefine and (not bStretchedMesh)) 
    mg.iterativeRefine(*pcrit);
  if (not bStretchedMesh)
    mg.smooth(nSmooth, wSmooth);
  dbStoreMesh(psf->name()+"Premesh.msh");
  
  transfer();
  bFreshMesh = true;
}

void MeshComponent::premesh(const PointList<2> & pp, const Indices & tri)
{
  clear();

  // we will make constraint node indices meaningless
  icon.clear();

  // use custom initialization
  mg.importMesh(pp, tri);
  dbStoreMesh(psf->name()+"Init.msh");

  // before calling refine the first time,
  // we must mark kinks
  if (rKinkLimit < PI)
    mg.markKinks(rKinkLimit);

  transfer();
  bFreshMesh = true;
}

bool MeshComponent::constrain(const PointList<2> & uvc, const PointList<3> & rep)
{
  // debug
  dbprint("Constraining:", psf->name());

  assert(uvc.size() == rep.size());
  
  Indices idx = mg.addConstraint(uvc, false);
  if (idx.empty()) {
    dbprint( mg.lastError() );
    dbStoreMesh(psf->name()+"ConstrainFailed.xml");  
    return false;
  }
  dbStoreMesh(psf->name()+"Constrained.msh");
  
  assert(idx.size() == uvc.size());
  icon.push_back(idx);
  pcon.push_back(uvc);
  rcon.push_back(rep);
  
  return true;
}

bool MeshComponent::reconstrain()
{
  assert(pcon.size() == rcon.size());
  const int nc = pcon.size();
  if (nc == 0)
    return true;
  
  // parametrization may have changed
  for (int ic=0; ic<nc; ++ic) {
    const int n = pcon[ic].size();
    for (int i=0; i<n; ++i) {
      Vct2 qn, qp;
      qn = qp = pcon[ic][i];
      Vct3 rp = rcon[ic][i];
      Real pdist = norm(rp - psf->eval(qp[0], qp[1]));
      if (psf->project(rp, qn)) {
        Real ndist = norm(rp - psf->eval(qn[0], qn[1]));
        if (ndist < pdist) {
          pcon[ic][i] = qn;
          // dbprint("OK: ",ndist," < ",pdist);
        } else {
          // dbprint("No decrease: ",ndist," > ",pdist);
        }
      }
#ifndef NDEBUG
      else {
        Real ndist = norm(rp - psf->eval(qn[0], qn[1]));
        cerr << "Pj failed at " << qp << ", " << pdist << " : " << ndist << endl;
        if (qp[1] == 0.0) {
          cerr << "psf(u,0): " << psf->eval(qp[0], 0.0) << endl;
          cerr << "rcon    : " << rp << endl;
          cerr << "<r,Sv>  : " << dot(psf->derive(qp[0],qp[1],0,1),
                                      rp-psf->eval(qp[0], 0.0)) << endl;
        }
      }
#endif
    }
  }

  icon.resize(nc);
  for (int i=0; i<nc; ++i) {
    Indices idx = mg.addConstraint(pcon[i], false);
    if (idx.empty()) {
      dbprint( mg.lastError() );
      dbStoreMesh(psf->name()+"ConstrainFailed.xml");
      return false;
    }
    icon[i].swap(idx);
  }

  dbStoreMesh(psf->name()+"ReConstrained.msh");
  return true;
}

bool MeshComponent::insertBoundaryPoints(const PointList<2> & uvc, 
                                         const PointList<3> & rep)
{
  const Real ptol = 1e-7;
  const int np = uvc.size();
  assert(rep.size() == uvc.size());
  
  mg.enableBoundarySplit();
  Indices idx(np);
  for (int i=0; i<np; ++i) {
    uint ix = mg.insertBoundaryVertex(uvc[i], ptol);
    if (ix == NotFound) {
      cout << "Failed to insert " << uvc[i] << " at "<< rep[i] << endl;
      dbStoreMesh(psf->name()+"BndInsertFailed.xml");
      return false;
    }
//    cout << "Inserted " << rep[i] << " as " << ix << endl;
    idx[i] = ix;
  }
  dbStoreMesh(psf->name()+"BndInsert.xml");
  
  pcon.push_back(uvc);
  rcon.push_back(rep);
  icon.push_back(idx);
  mg.disableBoundarySplit();
  
  return true;
}

void MeshComponent::refine()
{
  assert(pcrit);

  if ((not bStretchedMesh) or (not icon.empty()))
    mg.smooth(nSmooth, wSmooth);
  if (bRefine and (not bStretchedMesh)) {
    mg.smoothStretched( pcrit->maxStretch() );
    mg.iterativeRefine(*pcrit);
    mg.smoothStretched( pcrit->maxStretch() );
    mg.smooth(nSmooth, wSmooth);
    dbStoreMesh(psf->name()+"Refined.msh");
  }

  transfer();
}
    
void MeshComponent::refineAround(const Indices & vlist)
{
  assert(pcrit);

  if ((not bStretchedMesh) or (not icon.empty()))
    mg.smooth(nSmooth, wSmooth);
  if (bRefine and (not bStretchedMesh)) {
    mg.refineAround(vlist, *pcrit);
    mg.smooth(nSmooth, wSmooth);
    dbStoreMesh(psf->name()+"Refined.msh");
  }

  transfer();
}
    
void MeshComponent::adapt()
{
  // child classes may need to adapt geometry and/or mesh depending
  // on parent objects etc.
}

void MeshComponent::genStretched()
{
  if (pcon.empty()) {
    psf->initMesh(*pcrit, mg);
  } else {
    
    // manually create an initial grid mesh
    PointGrid<2> qts;
    Real lmax = pcrit->maxLength();
    Real lmin = pcrit->minLength();
    Real phimax = min(rad(45.), pcrit->maxPhi());
    psf->initGrid(lmax, lmin, phimax, qts);
    mg.init(qts);
    mg.elimNeedles(1.5*pcrit->maxStretch(), 0.5*pcrit->maxPhi());
    
    // define the regions to refine - align with existing grid
    // FIXME : Will not work if several intersections overlap 
    //         in v-direction (may happen for fuselage bodies)
    const uint nr(qts.nrows());
    const uint nc(qts.ncols());
    Vct2 plo, phi;
    DnBoxAdaptor bxa(*pcrit); 
    Indices ccols;
    vector<BndRect> bbs;
    for (uint i=0; i<pcon.size(); ++i) {
      BndRect b;
      b.findBndRect(pcon[i]);
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
      mg.addConstraint(ccon);
    }
    
    // refine regions affected by constraints
    mg.refine(bxa);
  
    // insert actual constraints
    reconstrain();
  }
  
  transfer();
}
    
void MeshComponent::transfer()
{
  TriMesh::clear();
  
  Indices qtri;
  const int nf = mg.exportMesh(ppt, TriMesh::vertices(),
                               TriMesh::normals(), qtri);
  
  dbprint("transfer() for ", psf->name());

  // replace constrained vertices
  for (uint j=0; j<icon.size(); ++j) {
    const int n = icon[j].size();
    assert(rcon[j].size() == uint(n));
    for (int i=0; i<n; ++i) {

      // debug
      Real dst = norm( TriMesh::vertex(icon[j][i]) - rcon[j][i] );
      if (dst > 1e-3)
        dbprint("***!* Replacing", TriMesh::vertex(icon[j][i]), ", dist", dst);
      TriMesh::vertex(icon[j][i]) = rcon[j][i];
    }
  }
  
  for (int i=0; i<nf; ++i)
    TriMesh::addFace( qtri[3*i], qtri[3*i+1], qtri[3*i+2] );

  TriMesh::fixate();
}

uint MeshComponent::fixNormals()
{
  uint nfixed = 0;
  if (not psf)
    return 0;

  const int nf = nfaces();

#pragma omp parallel for
  for (int i=0; i<nf; ++i) {
    const uint *vi = face(i).vertices();
    Vct3 tn = cross( vtx[vi[1]]-vtx[vi[0]], vtx[vi[2]]-vtx[vi[0]] );
    Vct2 mp = (ppt[vi[0]] + ppt[vi[1]] + ppt[vi[2]]) / 3.0;
    Vct3 sn = psf->normal( mp[0], mp[1] );
    if ( dot(sn, tn) < 0.0 ) {
      face(i).reverse();
#pragma omp atomic
      ++nfixed;
    }
  }

  return nfixed;
}

void MeshComponent::boundary(side_t s, Indices & si) const
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

void MeshComponent::clear()
{
  TriMesh::clear();
  ppt.clear();
//   pcon.clear();
//   rcon.clear();
//   icon.clear();
  mg = DnMesh(psf, DnSpatial);
}

void MeshComponent::registerNeighbor(const MeshComponent *nb)
{
  insert_once(tnb, nb);
//  vector<const MeshComponent*>::iterator pos;
//  pos = lower_bound(tnb.begin(), tnb.end(), nb);
//  if (pos == tnb.end() or *pos != nb) {
//    tnb.insert(pos, nb);
//  }
}

bool MeshComponent::isNeighbor(const MeshComponent *a) const
{
  return binary_search(tnb.begin(), tnb.end(), a);
}

void MeshComponent::registerParent(const MeshComponent *nb)
{
  insert_once(parents, nb);
//  vector<const MeshComponent*>::iterator pos;
//  pos = lower_bound(parents.begin(), parents.end(), nb);
//  if (pos == parents.end() or *pos != nb) {
//    tnb.insert(pos, nb);
//  }
}

bool MeshComponent::isParent(const MeshComponent *a) const
{
  return binary_search(parents.begin(), parents.end(), a);
}

#ifndef NDEBUG
void MeshComponent::dbStoreMesh(const std::string & fname) const
{
  mg.toXml().write(fname, XmlElement::ZippedXml);
}
#else
void MeshComponent::dbStoreMesh(const std::string &) const
{}
#endif
