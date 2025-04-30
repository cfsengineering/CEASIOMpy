
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
 
#ifndef SURF_UVPOLYLINE_H
#define SURF_UVPOLYLINE_H

#include "abstractuvcurve.h"
#include "uvsplinecurve.h"
#include <genua/xmlelement.h>

/** Straight-segment line in parameter space.
 *
 * The simplest possible curve in parameter space is a polyline, that is,
 * a sequence of straight-line segments in (u,v) space.
 *
 * \ingroup geometry
 * \sa AbstractUvCurve, UvSplineCurve
 */
class UvPolyline : public UvSplineCurve<1>
{
public:

  /// initialize with surface
  explicit UvPolyline(SurfacePtr psf) : UvSplineCurve<1>(psf) {}

  /// initialize with surface and point set
  UvPolyline(SurfacePtr psf, const PointList<2> &pts);

  /// initialize with surface and point set
  UvPolyline(SurfacePtr psf, const Vector &u, const PointList<2> &pts);

  /// initialize with surface and two points
  UvPolyline(SurfacePtr psf, const Vct2 &a, const Vct2 &b);

  /// clone object
  UvPolyline *clone() const;

  /// generate simplest possible parameter-space curve
  void interpolate(const Vct2 &a, const Vct2 &b);

  /// forward to help compiler
  const Vector &interpolate(const PointList<2> &pts) {
    return UvSplineCurve<1>::interpolate(pts);
  }

  /// generate a boundary curve
  const Vector& uBoundary(Real u, const Vector &v, bool flip=false);

  /// generate a boundary curve
  const Vector &vBoundary(Real v, const Vector &u, bool flip=false);

  /// split curve at t
  AbstractUvCurvePair split(Real t) const;

  /// generate xml representation
  XmlElement toXml(bool share) const;

  /// recover from xml representation
  void fromXml(const XmlElement &xe);
};

#endif // UVPOLYLINE_H
