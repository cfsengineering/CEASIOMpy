
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
 
#ifndef SURF_DNRFREGION_H
#define SURF_DNRFREGION_H

#include <vector>
#include <genua/svector.h>
#include <genua/xmlelement.h>

/** Mesh refinement region.

  Instances of this class are used to specify parametric mesh regions 
  to be refined. Currently, rectangular regions with a constant refinement
  ratio and elliptical regions with a linear radial refinement are supported.

  For compatibility reasons, the refinement factor specified in the constructor
  or XML representation is smaller than 1.0 for refinement and larger for
  coarsening. The function factor() returns the inverse of this value, which
  is used by DnRegionCriterion and children. 

 \ingroup meshgen
 \sa DnMesh
  */
class DnRefineRegion
{
  public:
    
    /// initialize rectangular region
    DnRefineRegion(const Vct2 & plo, const Vct2 & phi, Real rf) : 
      rtype(DnRectRegion) 
    {
      assert(rf > 0.0);
      rfd[0] = plo[0];
      rfd[1] = plo[1];
      rfd[2] = phi[0];
      rfd[3] = phi[1];
      rfd[4] = 1.0 / rf;
    }
    
    /// initialize circular region
    DnRefineRegion(const Vct2 & ctr, Real ru, Real rv, Real rf) : 
      rtype(DnRadialRegion) 
    {
      assert(ru > 0.0);
      assert(rv > 0.0);
      assert(rf > 0.0);
      rfd[0] = ctr[0];
      rfd[1] = ctr[1];
      rfd[2] = ru;
      rfd[3] = rv;
      rfd[4] = 1.0 / rf;
    }
    
    /// initialize from XML representation 
    explicit DnRefineRegion(const XmlElement & xe) {fromXml(xe);}
    
    /// compute refinement factor
    inline Real factor(const Vct2 & p) const 
    {
      if (rtype == DnRadialRegion) {
        Real usq = sq( (p[0]-rfd[0]) / rfd[2] );
        Real vsq = sq( (p[1]-rfd[1]) / rfd[3] );
        if (usq+vsq > 1.0) {
          return 1.0;
        } else {
          // Real t = sqrt(usq + vsq);
          Real t = usq + vsq;
          return (1-t)*rfd[4] + t;
        }
      } else {
        if (p[0] < rfd[0] or p[0] > rfd[2])
          return 1.0;
        else if (p[1] < rfd[1] or p[1] > rfd[3])
          return 1.0;
        else
          return rfd[4];
      } 
    }
    
    /// generate an xml representation 
    XmlElement toXml() const;
    
    /// recover from xml representation 
    void fromXml(const XmlElement & xe);
    
  private:
    
    /// region boundaries and refinement factors
    Real rfd[5];
    
    /// type switch
    enum {DnRadialRegion, DnRectRegion} rtype;
};

typedef std::vector<DnRefineRegion> DnRegionArray;

#endif

