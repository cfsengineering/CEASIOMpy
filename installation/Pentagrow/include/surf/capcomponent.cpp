
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
 
#include "capcomponent.h"
#include "longcapsurf.h"
#include "ringcapsurf.h"
#include "dnrefine.h"

using namespace std;

CapComponent::CapComponent(MeshComponentPtr parent,
                           side_t side, Shape shape, Real hgt)
  : MeshComponent( CapComponent::createCap(parent.get(), side, shape, hgt),
                   DnRefineCriterionPtr(new DnRefineCriterion(*parent->criterion())) )
{
  m_mainside = side;
  m_shape = shape;
  m_height = hgt;

  // set tag to parents tag (can be changed by caller)
  tag( parent->tag() );

  // set mesh generation defaults for caps
  allowRefinement(false);
  kinkLimit(PI);
  smoothingIterations(0);
  smoothingFactor(0.0);
}

void CapComponent::premesh(const PointGrid<2> &)
{
  MeshComponent::mg = DnMesh(MeshComponent::psf, DnSpatial);
  MeshComponent::psf->initMesh( *criterion(), mg );
//  if (m_shape == RingCap) {
//    const RingCapSurf *rcf = dynamic_cast<const RingCapSurf *>(psf.get());
//    if (rcf == 0)
//      throw Error("CapComponent: Attempting to premesh an uninitialized RingCap.");
//    rcf->
//  }
}

void CapComponent::premesh(const PointList<2> &, const Indices &)
{
  MeshComponent::mg = DnMesh(MeshComponent::psf, DnSpatial);
  MeshComponent::psf->initMesh( *criterion(), mg );
}

void CapComponent::adapt()
{
  // retrieve parent component
  assert(MeshComponent::parents.size() == 1);
  const MeshComponent *main = parents.front();

  MeshComponent::psf = createCap(main, m_mainside, m_shape, m_height);

  // use cap's specialized mesh generation procedure
  MeshComponent::mg = DnMesh(MeshComponent::psf, DnSpatial);
  MeshComponent::psf->initMesh( *criterion(), mg );

  reconstrain();
  transfer();
  refine();
}

SurfacePtr CapComponent::createCap(const MeshComponent *main, side_t side,
                                   Shape shape, Real hgt)
{
  assert(main != 0);

  // parent surface object
  SurfacePtr parsf = main->surface();
  assert(parsf);

  // cap surface name
  string capname = parsf->name();
  capname += "Cap";
  if (side == west)
    capname += "1";
  else if (side == east)
    capname += "2";
  else if (side == south)
    capname += "3";
  else if (side == north)
    capname += "4";

  // extract boundary points
  Indices idx;
  main->boundary(side, idx);

  // adapt normal direction to make it point outward
  if (side == north or side == east)
    std::reverse(idx.begin(), idx.end());

  int np = idx.size();
  PointList<3> pts;
  PointList<2> qts;

  // on initialization, the parent may not be meshed yet, we must therefore
  // generate a some boundary points to allow for a coarse initial surface.
  if (np == 0) {

    np = 60;
    Vct2 q1, q2;
    if (side == west) {
      q1 = vct(0, 0);
      q2 = vct(0, 1);
    } else if (side == east) {
      q1 = vct(1, 0);
      q2 = vct(1, 1);
    } else if (side == south) {
      q1 = vct(0, 0);
      q2 = vct(1, 0);
    } else if (side == north) {
      q1 = vct(0, 1);
      q2 = vct(1, 1);
    } else {
      throw Error("CapComponent: Attachment side must be defined.");
    }

    if (shape == LongCap) {
      pts.resize(np);
      for (int i=0; i<np; ++i) {
        Real t = Real(i) / (np-1);
        Vct2 q = (1-t)*q1 + t*q2;
        pts[i] = parsf->eval(q[0], q[1]);
      }
    } else if (shape == RingCap) {
      qts.resize(np);
      for (int i=0; i<np; ++i) {
        Real t = Real(i) / (np-1);
        qts[i] = (1-t)*q1 + t*q2;
      }
    }

  } else {

    if (shape == LongCap) {
      pts.resize(np);
      for (int i=0; i<np; ++i)
        pts[i] = main->vertex( idx[i] );
    } else if (shape == RingCap) {
      qts.resize(np);
      for (int i=0; i<np; ++i)
        qts[i] = main->parameter( idx[i] );
    }

  }

  SurfacePtr psf;
  if (shape == LongCap) {
    assert(not pts.empty());
    LongCapSurf *rcp = new LongCapSurf(pts, hgt);
    psf = SurfacePtr(rcp);
  } else if (shape == RingCap) {
    assert(not qts.empty());
    RingCapSurf *rcp = new RingCapSurf;
    rcp->init(*(main->surface()), qts, hgt);
    psf = SurfacePtr(rcp);
  }
  psf->rename(capname);

  return psf;
}
