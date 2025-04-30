
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
 
#ifndef ENDCAP_H
#define ENDCAP_H

#include <genua/defines.h>
#include "meshcomponent.h"

/** Properties of caps on AsyComponents.
 *
 * \ingroup meshgen
 * \sa AsyComponent
 */
class EndCap
{
  public:

    typedef enum {LongCap, RingCap} Shape;

    /// default cap is not present
    EndCap() : fheight(0.0), shape(EndCap::LongCap),
               mainside(none), itag(NotFound), present(false) {}

    /// instanciate default long cap (simple wingtip cap)
    explicit EndCap(Real h) : fheight(h), shape(EndCap::LongCap),
                     mainside(none), itag(NotFound), present(true) {}

    /// detailed constructor
    EndCap(Shape s, Real h) : fheight(h), shape(s), mainside(none),
                              itag(NotFound), present(true) {}

    /// construct from xml element
    explicit EndCap(const XmlElement & xe) {fromXml(xe);}

    /// destroy surface
    void reset() {
      fheight = 0.0;
      shape = LongCap;
      mainside = none;
      itag = NotFound;
      present = false;
      cap.reset();
    }

    /// access shape type
    EndCap::Shape capShape() const {return shape;}

    /// access shape type
    void capShape(EndCap::Shape s) {shape = s;}

    /// access height value
    Real height() const {return fheight;}

    /// access height value
    void height(Real h) {fheight = h;}

    /// switch on/off
    void toggle(bool flag) {present = flag;}

    /// retrieve attachment side tag
    side_t attachedSide() const {return mainside;}

    /// set attachment side
    void attachedSide(side_t s) {mainside = s;}

    /// check if present
    bool isPresent() const {return present;}

    /// set tag
    void tag(uint t) {itag = t;}

    /// query tag
    uint tag() const {return itag;}

    /// create cap on component 'body'
    MeshComponentPtr create(MeshComponentPtr main, side_t side);

    /// adapt cap to current main body geometry
    void adapt(MeshComponentPtr main, side_t side);

    /// access component of the current cap surface
    const MeshComponentPtr & component() const {
      return cap;
    }

    /// access current cap surface itself
    const SurfacePtr & surface() const {
      assert(cap);
      return cap->surface();
    }

    /// generate xml representation
    XmlElement toXml() const;

    /// recover from xml representation
    void fromXml(const XmlElement & xe);

  private:

    /// cap surface geometry
    MeshComponentPtr cap;

    /// height parameter
    Real fheight;

    /// shape identifier
    EndCap::Shape shape;

    /// which side of main is closed by this cap?
    side_t mainside;

    /// tag set after mesh generation
    uint itag;

    /// present at all?
    bool present;
};

#endif // ENDCAP_H
