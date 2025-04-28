
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
 
#include <genua/xcept.h>
#include <genua/xmlelement.h>
#include <genua/strutils.h>
#include <genua/meshfields.h>
#include "patchmerger.h"
#include "intersect.h"
#include "roundcapsurf.h"
#include "longcapsurf.h"

using namespace std;

// ---------------- PatchMerger ------------------------------------------

uint PatchMerger::addSurface(const SurfacePtr & srf, const DnRegionCriterionPtr & tq)
{
  // store a copy of the mesh criterion so that we can modify it internally
  surfaces.push_back(srf);
  mcrits.push_back( DnRegionCriterionPtr(tq->clone()) );
  noreg.push_back(mcrits.back()->nregions());
  
  MeshPatchPtr mp(new MeshPatch(srf));
  patches.push_back(mp);

  return patches.size()-1;
}

void PatchMerger::premesh(uint i, bool psm) 
{
//   clog << "Premeshing surface '" << surfaces[i]->name();
//   if (psm)
//     clog << "'  (balancing)... ";
//   else
//     clog << "'  ... ";
  patches[i]->premesh(*mcrits[i], psm);
//  clog << patches[i]->nfaces() << " triangles." << endl;
}

void PatchMerger::addConstraints(uint i, const PointList<2> & c)
{
  assert(i < patches.size());
  patches[i]->addConstraints(c);
}

bool PatchMerger::findIntersections(uint i, uint j,
                                    IsecTopology & si, IsecTopology & sj,
                                    MeshFields & itrack)
{
  assert(i < patches.size());
  assert(j < patches.size());
  assert(j > i);

  // since meshes of adjacent surfaces are (in general) generated with
  // different criteria, we pick the more stringent of each pair to
  // process the intersection lines
  Real minlen = sqrt(mcrits[i]->minLength() * mcrits[j]->minLength());
  Real maxphi = min(mcrits[i]->maxPhi(), mcrits[j]->maxPhi());
  maxphi = min( rad(15.), maxphi );
  
  // parameter values smaller than this will be considered
  // exactly on the boundary
  const Real ptol = 1e-4; 
  
  Intersector isec(patches[i].get(), patches[j].get());
  isec.findIntersections(0.01*minlen);
  //const IsecSet & isl( isec.findIntersections(0.01*minlen) );
  
  // determine bounding boxes for intersections for later refinement 
  if (patches[i].get() < patches[j].get()) {
    isec.boxes( si.bb, sj.bb );
    isec.locateXsrSpots(40.0, si.xsa, sj.xsa);
  } else {
    isec.boxes( sj.bb, si.bb );
    isec.locateXsrSpots(40.0, sj.xsa, si.xsa);
  }
  
  const IsecSet & isl( isec.reduce(maxphi, 0.5*minlen, ptol) );
  
  if (not isl.empty())
    haveIsecs = true;
  
  Real tol = max(gmepsilon, 0.01*minlen);
  bool lclosed = isec.closedLoops(tol);
  bool lconnect = isec.connectedLines(tol);
  bool lbound = isec.endsOnBoundaries(ptol);
  bool lacceptable = lclosed or lconnect or lbound;
  
#ifndef NDEBUG
  clog << "Intersections closed: " << lclosed 
       << " connected: " << lconnect
       << " on boundaries: " << lbound << endl;
  
  MeshFields dbviz;
  dbviz.addMesh(*patches[i]);
  dbviz.addMesh(*patches[j]);
  isec.addViz(dbviz);
  string isname("Is");
  isname += patches[i]->surface()->name();
  isname += patches[j]->surface()->name();
  isname += ".xml";
  dbviz.toXml().write(isname, XmlElement::ZippedXml);
#endif
  
  // if this did not work, see if we can bind some
  // loose end together
  if (not lacceptable) {
    isec.sortLooseLines(ptol);
    Indices lei, lej;
    const uint nl(isl.size());
    for (uint ki=0; ki<nl; ++ki) {
      for (uint kj=ki+1; kj<nl; ++kj) {
        if (isec.openLeadingEdge(ki,kj,ptol)) {
          lei.push_back(ki);
          lej.push_back(kj);
        }
      }
    }
    isec.connectLeadingEdge(lei, lej);
  
    // see if this helped 
    lclosed = isec.closedLoops(tol);
    lconnect = isec.connectedLines(tol);
    lbound = isec.endsOnBoundaries(ptol);
    lacceptable = lclosed or lconnect or lbound;
  }
    
  // still not acceptable - try to join seamlines 
  if ((not lacceptable) and (not lclosed)) {
    // uint nfop = isec.joinSeamLines(tol, ptol);
    // clog << "Joined " << nfop << " seam lines." << endl;
  
    // see if this helped 
    lclosed = isec.closedLoops(tol);
    lconnect = isec.connectedLines(tol);
    lbound = isec.endsOnBoundaries(ptol);
    lacceptable = lclosed or lconnect or lbound;
  }
  
  if (not lacceptable) {
    
    // append visualization to itrack if failed
    itrack.clear();
    itrack.addMesh(*patches[i]);
    itrack.addMesh(*patches[j]);
    isec.addViz(itrack);
    
    si.shape = sj.shape = IsSpatialLoopNotClosed;
    return false;
  }
  
  // all intersections succeeded, propagate to MeshPatch
  si.shape = sj.shape = IsUnclassified;
  patches[i]->addIntersections(isl);
  patches[j]->addIntersections(isl);
  
  return true;
}

void PatchMerger::resetRegions(uint i)
{
  assert(i < mcrits.size());
  DnRegionCriterion & crit(*mcrits[i]);
  if (crit.nregions() > noreg[i])
    crit.removeRegions(noreg[i], crit.nregions());
}

void PatchMerger::refineIntersectionRegions(uint i, uint j, Real rf,
                                              const IsecTopology & si,
                                              const IsecTopology & sj)
{
  assert(si.bb.size() == sj.bb.size());
  const uint nr(si.bb.size());
  
  // remove existing regions if necessary
  resetRegions(i);
  resetRegions(j);

  // add regions to meshing criterions
  for (uint k=0; k<nr; ++k) {
    BndRect bbi(si.bb[k]);
    bbi.expand( 1.2*bbi.width(), 1.2*bbi.height() );
    mcrits[i]->addRegion(bbi, rf);

    BndRect bbj(sj.bb[k]);
    bbj.expand( 1.2*bbj.width(), 1.2*bbj.height() );
    mcrits[j]->addRegion(bbj, rf);
  }
}

void PatchMerger::refineRegion(uint i, const DnRefineRegion & rg)
{
  assert(i < mcrits.size());
  mcrits[i]->addRegion(rg);
}

void PatchMerger::resetMeshCriteria()
{
  const uint nc(mcrits.size());
  for (uint i=0; i<nc; ++i)
    resetRegions(i);
}

MgError PatchMerger::mainPass(uint i, bool psm, bool xcoarse, bool pir)
{
  MeshPatchPtr mp(patches[i]);
  SurfacePtr srf(surfaces[i]);

//   clog << "Refining surface '" << surfaces[i]->name();
//   if (psm)
//     clog << "'  (balancing)... "  << endl;
//   else
//     clog << "'  ... " << endl;
  
  if (xcoarse)
    return mp->meshCoarse(*mcrits[i]);
  else
    return mp->mesh(*mcrits[i], psm, pir);
}

bool PatchMerger::finalize()
{
  // merge external triangles of all patches
  TriMesh::clear();
  const uint np(patches.size());
  for (uint i=0; i<np; ++i) {
    TriMesh::merge(*patches[i]);
//     clog << "Merged patch '" << surfaces[i]->name() << "' with ";
//     clog << patches[i]->nfaces() << " triangles ";
//     clog << "( " << nfaces() << " )" << endl;
  }
  
  bool mok(true);
  if (haveIsecs) {
    
    // identify a vertex which is definitely on the
    // external surface, i.e. not on one of the interior parts
    Real xmin(huge);
    uint nt(nfaces()), tstart(0);
    for (uint i=0; i<nt; ++i) {
      Vct3 ctr( TriMesh::face(i).center() );
      if (ctr[0] < xmin) {
        xmin = ctr[0];
        tstart = i;
      }
    }
    
    // drop internal triangles 
    Real slen = 0.5 * TriMesh::shortestEdgeLength();
    mok = TriMesh::mergeAndDrop(tstart, gmepsilon, slen);
    if (mok) {
      TriMesh::joinSingleEdges(slen);
    }
    
  } else {
    
    // no intersection -- just cleanup seam line
    TriMesh::cleanup( gmepsilon );
  }
  
#ifndef NDEBUG
  TriMesh::toXml(true).write("Finalized.msh", XmlElement::ZippedXml);
#endif
  
  return mok;
}

bool PatchMerger::closeHoles()
{
  // identify all boundary segments
  Indices pce;
  const uint ne(TriMesh::nedges());
  for (uint i=0; i<ne; ++i) {
    if (TriMesh::edegree(i) == 1)
      pce.push_back(i);
  }
  sort(pce.begin(), pce.end());
  
  if (pce.empty()) {
    // clog << "No open holes found" << endl;
    return true;
  }
  
  // process all well-defined boundaries first
  vector<Indices> lns;
  vector<deque<uint> > oplns;
  while (not pce.empty()) {
    deque<uint> bdi;
    bool ok = traceBoundary(pce, bdi);
    if (ok) {
      lns.push_back(Indices(bdi.size()));
      copy(bdi.begin(), bdi.end(), lns.back().begin());
    } else {
      oplns.push_back(bdi);
    }
  }
  
  // try to find continuations for open lines
  for (uint i=0; i<oplns.size(); ++i) {
    deque<uint> & bdi(oplns[i]);
    bool ok = contBoundaryLine(bdi);
    if (ok) {
      lns.push_back(Indices(bdi.size()));
      copy(bdi.begin(), bdi.end(), lns.back().begin());
    } else {
      // clog << "Failed to find continuation for open boundary." << endl;
      pfail = vertex(bdi.front());
      return false;
    }
  }
  
  if (lns.empty() or lns.front().empty()) {
    // clog << "No open holes found" << endl;
    return true;
  }

  TriMesh capmerge;
  for (uint i=0; i<lns.size(); ++i) {
    Indices & lni(lns[i]);
    if (lni.back() != lni.front())
      lni.push_back(lni.front());
    buildCapSurface(capmerge, lni);
  }
  
  TriMesh::merge(capmerge);
  TriMesh::cleanup(0.25 * TriMesh::shortestEdgeLength());
  
  // drop triangles inside the body -- again
  if (haveIsecs) {
    Real xmin(huge);
    uint nt(nfaces()), tstart(0);
    for (uint i=0; i<nt; ++i) {
      Vct3 ctr( TriMesh::face(i).center() );
      if (ctr[0] < xmin) {
        xmin = ctr[0];
        tstart = i;
      }
    }
    TriMesh::dropInternalTriangles(tstart);
  }
  
  return true;
}

bool PatchMerger::traceBoundary(Indices & bde, std::deque<uint> & lni) const
{
  // start at the source vertex of the last edge in bde 
  lni.clear();
  const TriEdge & efirst(TriMesh::edge(bde.back()));
  lni.push_back(efirst.source());
  lni.push_back(efirst.target());
  bde.pop_back();
  
  bool forward(true);
  Indices::iterator pos;
  TriMesh::nb_edge_iterator ite, first, last;
  while (not bde.empty()) {
    
    // pick the next vertex
    uint icur;
    if (forward)
      icur = lni.back();
    else
      icur = lni.front();
    
    // search for a continuation edge
    first = TriMesh::v2eBegin(icur);
    last = TriMesh::v2eEnd(icur);
    for (ite = first; ite != last; ++ite) {
      uint ei = ite.index();
      pos = lower_bound(bde.begin(), bde.end(), ei);
      if (pos != bde.end() and *pos == ei) {
        bde.erase(pos);
        icur = ite->opposed(icur);
        break;
      }
    }
    
    // if continuation found, check if the loop is closed 
    // or continue with search 
    if (ite != last) {
      if (forward) {
        if (icur == lni.front())
          return true;
        else
          lni.push_back(icur);
      } else {
         if (icur == lni.back())
          return true;
        else
          lni.push_front(icur);
      }
      
      // proceed with search loop
      continue;
      
    } else {
    
      // no continuation found using boundary edges - flip direction
      // if possible, otherwise, give up
      if (forward) {
        forward = false;
#ifndef NDEBUG
        clog << "Tracer switching at " << vertex(lni.back()) << endl;
        for (uint i=0; i<lni.size(); ++i)
          clog << i << " at " << vertex(lni[i]) << endl;
#endif        
        continue;
        
      } else {
#ifndef NDEBUG
        cout << "Tracer giving up at " << vertex(lni.front()) << endl;
        for (uint i=0; i<lni.size(); ++i)
          cout << i << " at " << vertex(lni[i]) << endl;
#endif
        return false;
      }
    }
  }
  
  return false;
}

bool PatchMerger::contBoundaryLine(std::deque<uint> & bdi) const
{
  // unable to find a continuation between first and last vertex in bdi
  // which only includes boundary edges (degree == 1)
  // hence, try to find the most direct possible continuation 
  // which does not run along boundary edges (T-tail opening)
  
  // keep a sorted list of tagged vertices 
  Indices vtag(bdi.size());
  copy(bdi.begin(), bdi.end(), vtag.begin());
  sort(vtag.begin(), vtag.end());
  
  uint itarget = bdi.front();
  uint icur = bdi.back();
  TriMesh::nb_edge_iterator ite, first, last;
  while (bdi.size() < nvertices()) {
    
    // search vertex nearest to target
    uint ibest(NotFound);
    first = TriMesh::v2eBegin(icur);
    last = TriMesh::v2eEnd(icur);
    Real dst, mindst(huge);
    for (ite = first; ite != last; ++ite) {
      
      // check if we found a loop
      uint iop = ite->opposed(icur);
      if (iop == itarget)
        return true;
      
      // skip vertices which are already here
      if (binary_search(vtag.begin(), vtag.end(), iop))
        continue;
      dst = norm(vertex(itarget) - vertex(iop));
      if (dst < mindst) {
        mindst = dst;
        ibest = iop;
      }
    }
    
    // give up if there is no suitable continuation 
    if (ibest == NotFound)
      return false;
    
    // continue via ibest
    bdi.push_back(ibest);
    insert_sorted(vtag, ibest);
    icur = ibest;
  }
  
  // could not identify a loop
  return false;  
}

void PatchMerger::buildCapSurface(TriMesh & tmerge, const Indices & idx)
{
  // fetch points
  Vct3 pmid, nmean;
  const uint np(idx.size());
  PointList<3> pts(np), rmid(np);
  for (uint i=0; i<np; ++i) 
    pts[i] = TriMesh::vertex(idx[i]);

  // reference normal 
  Vct3 nref;
  for (uint i=0; i<np; ++i) {
    TriMesh::nb_face_iterator itf, flast;
    flast = TriMesh::v2fEnd(idx[i]);
    for (itf = TriMesh::v2fBegin(idx[i]); itf != flast; ++itf)
      nref += itf->normal();
  }
  normalize(nref);
  
  // compute geometric mid-point of the boundary
  Real dl, len(0);
  for (uint i=1; i<np; ++i) {
    dl = norm(pts[i] - pts[i-1]);
    len += dl;
    pmid += 0.5*dl*(pts[i] + pts[i-1]);
  }
  pmid /= len;

  // compute mean normal of the boundary cap
  for (uint i=0; i<np; ++i)
    rmid[i] = pts[i] - pmid;
  for (uint i=1; i<np; ++i)
    nmean += cross(rmid[i], rmid[i-1]);
  normalize(nmean);

  // decide which surface to generate, by aspect ratio
  Real lmax(0.0), lmin(huge);
  for (uint i=0; i<np; ++i) {
    dl = norm(rmid[i]);
    lmax = max(dl, lmax);
    lmin = min(dl, lmin);
  }

  // sorted boundary indices for binary search
  Indices six(idx);
  std::sort(six.begin(), six.end());
  
  // choose the sign of the elevation so that the
  // bulge points outward: consider points which are neighbors
  // of boundary points and compute their direction to the boundary
  Vct3 out;
  TriMesh::nb_edge_iterator ite, first, last;
  for (uint i=0; i<np; ++i) {
    first = TriMesh::v2eBegin(idx[i]);
    last = TriMesh::v2eEnd(idx[i]);
    for (ite = first; ite != last; ++ite) {
      uint k = ite->opposed(idx[i]);
      if (not binary_search(six.begin(), six.end(), k)) {
        out += (pts[i] - TriMesh::vertex(k)).normalized();
      }
    }
  }
  normalize(out);
  Real nsign = sign(dot(out, nmean));
  
  // check if the shape of the boundary is very irregular
  bool irregular(false);
  if (idx.size() < 8)
    irregular = true;

  // construct segments
  const uint nseg(np-1);
  PointList<3> seg(nseg);
  for (uint i=1; i<np; ++i)
    seg[i-1] = pts[i] - pts[i-1];

  // sum large angles between adjacent segments
  Real maxphi(rad(60.0)), phi, phisum(0.0);
  for (uint i=0; i<nseg; ++i) {
    uint inext = (i+1) % nseg;
    phi = fabs(arg(seg[i], seg[inext]));
    if (phi > maxphi) {
      phisum += phi;
    }
  }

  // heuristic criterion
  if (phisum > rad(270.))
    irregular = true;
  
//   // debug 
//   clog << "Hole at " << pmid << " lmax/lmin " << lmax/lmin 
//        << " irrg: " << irregular << endl;
//   clog << "nmean: " << nmean << endl;
//   clog << "nref: " << nref << endl;
//   clog << "out: " << out << endl;
  
  // for approximately circular holes, use the radially symmetric
  // cap, otherwise, use a longitudinally parametrized version
  if (irregular) {
    RoundCapSurf rcap(pts, 0.1*nsign);
    rcap.merge(2, tmerge);
  } else if (lmax/lmin < 3) {
    RoundCapSurf rcap(pts, 0.25*nsign);
    rcap.merge(nref, max(pts.size()/6, 4u) , tmerge);
  } else {
    LongCapSurf lcap(pts, 0.8*nsign);
    lcap.merge(tmerge);
  }
}

void PatchMerger::progress(const std::string & msg) const
{
  cout << "Operation: " << msg << endl;
}

uint PatchMerger::destretch(Real maxstr, Real maxphi, int npass)
{
  // pick very moderate destretching parameters 
  if (maxstr < 0 or maxphi < 0) {
    maxphi = PI/9.;
    maxstr = 4.0;
    const int ns(mcrits.size());
    for (int i=0; i<ns; ++i) {
      maxphi = min(maxphi, 0.5*mcrits[i]->maxPhi());
      maxstr = max(maxstr, mcrits[i]->maxStretch());
    }
  }
  
  if (npass < 0)
    npass = 16;
  
  int nmod(0), nplus, ipass(0);
  TriMesh::dropTriStars();
  do {
    nplus = TriMesh::dropStretchedTriangles(maxstr, maxphi);
    TriMesh::dropTriStars();
    nmod += nplus;
    ++ipass;
  } while (ipass < npass and nplus > 0);
  
  // try to repair flipped triangles  
  Indices fflip;
  TriMesh::findFlippedFaces(fflip);
  const int nfe(fflip.size());
  for (int i=0; i<nfe; ++i) {
//    clog << "Reversing flipped face " << fflip[i] << endl;
    TriMesh::face(fflip[i]).reverse();
  }
  
  return nmod;
}

