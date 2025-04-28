
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
 
#ifndef SURF_SPOTREFINE_H
#define SURF_SPOTREFINE_H

#include <genua/svector.h>
#include "dnrefine.h"

class MeshComponent;
class SpotRefine;
typedef std::vector<SpotRefine> RSpotArray;

/** Point mesh refinement

  \ingroup meshgen
  \sa DnMesh
  */
class SpotRefine
{
  public:
  
    /// undefined 
    SpotRefine() : ru(0.0), rv(0.0) {}
  
    /// construct from triangle
    SpotRefine(const MeshComponent & c, const uint *vi, Real sratio);
    
    /// check if this overlaps spot a
    bool overlaps(const SpotRefine & a) const;
  
    /// extand this spot to cover a
    void merge(const SpotRefine & a);
    
    /// add corresponding region to criterion
    void append(Real f, DnRegionCriterionPtr rcp) const;
    
    /// join neighbor spots
    static void mergeOverlaps(RSpotArray & xsa);
    
    /// append all spots to criterion, return marker
    static uint append(const RSpotArray & xsa, Real f, DnRefineCriterionPtr rcp);
    
    /// erase appended regions using marker
    static void erase(uint npre, DnRefineCriterionPtr rcp);
    
    // debug
    std::ostream & write(std::ostream & os) const;
    
  private:
    
    /// center in parameter space
    Vct2 ctr;
    
    /// u and v radius in parameter space
    Real ru, rv, maxsr;
};



#endif
