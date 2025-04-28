
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
 #include "topology.h"
#include "abstractuvcurve.h"
#include "planesurface.h"
#include "uvpolyline.h"
#include "uvsplinecurve.h"
#include "lazyisectree.h"
#include "topoisecsegment.h"
#include "sides.h"
#include <genua/dbprint.h>
#include <genua/trimesh.h>
#include <genua/ndpointtree.h>
#include <genua/mxmesh.h>
#include <atomic>
#include <iostream>

#ifdef HAVE_TBB
#include <tbb/parallel_for.h>
#endif

using namespace std;

uint Topology::appendVertex(uint iface, const Vct2 &uvp)
{
  m_vertices.push_back( TopoVertex(*this, iface, uvp) );
  return m_vertices.size() - 1;
}

uint Topology::appendVertex(uint ifa, const Vct2 &uva,
                            uint ifb, const Vct2 &uvb)
{
  m_vertices.push_back( TopoVertex(*this, ifa, uva, ifb, uvb) );
  return m_vertices.size() - 1;
}

bool Topology::vEnchain(const SurfaceArray &surfaces)
{
  if (surfaces.empty())
    return true;

  bool matching = true;
  uint ifirst, iprev, iface, nsf = surfaces.size();
  ifirst = iprev = appendFace( surfaces.front(), true, false );
  for (uint i=1; i<nsf; ++i) {
    iface = appendFace( surfaces[i], true, false );
    matching &= vEnchain(iprev, iface);
    iprev = iface;
  }

  return matching;
}

uint Topology::findVertex(uint iface, const Vct2 &uvp)
{
  const int nv = m_vertices.size();
  for (int i=0; i<nv; ++i) {
    const TopoVertex & v( m_vertices[i] );
    uint lfi = v.findFace(iface);
    if (lfi == NotFound)
      continue;
    if ( sq(uvp - v.uvpos(lfi)) < gmepsilon )
      return i;
  }
  return NotFound;
}

uint Topology::findConnection(uint iface, uint sideTag, Real tol) const
{
  assert(sideTag < none);
  switch (sideTag) {
  case west:
    return findConnection(iface, Vct2(0,0), Vct2(0,1), tol);
  case north:
    return findConnection(iface, Vct2(0,1), Vct2(1,1), tol);
  case east:
    return findConnection(iface, Vct2(1,1), Vct2(1,0), tol);
  case south:
    return findConnection(iface, Vct2(1,0), Vct2(0,0), tol);
  default:
    return NotFound;
  }
  return NotFound;
}

uint Topology::appendEdge(uint iface, uint a, uint b)
{
  TopoEdge e(*this, iface, a, b);
  m_edges.push_back(e);
  return m_edges.size() - 1;
}

uint Topology::appendEdge(const TopoEdge &edg)
{
  const uint eix = m_edges.size();
  m_edges.push_back(edg);
  for (uint i=0; i<edg.nfaces(); ++i)
    face( edg.face(i) ).appendEdge(eix);
  return eix;
}

uint Topology::appendFace(SurfacePtr psf, bool uperiodic, bool vperiodic)
{
  uint ied, iface = m_faces.size();
  TopoFace f(psf, iface);
  m_faces.push_back(f);

  // generate corner vertices
  // v4,v1 at u = 0.0
  // v2,v3 at u = 1.0
  // v1,v2 at v = 0.0
  // v3,v4 at v = 1.0
  uint v1 = appendVertex(iface, Vct2(0.0, 0.0));
  uint v2 = appendVertex(iface, Vct2(1.0, 0.0));
  uint v3 = appendVertex(iface, Vct2(1.0, 1.0));
  uint v4 = appendVertex(iface, Vct2(0.0, 1.0));

  // boundary edges
  // uperiodic means that psf(0.0, v) == psf(1.0, v) for all v
  // vperiodic means that psf(u, 0.0) == psf(u, 1.0) for all u
  AbstractUvCurvePtr opcv;
  if (uperiodic and vperiodic) {

    ied = appendEdge(iface, v1, v4);
    m_faces[iface].appendEdge(ied);
    opcv = TopoEdge::boundaryCurve(*this, iface, v2, v3);
    m_edges[ied].attachFace(iface, opcv);

    ied = appendEdge(iface, v1, v2);
    m_faces[iface].appendEdge(ied);
    opcv = TopoEdge::boundaryCurve(*this, iface, v4, v3);
    m_edges[ied].attachFace(iface, opcv);

  } else if (uperiodic) {

    ied = appendEdge(iface, v1, v4);
    m_faces[iface].appendEdge(ied);
    opcv = TopoEdge::boundaryCurve(*this, iface, v2, v3);
    m_edges[ied].attachFace(iface, opcv);

    m_faces[iface].appendEdge(appendEdge(iface, v1, v2));
    m_faces[iface].appendEdge(appendEdge(iface, v3, v4));

  } else if (vperiodic) {

    ied = appendEdge(iface, v1, v2);
    m_faces[iface].appendEdge(ied);
    opcv = TopoEdge::boundaryCurve(*this, iface, v4, v3);
    m_edges[ied].attachFace(iface, opcv);

    m_faces[iface].appendEdge(appendEdge(iface, v1, v4));
    m_faces[iface].appendEdge(appendEdge(iface, v2, v3));

  } else {

    m_faces[iface].appendEdge(appendEdge(iface, v1, v4));
    m_faces[iface].appendEdge(appendEdge(iface, v1, v2));
    m_faces[iface].appendEdge(appendEdge(iface, v3, v4));
    m_faces[iface].appendEdge(appendEdge(iface, v2, v3));

  }

  return iface;
}

uint Topology::appendFace(const TopoFace &f)
{
  const uint idx = m_faces.size();
  m_faces.push_back(f);
  m_faces.back().iid(idx);
  return idx;
}

bool Topology::shareEdge(uint i, uint j) const
{
  assert(i < m_faces.size());
  assert(j < m_faces.size());

  const Indices &edi = m_faces[i].edges();
  const int ne = edi.size();
  for (int k=0; k<ne; ++k) {
    if (m_edges[edi[k]].findFace(j) != NotFound)
      return true;
  }

  return false;
}

void Topology::connectEdge(uint fa, uint ea,
                           AbstractUvCurvePtr pcv, bool isHole)
{
  assert(fa < m_faces.size());
  assert(ea < m_edges.size());
  face(fa).appendEdge(ea, isHole);
  edge(ea).attachFace(fa, pcv);
}

bool Topology::connectFaces(uint, uint b, uint ea, uint eb, Real tol)
{
  if (ea == NotFound or eb == NotFound) {
    dbprint("Trying to connect non-existing edges: ", ea, eb);
    return false;
  }
  if (b == NotFound) {
    dbprint("Trying to connect non-existing face.");
    return false;
  }

  // assert(a < m_faces.size());
  assert(b < m_faces.size());
  assert(ea < m_edges.size());
  assert(eb < m_edges.size());

  // argument a is kept for later use
  // TopoFace &fca( m_faces[a] );
  TopoFace &fcb( m_faces[b] );
  TopoEdge &eda( m_edges[ea] );
  TopoEdge &edb( m_edges[eb] );

  const int cmp = eda.compare(*this, edb, tol);
  bool rev = false;
  if (cmp == TopoEdge::ForwardFit) {
    dbprint("Edges match.");
    rev = false;
  } else if (cmp == TopoEdge::ReverseFit) {
    dbprint("Edges match when reversed.");
    rev = true;
  } else {
    dbprint("Edges to merge do not match at all.");
    return false;
  }

  // merge vertices on face b into those on face a
  TopoVertex &vas = vertex( eda.source() );
  TopoVertex &vat = vertex( eda.target() );
  const TopoVertex &vbs = vertex( edb.source() );
  const TopoVertex &vbt = vertex( edb.target() );

  const uint ekb = edb.findFace(b);
  if (ekb == NotFound) {
    dbprint("Face",b,"is not adjacent to edge",eb);
    return false;
  }

  // extract curve of edge eb on face b; clone curve so that changes
  // (reversal) do not affect original curve on face b
  AbstractUvCurvePtr cb(static_cast<AbstractUvCurve*>(edb.curve(ekb)->clone()));

  // nothing has been modified up to this point
  //
  // merge vertices on face a which match their neighbors to within tol in 3D
  // space with those on face b, while considering the possible change
  // in edge direction
  if (rev) {
    cb->reverse();
    vas.merge(vbt);
    vat.merge(vbs);
  } else {
    vas.merge(vbs);
    vat.merge(vbt);
  }

  // attach face b to edge ea, along with curve on b
  eda.attachFace(b, cb);
  edb.detachFace(b);

  // make face b use edge ea instead of eb
  fcb.replaceEdge(eb, ea);

  return true;
}

bool Topology::connectFaces(uint fa, uint fb, Real tol)
{
  const Indices &efa( face(fa).edges() );
  const Indices &efb( face(fb).edges() );
  for (uint ea : efa) {
    for (uint eb : efb) {
      const int cmp = edge(ea).compare(*this, edge(eb), tol);
      if (cmp == TopoEdge::ForwardFit or cmp == TopoEdge::ReverseFit)
        return connectFaces(fa, fb, ea, eb, tol);
    }
  }

  return false;
}

bool Topology::vEnchain(uint a, uint b, Real tol)
{
  assert(a < m_faces.size());
  assert(b < m_faces.size());

  // find v = 1 boundary on a
  uint ea(NotFound), eb(NotFound);
  {
    const Vct2 s(0.0, 1.0);
    const Vct2 t(1.0, 1.0);
    const Indices & vea( m_faces[a].edges() );
    for (uint i=0; i<vea.size(); ++i) {
      assert(vea[i] < m_edges.size());
      int fit = m_edges[vea[i]].connects(a, s, t, tol);
      if (fit != TopoEdge::NoMatch) {
        ea = vea[i];
        break;
      }
    }
  }

  // abort if the upper v-boundary of a could not be located
  if (ea == NotFound)
    return false;

  // find v = 0 boundary on b
  {
    const Vct2 s(0.0, 0.0);
    const Vct2 t(1.0, 0.0);
    const Indices & vea( m_faces[b].edges() );
    for (uint i=0; i<vea.size(); ++i) {
      assert(vea[i] < m_edges.size());
      int fit = m_edges[vea[i]].connects(b, s, t, tol);
      if (fit != TopoEdge::NoMatch) {
        eb = vea[i];
        break;
      }
    }
  }

  // abort if the lower v-boundary of b could not be located
  if (eb == NotFound)
    return false;

  return connectFaces(a, b, ea, eb);
}

uint Topology::fillPlaneBoundary(uint ebound)
{
  if (ebound >= m_edges.size())
    return NotFound;

  TopoEdge & edg( m_edges[ebound] );
  assert(edg.npoints() >= 3);
  const int np = edg.npoints();
  PointList<3> pts(np);
  for (int i=0; i<np; ++i)
    pts[i] = edg.point(i);

  // construct plane surface
  PlaneSurfacePtr pps;
  pps = boost::make_shared<PlaneSurface>("PlaneCap"+str(ebound));
  pps->init(pts, 1.5);

  // create face for cap surface
  SurfacePtr psf(pps);
  uint iface = m_faces.size();
  {
    TopoFace capface(psf, iface);
    capface.appendEdge(ebound);
    m_faces.push_back(capface);
  }

  // compute edge points on cap face
  PointList<2> qcap(np);
  for (int i=0; i<np; ++i)
    pps->project( edg.point(i), qcap[i], 0.0, 0.0 );
  edg.attachFace(iface, boost::make_shared<UvPolyline>(psf,
                                                       edg.pattern(), qcap));

  return iface;
}

void Topology::meshEdges()
{
  // trivially parallel
  const int ne = m_edges.size();
  for (int i=0; i<ne; ++i)
    m_edges[i].discretize(*this);
}

void Topology::meshFaces(bool allowConstraintSplit)
{
  const int nf = m_faces.size();
  std::atomic_int needEdgeUpdate;
  needEdgeUpdate.store(0);

//#ifdef HAVE_TBB

//  tbb::parallel_for( 0, nf, [&](int i)
//  {
//    if (not m_faces[i].keepExplicitMesh()) {
//      uint nvc = 0;
//      m_faces[i].clearMesh();
//      nvc  = m_faces[i].insertEdges(*this, allowConstraintSplit);
//      nvc += m_faces[i].generateMesh(*this);
//      needEdgeUpdate |= (nvc > 0);
//    }
//  } );

//#else

//#pragma omp parallel for schedule(dynamic,1)
  for (int i=0; i<nf; ++i) {

    if (m_faces[i].keepExplicitMesh()) {
      continue;
    }

    uint nvc = 0;
    m_faces[i].clearMesh();
    nvc  = m_faces[i].insertEdges(*this, allowConstraintSplit);
    nvc += m_faces[i].generateMesh(*this);
    needEdgeUpdate |= (nvc > 0);
  }

//#endif

  if (needEdgeUpdate != 0) {

    // update edge discretization to reflect points inserted
    // on intersection edges by neighbor faces
    for (int i=0; i<nf; ++i) {
      if (m_faces[i].keepExplicitMesh())
        continue;
      m_faces[i].pushSplitsToEdges(*this);
    }

    // once complete, push new edge discretizations to faces
    for (int i=0; i<nf; ++i) {
      if (m_faces[i].keepExplicitMesh())
        continue;
      m_faces[i].insertEdges(*this, allowConstraintSplit);
    }
  }
}

void Topology::mergeFaceMeshes(TriMesh &globMesh) const
{
  const int nf = nfaces();
  for (int i=0; i<nf; ++i) {
    globMesh.merge( m_faces[i].mesh() );
    globMesh.tagName( i, m_faces[i].surface()->name() );
  }
}

void Topology::intersect(TopoIsecArray &segm) const
{
  // generate trees first
  const int nf = nfaces();
  std::vector<LazyIsecTree> tree(nf);

  // trivially parallel, but not much work (only root node processed)
  for (int i=0; i<nf; ++i) {
    tree[i] = LazyIsecTree( &(face(i).mesh()) );
  }

  // serial, while testing
  bool parallel = false;

  // compute all intersections
  IndexPairArray pairs;
  PointList<3> ipoints;
  segm.clear();
  for (int i=0; i<nf; ++i) {
    for (int j=i+1; j<nf; ++j) {

      // do not test for intersections when faces share an edge
      if ( shareEdge(i,j) )
        continue;

      pairs.clear();
      ipoints.clear();
      tree[i].intersect(tree[j], pairs, parallel);
      tree[i].segments(tree[j], pairs, ipoints);
      TopoIsecSegment::append(i, j, pairs, ipoints, segm);
    }
  }

  const int nis = segm.size();
  for (int i=0; i<nis; ++i)
    segm[i].uvMap(*this);
}

void Topology::toMx(MxMesh &mx) const
{
  for (uint i=0; i<nfaces(); ++i) {
    uint isec = mx.appendSection( face(i).mesh() );
    mx.section(isec).rename( face(i).surface()->name() );
  }

  for (uint i=0; i<nedges(); ++i)
    edge(i).toMx( mx );
}

void Topology::print(std::ostream &os) const
{
  os << "Topology: "<< endl;
  for (uint i=0; i<m_faces.size(); ++i)
    m_faces[i].print(i, os);
  for (uint i=0; i<m_edges.size(); ++i)
    m_edges[i].print(i, os);
  for (uint i=0; i<m_vertices.size(); ++i)
    m_vertices[i].print(i, os);
}

