
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
 
#ifndef SURF_ROTSURF_H
#define SURF_ROTSURF_H

#include "curve.h"
#include "surface.h"

/** Rotational surface
 *
 * \deprecated
 */
class RotSurf : public Surface
{
  public:

    /// init surface
    RotSurf(const std::string & s) : Surface(s) {}

    /// rotate curve about axis through pa and pb
    void init(const CurvePtr & c, const Vct3 & pa, const Vct3 & pb);

    /// evaluate spline surface
    Vct3 eval(Real u, Real v) const;

    /// derive spline surface
    Vct3 derive(Real u, Real v, uint ku, uint kv) const;

    /// coordinate transformation
    void apply();
    
    /// XML output 
    XmlElement toXml(bool share=false) const;
    
    /// XML input
    void fromXml(const XmlElement & xe);

    /// generate clone 
    RotSurf *clone() const {return new RotSurf(*this);}
    
  // protected:
    
    /// return an initial discretization pattern to start with 
    void initGridPattern(Vector & up, Vector & vp) const;
    
    /// return if surface is symmetric in u- or v-direction 
    void isSymmetric(bool & usym, bool & vsym) const;
    
  private:

    /// original outline curve
    CurvePtr corg;
    
    /// curves used for surface evaluation
    Curve cva, cvb;

    /// origin and rotation axis
    Vct3 org, rax;
};

#endif
