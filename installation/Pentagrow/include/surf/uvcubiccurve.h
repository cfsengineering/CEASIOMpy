
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
 
#ifndef SURF_UVCUBICCURVE_H
#define SURF_UVCUBICCURVE_H

#include "uvsplinecurve.h"
#include <genua/xmlelement.h>

/** Cubic spline curve in parameter space.
 *
 * \ingroup geometry
 * \sa AbstractUvCurve, UvSplineCurve
 */
class UvCubicCurve : public UvSplineCurve<3>
{
public:

  /// initialize with surface
  explicit UvCubicCurve(SurfacePtr psf = SurfacePtr()) : UvSplineCurve<3>(psf) {}

  /// forward to help compiler
  void interpolate(const PointList<2> &pts) {
    UvSplineCurve<3>::interpolate(pts);
  }

  /// create cloned object
  UvCubicCurve *clone() const;

  /// split curve at t
  AbstractUvCurvePair split(Real t) const;

  /// generate xml representation
  XmlElement toXml(bool share) const;

  /// recover from xml representation
  void fromXml(const XmlElement &xe);
};

#endif // UVCUBICCURVE_H
