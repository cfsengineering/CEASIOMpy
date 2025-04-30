
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
 #include "topoface.h"
#include "topoedge.h"
#include "topology.h"
#include "dcedge.h"
#include "dcmeshcrit.h"
#include "dcmeshgenerator.h"
#ifdef HAVE_JRSTRIANGLE
#include "jrstriangle/jrsmeshgenerator.h"
#endif
#include <genua/flagset.h>
#include <genua/trimesh.h>
#include <genua/xcept.h>
#include <genua/pattern.h>
#include <genua/dbprint.h>
#include <genua/timing.h>
#include <genua/mxmesh.h>
#include <genua/ndpointtree.h>
#include <iostream>

using namespace std;

int TopoFace::s_backend = TopoFace::DcMeshGen;

TopoFace::TopoFace() : m_iid(NotFound), m_keepExplicitMesh(false)
{
  constructMeshGen();
}

TopoFace::TopoFace(SurfacePtr psf, uint id)
  : m_psf(psf), m_iid(id), m_keepExplicitMesh(false)
{
  constructMeshGen();
  m_mg->initMap(m_psf);
}

void TopoFace::constructMeshGen()
{
#ifdef HAVE_JRSTRIANGLE
  if (s_backend == JrsTriangle)
    m_mg = boost::make_shared<JrsMeshGenerator>();
  else
    m_mg = boost::make_shared<DcMeshGenerator>();
#else
  m_mg = boost::make_shared<DcMeshGenerator>();
#endif
}

uint TopoFace::generateMesh(const Topology &topo)
{
  // we need at least some initial points; since the user didn't pass any,
  // lets generate some default values
  const int niu(8);
  const int niv(8);
  Real du = 1.0 / (niu + 1);
  Real dv = 1.0 / (niv + 1);
  PointList<2> pini(niu*niv);
  for (int i=0; i<niu; ++i)
    for (int j=0; j<niv; ++j)
      pini[i*niv+j] = Vct2((i+1)*du, (j+1)*dv);

  return generateMesh(topo, pini);
}

uint TopoFace::generateMesh(const Topology &topo, const PointList<2> &pini)
{
  dbprint("generateMesh on ", surface()->name());
  assert(m_psf);
  assert(m_pmc);

  m_keepExplicitMesh = false;

  if (m_mg->surface() != m_psf)
    m_mg->initMap(m_psf);

  // mark holes resulting from internal boundaries
  for (size_t i=0; i<m_edges.size(); ++i) {
    if (m_edgeIsHole[i]) {
      dbprint("Punching hole for edge ", m_edges[i]);
      carveHole( topo.edge( m_edges[i] ) );
    }
  }

  // initialize with segments and initial point set and carve holes,
  // then refine according to criterion
  m_mg->generate(pini);
  m_mg->faceTag(m_iid);

  replaceEdgeNodes(topo, false);
  return 0;

//  // -------------------------------------------------------------------

//  dbprint("generateMesh on ", surface()->name());
//  assert(m_psf);
//  assert(m_pmc);
//  assert(m_pmg);

//  Wallclock clk;
//  clk.start();

//  m_keepExplicitMesh = false;

//  UvMapDelaunay & mg( *m_pmg );
//  mg.removeOutsideCorners();
//  mg.enableExtension(false);

//  // reset list of vertices inserted on constraints
//  mg.verticesOnConstraints().clear();

//  if (mg.nfaces() == 0) {
//    m_mg->clear();
//    dbprint("Face",surface()->name(),"eliminated; no closed constraints.");
//    return 0;
//  }

//  // insert initial points
//  const size_t nini = pini.size();
//  for (size_t i=0; i<nini; ++i)
//    mg.insertVertex(pini[i]);

//  // perform mesh refinement in the interior domain
//  mg.refineInternal(*m_pmc);

//  clk.stop();
//  cout << "Refinement: " << clk.elapsed() << endl;

//  clk.start();
//  mg.smooth(m_pmc->nSmooth(), m_pmc->wSmooth());
//  clk.stop();
//  cout << "Smoothing: " << clk.elapsed() << endl;

//  // carve out internal boundaries
//  for (size_t i=0; i<m_edges.size(); ++i) {
//    if (m_edgeIsHole[i]) {
//      dbprint("Carving hole for edge ", m_edges[i]);
//      carveHole( topo.edge( m_edges[i] ) );
//    }
//  }

//  clk.start();
//  m_uvp = mg.uvVertices();
//  Indices tri;
//  mg.triangles(tri);

//  m_mg->clear();
//  m_mg->importMesh(mg.xyzVertices(), mg.xyzNormals(), tri, false);
//  m_mg->faceTag(m_iid);

//  replaceEdgeNodes(topo, false);

//  clk.stop();
//  cout << "Vertex replacement: " << clk.elapsed() << endl;

//  // debug
//  cout << m_psf->name() << " : " << m_mg->nvertices() << " vertices." << endl;

//  return mg.verticesOnConstraints().size();
}

void TopoFace::importMesh(const PointList<2> &uvp, const Indices &tri,
                          bool keepExplicit)
{
  m_keepExplicitMesh = keepExplicit;
  m_mg->importMesh(uvp, tri, m_iid);

  // may need to call vertex replacement separately
}

void TopoFace::replaceEdgeNodes(const Topology &topo, bool isecOnly)
{
  // replace (x,y,z)-space positions of vertices on edges with position
  // of edge vertices in order to make intersecting surfaces match
  NDPointTree<2,Real> ptree;
  ptree.allocate( m_mg->uvVertices() , true, 4);
  ptree.sort();

  const int ne = m_edges.size();
  for (int i=0; i<ne; ++i) {
    const TopoEdge & edg( topo.edge( m_edges[i] ) );
    if (isecOnly and (edg.edgeOrigin() != TopoEdge::Intersection))
      continue;
    const int np = edg.npoints();
    const int nf = edg.nfaces();
    for (int jf=0; jf<nf; ++jf) {
      if (edg.face(jf) != m_iid)
        continue;
      for (int j=0; j<np; ++j) {
        uint inear = ptree.nearest( edg.uvpoint(jf, j) );
        m_mg->vertex(inear) = edg.point(j);
      }
    }
  }
}

const TriMesh &TopoFace::mesh() const
{
  assert(m_mg);
  const TriMesh &msh( *m_mg );
  return msh;
}

TriMesh &TopoFace::mesh()
{
  assert(m_mg);
  TriMesh &msh( *m_mg );
  return msh;
}

const PointList2d &TopoFace::uvVertices() const
{
  return m_mg->uvVertices();
}

bool TopoFace::carveHole(const TopoEdge &e)
{
  const int n = e.npoints();
  const uint li = e.findFace( m_iid );
  assert(li != NotFound);
  assert(n > 2);

  PointList2d poly(n);
  for (int i=0; i<n; ++i)
    poly[i] = e.uvpoint(li, i);

  if ( sq(poly.front() - poly.back()) > gmepsilon ) {
    dbprint("[W] Carving hole in open contour, may eliminate face!");
    dbprint("[W] First point:", poly.front());
    dbprint("[W] Last point: ", poly.back());
  }

  // march along polygon and generate test points along each segment;
  // if a test point is inside the polygon, use it to remove internal
  // triangles starting from that point
  for (int i=1; i<n; ++i) {
    const Vct2 &src( poly[i-1] );
    const Vct2 &trg( poly[i] );
    Vct2 crs, px[2];
    crs[0] = trg[1] - src[1];
    crs[1] = src[0] - trg[0];

    px[0] = 0.5*(src + trg + crs);
    px[1] = 0.5*(src + trg - crs);

    for (int k=0; k<2; ++k) {
      Real u = px[k][0];
      if (u <= 0.0 or u >= 1.0)
        continue;
      Real v = px[k][1];
      if (v <= 0.0 or v >= 1.0)
        continue;
      if ( point_in_polygon(poly, px[k]) ) {
        m_mg->punchHole(px[k]);
        return true;
      }
    }
  }

  return false;
}

void TopoFace::clearMesh()
{
  assert(m_psf);
  assert(m_mg);

  // initialize (u,v) -> (s,t) map when necessary
  if (m_mg->surface() != m_psf) {
    Wallclock clk;
    clk.start();
    m_mg->initMap(m_psf);
    clk.stop();
    cout << "UvMap initialization: " << clk.elapsed() << endl;
  }

  m_mg->clear();
}

uint TopoFace::insertEdges(const Topology &topo, bool allowSplit)
{
  assert(m_psf);
  assert(m_pmc);
  assert(m_mg);

  // flags for constrained edges
  int cflags = DcEdge::Constrained;
  if (not allowSplit)
    cflags |= DcEdge::NeverSplit;

  // enforce edge constraints
  PointList<2> ec;
  const int ne = m_edges.size();
  assert(ne != 0);
  for (int i=0; i<ne; ++i) {
    const TopoEdge & edg( topo.edge( m_edges[i] ) );
    const int np = edg.npoints();
    const int nf = edg.nfaces();
    ec.resize(np);
    for (int jf=0; jf<nf; ++jf) {

      // loop is not the same as edg.find(m_iid) because one edge can be
      // connected to the same face more than once (on seams)

      if (edg.face(jf) != m_iid)
        continue;

      for (int j=0; j<np; ++j)
        ec[j] = edg.uvpoint(jf, j);

      // inject edge points as a constraint into *this
      int nic = m_mg->enforceConstraint(ec, cflags);

      // dump mesh if constraint insertion failed; should never happen!
      if (nic != np) {
        // mg.dbgDump( m_psf->name() );
        throw Error("Constraint insertion failed: "+m_psf->name());
      }
      dbprint(m_psf->name(), " - inserted edge ",m_edges[i],"points:",np);
    }
  }

//  // debug
//  dbprint(ne,"edges inserted on face",m_psf->name(),
//          "constraints split:",mg.verticesOnConstraints().size());
//  uvDump(topo, m_psf->name()+"_post_edge_insert.zml");

  return 0; // mg.verticesOnConstraints().size();
}

void TopoFace::pushSplitsToEdges(Topology &) const
{
//  // FIXME: Algorithm not robust
//  // There are edge cases where the below method can inject nodes
//  // on the wrong topological edge when a point is exactly on one
//  // edge, but also closer than tol = 1e-6 to another which may be
//  // tested first.

//  assert(m_pmg);
//  UvMapDelaunay & mg( *m_pmg );
//  const Indices & voc( mg.verticesOnConstraints() );
//  const int nvp = voc.size();
//  std::vector<bool> injected(nvp, false);
//  if (not voc.empty()) {
//    const PointList<2> & puv( mg.uvVertices() );
//    const int ne = m_edges.size();
//    for (int ie=0; ie<ne; ++ie) {
//      TopoEdge & edg( topo.edge( m_edges[ie] ) );
//      const uint kf = edg.findFace(m_iid); assert(kf != NotFound);
//      for (int j=0; j<nvp; ++j) {
//        // this is called even for points in voc which are not even
//        // on this edge but on the opposite side of the face...
//        if (not injected[j])
//          injected[j] = edg.injectPoint(kf, puv[voc[j]], 1e-6);
//      }
//    }
//  }

//#ifndef NDEBUG
//  const PointList<2> & puv( mg.uvVertices() );
//  for (int i=0; i<nvp; ++i) {
//    if (not injected[i])
//      cerr << "Could not inject: " << puv[voc[i]] << endl;
//  }
//#endif

//  // debug
//  mg.dbgDump( surface()->name() );
}


void TopoFace::criterion(DcMeshCritBasePtr pmc)
{
  m_pmc = pmc->clone();
  m_mg->criterion(m_pmc);
}

Real TopoFace::sqMergeTolerance() const
{
//  if (m_pmg != nullptr)
//    return m_pmg->sqMergeTolerance();
//  else
    return sq(1e-7);
}

uint TopoFace::detachEdge(uint e)
{
  uint lix = findEdge(e);
  if (lix == NotFound)
    return lix;

  m_edges.erase( m_edges.begin() + lix );
  m_edgeIsHole.erase( m_edgeIsHole.begin() + lix );

  return lix;
}

uint TopoFace::findConnection(const Topology &topo,
                              const Vct2 &q1, const Vct2 &q2, Real tol) const
{
  const int ne = m_edges.size();
  for (int i=0; i<ne; ++i) {
    const TopoEdge &edg( topo.edge(m_edges[i]) );
    if (edg.connects(m_iid, q1, q2, tol) != TopoEdge::NoMatch) {
      return m_edges[i];
    }
  }
  return NotFound;
}

void TopoFace::uvDump(const Topology &topo, const string &fname) const
{
  const int nv = m_mg->uvVertices().size();
  PointList<3> uvp(nv);
  for (int i=0; i<nv; ++i)
    uvp[i] = Vct3(m_mg->uvVertices()[i][0], m_mg->uvVertices()[i][1], 0.0);

  const int nt = m_mg->nfaces();
  Indices tri(3*nt);
  for (int i=0; i<nt; ++i) {
    const uint *vi = m_mg->face(i).vertices();
    for (int j=0; j<3; ++j)
      tri[3*i+j] = vi[j];
  }

  MxMesh mx;

  // triangle mesh
  mx.appendNodes(uvp);
  mx.appendSection(Mx::Tri3, tri);

  // overlay edges
  const int ne = m_edges.size();
  for (int i=0; i<ne; ++i) {
    const TopoEdge &edg( topo.edge(m_edges[i]) );
    const uint kf = edg.findFace( m_iid );
    assert(kf != NotFound);
    const int np = edg.npoints();
    uvp.resize(np);
    for (int j=0; j<np; ++j) {
      Vct2 q = edg.uvpoint(kf, j);
      uvp[j] = Vct3(q[0], q[1], 0.0);
    }
    uint isec = mx.appendSection(uvp);
    mx.section(isec).rename("Edge "+str(m_edges[i]));
  }

  mx.toXml(true).zwrite(fname);
}

void TopoFace::splitBoundaries(Topology &topo)
{
  const int ne = m_edges.size();
  vector<bool> esplit(ne, false);
  Vector tsplit(ne);
  for (int i=0; i<ne; ++i) {
    const TopoEdge & ei( topo.edge(m_edges[i]) );
    if (ei.edgeOrigin() != TopoEdge::Specified)
      continue;
    for (int j=0; j<ne; ++j) {
      if (i == j)
        continue;
      const TopoEdge & ej( topo.edge(m_edges[j]) );
      if (ej.edgeOrigin() != TopoEdge::Intersection)
        continue;
      Vct2 tij;
      if ( TopoEdge::intersects(m_iid, ei, ej, tij) ) {
        esplit[i] = true;
        tsplit[i] = tij[0];
        dbprint("Split boundary edge",m_edges[i],"at",tij[0]);
      }
    }
  }

  // do not actually split, but insert point into discretization
  for (int i=0; i<ne; ++i) {
    if (esplit[i]) {
      TopoEdge & ei( topo.edge(m_edges[i]) );
      ei.enforcePoint( tsplit[i] );
    }
  }
}

void TopoFace::print(uint k, std::ostream &os) const
{
  os << "TopoFace " << k << " srf: ";
  if (m_psf)
    os << m_psf->name();
  if (m_mg->nvertices() > 0)
    os << " (" << m_mg->nvertices() << " vertices)";
  os << endl;

  const int ne = m_edges.size();
  for (int i=0; i<ne; ++i)
    os << " - Edge " << m_edges[i] << endl;
}

void TopoFace::backend(int b)
{
#ifdef HAVE_JRSTRIANGLE
  s_backend = b;
#else
  if (b == JrsTriangle)
    dbprint("[w] JrsTriangle not compiled in - not available.");
  s_backend = DcMeshGen;
#endif
}




