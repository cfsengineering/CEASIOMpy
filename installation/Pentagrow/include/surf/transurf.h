
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
 
#ifndef SURF_TRANSURF_H
#define SURF_TRANSURF_H

#include "surface.h"
#include "curve.h"

/** Cubic transition patch.

  TranSurf is a surface which is meant to be created as a transition between 
  two other surfaces. 

  \ingroup geometry
  \sa Surface
*/
class TranSurf : public Surface
{
  public:
    
    /// create undefined transition surface
    TranSurf(const std::string & s) : Surface(s) {}
    
    /// enable inheritance
    virtual ~TranSurf() {}

    /// initialize with surfaces and boundary curves 
    void init(const SurfacePtr & s0, const CurvePtr & c0,
              const SurfacePtr & s1, const CurvePtr & c1, Real lenf=0.5);  
    
    /// special case : slope at first curve is constant
    void init(const Vct3 & slope0, const CurvePtr & c0,
              const SurfacePtr & s1, const CurvePtr & c1, Real lenf=0.5);  
    
    /// special case : slope at last curve is constant
    void init(const SurfacePtr & s0, const CurvePtr & c0,
              const Vct3 & slope1, const CurvePtr & c1, Real lenf=0.5);
    
    /// evaluation interface
    Vct3 eval(Real u, Real v) const;

    /// derive at (u,v)
    Vct3 derive(Real u, Real v, uint du, uint dv) const;

    /// compute point and tangent derivatives at (u,v), for efficiency
    void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const;
    
    /// coordinate transformation
    void apply();
    
    /// XML output
    virtual XmlElement toXml(bool share=false) const;
    
    /// XML input
    virtual void fromXml(const XmlElement & xe);
    
    /// append to IGES file and return the directory entry index, if implemented 
    int toIges(IgesFile & file, int tfi = 0) const;
    
    /// generate a clone 
    virtual Surface *clone() const {return new TranSurf(*this);}
    
  protected:
    
    /// initialize outer control point columns (first and last)
    uint initOuterCols(const CurvePtr & c0, const CurvePtr & c1, Vector & upar);
    
  protected:
    
    /// spline bases 
    SplineBasis ub, vb;
    
    /// control point grid 
    PointGrid<3> cp;
};

#endif
