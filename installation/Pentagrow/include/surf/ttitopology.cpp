
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
 
#include <iostream>
 
#include <genua/meshfields.h>
#include <genua/boxsearchtree.h>
#include <genua/dbprint.h>
#include "spotrefine.h"
#include "ttitopology.h"

using namespace std;

Real TTiTopology::tolBound = 1e-7;

TTiTopology::TTiTopology(const TTIntersectorPtr & tti) : tip(tti)
{
  // collect intersected triangles in tip and compute connectivity
  tip->collect(segments);
  sort_unique(segments);
  
  findTriples();
  mergeNodes(gmepsilon);
  
  fixate();
}

void TTiTopology::mergeNodes(Real mthreshold)
{
  const int ns = segments.size();
  PointList<3> vtx(2*ns);
  
  // mark vertices which are on a parameter boundary
  vector<bool> onBound(2*ns, false);
  bool ub, vb;
  for (int i=0; i<ns; ++i) {
    TTIntersection & s( *segments[i] );
    vtx[2*i+0] = s.srcPoint();
    vtx[2*i+1] = s.trgPoint();
    s.source(2*i+0);
    s.target(2*i+1);
    s.srcOnBoundary(tolBound, ub, vb);
    onBound[2*i+0] = (ub or vb);
    s.trgOnBoundary(tolBound, ub, vb);
    onBound[2*i+1] = (ub or vb);
  }
  
  uint nv(vtx.size()), ndpl;
  BSearchTree btree(vtx);
  
  // find (nearly) identical vertices
  Indices repl(nv), idt;
  fill(repl.begin(), repl.end(), NotFound);
  uint count(0);
  PointList<3> kept;
  for (uint i=0; i<nv; ++i) {
    
    // for each vertex which is not yet marked as duplicate 
    if (repl[i] == NotFound) {
      
      // mark as a vertex to keep 
      repl[i] = count;
      
      // locate vertices within radius of threshold 
      idt.clear();
      btree.find(vtx[i], mthreshold, idt);
      
      // mark duplicates with indices beyond i
      // do not mark duplicates which are on the other side of the surface  
      for (uint j=0; j<idt.size(); ++j) {
        if (idt[j] > i and uvDistance(onBound, i, idt[j]) < 1e-7 )
          repl[idt[j]] = count;
      }
      
      // store vertex as kept
      ++count;
      kept.push_back(vtx[i]);
    }
    
    // skip vertices marked as duplicates
  }

  // eliminate duplicate vertices
  ndpl = vtx.size() - kept.size();
  
  // store nodes
  const int nkv = kept.size(); 
  nodes.resize(nkv);
  for (int i=0; i<nkv; ++i) {
    nodes[i] = TTiNode( kept[i] );
  }
  
  // apply node index translation to segments
  if (ndpl > 0) {
    for (int i=0; i<ns; ++i) {
      TTIntersection & s( *segments[i] );
      s.source( repl[s.source()] );
      s.target( repl[s.target()] );
    }
    
    TTIntersectionArray::iterator last;
    std::sort(segments.begin(), segments.end(), less_by_nodes);
    last = std::unique(segments.begin(), segments.end(), equal_by_nodes);
    segments.erase(last, segments.end());
  }

//  // mark TTiNodes which touch an enforced segment as enforced
//  for (int i=0; i<ns; ++i) {
//    TTIntersection & s( *segments[i] );
//    if (s.enforced()) {
//      assert(s.source() < nodes.size());
//      assert(s.target() < nodes.size());
//      nodes[s.source()].enforced(true);
//      nodes[s.target()].enforced(true);
//    }
//  }
}

Real TTiTopology::uvDistance(const std::vector<bool> & onb, uint i, uint j) const
{
  if ( (not onb[i]) or (not onb[j])  )
    return 0.0;
    
  const TTIntersection & si( *segments[i/2] );
  const TTIntersection & sj( *segments[j/2] );
  
  bool isrc = (i%2 == 0);
  bool jsrc = (j%2 == 0);
  
  Vct2 iq1, iq2, jq1, jq2;
  if (isrc)
    si.srcParameter(iq1, iq2);
  else
    si.trgParameter(iq1, iq2);
  if (jsrc)
    sj.srcParameter(jq1, jq2);
  else
    sj.trgParameter(jq1, jq2);
   
  const MeshComponent *mi1, *mi2, *mj1, *mj2;
  mi1 = si.firstPatch();
  mi2 = si.secondPatch();
  mj1 = sj.firstPatch();
  mj2 = sj.secondPatch();
  
  if (mi1 == mj1)
    return norm(iq1-jq1) + norm(iq2-jq2);
  else
    return norm(iq1-jq2) + norm(iq2-jq1);
}

void TTiTopology::findTriples()
{
  Real t;
  std::map<uint, Real> splitmap;
  std::map<uint, Real>::const_iterator itm, last;
  bool itagged, jtagged;
  const int ns = segments.size(); 
  for (int i=0; i<ns; ++i) {
    const TTIntersection & si( *segments[i] );
    for (int j=i+1; j<ns; ++j) {
      const TTIntersection & sj( *segments[j] ); 
      itagged = (splitmap.find(i) != splitmap.end());
      jtagged = (splitmap.find(j) != splitmap.end());
      if (not itagged) {
        t = si.intersectsFace( sj.first() );
        if (t > gmepsilon and t < 1.0 - gmepsilon)
          splitmap[i] = t;
        t = si.intersectsFace( sj.second() );
        if (t > gmepsilon and t < 1.0 - gmepsilon)
          splitmap[i] = t;
      } else if (not jtagged) {
        t = sj.intersectsFace( si.first() );
        if (t > gmepsilon and t < 1.0 - gmepsilon)
          splitmap[j] = t;
        t = sj.intersectsFace( si.second() );
        if (t > gmepsilon and t < 1.0 - gmepsilon)
          splitmap[j] = t;
      }
    }
  }

  dbprint(splitmap.size(), "intersection segments will be split.");
  
  last = splitmap.end();
  for (itm = splitmap.begin(); itm != last; ++itm) {
    segments.push_back( segments[itm->first]->split(itm->second) );
  }
}

void TTiTopology::fixate()
{
  const int ns = segments.size();
  {
    Indices lmap(4*ns);
    for (int i=0; i<ns; ++i) {
      const TTIntersection & s( *segments[i] );
      lmap[4*i+0] = s.source();
      lmap[4*i+1] = i;
      lmap[4*i+2] = s.target();
      lmap[4*i+3] = i;
    }
    n2smap.assign(nodes.size(), lmap);
  }

  // assign surfaces and parameter positions to nodes
  Vct2 q1, q2;
  const uint nv = nodes.size();
  ConnectMap::const_iterator itr, slast;
  for (uint i=0; i<nv; ++i) {
    uint ctr[3] = {0, 0, 0};
    slast = n2smap.end(i);
    for (itr = n2smap.begin(i); itr != slast; ++itr) {
      const TTIntersection & s( *segments[*itr] );
      assert(s.source() == i or s.target() == i);
      if (s.source() == i) 
        s.srcParameter(q1, q2);
      else 
        s.trgParameter(q1, q2);
      nodes[i].addParametric(s.firstPatch(), q1, ctr);
      nodes[i].addParametric(s.secondPatch(), q2, ctr);
    }
    nodes[i].average(ctr);
    nodes[i].snapToBoundary(tolBound);
  }
}

uint TTiTopology::findLines()
{
  // debug
  {
    const int nn = n2smap.size();
    int n1(0), n2(0), n3(0);
    for (int i=0; i<nn; ++i) {
      int nnb = n2smap.size(i);
      if (nnb == 1)
        ++n1;
      else if (nnb == 2)
        ++n2;
      else
        ++n3;
    }
    dbprint("Connections:", n1, n2, n3);
  }


  lines.clear();
  const uint ns = segments.size();
  vector<bool> tag(ns, false);
  uint ntag(0);
  while (ntag < ns) {
  
    // currently processed line
    deque<uint> line;
    
    // pick first segment not tagged
    uint istart, iseg, inose, itail;
    for (iseg=0; iseg<ns; ++iseg) {
      if (not tag[iseg])
        break;
    }
    if (iseg == ns)
      break;
    
    istart = iseg;
    inose = segments[iseg]->source();
    itail = segments[iseg]->target();
    line.push_front(inose);
    tag[iseg] = true;
    ++ntag;
    
    // forward search (extend at nose) 
    while (n2smap.size(inose) == 2 and inose != itail
           and (not nodes[inose].onBoundary()))
    {
      const uint *nbs = n2smap.first(inose);
      assert(nbs[0] == iseg or nbs[1] == iseg);
      if (nbs[0] == iseg) 
        iseg = nbs[1];
      else
        iseg = nbs[0];
      inose = segments[iseg]->opposed(inose);
      assert(inose != NotFound);
      line.push_front(inose);
      tag[iseg] = true;
      ++ntag;
    }
    
    // backward search (extend at tail) 
    iseg = istart;
    line.push_back(itail);
    while (n2smap.size(itail) == 2 and inose != itail
           and (not nodes[itail].onBoundary()))
    {
      const uint *nbs = n2smap.first(itail);
      assert(nbs[0] == iseg or nbs[1] == iseg);
      if (nbs[0] == iseg) 
        iseg = nbs[1];
      else 
        iseg = nbs[0];
      itail = segments[iseg]->opposed(itail);
      assert(itail != NotFound);
      line.push_back(itail);
      tag[iseg] = true;
      ++ntag;
    }
    
    // consider this line closed
    lines.push_back(line);
  }
  return lines.size();
}

void TTiTopology::refine()
{
  // TODO embarassingly parallel!
  // iteratively refine intersection nodes, but limit motion to half 
  // the shortest attached segment length 
  const int nnodes(nodes.size());
  for (int i=0; i<nnodes; ++i) {
    const int ns = n2smap.size(i);
    const uint *nbs = n2smap.first(i);
    Real slen = huge;
    for (int k=0; k<ns; ++k) {
      Real len = segments[nbs[k]]->length();
      slen = min(slen, len);
    }
    slen *= 0.4;
    nodes[i].reproject(16, slen, 1e-6);
  }
}

void TTiTopology::filter(uint jline)
{
  deque<uint> tmp;
  deque<uint> & line( lines[jline] );
  const int n = line.size();
  if (n < 3)
    return;
  
  // always keep first and last point
  uint ndrop(0);
  Real maxlen, minlen, maxphi;
  Real phi, ephi, vphi;
  tmp.push_back(line.front());
  for (int i=1; i<n-1; ++i) {
    const TTiNode & nlast( nodes[tmp.back()] );
    const TTiNode & nhere( nodes[line[i]] );
    const TTiNode & nnext( nodes[line[i+1]] );

//    // keep all nodes marked as enforced in any case
//    if (nhere.enforced()) {
//      tmp.push_back(line[i]);
//      continue;
//    }

    // compute geometric filtering criteria
    Real pdst = norm( nlast.location() - nhere.location() );
    Real ndst = norm( nhere.location() - nnext.location() );
    Real dst = norm( nlast.location() - nnext.location() );

    // determine local filter criteria
    nhere.localCriteria(maxlen, minlen, maxphi);

    // if the length already exceeds maxlen, there is no discussion.
    if (dst > maxlen) {
      tmp.push_back(line[i]);
      continue;
    }
      
    // likewise, if the angle between normals is already too large
    vphi = arg( nlast.normal(), nnext.normal() );
    if (i < n-2) {
      const TTiNode & n3xt( nodes[line[i+2]] );
      ephi = arg( n3xt.location() - nnext.location(),
                  nnext.location() - nlast.location() );
    } else {
      ephi = arg( nnext.location() - nhere.location(),
                  nhere.location() - nlast.location() );
    }
    
    phi = max(vphi, ephi);
    if (phi > maxphi or (phi > 0.5*maxphi and dst > minlen)) {
      tmp.push_back(line[i]);
      continue;      
    }
    
    // if the distance from last to current is not even minlen,
    // then drop definitely (probably a micrometer edge anyway)
    if (dst < minlen or pdst < 0.5*minlen or ndst < 0.5*minlen) {
      ++ndrop;
      continue;
    }
    
    // compare dst to the local dimensions
    Real loclen = localLength(line[i]);
    if (dst > 2*loclen) {
      tmp.push_back(line[i]);
      continue;
    }
    
    ++ndrop;
    
    // otherwise drop
  }
  tmp.push_back(line.back());
  line.swap(tmp);
}

Real TTiTopology::localLength(uint k) const
{
  Real lmin(huge);
  ConnectMap::const_iterator slast, itr;
  slast = n2smap.end(k);
  for (itr = n2smap.begin(k); itr != slast; ++itr) 
    lmin = min(lmin, segments[*itr]->localDimension());
  return lmin;
}

bool TTiTopology::projection(uint k, const MeshComponent *c, 
                             PointList<2> & ppt, PointList<3> & vtx) const
{
  assert(k < lines.size());
  const deque<uint> & line( lines[k] );
  const int np = line.size();
  ppt.resize(np);
  vtx.resize(np);
  for (int i=0; i<np; ++i) {
    const TTiNode & nd( nodes[line[i]] );
    vtx[i] = nd.location();
    uint si = nd.index(c);
    if (si == NotFound)
      return false;
    else
      ppt[i] = nd.parameter(si);
  }
  
  return true;
}

void TTiTopology::addLineViz(MeshFields & mvz) const
{
  const int off = mvz.nvertices();
  const int nv = nodes.size();
  for (int i=0; i<nv; ++i)
    mvz.addMarker( mvz.addVertex(nodes[i].location()) );
  
  if (lines.empty()) {
    const int ns = segments.size();
    for (int i=0; i<ns; ++i) {
      const TTIntersection & s( *segments[i] );
      mvz.addLine2( off+s.source(), off+s.target() );
    }
  } else {
    for (uint j=0; j<lines.size(); ++j) {
      const deque<uint> & line( lines[j] );
      const int n = line.size();
      for (int i=1; i<n; ++i)
        mvz.addLine2( off+line[i-1], off+line[i] );
    }
  }   
}

void TTiTopology::spotRefinement(const MeshComponent *c, 
                                 Real smax, RSpotArray & sra) const
{
  sra.clear();
  
  Vct3 elen1, elen2;
  const int nseg = segments.size();
  for (int i=0; i<nseg; ++i) {
    
    const uint *vi(0);
    const TTIntersection & tti(*segments[i]);
    if (tti.firstPatch() == c) {
      const TriFace & f1( tip->face(tti.first()) );
      const TriFace & f2( tip->face(tti.second()) );
      f1.edgeLengths(elen1);
      f2.edgeLengths(elen2);
      vi = f1.vertices();
    } else if (tti.secondPatch() == c) {
      const TriFace & f2( tip->face(tti.first()) );
      const TriFace & f1( tip->face(tti.second()) );
      f1.edgeLengths(elen1);
      f2.edgeLengths(elen2);
      vi = f1.vertices();
    } else {
      continue;
    }
    
    // compare by sum of edge lengths
    elen1[0] += elen1[1] + elen1[2];
    elen2[0] += elen2[1] + elen2[2];
    
    // size ratio > 1 if triangle on c has longer longest edge
    Real sratio = elen1[0] / elen2[0];
    if (sratio > smax) 
      sra.push_back( SpotRefine(*c, vi, sratio) );
  }
  
  SpotRefine::mergeOverlaps(sra);
}

void TTiTopology::affectedVertices(const MeshComponent *c, Indices & vlist) const
{
  vlist.clear();
  
  const int nseg = segments.size();
  for (int i=0; i<nseg; ++i) {
    
    Real sr = 1.0;
    const uint *vi(0);
    const TTIntersection & tti(*segments[i]);
    if (tti.firstPatch() == c) {
      const TriFace & f1( tip->face(tti.first()) );
      const TriFace & f2( tip->face(tti.second()) );
      vi = f1.vertices();
      sr = norm(f1.normal()) / norm(f2.normal());
    } else if (tti.secondPatch() == c) {
      const TriFace & f1( tip->face(tti.first()) );
      const TriFace & f2( tip->face(tti.second()) );
      vi = f2.vertices();
      sr = norm(f2.normal()) / norm(f1.normal());
    } else { 
      continue;
    }
    
    // if the size of the triangle on c is less than the size of
    // the other one, please don't split it further
    if (sr < 0.8)
      continue;
    
    for (int k=0; k<3; ++k)
      insert_once(vlist, vi[k]);
  }
}

