
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
 
#include "planesurface.h"
#include "roundcapsurf.h"
#include "longcapsurf.h"
#include "ringcapsurf.h"
#include "meshgenerator.h"
#include "dnrefine.h"
#include "dnwingcriterion.h"
#include "asycomponent.h"

using namespace std;

AsyComponent::AsyComponent() 
{
  sScl = vct(1.0, 1.0, 1.0);
//  fill(bCap, bCap+4, false);
//  fill(captag, captag+4, NotFound);
  maintag = NotFound;
}

void AsyComponent::defaultCriterion()
{
  if (main) {
    main->criterion( DnRefineCriterionPtr(new DnRefineCriterion) );
  }
}

void AsyComponent::buildInitGrid(PointGrid<2> & pgi)
{
  const DnRefineCriterion & c(*criterion());
  surface()->initGrid(c.maxLength(), c.minLength(), c.maxPhi(), pgi);
}

void AsyComponent::surface(const SurfacePtr & s)
{
  if (main) {
    main->surface(s);
  } else {
    main = MeshComponentPtr(new MeshComponent(s));
    defaultCriterion();
  }
}

void AsyComponent::endCap(CapSide s, EndCap::Shape shape, Real h)
{
  const int k = (int) s;
  ecaps[k] = EndCap(shape, h);
  switch (s) {
  case CapULo:
    ecaps[k].attachedSide( west );
    break;
  case CapUHi:
    ecaps[k].attachedSide( east );
    break;
  case CapVLo:
    ecaps[k].attachedSide( south );
    break;
  case CapVHi:
    ecaps[k].attachedSide( north );
    break;

  };
}

void AsyComponent::endCap(const EndCap & c)
{
  switch (c.attachedSide()) {
  case west:
    ecaps[ CapULo ] = c;
    break;
  case south:
    ecaps[ CapVLo ] = c;
    break;
  case east:
    ecaps[ CapUHi ] = c;
    break;
  case north:
    ecaps[ CapVHi ] = c;
    break;
  default:
    throw Error("AsyComponent::endCap() - trying to "
                "register unattached end cap.");
  }
}

void AsyComponent::generateCaps()
{
  const side_t sides[] = {west, east, south, north};
  for (int k=0; k<4; ++k) {
    if (ecaps[k].isPresent())
      ecaps[k].create(main, sides[k]);
  }
}

void AsyComponent::adaptCaps()
{
  const side_t sides[] = {west, east, south, north};
  for (int k=0; k<4; ++k) {
    if (ecaps[k].isPresent())
      ecaps[k].adapt(main, sides[k]);
  }
}

void AsyComponent::transform()
{
  assert(defined());
  SurfacePtr psf = main->surface();
  psf->rotate(sRot[0], sRot[1], sRot[2]);
  psf->translate(sTrn);
  psf->apply();
}

void AsyComponent::append(MeshGenerator & mg)
{
  if (not main->freshMesh()) {
    PointGrid<2> pgi;
    buildInitGrid(pgi);
    main->clearConstraints();
    main->premesh(pgi);
  }
  
  generateCaps();
  mg.addComponent(main);
  for (int k=0; k<4; ++k) {
    if (ecaps[k].isPresent())
      mg.addComponent(ecaps[k].component());
  }
}

XmlElement AsyComponent::toXml() const
{
  XmlElement xe("AsyComponent");
  xe["origin"] = str(sTrn);
  xe["rotation"] = str(sRot);
  xe["scale"] = str(sScl);
  
  xe.append(surface()->toXml());
  xe.append(criterion()->toXml());
  
  for (int k=0; k<4; ++k) {
    if (ecaps[k].isPresent()) {
      XmlElement xc(ecaps[k].toXml());
      xc["side"] = str(k);
      xe.append(std::move(xc));
    }
  }
  
  return xe;
}
     
void AsyComponent::fromXml(const XmlElement & xe)
{
  sTrn = 0.0;
  sRot = 0.0;
  sScl = 1.0;
  
  if (xe.hasAttribute("origin"))
    fromString(xe.attribute("origin"), sTrn);
  if (xe.hasAttribute("rotation"))
    fromString(xe.attribute("rotation"), sRot);
  if (xe.hasAttribute("scale"))
    fromString(xe.attribute("scale"), sScl);
  
  // generate surface and mesh criterion
  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    if (itr->name() == "MeshCriterion") {
      if (itr->hasAttribute("lerfactor")) {
        DnWingCriterion *wc = new DnWingCriterion;
        wc->fromXml(*itr);
        main->criterion(DnRefineCriterionPtr(wc));
      } else {
        DnRegionCriterion *rc = new DnRegionCriterion;
        rc->fromXml(*itr);
        main->criterion(DnRefineCriterionPtr(rc));
      }
    } else {
      SurfacePtr psf = Surface::createFromXml(*itr);
      if (psf)
        main->surface(psf);
    }
  }
  
  // generate caps
  for (int k=0; k<4; ++k)
    ecaps[k].reset();
  
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    if (itr->name() == "Cap") {
      int k = Int(itr->attribute("side"));
      ecaps[k].fromXml(*itr);
    }
  }
}

//void AsyComponent::cap(CapSide s, const SurfacePtr & cp)
//{
//  DnRefineCriterionPtr rc(new DnRefineCriterion(*criterion()));
//  MeshComponentPtr mcp(new MeshComponent(cp, rc));
//  mcp->allowRefinement(false);
//  mcp->kinkLimit(PI);
//  caps[(int) s] = mcp;
//  mcp->registerNeighbor(main.get());
//  main->registerNeighbor(mcp.get());
//}
//void AsyComponent::generateCaps()
//{
//  Indices idx;
//  const side_t sides[] = {west, east, south, north};
//  for (int k=0; k<4; ++k) {
//    if (bCap[k]) {
//
//      // extract boundary points
//      main->boundary(sides[k], idx);
//
//      // adapt normal direction
//      if (sides[k] == north)
//        std::reverse(idx.begin(), idx.end());
//
//      const int np = idx.size();
//      PointList<3> pts(np);
//      for (int i=0; i<np; ++i)
//        pts[i] = main->vertex(idx[i]);
//
//      PointList<2> qts(np);
//      for (int i=0; i<np; ++i)
//        qts[i] = main->parameter(idx[i]);
//
//      string capname =  main->surface()->name() + "Cap" + str(k+1);
//      if ( fabs(capheight[k]) == 0.0 ) {
//        RingCapSurf *rcp = new RingCapSurf(capname);
//        rcp->initFlat(*(main->surface()), qts);
//        cap(CapSide(k), SurfacePtr(rcp));
//        // caps[k]->allowRefinement(true);
//      } else {
//        LongCapSurf *rcp = new LongCapSurf(pts, capheight[k]);
//        rcp->rename(capname);
//        cap(CapSide(k), SurfacePtr(rcp));
//      }
//
//      caps[k]->smoothingIterations(0);
//      caps[k]->smoothingFactor(0.0);
////      if ( fabs(capheight[k]) < 0.01) {
////        caps[k]->smoothingIterations(2);
////        caps[k]->smoothingFactor(0.25);
////      } else {
////        caps[k]->smoothingIterations(0);
////        caps[k]->smoothingFactor(0.0);
////      }
//    }
//  }
//
//  bCapIntersected = false;
//}
//
//void AsyComponent::adaptLongCap(int k)
//{
//  if (not caps[k])
//    return;
//
//  // test if this cap is intersected by any other surface
//  bCapIntersected |= (caps[k]->nConstraint() != 0);
//
//  // extract mesh boundary
//  const side_t sides[] = {west, east, south, north};
//  Indices idx;
//  main->boundary(sides[k], idx);
//
//  // adapt normal direction
//  if (sides[k] == north)
//    std::reverse(idx.begin(), idx.end());
//
//  int np = idx.size();
//  PointList<3> pts(np);
//  for (int i=0; i<np; ++i)
//    pts[i] = main->vertex(idx[i]);
//
//  PointList<2> qts(np);
//  for (int i=0; i<np; ++i)
//    qts[i] = main->parameter(idx[i]);
//
//  LongCapSurf *rcp;
//  RingCapSurf *pcp;
//  rcp = dynamic_cast<LongCapSurf*>( caps[k]->surface().get() );
//  pcp = dynamic_cast<RingCapSurf*>( caps[k]->surface().get() );
//  assert(rcp != 0 or pcp != 0);
//  if (rcp != 0) {
//    rcp->init(pts, capheight[k]);
//    caps[k]->premesh();
//    caps[k]->reconstrain();
//  } else if (pcp != 0) {
//    pcp->initFlat(*(main->surface()), qts);
//    caps[k]->premesh();
//    caps[k]->reconstrain();
//  }
//
//  caps[k]->refine();
//
////   // project boundary points and insert
////   Indices ibnd;
////   main->boundary(sides[k], ibnd);
////   int np = ibnd.size();
////   PointList<2> qbnd(np);
////   PointList<3> pbnd(np);
////   for (int i=0; i<np; ++i) {
////     pbnd[i] = main->vertex(ibnd[i]);
////     qbnd[i] = rcp->boundaryProjection(pbnd[i]);
////   }
////
////   if (not caps[k]->insertBoundaryPoints(qbnd, pbnd)) {
////     throw Error("Could not insert boundary points.");
////   }
////   caps[k]->refine();
//}


