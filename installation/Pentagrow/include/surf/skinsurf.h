
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
 
#ifndef SURF_SKINSURF_H
#define SURF_SKINSURF_H

#include <boost/shared_ptr.hpp>
#include <genua/point.h>
#include <genua/sharedvector.h>
#include <genua/splinebasis.h>
#include "curve.h"
#include "surface.h"

class IgesFile;

/** Skinned surface.

  SkinSurf is a bicubic spline surface which interpolates a set of curves. 
  Since this surface type is used very often, evaluation and derivatives must
  be computed efficiently. Therefore, the degree is restricted to 3 in both
  directions (bicubic nonrational spline surface). 

  When the surface is constructed, the set of curves can be interpolated 
  globally or locally using the Bessel or Akima methods for tangent 
  construction. For interactive applications, the local methods appear far more
  usefull.

  \ingroup geometry
  \sa LinearSurf, RevoSurf
  */
class SkinSurf : public Surface
{
  public:
    
    /// init surface
    SkinSurf(const std::string & s) : Surface(s) {}

    /// interpolate a vector of curves
    void init(CurvePtrArray & cv, bool iplocal=true, bool akima=false);

    /// evaluate spline surface
    Vct3 eval(Real u, Real v) const;

    /// derive spline surface
    Vct3 derive(Real u, Real v, uint ku, uint kv) const;
    
    /// compute surface point and tangent derivatives
    void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const;

    /// coordinate transformation
    void apply();
    
    /// XML output
    XmlElement toXml(bool share=false) const;
    
    /// XML input
    void fromXml(const XmlElement & xe);

    /// generate clone 
    SkinSurf *clone() const {return new SkinSurf(*this);}
    
    /// generate an IGES entity 128 
    int toIges(IgesFile & file, int tfi = 0) const;
    
    /// change knot merging tolerance 
    static void uKnotMergeTolerance(Real tol) {umergetol = tol;}
    
    /// set this to 100 if you need IGES export to CAD 
    static void limitUKnotCount(uint c) {iMaxKnots = c;} 
    
    /// compute statistics
    void dimStats(DimStat &stat) const;
    
    /// return an initial discretization pattern to start with 
    void initGridPattern(Vector & up, Vector & vp) const;
    
    /// return if surface is symmetric in u- or v-direction 
    void isSymmetric(bool & usym, bool & vsym) const;

  private:

    /// interpolate globally
    void globalIpol(CurvePtrArray & cv);

    /// interpolate locally
    void localIpol(CurvePtrArray & cv, bool akima = false);

    /// make curves compatible
    uint adaptCurves(CurvePtrArray & cv);

    /// determine one row of control points by local cubic interpolation
    void lcubCtlPoints(const PointGrid<3> & cvp, uint row, bool akima);

    /// compute approximate tangent vectors for surface slice
    void tangentsBessel(const PointList<3> & pts, PointList<3> & tng) const;
    
    /// compute approximate tangent vectors for surface slice
    void tangentsAkima(const PointList<3> & pts, PointList<3> & tng) const;
    
  private:

    /// basis in u- and v-direction
    SplineBasis ub, vb;

    /// control points
    PointGrid<3> cp;
    
    /// curve pointers used for interpolation
    CurvePtrArray ipc;
    
    /// interpolation parameter
    bool iploc, ipakima;
    
    /// tolerance for merging knot vectors 
    static Real umergetol;
    
    /// avoid more than 100 knots in u-direction 
    static uint iMaxKnots;
};

typedef boost::shared_ptr<SkinSurf> SkinSurfPtr;

#endif

