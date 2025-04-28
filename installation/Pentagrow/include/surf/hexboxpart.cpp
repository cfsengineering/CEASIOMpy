
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
 
#include "hexboxpart.h"
#include "planesurface.h"
#include "topology.h"
#include "uvpolyline.h"
#include "dcmeshcrit.h"
#include <genua/mxmesh.h>
#include <genua/dbprint.h>

using namespace std;

HexBoxPart::HexBoxPart(const string &s) : TopoPart(s),
  m_length(1.0, 0.0, 0.0), m_width(0.0, 1.0, 0.0), m_height(0.0, 0.0, 1.0)
{
  fill( begin(m_ifaces), end(m_ifaces), NotFound );
  fill( begin(m_ibocos), end(m_ibocos), NotFound );
  fill( begin(m_bctype), end(m_bctype), Mx::BcFarfield );
}

void HexBoxPart::rescale(Real l, Real w, Real h)
{
  m_length *= l / norm(m_length);
  m_width *= w / norm(m_width);
  m_height *= h / norm(m_height);
}

void HexBoxPart::inject(Topology &topo)
{
  // corner nodes
  Vct3 c0 = m_center - 0.5*m_length - 0.5*m_width - 0.5*m_height;
  Vct3 c1 = c0 + m_length;
  Vct3 c3 = c0 + m_height;
  Vct3 c4 = c0 + m_width;

  // generate surfaces
  m_sides[0] = boost::make_shared<PlaneSurface>(c0, m_height,
                                                m_length, "LeftSide");
  m_sides[1] = boost::make_shared<PlaneSurface>(c3, m_width,
                                                m_length, "TopSide");
  m_sides[2] = boost::make_shared<PlaneSurface>(c4, m_length,
                                                m_height, "RightSide");
  m_sides[3] = boost::make_shared<PlaneSurface>(c0, m_length,
                                                m_width, "BottomSide");
  m_sides[4] = boost::make_shared<PlaneSurface>(c0, m_width,
                                                m_height, "FrontSide");
  m_sides[5] = boost::make_shared<PlaneSurface>(c1, m_height,
                                                m_width, "RearSide");

  // generate a reasonable default if there is no present criterion
  if (m_mcrit == nullptr) {

    Real blmin = norm(m_length);
    blmin = std::min(blmin, norm(m_width));
    blmin = std::min(blmin, norm(m_height));

    DcMeshCritPtr pmc = boost::make_shared<DcMeshCrit>();
    pmc->maxNodes(16*1024);
    pmc->npass(8);
    pmc->nSkipSmooth(1);
    pmc->nSmooth(1);
    pmc->xyzLength( blmin/16, 0.0 );
    pmc->apexAngle( rad(18.), rad(165.) );
    m_mcrit = pmc;
  }

  for (int i=0; i<6; ++i) {
    m_ifaces[i] = topo.appendFace(m_sides[i]);
    assert(m_ifaces[i] != NotFound);
    TopoFace &face( topo.face(m_ifaces[i]) );
    face.criterion( m_mcrit );
  }

  // generate connections between surfaces
  topo.connectFaces( m_ifaces[0], m_ifaces[1] );
  topo.connectFaces( m_ifaces[1], m_ifaces[2] );
  topo.connectFaces( m_ifaces[2], m_ifaces[3] );
  topo.connectFaces( m_ifaces[0], m_ifaces[3] );

  for (int k=0; k<4; ++k) {
    topo.connectFaces( m_ifaces[4], m_ifaces[k] );
    topo.connectFaces( m_ifaces[5], m_ifaces[k] );
  }
}

void HexBoxPart::imprint(Topology &topo, uint eix, HexBoxPart::SideType s)
{
  TopoEdge &e( topo.edge(eix) );
  const size_t npt = e.npoints();
  assert(npt > 0);

  // create (u,v)-space curve on side surface
  assert( m_sides[int(s)] != nullptr );
  PointList2d uv(npt);
  const PlaneSurfacePtr psf( m_sides[int(s)] );
  if (psf == nullptr)
    throw Error("HexBoxPart: "
                "Cannot imprint curve before side surface is created.");

  // dbprint("Imprinting edge ",eix," on ",psf->name());
  for (size_t i=0; i<npt; ++i) {
    psf->project(e.point(i), uv[i]);

    // assertions check whether points are all within surface;
    // TODO: imprint edge crossing surface boundaries
    assert(uv[i][0] >= 0.0 and uv[i][0] <= 1.0);
    assert(uv[i][1] >= 0.0 and uv[i][1] <= 1.0);
  }
  bool isclosed = sq(uv.front() - uv.back()) <= gmepsilon;

  const uint fix = m_ifaces[int(s)];
  assert(fix != NotFound);

  // make sure to pass the e.m_tp to polyline interpolation in order to
  // match (u,v) point interpolation of the curve with projection above
  AbstractUvCurvePtr uvc = boost::make_shared<UvPolyline>(psf, e.pattern(), uv);
  e.attachFace(fix, uvc);
  topo.face(fix).appendEdge(eix, isclosed);
}

void HexBoxPart::appendTo(const Topology &topo, MxMesh &mx, bool)
{
  for (int i=0; i<6; ++i) {
    const TopoFace &face( topo.face(m_ifaces[i]) );
    uint sbegin = mx.nelements();
    uint isec = mx.appendSection( face.mesh() );
    uint send = sbegin + mx.section(isec).nelements();
    mx.section(isec).rename( face.surface()->name() );

    MxMeshBoco bc(m_bctype[i]);
    bc.setRange(sbegin, send);
    bc.rename( face.surface()->name() );
    m_ibocos[i] = mx.appendBoco(bc);
  }
}


