
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
 
#ifndef SURF_WINGLETBLEND_H
#define SURF_WINGLETBLEND_H

#include "curve.h"
#include "surface.h"

/** Elliptic arc surface for blended winglets.

  This surface generates an elliptic blending surface between two
  (translated, rotated) interface curves. As the name suggests, it is 
  primarily meant to create smooth wing-to-winglet transitions.
  
  \ingroup geometry
  \sa TranSurf
  */
class WingletBlend : public Surface
{
  public:
    
    /// initialize with name
    WingletBlend(const std::string & s): Surface(s) {}
    
    /// destructor
    ~WingletBlend() {}
    
    /// construct from two curves (throws on failure)
    void init(const Curve & a, const Curve & b);
    
    /// evaluate blend surface
    Vct3 eval(Real u, Real v) const;
    
    /// compute point and tangent derivatives at (u,v), for efficiency
    void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const; 
    
    /// compute normal vector
    Vct3 normal(Real u, Real v) const;
    
    /// derive at (u,v)
    Vct3 derive(Real u, Real v, uint du, uint dv) const;

    /// coordinate transformation
    void apply();
        
    /// XML output
    XmlElement toXml(bool share=false) const;
    
    /// XML input
    void fromXml(const XmlElement & xe);
    
    /// generate a clone 
    WingletBlend *clone() const {return new WingletBlend(*this);}
    
  protected:
    
    /// return an initial discretization pattern to start with 
    void initGridPattern(Vector & up, Vector & vp) const;
    
    /// return if surface is symmetric in u- or v-direction 
    void isSymmetric(bool & usym, bool & vsym) const;
    
  private:
    
    /// compute rotation parameters from flat base surface
    void initRotation();
    
  private:
    
    /// baseline curves at v=0 and v=1
    CurvePtr c0, c1;
    
    /// rotation axis
    Vct3 lp, ldir;
    
    /// constant transformation matrix
    Mtx22 csm;
    
    /// angular parameters
    Real theta0, theta1;
};

#endif
