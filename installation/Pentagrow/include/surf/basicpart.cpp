
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
 
#include "basicpart.h"
#include "surface.h"
#include "topology.h"
#include "dcmeshcrit.h"
#include "ringcapsurf.h"
#include "uvpolyline.h"
#include "sides.h"
#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <iostream>

using namespace std;

BasicPart::BasicPart(const std::string &s) : TopoPart(s)
{
  std::fill(m_bocoface, m_bocoface+5, (uint) Mx::BcAdiabaticWall);
  std::fill(m_iface, m_iface+5, NotFound);
  std::fill(m_capheight, m_capheight+4, -1.0);
  m_noseRefine = 1;
  m_tailRefine = 1;
}

BasicPart::~BasicPart() {}

void BasicPart::surface(SurfacePtr psf, DcMeshCritBasePtr mcrit)
{
  m_surface = psf;
  name(psf->name());

  m_vperiodic =
      (norm(m_surface->eval(0.5,0.0) - m_surface->eval(0.5,1.0)) < gmepsilon);
  m_uperiodic =
      (norm(m_surface->eval(0.0,0.5) - m_surface->eval(1.0,0.5)) < gmepsilon);

  if (mcrit != nullptr) {
    m_mcrit = mcrit;
  } else if (m_surface != nullptr) {
    m_mcrit = basicCriterion(*m_surface);
  }
}

void BasicPart::meshBias(Real noseRefine, Real tailRefine)
{
  m_noseRefine = noseRefine;
  m_tailRefine = tailRefine;
}

void BasicPart::capBocoType(uint side, uint bc)
{
  assert(side >= 0 and side < 4);
  m_bocoface[side] = bc;
}

void BasicPart::inject(Topology &topo)
{
  assert(m_mcrit != nullptr);
  m_iface[0] = topo.appendFace(m_surface, m_uperiodic, m_vperiodic);
  TopoFace & face( topo.face(m_iface[0]) );

  if (m_mcrit == nullptr) {
    DcMeshCritPtr pmc = basicCriterion(*m_surface);
    pmc->vbias(0, m_noseRefine, 0.1);
    pmc->vbias(2, m_tailRefine, 0.1);
    m_mcrit = pmc;
  }

  face.criterion( m_mcrit );
}

uint BasicPart::makeFlatCap(Topology &topo, uint sideTag)
{
  assert(m_iface[0] != NotFound);
  uint iedge = topo.findConnection(m_iface[0], sideTag);
  if (iedge == NotFound)
    throw Error("Surface side "+str(sideTag)+" not found: "+name());
  else
    m_iface[sideTag] = topo.fillPlaneBoundary(iedge);

  DcMeshCritPtr pmc, mmc = boost::dynamic_pointer_cast<DcMeshCrit>(m_mcrit);
  if (mmc != nullptr) {
    pmc = boost::make_shared<DcMeshCrit>(*mmc);
    pmc->apexAngle( rad(18.), rad(120.) );
  }
  //topo.face(m_iface[sideTag]).criterion(pmc != nullptr ? pmc : m_mcrit);
  topo.face(m_iface[sideTag]).criterion(mmc);
  topo.face(m_iface[sideTag]).clearMesh();
  topo.face(m_iface[sideTag]).generateMesh(topo);
  return m_iface[sideTag];
}

uint BasicPart::makeRoundedCap(Topology &topo, uint sideTag, Real h)
{
  // check whether this request makes sense, geometrically
  if (sideTag == north or sideTag == south) {
    if (not m_uperiodic)
      throw Error("BasicPart::makeRoundedCap(): Main surface must be "
                  "slope-continuous in u-direction for round cap.");
    else if (m_vperiodic)
      throw Error("BasicPart::makeRoundedCap(): Requested cap surface "
                  "for periodic surface boundary.");
  } else {
    if (not m_vperiodic)
      throw Error("BasicPart::makeRoundedCap(): Main surface must be "
                  "slope-continuous in v-direction for round cap.");
    else if (m_uperiodic)
      throw Error("BasicPart::makeRoundedCap(): Requested cap surface "
                  "for periodic surface boundary.");
  }

  assert(m_iface[0] != NotFound);
  uint iedge = topo.findConnection(m_iface[0], sideTag);
  if (iedge == NotFound)
    throw Error("Surface side "+str(sideTag)+" not found: "+name());

  assert(topo.edge(iedge).npoints() >= 3);
  const int np = topo.edge(iedge).npoints();

  // extract (u,v) points of edge on side 'sideTag' lying on main surface
  PointList<2> pts(np);
  for (int i=0; i<np; ++i)
    pts[i] = topo.edge(iedge).uvpoint(m_iface[0], i);

  // construct plane surface
  RingCapSurfPtr pps = boost::make_shared<RingCapSurf>("RingCapOn"+str(iedge));
  pps->init(*m_surface, pts, h);

  // create face for cap surface, explicit form to avoid generating internal
  // edges inside the domain (not needed)
  uint iface = topo.appendFace(TopoFace(pps, topo.nfaces()));
  assert(iface != NotFound);
  topo.face(iface).appendEdge(iedge);

  const Vector &upat = topo.edge(iedge).pattern();
  assert(upat.size() == pps->boundaryRing().size());
  UvPolylinePtr pline;
  pline = boost::make_shared<UvPolyline>(m_surface, upat, pps->boundaryRing());
  topo.edge(iedge).attachFace(iface, pline);

  m_iface[sideTag] = iface;
  TopoFace &cface = topo.face(m_iface[sideTag]);
  cface.criterion(m_mcrit);
  cface.clearMesh();

  // use a paved (advancing-front) mesh for better quality
  PointList<2> pini;
  Indices itri;
  pps->pavedMesh(pini, itri);
  cface.importMesh(pini, itri, true);
  cface.replaceEdgeNodes(topo);

  return m_iface[sideTag];
}

void BasicPart::makeLegacyCaps(Topology &topo)
{
  for (uint k=0; k<4; ++k) {
    Real h = m_capheight[k];
    if (h == 0)
      makeFlatCap(topo, k);
    else if (h > 0)
      makeRoundedCap(topo, k, h);
  }
}

void BasicPart::appendTo(const Topology &topo, MxMesh &mx, bool mergeBc)
{
  if (not mergeBc) {

    for (int k=0; k<5; ++k) {
      if (m_iface[k] == NotFound)
        continue;
      appendWithBC(topo.face(m_iface[k]), m_bocoface[k], mx);
    }

  } else {

    uint sbegin, send;
    sbegin = mx.nelements();

    const char *suffix[5] = {"", "Cap1", "Cap2", "Cap3", "Cap4"};
    for (int k=0; k<5; ++k) {
      if (m_iface[k] == NotFound)
        continue;
      uint isec = mx.appendSection( topo.face(m_iface[k]).mesh() );
      mx.section(isec).rename( name() + suffix[k] );
    }

    mx.countElements();
    send = mx.nelements();

    {
      MxMeshBoco bc( (Mx::BocoType) m_bocoface[0] );
      bc.setRange(sbegin, send);
      bc.rename( name() );
      mx.appendBoco(bc);
    }
  }
}

void BasicPart::importLegacy(const XmlElement &xe)
{
  SurfacePtr psf = Surface::createFromXml(xe);
  if (psf != nullptr) {

    DcMeshCritPtr pmc = basicCriterion(*psf);
    pmc->vbias(0, m_noseRefine, 0.1);
    pmc->vbias(2, m_tailRefine, 0.1);

    for (const XmlElement &x : xe) {
      if (x.name() == "MeshCriterion") {
        pmc->importLegacy(x);
        pmc->npass(32);
      } else if (x.name() == "Cap") {
        side_t sd;
        fromString(x.attribute("side"), sd);
        if (sd != none)
          m_capheight[uint(sd)] = x.attr2float("height", 0.0);
      }
    }

    // disable apex angle criterion for now
    pmc->apexAngle(0.0, M_PI);

    surface(psf, pmc);
  }
}

