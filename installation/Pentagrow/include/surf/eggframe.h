
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
 
#ifndef SURF_EGGFRAME_H
#define SURF_EGGFRAME_H

#include "symframe.h"

/** Huegelschaeffer curve.

  EggFrame is a symmetric cubic spline curve which closely approximates
  the Huegelschaeffer (egg-shaped) curve with continuous curvature. The curve
  is defined by three points. The bottom (pzl) and top (pzu) points define
  the lowest and highest point of the contour, while the side point (pys)
  defines the lateral point of maximum width. 

  \ingroup geometry
  \sa SymFrame
  */
class EggFrame : public SymFrame
{
  public:

    /// initialize with name
    explicit EggFrame(const std::string & s) : SymFrame(s) {}

    /// create spline approximation
    void init(const Vct3 & pzl, const Vct3 & pzu, const Vct3 & pys);
    
    /// xml representation stores interpolation points
    virtual XmlElement toXml(bool share=false) const;
    
    /// construct from xml definition
    virtual void fromXml(const XmlElement & xe);
    
    /// generate clone 
    virtual EggFrame *clone() const;
    
  private:
    
    /// defining points
    Vct3 zl, zu, ys;
};

#endif
