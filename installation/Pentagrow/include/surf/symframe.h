
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
 
#ifndef SURF_SYMFRAME_H
#define SURF_SYMFRAME_H

#include <genua/point.h>
#include "curve.h"

/** Symmetric fuselage frame.

  SymFrame is typically used to create fuselage sections which are symmetric
  with respect to the center (xz-) plane. Interpolation points are only those
  on that side of the fuselage which belongs to lower [0,0.5] circumferential
  parameter (u).
  
  The XML representation stores only these interpolation points.

  \ingroup geometry
  */
class SymFrame : public Curve
{
  public:

    /// initialize with name
    explicit SymFrame(const std::string & s) : Curve(s) {}

    /// interpolate points (always with degree 3)
    Vector init(const PointList<3> & pts);
    
    /// xml representation stores interpolation points
    virtual XmlElement toXml(bool share=false) const;
    
    /// construct from xml definition
    virtual void fromXml(const XmlElement & xe);
    
    /// generate a clone
    virtual SymFrame *clone() const;
    
  private:
    
    /// interpolation points
    PointList<3> ipp;
};

#endif

