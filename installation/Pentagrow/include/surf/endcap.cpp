
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
 

#include "endcap.h"
#include "longcapsurf.h"
#include "ringcapsurf.h"
#include "dnrefine.h"
#include <genua/xcept.h>

using namespace std;

MeshComponentPtr EndCap::create(MeshComponentPtr main, side_t side)
{
  MeshComponentPtr cp;
  if (not present)
    return cp;

  mainside = side;

  // cap surface name
  string capname = main->surface()->name();
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

  // adapt normal direction for long cap
  if (side == north or side == east)
  // if ((shape == LongCap) and (side == north or side == east))
    std::reverse(idx.begin(), idx.end());

  const int np = idx.size();
  PointList<3> pts(np);
  for (int i=0; i<np; ++i)
    pts[i] = main->vertex(idx[i]);

  SurfacePtr psf;
  if (shape == LongCap) {
    LongCapSurf *rcp = new LongCapSurf(pts, fheight);
    psf = SurfacePtr(rcp);
  } else if (shape == RingCap) {
    PointList<2> qts(np);
    for (int i=0; i<np; ++i)
      qts[i] = main->parameter(idx[i]);
    RingCapSurf *rcp = new RingCapSurf;
    rcp->init(*(main->surface()), qts, fheight);
    psf = SurfacePtr(rcp);
  }
  psf->rename(capname);

  // assign the main bodies
  DnRefineCriterionPtr rc(new DnRefineCriterion(*(main->criterion())) );
  assert(psf);
  cap = MeshComponentPtr(new MeshComponent(psf, rc));

  // cannot refine surfaces with degenerate parametrization
  cap->allowRefinement(false);
  cap->kinkLimit(PI);
  cap->registerNeighbor(main.get());
  main->registerNeighbor(cap.get());

  // switch mesh smoothing off
  cap->smoothingIterations(0);
  cap->smoothingFactor(0.0);

  return cap;
}

void EndCap::adapt(MeshComponentPtr main, side_t side)
{
  if (not present)
    return;
  if (not cap)
    return;

  mainside = side;

  Indices idx;
  main->boundary(side, idx);

  // adapt normal direction for long cap
  if (side == north or side == east)
  // if ((shape == LongCap) and (side == north or side == east))
    std::reverse(idx.begin(), idx.end());

  const int np = idx.size();
  PointList<3> pts(np);
  for (int i=0; i<np; ++i)
    pts[i] = main->vertex(idx[i]);

  if (shape == LongCap) {
    LongCapSurf *lcp(0);
    lcp = dynamic_cast<LongCapSurf*>( cap->surface().get() );
    assert(lcp != 0);
    lcp->init(pts, fheight);
  } else if (shape == RingCap) {

    PointList<2> qts(np);
    for (int i=0; i<np; ++i)
      qts[i] = main->parameter(idx[i]);

    RingCapSurf *rcp(0);
    rcp = dynamic_cast<RingCapSurf*>( cap->surface().get() );
    assert(rcp != 0);
    rcp->init(*(main->surface()), qts, fheight);
  }

  cap->premesh();
  cap->reconstrain();
  cap->refine();
}

XmlElement EndCap::toXml() const
{
  XmlElement xc("Cap");
  switch (shape) {
  case LongCap:
    xc["shape"] = "LongCap";
    break;
  case RingCap:
    xc["shape"] = "RingCap";
    break;
  }
  xc["height"] = str(fheight);
  xc["side"] = str(mainside);
  return xc;
}

void EndCap::fromXml(const XmlElement & xe)
{
  assert(xe.name() == "Cap");
  reset();
  fheight = xe.attr2float("height", 0.0);
  if (not xe.hasAttribute("shape")) {
    shape = LongCap;
  } else {
    string ss = xe.attribute("shape");
    if (ss == "LongCap")
      shape = LongCap;
    else if (ss == "RingCap")
      shape = RingCap;
    else
      throw Error("EndCap::fromXml(): Do not recognize cap shape.");
  }
  if (xe.hasAttribute("side"))
    fromString(xe.attribute("side"), mainside);

  toggle(true);
}
