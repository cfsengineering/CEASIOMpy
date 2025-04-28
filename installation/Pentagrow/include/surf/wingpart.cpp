
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

#include "wingpart.h"
#include "topology.h"
#include "symsurf.h"
#include "dcmeshcrit.h"
#include "stitchedsurf.h"
#include "slavedwake.h"
#include "instancesurf.h"
#include "longcapsurf.h"
#include "uvpolyline.h"
#include "sides.h"
#include <genua/xcept.h>
#include <genua/mxmesh.h>
#include <genua/plane.h>
#include <genua/dbprint.h>
#include <genua/transformation.h>
#include <genua/xmlelement.h>
#include <genua/configparser.h>

#include <fstream>
#include <iostream>
using namespace std;

WingPart::WingPart(const string &s)
  : TopoPart(s), m_relWakeLength(2.0),
    m_leBias(1.0), m_teBias(1.0), m_tipBias(1.0), m_maxProjectedU(0.1),
    m_rightCap(NotFound), m_leftCap(NotFound),
    m_toroidal(false), m_bluntEdge(false), m_fromSymSurf(false)
{
}

WingPart::~WingPart() {}

void WingPart::configure(const ConfigParser &cfg)
{
  m_relWakeLength = cfg.getFloat("RelativeWakeLength", m_relWakeLength);
  m_teBias = cfg.getFloat("TEMeshBias", m_teBias);
  m_leBias = cfg.getFloat("LEMeshBias", m_leBias);
  m_tipBias = cfg.getFloat("TipMeshBias", m_tipBias);
  m_maxProjectedU = 0.5*cfg.getFloat("MaxRelChordEdgeLength",
                                     2*m_maxProjectedU);
}

void WingPart::meshBias(Real leRefine, Real teRefine, Real tipRefine)
{
  m_leBias = leRefine;
  m_teBias = teRefine;
  m_tipBias = tipRefine;
}

void WingPart::meshQuality(DcMeshCritBasePtr wingCrit,
                           DcMeshCritBasePtr wakeCrit)
{
  m_wingCrit = wingCrit;
  if (wakeCrit != nullptr)
    m_wakeCrit = wakeCrit;
  else
    m_wakeCrit = wingCrit->clone();
}

uint WingPart::appendSegment(SurfacePtr wingSegment)
{
  m_wakes.clear();
  m_segments.push_back(wingSegment);
  return m_segments.size() - 1;
}

uint WingPart::appendSegment(SurfacePtr wingSegment, SurfacePtr wakeSegment)
{
  assert(m_segments.size() == m_wakes.size());
  m_segments.push_back(wingSegment);
  m_wakes.push_back(wakeSegment);
  return m_segments.size() - 1;
}

void WingPart::mirrorSegments(const Vct3 &mipo, const Vct3 &mipn)
{
  const int nseg = m_segments.size();
  if (nseg == 0)
    return;

  // transformation matrix for mirroring
  Trafo3d trafo;
  trafo.translate(-mipo);
  trafo.reflect(mipn[0], mipn[1], mipn[2]);
  Mtx44 tfm = trafo.matrix();

  // append backwards
  for (int i=(nseg-1); i>=0; --i) {
    const SurfacePtr & psf( m_segments[i] );
    InstanceSurfPtr pmi = boost::make_shared<InstanceSurf>(psf, tfm);
    pmi->vswap(true);
    m_segments.push_back( pmi );
  }

  const int nwak = m_wakes.size();
  assert(nwak == nseg);
  for (int i=(nwak-1); i>=0; --i) {
    const SurfacePtr & psf( m_wakes[i] );
    InstanceSurfPtr pmi = boost::make_shared<InstanceSurf>(psf, tfm);
    pmi->vswap(true);
    m_wakes.push_back( pmi );
  }
}

void WingPart::inject(Topology &topo)
{
  const int nseg = m_segments.size();
  bool connectWakes = (m_wakes.size() == size_t(nseg));
  bool uperiodic = !m_bluntEdge;
  bool vperiodic = m_toroidal and (nseg == 1);

  // create all wing segment faces first
  m_ifaces.resize(nseg);
  for (int i=0; i<nseg; ++i) {
    m_ifaces[i] = topo.appendFace(m_segments[i], uperiodic, vperiodic);
    assert(m_wingCrit != nullptr);
    TopoFace & face( topo.face(m_ifaces[i]) );
    face.criterion( m_wingCrit );

    DcMeshCritPtr pmc;
    pmc = boost::dynamic_pointer_cast<DcMeshCrit>( face.criterion() );
    if (pmc != nullptr) {
      pmc->ubias(0, m_teBias, 0.25);
      pmc->ubias(1, m_leBias, 0.25);
      pmc->ubias(2, m_teBias, 0.25);
      if (i == 0)
        pmc->vbias(0, m_tipBias, 0.5);
      if (i == nseg-1)
        pmc->vbias(2, m_tipBias, 0.5);
    }
  }

  // then, connect segment faces along seams
  for (int i=1; i<nseg; ++i)
    if (not topo.vEnchain(m_ifaces[i-1], m_ifaces[i]))
      throw Error("Could not connect wing segments.");
  if (m_toroidal and (nseg > 1))
    if (not topo.vEnchain(m_ifaces.back(), m_ifaces.front()))
      throw Error("Could not connect wing segments to ring.");

  // connect wake surfaces to (upper, if blunt) wing trailing edge
  // this is where the convention for wake parametrization is used
  m_iwakes.clear();
  Vct2 upperRight(0.0, 0.0), upperLeft(0.0, 1.0);
  if (connectWakes) {
    m_iwakes.resize(nseg);
    for (int i=0; i<nseg; ++i) {
      m_iwakes[i] = topo.appendFace(m_wakes[i], false, vperiodic);
      TopoFace & face( topo.face(m_iwakes[i]) );
      face.criterion( m_wakeCrit );
      uint teWing = topo.findConnection(m_ifaces[i], upperRight, upperLeft);
      uint leWake = topo.findConnection(m_iwakes[i], upperRight, upperLeft);
      if (not topo.connectFaces(m_ifaces[i], m_iwakes[i], teWing, leWake)) {
        throw Error("Could not connect wake surface '" + m_wakes[i]->name() +
                    "' to wing trailing edge.");
      }

      DcMeshCritPtr pmc, pmw;
      pmw = boost::dynamic_pointer_cast<DcMeshCrit>( face.criterion() );
      pmc = boost::dynamic_pointer_cast<DcMeshCrit>( topo.face(m_ifaces[i]).criterion() );
      if ((pmw != nullptr) and (pmc != nullptr)) {
        Real lratio = sqrt( pmw->sqMaxLengthXyz() / pmc->sqMaxLengthXyz() );
        pmw->ubias(0, m_teBias / lratio, 0.5);
        pmw->ubias(1, 1.0, 0.25);
        pmw->ubias(2, 1.0, 0.25);
        dbprint("Wake bias: ", m_teBias / lratio);
      }
    }

    // now, connect the inner seams between wake segments
    for (int i=1; i<nseg; ++i)
      if (not topo.vEnchain(m_iwakes[i-1], m_iwakes[i]))
        throw Error("Could not connect wake segments.");
    if (m_toroidal and (nseg > 1))
      if (not topo.vEnchain(m_iwakes.back(), m_iwakes.front()))
        throw Error("Could not connect wake segments to ring.");
  }

  // TODO: Generate (?) closure surfaces for blunt trailing edges


}

std::pair<uint,uint> WingPart::makeFlatCaps(Topology &topo,
                                            bool makeLeft, bool makeRight)
{
  if (makeRight) {
    uint rightTip = findWingTipEdge(topo, 0.0);
    if (rightTip != NotFound)
      m_rightCap = topo.fillPlaneBoundary(rightTip);
    else
      throw Error("Cannot find right wing-tip edge for cap creation.");
    topo.face(m_rightCap).criterion(m_wingCrit);
    topo.face(m_rightCap).clearMesh();
    topo.face(m_rightCap).generateMesh(topo);
  }

  if (makeLeft) {
    uint leftTip = findWingTipEdge(topo, 1.0);
    if (leftTip != NotFound)
      m_leftCap = topo.fillPlaneBoundary(leftTip);
    else
      throw Error("Cannot find left wing-tip edge for cap creation.");
    topo.face(m_leftCap).criterion(m_wingCrit);
    topo.face(m_leftCap).clearMesh();
    topo.face(m_leftCap).generateMesh(topo);
  }

  return std::make_pair(m_leftCap, m_rightCap);
}

std::pair<uint, uint> WingPart::makeRoundedCaps(Topology &topo,
                                                bool makeLeft, bool makeRight)
{
  // right tip -> v = 0.0
  if (makeRight) {

    uint rightTip = findWingTipEdge(topo, 0.0);
    if (rightTip == NotFound)
      throw Error("Cannot find right wing-tip edge for cap creation.");

    TopoEdge &tipEdge = topo.edge(rightTip);
    const size_t np = tipEdge.npoints();
    if (np < 3)
      throw Error("Tip cap construction requires that edges are "
                  "discretized first.");
    if (tipEdge.nfaces() != 1)
      throw Error("Tip edge on wing is already connected to multiple faces.");

    // extract (u,v) points on wing along existing tip edge
    PointList2d buv(np);
    for (size_t i=0; i<np; ++i)
      buv[i] = tipEdge.uvpoint(0, i);

    // extract 3D-space points along wing tip section
    PointList3d bpts(np);
    for (size_t i=0; i<np; ++i)
      bpts[i] = tipEdge.point(i);

    // build cap surface and extract breakpoint
    LongCapSurfPtr psfCap = boost::make_shared<LongCapSurf>("RightTipCap");
    Real rh = 1.0;
    uint ibreak = psfCap->init(bpts, rh);
    Vct2 pbreak = tipEdge.uvpoint(0, ibreak);

    // append cap face
    TopoFace capFace(psfCap, NotFound);
    m_rightCap = topo.appendFace(capFace);

    // insert vertex at leading-edge breakpoint
    uint wingFace = m_ifaces.front();
    uint vbreak = topo.appendVertex(wingFace, pbreak);
    Real vlecap = (rh >= 0) ? 1.0 : 0.0;
    topo.vertex(vbreak).append( m_rightCap, Vct2(0.0, vlecap) );
    topo.vertex(vbreak).append( m_rightCap, Vct2(1.0, vlecap) );

    // retrieve vertex indices, west -> u = 0, east -> u = 1 on wing
    uint vteWest = tipEdge.source();
    uint vteEast = tipEdge.target();
    if ( topo.vertex(vteWest).cornerType(wingFace) != TopoVertex::SouthWest )
      std::swap(vteWest, vteEast);

    // break connectivity between old wingtip edge and wing surface segment
    topo.face(wingFace).detachEdge(rightTip);
    tipEdge.detach();

    // inject two new edges along the wing tip, named with respect to
    // value of u on the wing side
    TopoEdge westEdge(vteWest, vbreak);
    TopoEdge eastEdge(vteEast, vbreak);

    uint iWestEdge = topo.appendEdge(westEdge);
    uint iEastEdge = topo.appendEdge(eastEdge);

    // generate boundary curves on cap and connect
    UvPolylinePtr capWestBnd = boost::make_shared<UvPolyline>(psfCap);
    const Vector & tpwest = capWestBnd->uBoundary(0.0,
                                                 psfCap->westEdge(), rh < 0);
    UvPolylinePtr capEastBnd = boost::make_shared<UvPolyline>(psfCap);
    const Vector & tpeast = capEastBnd->uBoundary(1.0,
                                                  psfCap->eastEdge(), rh >= 0);
    topo.connectEdge(m_rightCap, iWestEdge, capWestBnd, false);
    topo.connectEdge(m_rightCap, iEastEdge, capEastBnd, false);

    // prescribe edge discretization
    topo.edge(iWestEdge).discretize( tpwest );
    topo.edge(iEastEdge).discretize( tpeast );

    // generate boundary curves on wing and connect
    SurfacePtr wingPsf = topo.face(wingFace).surface();
    PointList2d uvWest(buv.begin(), buv.begin() + ibreak + 1);
    PointList2d uvEast(buv.begin()+ibreak, buv.end());
    topo.connectEdge(wingFace, iWestEdge,
                     boost::make_shared<UvPolyline>(wingPsf, uvWest), false);
    topo.connectEdge(wingFace, iEastEdge,
                     boost::make_shared<UvPolyline>(wingPsf, uvEast), false);

    // inject a fixed mesh and keep it
    PointList2d uvp;
    PointList3d dmy1, dmy2;
    Indices tri;
    psfCap->fixedMesh(uvp, dmy1, dmy2, tri);
    topo.face(m_rightCap).importMesh(uvp, tri, true);
    topo.face(m_rightCap).replaceEdgeNodes(topo, false);
  }

  // left tip -> v = 1.0
  if (makeLeft) {

    uint leftTip = findWingTipEdge(topo, 1.0);
    if (leftTip == NotFound)
      throw Error("Cannot find left wing-tip edge for cap creation.");

    TopoEdge &tipEdge = topo.edge(leftTip);
    const size_t np = tipEdge.npoints();
    if (np < 3)
      throw Error("Tip cap construction requires that edges are "
                  "discretized first.");
    if (tipEdge.nfaces() != 1)
      throw Error("Tip edge on wing is already connected to multiple faces.");

    // extract (u,v) points on wing along existing tip edge
    PointList2d buv(np);
    for (size_t i=0; i<np; ++i)
      buv[i] = tipEdge.uvpoint(0, i);

    // extract 3D-space points along wing tip section
    PointList3d bpts(np);
    for (size_t i=0; i<np; ++i)
      bpts[i] = tipEdge.point(i);

    // build cap surface and extract breakpoint
    LongCapSurfPtr psfCap = boost::make_shared<LongCapSurf>("LeftTipCap");
    Real rh = 1.0;
    uint ibreak = psfCap->init(bpts, rh);
    Vct2 pbreak = tipEdge.uvpoint(0, ibreak);

    // append cap face
    TopoFace capFace(psfCap, NotFound);
    m_leftCap = topo.appendFace(capFace);

    // insert vertex at leading-edge breakpoint
    uint wingFace = m_ifaces.back();
    uint vbreak = topo.appendVertex(wingFace, pbreak);
    Real vlecap = (rh >= 0) ? 1.0 : 0.0;
    topo.vertex(vbreak).append( m_leftCap, Vct2(0.0, vlecap) );
    topo.vertex(vbreak).append( m_leftCap, Vct2(1.0, vlecap) );

    // retrieve vertex indices, west -> u = 0, east -> u = 1 on wing
    uint vteWest = tipEdge.source();
    uint vteEast = tipEdge.target();
    if ( topo.vertex(vteWest).cornerType(wingFace) != TopoVertex::SouthWest )
      std::swap(vteWest, vteEast);

    // break connectivity between old wingtip edge and wing surface segment
    topo.face(wingFace).detachEdge(leftTip);
    tipEdge.detach();

    // inject two new edges along the wing tip, named with respect to
    // value of u on the wing side
    TopoEdge westEdge(vteWest, vbreak);
    TopoEdge eastEdge(vteEast, vbreak);

    uint iWestEdge = topo.appendEdge(westEdge);
    uint iEastEdge = topo.appendEdge(eastEdge);

    // generate boundary curves on cap and connect
    UvPolylinePtr capWestBnd = boost::make_shared<UvPolyline>(psfCap);
    const Vector & tpwest = capWestBnd->uBoundary(0.0,
                                                 psfCap->westEdge(), rh < 0);
    UvPolylinePtr capEastBnd = boost::make_shared<UvPolyline>(psfCap);
    const Vector & tpeast = capEastBnd->uBoundary(1.0,
                                                  psfCap->eastEdge(), rh >= 0);
    topo.connectEdge(m_leftCap, iWestEdge, capWestBnd, false);
    topo.connectEdge(m_leftCap, iEastEdge, capEastBnd, false);

    // prescribe edge discretization
    topo.edge(iWestEdge).discretize( tpwest );
    topo.edge(iEastEdge).discretize( tpeast );

    // generate boundary curves on wing and connect
    SurfacePtr wingPsf = topo.face(wingFace).surface();
    PointList2d uvWest(buv.begin(), buv.begin() + ibreak + 1);
    PointList2d uvEast(buv.begin()+ibreak, buv.end());
    topo.connectEdge(wingFace, iWestEdge,
                     boost::make_shared<UvPolyline>(wingPsf, uvWest), false);
    topo.connectEdge(wingFace, iEastEdge,
                     boost::make_shared<UvPolyline>(wingPsf, uvEast), false);

    // inject a fixed mesh and keep it
    PointList2d uvp;
    PointList3d dmy1, dmy2;
    Indices tri;
    psfCap->fixedMesh(uvp, dmy1, dmy2, tri);
    topo.face(m_leftCap).importMesh(uvp, tri, true);
    topo.face(m_leftCap).replaceEdgeNodes(topo, false);
  }

  cout << "Topology after cap generation:" << endl;
  topo.print(std::cout);

  return std::make_pair(m_leftCap, m_rightCap);
}

uint WingPart::findWingTipEdge(const Topology &topo, Real v) const
{
  if (m_ifaces.empty())
    throw Error("WingPart::findWakeTipEdge() : No wing face present.");

  assert(v == 0.0 or v == 1.0);
  if (v == 0.0)
    return topo.findConnection(m_ifaces.front(),
                               Vct2(0.0, 0.0), Vct2(1.0, 0.0));
  else
    return topo.findConnection(m_ifaces.back(),
                               Vct2(0.0, 1.0), Vct2(1.0, 1.0));
}

uint WingPart::findWakeTipEdge(const Topology &topo, Real v) const
{
  if (m_iwakes.empty())
    throw Error("WingPart::findWakeTipEdge() : No wake face present.");

  assert(v == 0.0 or v == 1.0);
  if (v == 0.0)
    return topo.findConnection(m_iwakes.front(),
                               Vct2(0.0, 0.0), Vct2(1.0, 0.0));
  else
    return topo.findConnection(m_iwakes.back(),
                               Vct2(0.0, 1.0), Vct2(1.0, 1.0));
}

void WingPart::createSimpleWakes(const Vct3 &edgeDistance,
                                 const Vct3 &farTangent, Real compression)
{
  m_wakes.clear();
  const int nseg = m_segments.size();
  m_wakes.resize(nseg);

  // determine default dimensions if not given
  Vct3 ed(edgeDistance), ft(farTangent);
  fillDefaultDimensions(ed, ft);
  for (int i=0; i<nseg; ++i) {
    SlavedWakePtr wp = boost::make_shared<SlavedWake>();
    wp->initRuledBezier( m_segments[i], ed, ft, compression );
    m_wakes[i] = wp;
  }
}

void WingPart::createAttachedWakes(SurfaceArray bodies,
                                   const Vct3 &edgeDistance,
                                   const Vct3 &farTangent)
{
  m_wakes.clear();
  const int nseg = m_segments.size();
  m_wakes.resize(nseg);

  // determine default dimensions if not given
  Vct3 ed(edgeDistance), ft(farTangent);
  fillDefaultDimensions(ed, ft);

  CurvePtr gc0, gc1;
  const int nb = bodies.size();
  for (int ki = 0; ki < nb; ++ki) {
    gc0 = tryAttachWake(bodies[ki], 0, 0.0, ed, ft);
    if (gc0 != nullptr)
      break;
  }
  if (gc0 == nullptr) {
    gc0 = SlavedWake::cubicGuide(m_segments[0], 0, ed, ft);
    dbprint("Using cubic guide for segment 0 v = 0");
  } else {
    dbprint("Using attached guide for segment 0 v = 0");
  }

  for (int i=0; i<nseg; ++i) {

    for (int ki = 0; ki < nb; ++ki) {
      gc1 = tryAttachWake(bodies[ki], i, 1.0, ed, ft);
      if (gc1 != nullptr)
        break;
    }
    if (gc1 == nullptr) {
      gc1 = SlavedWake::cubicGuide(m_segments[i], 1.0, ed, ft);
      dbprint("Using cubic guide for segment ",i," v = 1");
    } else {
      dbprint("Using attached guide for segment ",i," v = 1");
    }

    SlavedWakePtr wp = boost::make_shared<SlavedWake>();
    wp->initRuled(m_segments[i], gc0, gc1);
    m_wakes[i] = wp;
    gc0 = gc1;
  }
}

CurvePtr WingPart::tryAttachWake(SurfacePtr body, int iseg, Real v,
                                 const Vct3 &edgeDistance,
                                 const Vct3 &farTangent) const
{
  const Real dsqtol = 1e-4;
  const SurfacePtr &pwing = m_segments[iseg];

  Real vlo = std::min(v, 0.5);
  Real vhi = std::max(v, 0.5);
  Vct3 uvt = SlavedWake::findIntersection(pwing, body, vlo, vhi);
  Real sqd = sq(pwing->eval(0.0, uvt[2]) - body->eval(uvt[0], uvt[1]));
  Real sql = sq(pwing->eval(0.0, 0.0) - pwing->eval(0.0, 1.0));

  if (sqd > dsqtol*sql)
    return CurvePtr();

  Vct3 anchor = pwing->eval(0.0, 1.0);
  return SlavedWake::guideCurve(body, Vct2(uvt[0], uvt[1]),
                                anchor, edgeDistance, farTangent);
}

void WingPart::fillDefaultDimensions(Vct3 &ed, Vct3 &ft) const
{
  if (sq(ed) == 0) {
    Real telen = 0;
    const int nseg = m_segments.size();
    for (int i=0; i<nseg; ++i) {
      Vct3 te = m_segments[i]->eval(0.0, 1.0) - m_segments[i]->eval(0.0, 0.0);
      telen += norm(te);
    }
    ed[0] = m_relWakeLength * telen;
  }
  if (sq(ft) == 0)
    ft[0] = 1;
}

void WingPart::appendTo(const Topology &topo, MxMesh &mx, bool mergeBc)
{
  m_ifbocos.clear();
  m_iwbocos.clear();

  if (not mergeBc) {

    for (size_t i=0; i<m_ifaces.size(); ++i) {
      uint k = appendWithBC(topo.face(m_ifaces[i]), Mx::BcAdiabaticWall, mx);
      m_ifbocos.push_back(k);
    }

    if (m_leftCap != NotFound)
      m_ifbocos.push_back( appendWithBC(topo.face(m_leftCap),
                                        Mx::BcAdiabaticWall, mx) );
    if (m_rightCap != NotFound)
      m_ifbocos.push_back(  appendWithBC(topo.face(m_rightCap),
                                         Mx::BcAdiabaticWall, mx) );
    for (size_t i=0; i<m_wakes.size(); ++i)
      m_iwbocos.push_back( appendWithBC(topo.face(m_iwakes[i]),
                                        Mx::BcWakeSurface, mx) );

  } else {

    uint sbegin, send;
    sbegin = mx.nelements();
    for (size_t i=0; i<m_ifaces.size(); ++i) {
      uint isec = mx.appendSection( topo.face(m_ifaces[i]).mesh() );
      mx.section(isec).rename( topo.face(m_ifaces[i]).surface()->name() );
    }
    if (m_leftCap != NotFound) {
      uint isec = mx.appendSection( topo.face(m_leftCap).mesh() );
      mx.section(isec).rename( topo.face(m_leftCap).surface()->name() );
    }
    if (m_rightCap != NotFound) {
      uint isec = mx.appendSection( topo.face(m_rightCap).mesh() );
      mx.section(isec).rename( topo.face(m_rightCap).surface()->name() );
    }
    mx.countElements();
    send = mx.nelements();

    {
      MxMeshBoco bc( Mx::BcAdiabaticWall );
      bc.setRange(sbegin, send);
      bc.rename( name() );
      uint ib = mx.appendBoco(bc);
      m_ifbocos.push_back(ib);
    }

    sbegin = send;
    for (size_t i=0; i<m_wakes.size(); ++i) {
      uint isec = mx.appendSection( topo.face(m_iwakes[i]).mesh() );
      mx.section(isec).rename( topo.face(m_iwakes[i]).surface()->name() );
    }
    mx.countElements();
    send = mx.nelements();

    {
      MxMeshBoco bc( Mx::BcWakeSurface );
      bc.setRange(sbegin, send);
      bc.rename( name() + "Wake" );
      uint ib = mx.appendBoco(bc);
      m_iwbocos.push_back(ib);
    }
  }
}

void WingPart::importLegacy(const XmlElement &xe)
{
  DcMeshCritPtr pmc = boost::make_shared<DcMeshCrit>();
  if (xe.name() == "StitchedSurf") {

    pmc = appendStitched(xe);

  } else if (xe.name() == "SymSurf") {

    m_fromSymSurf = true;

    // import one side
    XmlElement::const_iterator itc = xe.findChild("StitchedSurf");
    if (itc != xe.end()) {
      pmc = appendStitched(*itc);
    } else {
      throw Error("Cannot handled mirrored general surface yet.");
    }

    // generate the other side
    mirrorSegments( Vct3(0,0,0), Vct3(0,1,0) );

  } else {

    // not a stitched surface, try to read as a single surface
    SurfacePtr legacySurf = Surface::createFromXml(xe);
    if (legacySurf != nullptr) {
      Surface::DimStat stats;
      legacySurf->dimStats(stats);
      Vct3 wakev( m_relWakeLength*stats.diagonal(), 0.0, 0.0 );
      cout << "Wake length: " << wakev[0] << endl;
      SurfacePtr wp = boost::make_shared<SlavedWake>(legacySurf, wakev);
      appendSegment(legacySurf, wp);
      pmc = basicCriterion(*legacySurf);
    }

  }

  std::fill( std::begin(m_capheight), std::end(m_capheight), 0.0 );

  // load mesh criteria and cap heights, if present
  for (const XmlElement &x : xe) {
    if (x.name() == "MeshCriterion") {
      pmc->importLegacy(x);
      m_leBias = x.attr2float("lerfactor", m_leBias);
      m_teBias = x.attr2float("terfactor", m_teBias);
    } else if (x.name() == "Cap") {
      side_t sd;
      fromString(x.attribute("side"), sd);
      if (sd != none)
        m_capheight[uint(sd)] = x.attr2float("height", 0.0);
    }
  }

  // allow more stretch for wing meshes
  pmc->apexAngle( rad(0.), rad(180.) );

  DcMeshCritPtr pmw = boost::dynamic_pointer_cast<DcMeshCrit>( pmc->clone() );
  pmw->xyzLength( 2*m_relWakeLength*pmc->maxLengthXyz(),
                  pmc->minLengthXyz() );
  pmw->apexAngle( rad(0.), rad(180.) );
  pmw->nSmooth(4);

  // minimum chordwise discretisation
  pmc->maxProjectionU(m_maxProjectedU);

  meshQuality(pmc, pmw);
}

DcMeshCritPtr WingPart::appendStitched(const XmlElement &xe)
{
  assert(xe.name() == "StitchedSurf");
  StitchedSurf ss;
  ss.fromXml(xe);
  DcMeshCritPtr pmc = basicCriterion(ss);

  // default wake
  Surface::DimStat stats;
  ss.dimStats(stats);
  Real wlen = m_relWakeLength*stats.diagonal();
  if (m_fromSymSurf)
    wlen *= 2;
  Vct3 wakev( wlen, 0.0, 0.0 );
  cout << "Wake length: " << wlen << endl;

  const SurfaceArray &surf( ss.segments() );
  for (size_t i=0; i<surf.size(); ++i) {
    SurfacePtr wp = boost::make_shared<SlavedWake>(surf[i], wakev);
    appendSegment(surf[i], wp);
  }

  return pmc;
}

void WingPart::makeLegacyCaps(Topology &topo)
{
  m_leftCap = m_rightCap = NotFound;

  bool leftFlat = (m_capheight[uint(north)] == 0.0);
  bool rightFlat = (m_capheight[uint(south)] == 0.0);
  bool leftRound = !leftFlat;
  bool rightRound = !rightFlat;

  if (leftFlat or rightFlat)
    makeFlatCaps(topo, leftFlat, rightFlat);
  if (leftRound or rightRound)
    makeRoundedCaps(topo, leftRound, rightRound);
}

void WingPart::toIges(IgesFile &file, int tfi) const
{
  for (const SurfacePtr &psf : m_segments)
    if (psf != nullptr)
      psf->toIges(file, tfi);
  for (const SurfacePtr &psf : m_wakes)
    if (psf != nullptr)
      psf->toIges(file, tfi);
}


