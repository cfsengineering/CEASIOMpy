
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
 #include "toposegmchain.h"
#include "topoisecsegment.h"
#include "topology.h"
#include "topoedge.h"
#include "uvpolyline.h"
#include "sides.h"
#include <genua/ndpointtree.h>
#include <genua/dbprint.h>

using namespace std;

void TopoSegmChain::mergeVertices(Real threshold)
{
  m_vtx.clear();

  // collect all points on intersections
  Indices repl, keep;
  const int nis = m_segm.size();
  if (nis == 0)
    return;

  PointList<3> isp(2*nis);
  for (int i=0; i<nis; ++i) {
    isp[2*i+0] = m_segm[i].psource();
    isp[2*i+1] = m_segm[i].ptarget();
  }

  NDPointTree<3,double> ptree;
  ptree.allocate(isp, true, 4);
  ptree.sort();
  ptree.repldup(threshold, repl, keep);

  const int nk = keep.size();
  m_vtx.resize(nk);
  for (int i=0; i<nk; ++i)
    m_vtx[i] = isp[keep[i]];

  for (int i=0; i<nis; ++i)
    m_segm[i].assign( repl[2*i+0], repl[2*i+1] );
}

int TopoSegmChain::mapSegments()
{
  // first, determine vertex count
  const int nis = m_segm.size();
  if (nis == 0)
    return 0;

  int nv = 0;
  for (int i=0; i<nis; ++i) {
    nv = std::max( nv, int(m_segm[i].source()) );
    nv = std::max( nv, int(m_segm[i].target()) );
  }
  ++nv;

  // construct a connectivity m_map from vertex to m_segment index
  m_map.beginCount(nv);
  for (int i=0; i<nis; ++i) {
    m_map.incCount( m_segm[i].source() );
    m_map.incCount( m_segm[i].target() );
  }
  m_map.endCount();
  for (int i=0; i<nis; ++i) {
    m_map.append( m_segm[i].source(), i );
    m_map.append( m_segm[i].target(), i );
  }
  m_map.compress();

  // debug
  uint nc[4] = {0,0,0,0};
  for (int i=0; i<nv; ++i) {
    uint k = m_map.size(i);
    if (k > 3)
      ++nc[3];
    else
      ++nc[k];
  }
  dbprint("Map: ", nc[0], nc[1], nc[2], nc[3]);

  return nv;
}

int TopoSegmChain::onBoundary(uint s, uint v) const
{
  assert(s < m_segm.size());
  const TopoIsecSegment & seg( m_segm[s] );
  int b = none;
  if (seg.source() == v) {
    b = whichside( seg.asource() );
    if (b != none)
      return b;
    b = whichside( seg.bsource() );
    if (b != none)
      return b;
  } else {
    assert(v == seg.target());
    b = whichside( seg.atarget() );
    if (b != none)
      return b;
    b = whichside( seg.btarget() );
    if (b != none)
      return b;
  }
  return b;
}

uint TopoSegmChain::extractTopology(const Topology &topo, Real threshold)
{
  m_segm.clear();
  topo.intersect(m_segm);
  dbprint(m_segm.size(),"Intersection segments.");
  if (m_segm.empty())
    return 0;

  mergeVertices(threshold);
  mapSegments();

  // assemble chains
  m_vchains.clear();
  m_schains.clear();
  const int nis = m_segm.size();
  vector<bool> segTag(nis, false);
  int nsu = 0;

  IdxChain vchain, schain;
  IndexPair sfp;
  bool forward = true;
  do {

    // find next m_segment to use if chain is empty
    if (vchain.empty()) {
      for (int i=0; i<nis; ++i) {
        if (segTag[i])
          continue;
        schain.push_back( i );
        vchain.push_back( m_segm[i].source() );
        vchain.push_back( m_segm[i].target() );
        sfp = m_segm[i].facePair();
        segTag[i] = true;
        ++nsu;
        break;
      }
      forward = true;
     // dbprint("Initialized chain with segment: ",schain.back());
    }

    assert(not vchain.empty());
    assert(not schain.empty());

    uint vcur, scur, nxseg(NotFound), next(NotFound);
    vcur = forward ? vchain.back() : vchain.front();
    scur = forward ? schain.back() : schain.front();

    // look for next vertex to pick as long as current vertex is not on
    // a parameter space boundary
    if (onBoundary(scur, vcur) == none) {
      const int nseg = m_map.size(vcur);
      if (nseg == 2) {
        const uint *iseg = m_map.first(vcur);
        for (int k=0; k<2; ++k) {
          uint ks = iseg[k];
          if ( (not segTag[ks]) and m_segm[ks].onFaces(sfp) ) {
            ++nsu;
            segTag[ks] = true;
            nxseg = ks;
            next = m_segm[ks].opposed(vcur);
            assert(next != NotFound);
            break;
          }
        }
      }
    } // fall through with next == NotFound when vcur on boundary
//    else {
//      dbprint(scur, "on boundary");
//    }

    if (forward) {
      if (next != NotFound) {
        vchain.push_back(next);
        schain.push_back(nxseg);
        //dbprint("fsaved",nxseg,next,m_vtx[next]);
      } else {
        //dbprint("switching to backward");
        forward = false;
      }
    } else {
      if (next != NotFound) {
        vchain.push_front(next);
        schain.push_front(nxseg);
        // dbprint("bsaved",nxseg,next,m_vtx[next]);
      } else {
        dbprint("Detected chain: ",vchain.size(),"on",sfp.first,sfp.second);
        m_vchains.push_back( vchain );
        m_schains.push_back( schain );
        m_sfp.push_back( sfp );
        vchain.clear();
        schain.clear();
      }
    }

  } while (nsu < nis);

  // store last chain
  if (not vchain.empty()) {
    dbprint("Detected chain: ",vchain.size(),"on",sfp.first,sfp.second);
    m_vchains.push_back( vchain );
    m_schains.push_back( schain );
    m_sfp.push_back( sfp );
  }

  dbprint(m_vchains.size(),"chains identified.");
  return m_vchains.size();
}

uint TopoSegmChain::generateEdge(Topology &topo, uint k) const
{
  assert(k < m_vchains.size());

  const IdxChain & vchain( m_vchains[k] );
  const IdxChain & schain( m_schains[k] );
  const uint ifa = m_sfp[k].first;
  const uint ifb = m_sfp[k].second;

  const int np = vchain.size();
  if (np == 0)
    return NotFound;

  assert(uint(np) == schain.size() + 1);
  PointList<2> uva(np), uvb(np);
  PointList<3> cp(np);
  for (int i=0; i<np; ++i) {

    const uint v = vchain[i];
    cp[i] = m_vtx[v];
    const uint iseg = (i > 0) ? schain[i-1] : schain[0];
    const TopoIsecSegment &seg( m_segm[iseg] );
    const uint src = seg.source();
    if (v == src) {
      uva[i] = seg.asource();
      uvb[i] = seg.bsource();
    } else {
      assert(v == seg.target());
      uva[i] = seg.atarget();
      uvb[i] = seg.btarget();
    }
  }

  // construct common parameterization
  Vector tp(np);
  for (int i=1; i<np; ++i)
    tp[i] = tp[i-1] + norm(cp[i] - cp[i-1]);
  tp /= tp.back();
  tp.front() = 0.0;
  tp.back() = 1.0;

  // parameter-space curves on surfaces
  AbstractUvCurvePtr cva, cvb;
  cva = boost::make_shared<UvPolyline>(topo.face(ifa).surface(), tp, uva);
  cvb = boost::make_shared<UvPolyline>(topo.face(ifb).surface(), tp, uvb);

  // create new topological vertices
  uint vxfront, vxback;
  vxfront = topo.findVertex( ifa, uva.front() );
  if (vxfront != NotFound) {
    topo.vertex(vxfront).append( ifb, uvb.front() );
  } else {
    vxfront = topo.findVertex( ifb, uvb.front() );
    if (vxfront != NotFound)
      topo.vertex(vxfront).append( ifa, uva.front() );
    else
      vxfront = topo.appendVertex( ifa, uva.front(), ifb, uvb.front() );
  }

  vxback = topo.findVertex( ifa, uva.back() );
  if (vxback != NotFound) {
    topo.vertex(vxback).append( ifb, uvb.back() );
  } else {
    vxback = topo.findVertex( ifb, uvb.back() );
    if (vxback != NotFound)
      topo.vertex(vxback).append( ifa, uva.back() );
    else
      vxback = topo.appendVertex( ifa, uva.back(), ifb, uvb.back() );
  }

  // reject degenerate edges (points)
  if ((vxfront == vxback) and (np == 2))
    return NotFound;

  TopoEdge edge;
  edge.assign(vxfront, vxback);
  edge.edgeOrigin( TopoEdge::Intersection );
  edge.attachFace(ifa, cva);
  edge.attachFace(ifb, cvb);
  edge.discretize(tp);

  // register edges with faces
  return topo.appendEdge(edge);
}


