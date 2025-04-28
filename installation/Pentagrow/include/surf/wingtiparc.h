
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
 
#ifndef SURF_WINGTIPARC_H
#define SURF_WINGTIPARC_H

#include "skinsurf.h"

/** Splined wing-tip arc.

  This is a fully-defined surface object for wingtip arcs with circular leading-
  and straight trailing edge. Both the rounded LE and the TE of the tip arc will
  be tangentially compatible with the surface to which the arc is attached.

  The surface is implemented using a SkinSurf, where the interpolated sections
  are internally created by referring to the surface to which the arc is 
  connected.

  As the name suggests, WingTipArc is meant as an extension of wing surfaces to
  the tips, and although it may generate usable result with other surfaces, it 
  is not intended to be used for that. 

  \ingroup geometry
  \sa Surface
  */
class WingTipArc : public Surface
{
  public:

    /// create named surface
    WingTipArc(const std::string & s) : Surface(s), skin(s) {}

    /** Create arc.
    A tip arc with span s is attached to surface 'srf', at the 
    position 'vpos' in the v-parametric direction (axial direction).
    Choose vpos equal to 0 or 1, and s smaller than the tip chord of the
    wing surface, otherwise, the result may not be well-defined. **/
    void init(const Surface & srf, Real vpos, Real s);
    
    /// evaluate position
    Vct3 eval(Real u, Real v) const {
      return skin.eval(u,v);
    }

    /// evaluate tangents
    Vct3 derive(Real u, Real v, uint ku, uint kv) const {
      return skin.derive(u,v,ku,kv);
    }

    /// apply coordinate transformation
    void apply() {
      skin.apply();
    }

    /// write to xml representation (SkinSurf)
    XmlElement toXml(bool share=false) const {
      return skin.toXml(share);
    }

    /// read from xml representation (SkinSurf)
    void fromXml(const XmlElement & xe) {
      skin.fromXml(xe);
    }

    /// generate clone 
    WingTipArc *clone() const {return new WingTipArc(*this);}
    
  private:

    /// initialize dimensions required for initialization
    void initDimensions(const Surface & srf, Real pos, Real s,
                        PointList<3> & pts);

    /// scale and shift a set of points 
    void scaleShift(Real sfc, Real sfh, Real db, Real y,
                    PointList<3> & pts) const;

  private:

    /// tip arc is implemented using a specialized lofted surface
    SkinSurf skin;

    /// directions needed for initialization
    Vct3 ple, rnormal, back, up;

    /// dimensions needed for initialization
    Real rchord, radius, alpha, gamma;

    /// flag: true if v=1 is at the tip and v=0 connects to the wing
    bool vfwd;
};

#endif
