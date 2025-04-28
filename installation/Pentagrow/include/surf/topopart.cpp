
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
 
#include "topopart.h"
#include "topoface.h"
#include "surface.h"
#include "dcmeshcrit.h"
#include <genua/mxmesh.h>
#include <iostream>

using namespace std;

TopoPart::~TopoPart() {}

void TopoPart::configure(const ConfigParser &)
{
  // no parent-level parameters to define
}

void TopoPart::importLegacy(const XmlElement &)
{
  // do nothing by default
}

void TopoPart::makeLegacyCaps(Topology &)
{
  // do nothing by default
}

DcMeshCritPtr TopoPart::basicCriterion(const Surface &srf, Real rfactor)
{
  Surface::DimStat stats;
  srf.dimStats(stats);

  DcMeshCritPtr c = boost::make_shared<DcMeshCrit>();
  c->npass(16);
  c->nSmooth(2);

  // select baseline length factor from bb diagonal
  Real bbd = rfactor * 0.01 * norm(stats.bbhi - stats.bblo);
  c->xyzLength( bbd, 0.03*bbd );

  Real sqr = std::sqrt(rfactor);
  c->maxNormalAngle( sqr * rad(30.) );

  Real minBeta = rad(12.0); // std::min( rad(21.), rad(15.) / sqr);
  Real maxBeta = rad(135.0); //std::max( rad(120.) / sqr, rad(100.) );
  c->apexAngle(minBeta, maxBeta);

  return c;
}

uint TopoPart::appendWithBC(const TopoFace &face, int btyp, MxMesh &mx)
{
  uint sbegin = mx.nelements();
  uint isec = mx.appendSection( face.mesh() );
  uint send = sbegin + mx.section(isec).nelements();
  mx.section(isec).rename( face.surface()->name() );

  MxMeshBoco bc( (Mx::BocoType) btyp );
  bc.setRange(sbegin, send);
  bc.rename( face.surface()->name() );
  return mx.appendBoco(bc);
}

