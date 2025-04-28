
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
 
#ifndef SURF_STITCHEDSURF_H
#define SURF_STITCHEDSURF_H

#include "surface.h"

class StitchedWingSpec;

/** Combined surface.

  StitchedSurf joins a number of other surfaces and maps the parameteric
  evaluation to one of them, depending on the value of the parameter v.
  The constituent surfaces may be discontinuous.

  \ingroup geometry
  */
class StitchedSurf : public Surface
{
  public:

    /// empty construction
    StitchedSurf(const std::string & s = "NoNameStitchedSurf") : Surface(s) {}

    /// make a deep copy 
    StitchedSurf(const StitchedSurf & a) : Surface(a) {init(a.sfl, a.vbreak);}
    
    /// create from surface array (copies surfaces)
    void init(const SurfaceArray & s, const Vector & vb);
    
    /** Initialize from curves. 
    Use the first nwl curves to construct the winglet, and the remaining
    to generate the main wing surface. If cubic is true, use a bicubic
    spline surface for the wing; otherwise, use a linear loft.*/
    // void init(CurvePtrArray & cpa, uint nwl = 0, bool cubic = false);
    
    /// initialize from detailed specification 
    void init(const StitchedWingSpec & spec);
    
    /// make breakpoints available
    const Vector & breakPoints() const {return vbreak;}

    /// access surface segments
    const SurfaceArray & segments() const {return sfl;}

    /// evaluation interface
    Vct3 eval(Real u, Real v) const;

    /// derive at (u,v)
    Vct3 derive(Real u, Real v, uint du, uint dv) const;

    /// compute point and tangent derivatives at (u,v), for efficiency
    void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const; 
    
    /// compute normal vector
    Vct3 normal(Real u, Real v) const;
    
    /// coordinate transformation
    void apply();
    
    /// initialize mesh generator (marks kink edges)
    void initMesh(const DnRefineCriterion & c, DnMesh & gnr) const;
    
    /// XML output 
    XmlElement toXml(bool share=false) const;
    
    /// XML input
    void fromXml(const XmlElement & xe);
    
    /// write constituent surfaces to IGES file 
    int toIges(IgesFile & file, int tfi=0) const;
    
    /// generate a clone 
    StitchedSurf *clone() const {return new StitchedSurf(*this);}
    
    /// compute dimensional statistics
    virtual void dimStats(DimStat & stat) const;

    /// return an initial discretization pattern to start with 
    void initGridPattern(Vector & up, Vector & vp) const;
    
    /// return if surface is symmetric in u- or v-direction 
    void isSymmetric(bool & usym, bool & vsym) const;
    
  private:

    /// build once surface list is present 
    // void construct();
    
    /// find surface for value of v
    uint segment(Real v) const {
      assert(v >= vbreak.front());
      assert(v <= vbreak.back());
      Vector::const_iterator pos;
      pos = std::lower_bound(vbreak.begin(), vbreak.end(), v);
      if (pos == vbreak.begin())
        return 1;
      else if (pos == vbreak.end())
        return vbreak.size()-1;
      else
        return std::distance(vbreak.begin(), pos);
    }

  private:

    /// break points in v direction
    Vector vbreak;

    /// child surfaces
    SurfaceArray sfl;
};

typedef boost::shared_ptr<StitchedSurf> StitchedSurfPtr;

/** Specification of wing with multiple segments.

  Temporary object to facilitate the construction of wings with multiple
  segments which are based on different types of interpolation. This is
  especially useful for wings with blended winglets and cubic segments.

  */
class StitchedWingSpec
{
  public:
    
    enum SegType {SegLinear, SegCubic, SegWlBlend};
  
    /// initialize with reference to curves 
    StitchedWingSpec(const CurvePtrArray & crv) : cpa(crv) {}
    
    /// define a new segment from curves [first, last] 
    uint addSegment(uint first, uint last, SegType s = SegLinear);
    
    /// number of segments 
    uint nsegments() const {return sType.size();}
    
    /// construct surfaces from segments 
    void construct(SurfaceArray & slist, Vector & vbreak) const;
    
  private:
    
    /// curves to use for interpolation 
    const CurvePtrArray & cpa;
    
    /// specify which curves make up segments 
    Indices sBegin, sEnd;
    
    /// segment types
    std::vector<SegType> sType;
};

#endif
