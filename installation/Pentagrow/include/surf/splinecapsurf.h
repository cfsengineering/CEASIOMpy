
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
 
#ifndef SURF_SPLINECAPSURF_H
#define SURF_SPLINECAPSURF_H

#include "polysplinesurf.h"

class Curve;

/** Cap surface as a polynomial spline surface.
 *
 * \ingroup geometry
 * \sa PolySplineSurf
 */
class SplineCapSurf : public PolySplineSurf
{
  public:
    
    /// create undefined cap surface
    SplineCapSurf(const std::string & s = "") : PolySplineSurf(s) {}

    /// generate flat cap from tip/first/last curve
    void init(Real tsplit, const Curve & c);
    
    /// generate flat cap from tip/first/last curve
    void init(const Vector & tc, const Curve & c);
    
    /// for visualization & debugging
    void initGridPattern(Vector & up, Vector & vp) const;
    
    /// set this to 100 if you need IGES export to CAD 
    static void limitUKnotCount(uint c) {iMaxKnots = c;} 
    
  private:
    
    /// mesh constraints?
    
    /// limit on knot count
    static uint iMaxKnots;
};

#endif
