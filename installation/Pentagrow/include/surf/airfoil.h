
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
 
#ifndef SURF_AIRFOIL_H
#define SURF_AIRFOIL_H

#include <iosfwd>
#include "openframe.h"

/** Airfoil as spline.

  Interpolates or approximates a set of coordinate points, or generates
  NACA airfoils. The read() function is modestly intelligent and can
  parse most airfoil coordinate files with two columns for x- and 
  y-coordinates.

  The default transformation puts the 2D coordinates in the xz-plane, 
  which is suitable for wings. For vertical fins, rotate by 90 degrees.

  \ingroup geometry
  */
class Airfoil : public OpenFrame
{
  public:
    
    /// default construction
    Airfoil() : OpenFrame("UnknownAirfoil"), napx(-1) {}

    /// construction
    Airfoil(const std::string & s, int nap = -1) : OpenFrame(s), napx(nap) {}

    /// construction
    Airfoil(const std::string & s, const PointList<2> & c, int nap = -1)
        : OpenFrame(s), crd(c), napx(nap) {rebuild();}
    
    /// read from text stream
    void read(std::istream & is, int nap = -1);

    /// read from text file
    void read(const std::string & fname, int nap = -1);
    
    /// write, with optional header string
    void write(std::ostream & os, std::string hdr = "") const;

    /// normalize coordinates to range [0,1]
    void renormalize();

    /// create NACA 4-digit wing section
    void naca(int code, bool closed = true);
    
    /// create NACA 4-digit wing section from spec 
    void naca4(Real camber, Real cpos, Real thick, bool closed=true);
    
    /// create NACA 5-digit wing section from spec 
    void naca5(int iMeanLine, Real dcl, Real thick, bool closed=true);
    
    /// create a NACA-16 series airfoil
    void naca16(Real tc, Real xtcmax, Real cli, bool closed=true);

    /// create a NACA 6-series airfoil with one mean line (may fail)
    int naca(int ifamily, int icamber, Real toc, Real cli, Real a = 1.0);
    
    /// create a NACA 6-series airfoil with multiple mean lines (may fail)
    int naca(int ifamily, int icamber, Real toc, 
             const Vector & vcli, const Vector & va);

    /// approximate flat-plate section
    void flatPlate(Real thick, int nap = -1);
    
    /// close trailing edge gap if necessary
    void closeTrailingEdge(Real gap = 0.0);

    /// extend the nose by dx, used to create intermediate fairing airfoils
    void extend(Real dxNose, Real dyNose=0, Real dxTail=0, Real dyTail=0);

    /// chop off points at the trailing edge (for structural modeling)
    void chop(Real xcut);
    
    /// locate leading edge parameter 
    Real findLeadingEdge(Real tol = 1e-4) const;
    
    /** Generate new point locations. Interpolate with coordinate points located 
        at nps points on upper and lower side, with leading edge expansion
        factor xle and trailing edge expansion factor xte. Return curve parameters
        in t.*/
    void xpattern(uint nps, Real xle, Real xte, Vector & t) const;

    /// interpolate from recomputed points
    void reparametrize(const Vector & t);

    /// approximate using n points
    void approximate(int n);

    /// find a reasonable parametrization with n points (evaluates!)
    void adaptiveParam(size_t na, Vector &ua) const;

    /// xml representation stores 2D airfoil points
    virtual XmlElement toXml(bool share = false) const;
    
    /// construct from xml definition
    virtual void fromXml(const XmlElement & xe);

    /// clone an airfoil object
    virtual Airfoil *clone() const;
    
    /// access 2D section coordinates		
    const PointList<2> & sectionCoordinates() const {return crd;}

    /// construct name of NACA4 section from spec 
    static std::string naca4name(Real camber, Real cpos, Real thick);
    
    /// construct name of NACA5 section from spec 
    static std::string naca5name(int iMeanLine, Real dcl, Real thick);
    
    /// construct name of NACA6 airfoil section 
    static std::string naca6name(int ifamily, Real toc, Real cli);

    /// try to identify airfoil name in coordinate file 
    static std::string searchCoordName(const std::string & fname);
    
  private:

    /// set coordinates in right order
    void sortCoords();

    /// rebuild default spline representation from crd
    void rebuild();

    /// search for curve parameter corresponding to x/c value
    Real parameter(Real x, Real start) const;

  private:

    /// the original coordinates
    PointList<2> crd;
    
    /// interpolate or approximate
    int napx;
};

#endif
