
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
 
#ifndef SURF_PLANESURFACE_H
#define SURF_PLANESURFACE_H

#include "forward.h"
#include "surface.h"

/** Simple plane surface.
 *
 *
 * \ingroup geometry
 * \sa Surface
 */
class PlaneSurface : public Surface
{
  public:
    
    /// named plane surface
    PlaneSurface(const std::string & s="UnknownPlaneSurf") : Surface(s) {}
    
    /// initialize from origin and directions
    PlaneSurface(const Vct3 & po, const Vct3 & Su, const Vct3 & Sv,
                 const std::string & s="UnknownPlaneSurf");

    /// virtual destructor
    virtual ~PlaneSurface() {}

    /// initialize with origin and directions
    void init(const Vct3 & po, const Vct3 & Su, const Vct3 & Sv) {
      org = po; tu = Su; tv = Sv;
    }
    
    /// fit plane surface to polyline
    void init(const PointList<3> & pts, Real expfactor = 1.25);

    /// move parallel to plane
    void shiftParallel(Real d) {org += d*normal(0.0,0.0);}
    
    /// evaluation interface
    Vct3 eval(Real u, Real v) const {return org + u*tu + v*tv;}

    /// derive at (u,v)
    Vct3 derive(Real u, Real v, uint du, uint dv) const;

    /// compute point and tangent derivatives at (u,v), for efficiency
    void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const;
    
    /// project point onto surface 
    bool project(const Vct3 & pt, Vct2 & q,
                 Real tol=1e-6, Real dpmin=1e-6) const;
    
    /// compute normal vector
    Vct3 normal(Real, Real) const {
      return cross(tu,tv).normalized();
    }    

    /// coordinate transformation
    void apply();

    /// compute typical dimension
    Real typLength() const {return 0.5*(norm(tu) + norm(tv));}
    
    /// initialize mesh generator
    void initMesh(const DnRefineCriterion & c, DnMesh & gnr) const;
    
    /// initialize u- and v-grid pattern
    void initGridPattern(Vector &up, Vector &vp) const;

    /// XML output
    XmlElement toXml(bool share=false) const;
    
    /// XML input
    void fromXml(const XmlElement & xe);
    
    /// append to IGES file and return the directory entry index, if implemented 
    // int toIges(IgesFile & file, int tfi = 0) const;
    
    /// generate a clone 
    virtual Surface *clone() const;
    
  private:
    
    /// origin (u=0, v=0), tangential directions
    Vct3 org, tu, tv;
};

#endif
