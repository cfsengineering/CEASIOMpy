
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
 
#ifndef SURF_DNWINGCRITERION_H
#define SURF_DNWINGCRITERION_H

#include "curve.h"
#include "dnrefine.h"

/** Refinement criterion adapted for wing surfaces.

  This is a specialized mesh refinement criterion for tapered wing surfaces.
  To provide a reasonable mesh quality, the maximum edge length parameter is
  scaled according to the local chord. Hence, the maxlen parameter should be
  given in terms of the maximum chord.

 \ingroup meshgen
 \sa DnMesh
*/
class DnWingCriterion : public DnRegionCriterion
{
  public:
    
    /// create unbound criterion
    DnWingCriterion() : DnRegionCriterion(), lerFactor(1.0), terFactor(1.0) {
      initBreaks();
    }
    
    /// copy refinement regions 
    explicit DnWingCriterion(const DnRegionCriterion & rc) : DnRegionCriterion(rc) {
      initBreaks();
    }
    
    /// add a break location
    void addBreak(Real v, Real f);
    
    /// register locations of kinks 
    void addVKinks(const Surface & srf, const Vector & vk);
    
    /// automatically generate breaks and scales from curve array
    void addBreaks(const CurvePtrArray & cpa, bool symflag = false);
    
    /// access current break positions
    const Vector & breaks() const {return vbreak;}
    
    /// change leading/trailing edge refinement factors 
    void edgeRefinement(Real lef, Real tef) {
      lerFactor = lef;
      terFactor = tef;
    }
    
    /// access factors 
    Real leRefinement() const {return lerFactor;}
    
    /// access factors 
    Real teRefinement() const {return terFactor;}
    
    /// evaluate triangle 'quality' - larger value means earlier refinement
    Real eval(const uint *vi) const;
    
    /// clone object 
    DnWingCriterion *clone() const;
  
    /// read criteria from xml representation
    void fromXml(const XmlElement & xe);

    /// write criteria to xml representation
    XmlElement toXml() const;
    
  private:
    
    /// default scale and breakpoints 0,1
    void initBreaks();
    
  private:
    
    /// position of breaks and kinks
    Vector vbreak, vkinks, scale;
    
    /// local derivatives Sv at kinks 
    PointList<3> svkinks; 
    
    /// leading-edge and trailing-edge refinement factors 
    Real lerFactor, terFactor;
};

typedef boost::shared_ptr<DnWingCriterion> DnWingCriterionPtr;

#endif

