
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
 
#include <boost/shared_ptr.hpp>
#include "dnrfregion.h"
#include "meshcomponent.h"
#include "spotrefine.h"

using namespace std;

SpotRefine::SpotRefine(const MeshComponent & c, const uint *vi, Real sratio) 
  : maxsr(sratio)
{
  assert(vi != 0);
  const Vct2 & q1( c.parameter(vi[0]) );
  const Vct2 & q2( c.parameter(vi[1]) );
  const Vct2 & q3( c.parameter(vi[2]) );
  
  ctr = (q1 + q2 + q3) / 3.0;
  ru = max(fabs(q1[0]-q2[0]), max(fabs(q1[0]-q3[0]), fabs(q2[0]-q3[0])));
  rv = max(fabs(q1[1]-q2[1]), max(fabs(q1[1]-q3[1]), fabs(q2[1]-q3[1])));
}

bool SpotRefine::overlaps(const SpotRefine & a) const 
{
  Real du = fabs(ctr[0] - a.ctr[0]);
  Real dv = fabs(ctr[1] - a.ctr[1]);
  if (du < ru+a.ru and dv < rv+a.rv)
    return true;
  else
    return false; 
}

void SpotRefine::merge(const SpotRefine & a) 
{
  Real umin = std::min(ctr[0]-ru, a.ctr[0]-a.ru);
  Real umax = std::max(ctr[0]+ru, a.ctr[0]+a.ru);
  Real vmin = std::min(ctr[1]-rv, a.ctr[1]-a.rv);
  Real vmax = std::max(ctr[1]+rv, a.ctr[1]+a.rv);
  ctr[0] = 0.5*(umin + umax);
  ctr[1] = 0.5*(vmin + vmax);
  ru = 0.5*(umax - umin);
  rv = 0.5*(vmax - vmin);
  maxsr = std::max(maxsr, a.maxsr);
}

void SpotRefine::append(Real f, DnRegionCriterionPtr rcp) const
{
  if (ru <= 0 or rv <= 0)
    return;
  f = max(f, 1.0/maxsr);
  DnRefineRegion r(ctr, ru, rv, f);
  rcp->addRegion(r);
}

void SpotRefine::mergeOverlaps(RSpotArray & xsa)
{
  const uint nx( xsa.size() );
  if (nx < 2)
    return;
  
  RSpotArray tmp;
  vector<bool> ovrlp(nx);
  for (uint i=0; i<nx; ++i)
    ovrlp[i] = false;
  
  for (uint i=0; i<nx; ++i) {
    if (ovrlp[i])
      continue;
    
    SpotRefine spot( xsa[i] );
    for (uint j=i+1; j<nx; ++j) {
      if (spot.overlaps(xsa[j])) {
        spot.merge(xsa[j]);
        ovrlp[j] = true;
      }
    }
    tmp.push_back(spot);
  }
  tmp.swap(xsa);
}

uint SpotRefine::append(const RSpotArray & xsa, Real f, 
                        DnRefineCriterionPtr rcp)
{
  DnRegionCriterionPtr rgp;
  rgp = boost::dynamic_pointer_cast<DnRegionCriterion>(rcp);
  if (not rgp)
    return 0;
  
  uint npre = rgp->nregions();
  for (uint i=0; i<xsa.size(); ++i)
    xsa[i].append(f, rgp);
  
  return npre;
}

void SpotRefine::erase(uint npre, DnRefineCriterionPtr rcp)
{
  DnRegionCriterionPtr rgp;
  rgp = boost::dynamic_pointer_cast<DnRegionCriterion>(rcp);
  if (not rgp)
    return;
  
  uint nlast = rgp->nregions();
  rgp->removeRegions(npre, nlast);
}
  
std::ostream & SpotRefine::write(std::ostream & os) const
{
  os << "RF region ctr " << ctr << " ru " << ru << " rv " << rv << endl;
  return os; 
}
