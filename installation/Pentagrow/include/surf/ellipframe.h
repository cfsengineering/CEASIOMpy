
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
 
#ifndef SURF_ELLIPFRAME_H
#define SURF_ELLIPFRAME_H

#include "symframe.h"

/** Elliptic fuselage frame.

  In the simplest case, this class represents a circular fuselage section
  in the (yz)-plane. Alternatively, it is possible to generate elliptical 
  and double elliptical frames (with different axes upward and downward).
  
  Note that all types of curve are finally created by interpolation using 
  cubic splines which is necessary for the generation of lofted surfaces.

  \ingroup geometry
  \sa SymFrame
  */
class EllipFrame : public SymFrame
{
  public:
    
    /// construction with name
    explicit EllipFrame(const std::string & s) : SymFrame(s) {}
  
    /// initialization for circle
    void init(const Vct3 & ctr, Real radius);
    
    /// initialization for simple ellipse
    void init(const Vct3 & ctr, Real rz, Real ry);
    
    /// initialization for double elliptic curve
    void init(const Vct3 & ctr, Real rzdown, Real rzup, Real ry);
    
    /// xml representation stores dimensions and center
    virtual XmlElement toXml(bool share=false) const;
    
    /// construct from xml representation
    virtual void fromXml(const XmlElement & xe);
    
    /// generate a clone
    virtual EllipFrame *clone() const;
    
  private:
 
    /// center position
    Vct3 ectr;
    
    /// radii
    Real rlo, rhi, rs;
};

#endif
