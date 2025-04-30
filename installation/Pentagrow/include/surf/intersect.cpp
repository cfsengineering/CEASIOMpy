
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
 
#include <genua/meshfields.h>
#include <genua/bounds.h>
#include "facetree.h"
#include "meshpatch.h"
#include "intersect.h"

using namespace std;

class IsecLinePoint
{
  public:

    IsecLinePoint(const EdgeFaceIsec & is, const IsecTags & t, bool fwd)
        : efi(is), tgs(t), forward(fwd)
    {
      if (forward)
        tng = efi.tangent();
      else
        tng = -1.0*efi.tangent();
      pt = efi.eval();
      // cout << "ILP created, tangent " << tng << " (" << fwd << ")" << endl;
    }

    /// check if 'a' would be a suitable continuation point
    bool valid(const EdgeFaceIsec & a) const
    {
      // invalid if already in use
      if (tgs.find(a) != tgs.end())
        return false;
      return acceptable(a);
    }

    /// check if 'a' would be a geometrically suitable continuation point
    bool acceptable(const EdgeFaceIsec & a) const
    {
      // invalid if angle between direction and tangent too large
      Vct3 dir = a.eval() - pt;
      if (arg(dir,tng) > PI/3.0) {
        return false;
      }

      // invalid if other point's tangent too different from ours
      Vct3 at = a.tangent();
      if (not forward)
        at *= -1.0;
      if (arg(at,tng) > PI/3.0) {
        return false;
      }

      return true;
    }
    
    Real wdistance(const EdgeFaceIsec & a) const
    {
      Vct3 r = a.eval() - pt;
      Real dst = norm(r);
      Real cphi = dot(r,tng) / dst;
      return dst*pow(cphi, -2.0);
    }

    Real distance(const EdgeFaceIsec & a) const
    {
      return norm(a.eval() - pt);
    }

    const TriEdge & segment() const {return efi.segment();}
    const TriFace & triangle() const {return efi.triangle();}
    const Vct3 & eval() const {return pt;}
    const Vct3 & tangent() const {return tng;}

  private:

    const EdgeFaceIsec & efi;
    const IsecTags & tgs;
    Vct3 pt, tng;
    bool forward;
};

// --------------------------------------------------------------------------

Intersector::Intersector(MeshPatch *sred, MeshPatch *sblue)
{
  assert(sred != sblue);
  if (sred < sblue) {
    sa = sred;
    sb = sblue;
  } else {
    sa = sblue;
    sb = sred;
  }
}

const IsecSet & Intersector::findIntersections(Real maxgap)
{
  FaceTree fta(*sa), ftb(*sb);
  fta.split(16, 8);
  ftb.split(16, 8);

  // compute face-edge intersections
  mf.clear();
  uint ni = fta.intersect(ftb, mf);
  
#ifndef NDEBUG
  clog << "Found " << ni << " face-edge intersections." << endl;
#endif

  isc.clear();
  if (ni == 0)
    return isc;

  // construct dual mapping (edge -> intersections)
  // and refine all face/edge intersections
  Real fsize, gap;
  me.clear();
  FaceIsecMap::iterator itm;
  std::vector<FaceIsecMap::iterator> rejected;
  for (itm = mf.begin(); itm != mf.end(); ++itm) {
    
    assert(not itm->second.empty());
    // fsize = sqrt(0.5*norm(itm->first.normal()));
    std::vector<EdgeFaceIsec> tmp;
    
    // drop intersection if refinement fails
    for (uint i=0; i<itm->second.size(); ++i) {
      EdgeFaceIsec & is(itm->second[i]);
      fsize = is.localSize();
      Real gaplimit = min(maxgap, 0.5*fsize);
      Vct3 pold = is.eval();
      gap = is.erefine(1e-6, 32);
      Vct3 pref = is.eval();
      if (gap < gaplimit and norm(pref-pold) < 4*fsize) {
        tmp.push_back(is);
      } else {
        // Newton-based refinement failed, try discrete method
        gap = is.refine(1e-6, 32);
        pref = is.eval();
        if (gap < gaplimit and norm(pref-pold) < 4*fsize) 
          tmp.push_back(is);
      }
    }
    
    if (tmp.empty()) {
      rejected.push_back(itm);
    } else {
      tmp.swap(itm->second);
    
      // create edge-intersection map
      for (uint i=0; i<itm->second.size(); ++i) {
        EdgeFaceIsec & is(itm->second[i]);
        me[is.segment()].push_back(is);
      }
    }
  }
  
  for (uint i=0; i<rejected.size(); ++i)
    mf.erase(rejected[i]);

  isc.clear();
  isc.push_back( IsecLine() );

  uint nf(0);
  bool forward(true);
  // const TriMesh *psf;
  IsecTags tagged;
  const EdgeFaceIsec *first, *cur;
  first = cur = findFirst(tagged);
  while (first) {
    tagged.insert(*cur);
    // psf = cur->triangle().mesh();
    if (forward)
      isc.back().push_back(*cur);
    else
      isc.back().push_front(*cur);
    ++nf;
    cur = findNext( IsecLinePoint(*cur, tagged, forward) );
    if ((not cur) and forward) {
      forward = false;
      cur = findNext( IsecLinePoint(*first, tagged, forward) );
    }
    if ((not cur) and (not forward)) {
      
      // test if first point of the line would be a suitable continuation
      // at its end, not considering that it already is in use
      const EdgeFaceIsec & lstart(isc.back().front());
      const EdgeFaceIsec & lend(isc.back().back());
      IsecLinePoint last(lend, tagged, true);
      if (last.acceptable(lstart)) { 
        isc.back().push_back(lstart);
        
#ifndef NDEBUG
        clog << "Connecting end to start at " << lstart.eval() << endl;
#endif
      }
      
      forward = true;
      first = cur = findFirst(tagged);
      if (not isc.back().empty())
        isc.push_back( IsecLine() );
    }
  }

  // drop lines with fewer than five points  
  IsecSet isl;
  for (uint i=0; i<isc.size(); ++i) {
    if (isc[i].size() < 5)
      continue;
    isl.push_back(isc[i]);
  }
  isl.swap(isc);
      
#ifndef NDEBUG
  const uint nisc = isc.size();
  clog << "Identified " << nisc << " intersection lines "
       << "with " << nf << " points." << endl;
  for (uint i=0; i<nisc; ++i) {
    clog << "Line " << i << ": " << endl;
    clog << "from " << isc[i].front().eval() 
         << " to " << isc[i].back().eval() << endl;
  }
#endif
  
  // experimental
  //joinConnectedLines(maxgap);
  
  return isc;
}

const EdgeFaceIsec *Intersector::findFirst(const IsecTags & t) const
{
  assert(not mf.empty());
  
  // find the intersection with the most extreme parameter values
  // currently not tagged
  pair<Vct2,Vct2> pp;
  Real w, xtr = -1.0;
  const EdgeFaceIsec *best(0);
  FaceIsecMap::const_iterator itm;
  itm = mf.begin();
  while (itm != mf.end()) {
    assert(itm->second.size() > 0);
    for (uint k=0; k<itm->second.size(); ++k) {
      const EdgeFaceIsec & is(itm->second[k]);
      if (t.find(is) == t.end()) {
        pp = parameter(is);
        for (uint i=0; i<2; ++i) {
          w = pp.first[i];
          w = max(w, 1-w);
          if (w > xtr) {
            best = &is;
            xtr = w;
          }
          w = pp.second[i];
          w = max(w, 1-w);
          if (w > xtr) {
            best = &is;
            xtr = w;
          }
        }
      }
    }
    ++itm;
  }
  
  return best;
}

const EdgeFaceIsec *Intersector::findNext(const IsecLinePoint & last) const
{
  Real mindist(huge);
  const EdgeFaceIsec *best(0), *isf(0);

  // check edges originating in the endpoints of the intersecting
  // edge for intersections
  const TriEdge & e(last.segment());
  isf = findNearest(last, patch(e), e.source(), mindist);
  if (isf != 0)
    best = isf;
  isf = findNearest(last, patch(e), e.target(), mindist);
  if (isf != 0)
    best = isf;

  // next, check edges near the last face for possible intersection
  const TriFace & f(last.triangle());
  const uint *vi(f.vertices());
  for (uint i=0; i<3; ++i) {
    isf = findNearest(last, patch(f), vi[i], mindist);
    if (isf != 0)
      best = isf;
  }

  return best;
}

const EdgeFaceIsec *Intersector::findNearest(const IsecLinePoint & lst,
    const MeshPatch *psf, uint i, Real & mdist) const
{
  Indices idone;
  Indices::iterator ipos;
  deque<uint> ntest;
  set<TriEdge> etag;
  const EdgeFaceIsec *best(0);
  EdgeIsecMap::const_iterator itm;
  TriMesh::nb_edge_iterator ite, first, last;

  // test edges incident on i itself, collect neighbor vertices
  ntest.push_back(i);
  uint iter(0);
  const uint abslimit(512), fndlimit(32);
  while ((not ntest.empty()) and iter < abslimit) {
    
    // fetch next vertex to test
    uint icur = ntest.front();
    ntest.pop_front();
    ipos = lower_bound(idone.begin(), idone.end(), icur);
    if (ipos == idone.end() or *ipos != icur)
      idone.insert(ipos, icur);
    
    // iterate over edges coincident on this vertex
    first = psf->v2eBegin(icur);
    last = psf->v2eEnd(icur);
    for (ite = first; ite != last; ++ite) {
      
      // skip if edge already processed
      if (etag.find(*ite) != etag.end())
        continue;
      
      // mark next vertex for processing if not already touched
      uint iopp = ite->opposed(icur);
      if (not binary_search(idone.begin(), idone.end(), iopp))
        ntest.push_back(iopp);
      
      // find local intersections and test for suitability
      itm = me.find(*ite);
      if (itm != me.end()) {
        for (uint j=0; j<itm->second.size(); ++j) {
          const EdgeFaceIsec & is(itm->second[j]);
          if (lst.valid(is)) {
            Real dst = lst.distance(is);
            if (dst < mdist) {
              best = &is;
              mdist = dst; 
            } 
          }
        }
      }
      
      // mark edge as processed
      etag.insert(*ite);
    }
    ++iter;
    
    // return early if an acceptable continuation was found
    if (best != 0 and iter >= fndlimit)
      return best;
  }

  return best;
}

const MeshPatch *Intersector::patch(const TriMesh *psf) const
{
  const MeshPatch *pm(0);
  pm = dynamic_cast<const MeshPatch *>(psf);
  assert(pm != 0);
  assert(pm == sa or pm == sb);
  return pm;
}

const MeshPatch *Intersector::patch(const TriEdge & e) const
  {return patch(e.mesh());}

const MeshPatch *Intersector::patch(const TriFace & f) const
  {return patch(f.mesh());}

std::pair<Vct2, Vct2> Intersector::parameter(const EdgeFaceIsec & is) const
{
  Vct2 pf, pe;
  const MeshPatch *pm = patch(is.triangle());
  if (pm == sa) {
    pf = is.fparameter();
    pe = is.eparameter();
    return make_pair(pf,pe);
  } else {
    pf = is.fparameter();
    pe = is.eparameter();
    return make_pair(pe,pf);
  }
}

bool Intersector::closedLoops(Real tol) const
{
  const uint ni(isc.size());
  for (uint i=0; i<ni; ++i) {
    Vct3 p1( isc[i].front().eval() );
    Vct3 p2( isc[i].back().eval() );
    if (norm(p2-p1) > tol) {
      return false;
    }
  }
  return true;
}

bool Intersector::connectedLines(Real tol) const
{
  // collect open intersection lines
  Indices oil;
  const uint ni(isc.size());
  for (uint i=0; i<ni; ++i) {
    Vct3 p1( isc[i].front().eval() );
    Vct3 p2( isc[i].back().eval() );
    if (norm(p2-p1) > tol)
      oil.push_back(i);
  }
  
  // check if these intersections are connected
  const uint no(oil.size());
  vector<bool> lok(no);
  for (uint i=0; i<no; ++i)
    lok[i] = false;
  for (uint i=0; i<no; ++i) {
    if (not lok[i]) {
      Vct3 i1( isc[i].front().eval() );
      Vct3 i2( isc[i].back().eval() );
      for (uint j=i+1; j<no; ++j) {
        Vct3 j1( isc[j].front().eval() );
        Vct3 j2( isc[j].back().eval() );
        if (norm(i1-j1) < tol and norm(i2-j2) < tol) {
          lok[i] = lok[j] = true;
          break;
        } else if (norm(i1-j2) < tol and norm(i2-j1) < tol) {
          lok[i] = lok[j] = true;
          break;
        }
      }
    }
  }
  
  for (uint i=0; i<no; ++i) {
    if (not lok[i])
      return false;
  }
  return true;
}

bool Intersector::endsOnBoundaries(Real ptol) const
{
  const uint ni(isc.size());
  for (uint i=0; i<ni; ++i) {
    Vct2 ep1( isc[i].front().eparameter() );
    Vct2 fp1( isc[i].front().fparameter() );
    if ( whichside(ep1[0], ep1[1], ptol) == none or 
         whichside(fp1[0], fp1[1], ptol) == none )
      return false;
    Vct2 ep2( isc[i].back().eparameter() );
    Vct2 fp2( isc[i].back().fparameter() );
    if ( whichside(ep2[0], ep2[1], ptol) == none or 
         whichside(fp2[0], fp2[1], ptol) == none)
      return false;
  }
  
  return true;  
}

const IsecSet & Intersector::filter(Real maxphi, Real maxlen, Real minlen)
{
  std::pair<Vct2,Vct2> pp;
  Real bntol(1e-3);
  
  for (uint i=0; i<isc.size(); ++i) {
    IsecLine & line(isc[i]);
    
    // store midpoints
    Indices kept;
    const uint nl(line.size());
    PointList<3> lpts(nl);
    for (uint j=0; j<nl; ++j) 
      lpts[j] = line[j].midpoint();
    
    // always keep first & last point - may be on boundary 
    kept.push_back(0);
    for (uint j=1; j<nl-1; ++j) {
      
      // keep points on/near boundary in any case
      const EdgeFaceIsec & is(line[j]);
      pp = Intersector::parameter(is);
      if (fabs(pp.first[0]) < bntol or fabs(pp.second[0]) < bntol) {
        kept.push_back(j);
        continue;
      } else if (fabs(pp.first[1]) < bntol or fabs(pp.second[1]) < bntol) {
        kept.push_back(j);
        continue;
      } else if (fabs(1-pp.first[0]) < bntol or fabs(1-pp.second[0]) < bntol) {
        kept.push_back(j);
        continue;
      } else if (fabs(1-pp.first[1]) < bntol or fabs(1-pp.second[1]) < bntol) {
        kept.push_back(j);
        continue;
      }
      
      const Vct3 & plast( lpts[kept.back()] );
      const Vct3 & pj( lpts[j] );
      const Vct3 & pnext( lpts[j+1] );
      
      // drop point if minlen would not be reached
      Real prelen = norm(pj - plast);
      Real postlen = norm(pnext - plast);
      if (prelen < minlen and postlen < minlen)
        continue;
      
      // kink at current position, if we insert j
      Real kink = arg( pnext-pj, pj-plast );
      if (kink > maxphi) {
        // keep j because kink is already too large
        kept.push_back(j);
        continue;
      } else if (kept.size() > 1 and j < nl-2) {
        // check if kink would become too large if we drop j
        uint k2 = kept.size() - 2;
        const Vct3 & plast2( lpts[kept[k2]] );
        const Vct3 & pnext2( lpts[j+2] );
        kink = arg(pnext2-plast, plast-plast2);
        if (kink > maxphi) {
          kept.push_back(j);
          continue;
        }
      }        
      
      if (prelen > maxlen or postlen > maxlen) {
        kept.push_back(j);
        continue;
      }
    }
    kept.push_back(nl-1);
    
    const uint nk(kept.size());
    IsecLine tmp;
    for (uint j=0; j<nk; ++j)
      tmp.push_back( line[kept[j]] );
    line.swap(tmp);
  }
  
  return isc;
}

const IsecSet & Intersector::reduce(Real maxphi, Real minlen, Real bntol)
{
  const Real cphimin(cos(maxphi));
  std::pair<Vct2,Vct2> pp, ppl;
  Real cphi(0.0);    
  for (uint i=0; i<isc.size(); ++i) {
    
    IsecLine & line(isc[i]);
    
    // store midpoints
    Indices kept;
    const uint nl(line.size());
    PointList<3> lpts(nl);
    for (uint j=0; j<nl; ++j) 
      lpts[j] = line[j].midpoint();
    
    // always keep first & last point
    kept.push_back(0);
    for (uint j=1; j<nl-1; ++j) {
      
      // keep points on/near boundary in any case, unless this is
      // the second or last but one point
      if (j != 1 and j != nl-2) {
        side_t lastside = line[kept.back()].onBoundary(bntol);
        side_t thisside = line[j].onBoundary(bntol);
        side_t nextside = line[j+1].onBoundary(bntol);
        if (thisside != none and thisside != lastside and thisside != nextside) {
          kept.push_back(j);
          continue;
        }
      }
      
      // compute length of the resulting segment
      // if we drop this particular point
      Vct3 rnew( lpts[j+1] - lpts[kept.back()] );
      Real seglen = norm(rnew);      
      
      // compare to angular criterion and previous length
      uint nk = kept.size();
      if (nk > 1) {
        Vct3 rlast( lpts[kept[nk-1]] - lpts[kept[nk-2]] );
        cphi = cosarg(rlast, rnew);
        if (cphi < cphimin) {
          kept.push_back(j);
          continue;
        }
      }
      
      const Vct3 & tg(line[kept.back()].tangent());
      if (dot(tg,rnew) > 0)
        cphi = cosarg(rnew, tg);
      else
        cphi = cosarg(-rnew, tg);
      
      if (cphi < cphimin) {
        kept.push_back(j);
        continue;
      }
      
      // drop point if very close to last point
      Real jlen = norm(lpts[j] - lpts[kept.back()]);
      if (jlen < minlen) {
        continue;
      }
      
      // compare to local length scale
      Real ls, ls1, ls2, ls3;
      ls1 = line[j-1].localSize();
      ls2 = line[j].localSize();
      ls3 = line[j+1].localSize();
      ls = pow(ls1*ls2*ls3, (1.0/3.0));
      if (seglen > ls and norm(lpts[j+1] - lpts[j]) > minlen) {
        kept.push_back(j);
        continue;
      } 
    }
    kept.push_back(nl-1);
    
    const uint nk(kept.size());
    IsecLine tmp;
    for (uint j=0; j<nk; ++j) {
      tmp.push_back( line[kept[j]] );
    }
    // first and last are condidates for boundary points
    tmp.front().forceToBoundary(bntol);
    tmp.back().forceToBoundary(bntol);
        
    line.swap(tmp);
  }
  
  return isc;
}

void Intersector::addViz(MeshFields & mvz) const
{
  // add markers at all discrete intersection points
  FaceIsecMap::const_iterator itm = mf.begin();
  FaceIsecMap::const_iterator last = mf.end();
  while (itm != last) {
    const vector<EdgeFaceIsec> & isv(itm->second);
    uint ni = isv.size();
    for (uint i=0; i<ni; ++i) 
      mvz.addMarker( mvz.addVertex(isv[i].eval())  );
    ++itm;
  }

  // add line elements for detected intersection lines
  for (uint i=0; i<isc.size(); ++i) {
    const IsecLine & iln(isc[i]);
    uint off = mvz.nvertices();
    uint nip = iln.size();

    // add nodes for this polyline
    for (uint j=0; j<nip; ++j) {
      mvz.addVertex( iln[j].eval() );
    }

    // add line segments
    for (uint j=0; j<nip-1; ++j)
      mvz.addLine2(off+j, off+j+1);
  }
}

void Intersector::boxes(std::vector<BndRect> & bra, std::vector<BndRect> & brb) const
{
  bra.clear();
  brb.clear();
  pair<Vct2, Vct2> pt;
  const uint nl(isc.size());
  for (uint i=0; i<nl; ++i) {
    Vct2 pa1, pa2, pb1, pb2;
    pa1 = pb1 = huge;
    pa2 = pb2 = -huge;
    uint np = isc[i].size();
    for (uint j=0; j<np; ++j) {
      pt = parameter( isc[i][j] );
      for (uint k=0; k<2; ++k) {
        pa1[k] = min(pa1[k], pt.first[k]);
        pa2[k] = max(pa2[k], pt.first[k]);
        pb1[k] = min(pb1[k], pt.second[k]);
        pb2[k] = max(pb2[k], pt.second[k]);
      }
    }
    bra.push_back( BndRect(pa1, pa2) );
    brb.push_back( BndRect(pb1, pb2) );
  }
}

void Intersector::sboxes(Real s, std::vector<BndRect> & bra, std::vector<BndRect> & brb) const
{
  bra.clear();
  brb.clear();
  pair<Vct2, Vct2> pt;
  const uint nl(isc.size());
  for (uint i=0; i<nl; ++i) {
    Vct2 pa1, pa2, pb1, pb2;
    pa1 = pb1 = huge;
    pa2 = pb2 = -huge;
    uint np = isc[i].size();
    for (uint j=0; j<np; ++j) {
      
      pt = parameter( isc[i][j] );
      Real sr = sizeRatio(i,j);
      if (sr > s) {
        // element on patch a is larger 
        for (uint k=0; k<2; ++k) {
          pa1[k] = min(pa1[k], pt.first[k]);
          pa2[k] = max(pa2[k], pt.first[k]);
        }
      } else if ((s*sr) < 1.0) {
        // element on patch b is larger 
        for (uint k=0; k<2; ++k) {
          pb1[k] = min(pb1[k], pt.second[k]);
          pb2[k] = max(pb2[k], pt.second[k]);
        }
      } else {
        continue;
      }
    }
    if (pa1[0] < huge)
      bra.push_back( BndRect(pa1, pa2) );
    if (pb1[0] < huge)
      brb.push_back( BndRect(pb1, pb2) );
  }
}

void Intersector::locateXsrSpots(Real s, XsrSpotArray & xsa, XsrSpotArray & xsb) const
{
  xsa.clear();
  xsb.clear();
  Vct2 plarge, pt, rp;
  const uint nl(isc.size());
  for (uint i=0; i<nl; ++i) {
    
    uint np = isc[i].size();
    XsrSpot aspot, bspot;
    aspot.maxsr = bspot.maxsr = 0.0;
    aspot.ru = bspot.ru = 0.0;
    aspot.rv = bspot.rv = 0.0;
    
    // collect critical points and locate maxima 
    for (uint j=0; j<np; ++j) {
      rp = 0.0;
      Real sr = sizeRatio(i, j, plarge, rp);
      if (sr > s) {
        aspot.ru = max(aspot.ru, rp[0]);
        aspot.rv = max(aspot.rv, rp[1]);
        aspot.maxsr = sr;
        aspot.ctr = plarge;
        xsa.push_back( aspot );
      } else if ((sr*s) < 1.0) {
        bspot.ru = max(bspot.ru, rp[0]);
        bspot.rv = max(bspot.rv, rp[1]);
        bspot.maxsr = 1.0 / sr;
        bspot.ctr = plarge;
        xsb.push_back( bspot );
      }
    }
  } 
  
  // merge spots if ellipses overlap 
  mergeOverlaps( xsa );
  mergeOverlaps( xsb );
}

void Intersector::mergeOverlaps(XsrSpotArray & xsa) const
{
  const uint nx( xsa.size() );
  if (nx < 2)
    return;
  
  XsrSpotArray tmp;
  vector<bool> ovrlp(nx);
  for (uint i=0; i<nx; ++i)
    ovrlp[i] = false;
  
  for (uint i=0; i<nx; ++i) {
    if (ovrlp[i])
      continue;
    
    XsrSpot spot = xsa[i];
    for (uint j=i+1; j<nx; ++j) {
      if (spot.overlaps(xsa[j])) {
        spot.merge(xsa[j]);
        ovrlp[j] = true;
      }
    }
    tmp.push_back(spot);
  }
  tmp.swap(xsa);
  
#ifndef NDEBUG
  clog << " a: " << sa->surface()->name();
  clog << " b: " << sb->surface()->name() << endl;
  clog << "xsr regions: " << endl;
  for (uint i=0; i<xsa.size(); ++i)
    clog << " xsr " << xsa[i].maxsr << " at " << xsa[i].ctr
         << " ru " << xsa[i].ru << " rv " <<  xsa[i].rv << endl;
#endif
}

Real Intersector::sizeRatio(uint i, uint j) const
{
  assert(i < isc.size());
  assert(j < isc[i].size());
  
  // ratio size(f) / size(e)
  Real sr = isc[i][j].sizeRatio();
  if (patch(isc[i][j].triangle()) == sa) {
    return sr;
  } else {
    return 1.0/sr;
  }
}

Real Intersector::sizeRatio(uint i, uint j, Vct2 & ctr, Vct2 & r) const
{
  assert(i < isc.size());
  assert(j < isc[i].size());
  
  // ratio size(f) / size(e)
  Real sr = isc[i][j].sizeRatio();
  
  // store center and distance of the farthest point of 
  // the larger item to the intersection point
  if (sr > 1.0) {
    ctr = isc[i][j].fparameter();
    const TriFace & f(isc[i][j].triangle());
    const MeshPatch & mp(*patch(f.mesh()));
    const uint *vi(f.vertices());
    const Vct2 & p1(mp.parameter(vi[0]));
    const Vct2 & p2(mp.parameter(vi[1]));
    const Vct2 & p3(mp.parameter(vi[2]));
    Vct2 r1(p1 - ctr);
    Vct2 r2(p2 - ctr);
    Vct2 r3(p3 - ctr);
    for (uint k=0; k<2; ++k) {
      r[k] = max(r[k], fabs(r1[k]));
      r[k] = max(r[k], fabs(r2[k]));
      r[k] = max(r[k], fabs(r3[k]));
    }
  } else {
    ctr = isc[i][j].eparameter();
    const TriEdge & e(isc[i][j].segment());
    const MeshPatch & mp(*patch(e.mesh()));
    Vct2 r1(mp.parameter(e.source()) - ctr);
    Vct2 r2(mp.parameter(e.target()) - ctr);
    for (uint k=0; k<2; ++k) {
      r[k] = max(r[k], fabs(r1[k]));
      r[k] = max(r[k], fabs(r2[k]));
    }
  }
  
  if (patch(isc[i][j].triangle()) == sa) {
    return sr;
  } else {
    return 1.0/sr;
  }
}

void Intersector::sortLooseLines(Real ptol)
{
  Vct2 pe, pf;
  side_t efirst, elast, ffirst, flast;
  const uint nl(isc.size());
  for (uint i=0; i<nl; ++i) {
    IsecLine & line(isc[i]);
    pe = line.front().eparameter();
    pf = line.front().fparameter();
    efirst = whichside(pe[0], pe[1], ptol);
    ffirst = whichside(pf[0], pf[1], ptol);
    pe = line.back().eparameter();
    pf = line.back().fparameter();
    elast = whichside(pe[0], pe[1], ptol);
    flast = whichside(pf[0], pf[1], ptol);
    
    // reverse only if the first point is loose while 
    // the last point is on a boundary
    if (efirst == none and ffirst == none 
        and (elast != none or flast != none)) 
      {
        reverse(line.begin(), line.end());
      }
  }
}

bool Intersector::openLeadingEdge(uint i, uint j, Real ptol) const
{
  if (i == j)
    return false;
  
  const IsecLine & li(isc[i]);
  const IsecLine & lj(isc[j]);
  
  // compute total length of li and lj 
  const uint ni(li.size());
  const uint nj(lj.size());
  Real ilen(0.0), jlen(0.0);
  for (uint k=1; k<ni; ++k) 
    ilen += norm(li[k].eval() - li[k-1].eval());
  for (uint k=1; k<nj; ++k) 
    jlen += norm(lj[k].eval() - lj[k-1].eval());
  
  // if length differs by more than 20%, these are not 
  // likely loose leading edges 
  Real chord = 0.5*(ilen + jlen);
  if ( fabs(jlen-ilen) > 0.2*chord ) {
#ifndef NDEBUG
    clog << "Relative chord length difference: " << fabs(jlen-ilen)/chord << endl;
#endif
    return false;
  }
  
// #ifndef NDEBUG
//   clog << "Testing " << i << " against " << j << endl;
//   clog << i << " starts at " << li.front().eval() << endl;
//   clog << i << " ends at " << li.back().eval() << endl;
//   clog << j << " starts at " << lj.front().eval() << endl;
//   clog << j << " ends at " << lj.back().eval() << endl;
// #endif
  
  // check if the start points are near each other --
  // trailing edge point must be identical 
  Real tegap = norm(li.front().eval() - lj.front().eval());
  if (tegap > 0.001*chord){
#ifndef NDEBUG
    clog << "Relative TE gap: " << tegap/chord << endl;
#endif
    return false;
  }
  
  // start points must be on u-boundary 
  Vct2 pe, pf;
  side_t se, sf;
  pe = li.front().eparameter(); 
  pf = li.front().fparameter();
  se = whichside(pe[0], pe[1], ptol);
  sf = whichside(pf[0], pf[1], ptol);
  if (se != east and se != west and sf != east and sf != west) {
#ifndef NDEBUG
    clog << "Side e: " << se << " side f " << sf << endl;
#endif
    return false;
  }
  
  pe = lj.front().eparameter(); 
  pf = lj.front().fparameter();
  se = whichside(pe[0], pe[1], ptol);
  sf = whichside(pf[0], pf[1], ptol);
  if (se != east and se != west and sf != east and sf != west) {
#ifndef NDEBUG
    clog << "Side e: " << se << " side f " << sf << endl;
#endif
    return false;
  }
  
  // distance at LE gap may not be too large 
  Real legap = norm(li.back().eval() - lj.back().eval()); 
  if (legap > 0.03*chord) {
#ifndef NDEBUG
    clog << "Relative LE gap: " << legap/chord << endl;
#endif
    return false;
  }
  
  return true;
}
    
bool Intersector::connectLeadingEdge(const Indices & vi, const Indices & vj)
{
  assert(vi.size() == vj.size());
  
  // collect all affected lines
  Indices afl(vi);
  afl.insert(afl.end(), vj.begin(), vj.end());
  sort_unique(afl);
  
  // copy all unaffected lines  
  IsecSet tmp;
  const uint nl(isc.size());
  for (uint i=0; i<nl; ++i) {
    if (not binary_search(afl.begin(), afl.end(), i)) {
      tmp.push_back(isc[i]);
    }
  }
  
  // connect paired edges, reversing the one from vj 
  const uint nc(vi.size());
  for (uint i=0; i<nc; ++i) {
    if (vi[i] == vj[i])
      return false;
    IsecLine line(isc[vi[i]]);
    const IsecLine & other(isc[vj[i]]);
    line.insert(line.end(), other.rbegin(), other.rend());
    tmp.push_back(line);
  }
  
  tmp.swap(isc);
  return true;
}

uint Intersector::joinSeamLines(Real tol, Real ptol)
{
  uint nfop(0);
  const uint nl(isc.size());
  for (uint i=0; i<nl; ++i) {
    EdgeFaceIsec & efi1( isc[i].front() );
    EdgeFaceIsec & efi2( isc[i].back() );
    Real dst = norm(efi1.eval() - efi2.eval());
    if (dst > tol and dst < 50*tol) {
      bool fopok;
      side_t s1 = efi1.onBoundary( ptol );
      side_t s2 = efi2.onBoundary( ptol );
      if (s1 == east or s1 == west) {
        EdgeFaceIsec fop;
        efi1.forceToBoundary(ptol);
        fopok = efi1.fakeOpposedPoint(ptol, fop);
        if (fopok) {
          // isc[i].insert(isc[i].end(), fop);
          efi2 = fop;
          ++nfop;
        }
      } else if (s2 == east or s2 == west) {
        EdgeFaceIsec fop;
        efi2.forceToBoundary(ptol);
        fopok = efi2.fakeOpposedPoint(ptol, fop);
        if (fopok) {
          // isc[i].insert(isc[i].begin(), fop);
          efi1 = fop;
          ++nfop;
        }
      }
    }
    
  }
  return nfop;
}

void Intersector::joinConnectedLines(Real tol)
{
  // collect open intersection lines
  const uint ni(isc.size());
  if (ni < 2)
    return;
  
  // find pairs with small gaps
  const int uncon = ni+1;
  vector<int> lcon(ni);
  fill(lcon.begin(), lcon.end(), uncon);
  for (uint i=0; i<ni; ++i) {
    if (lcon[i] == uncon) {
      Vct3 i1( isc[i].front().eval() );
      Vct3 i2( isc[i].back().eval() );
      if (norm(i1-i2) > tol) {
        for (uint j=i+1; j<ni; ++j) {
          Vct3 j1( isc[j].front().eval() );
          Vct3 j2( isc[j].back().eval() );
          if (norm(i1-j1) < tol and norm(i2-j2) < tol) {
            lcon[i] = j;
            lcon[j] = i;
            break;
          } else if (norm(i1-j2) < tol and norm(i2-j1) < tol) {
            lcon[i] = - int(j);
            lcon[j] = - int(i);
            break;
          }
        }
      }
    }
  }
  
  // join pairs
  IsecSet tmp;
  for (uint i=0; i<ni; ++i) {
    if (lcon[i] == uncon) {
      tmp.push_back( isc[i] );
    } else if (lcon[i] > int(i)) {
      // connect head to head and foot to foot
      tmp.push_back( isc[i] );
      IsecLine & isl(tmp.back());
      IsecLine & isk(isc[lcon[i]]);
      isl.insert(isl.end(), isk.begin(), isk.end());
      cout << "Connecting head to head at " << isk.front().eval() << endl;
      
    } else if (lcon[i] < -int(i)) {
      // connect head to head and foot to foot
      tmp.push_back( isc[i] );
      IsecLine & isl(tmp.back());
      IsecLine & isk(isc[-lcon[i]]);
      isl.insert(isl.end(), isk.begin(), isk.end());
      
      cout << "Connecting head to foot at " << isk.front().eval() << endl;
    }
  }
  tmp.swap(isc);
}

