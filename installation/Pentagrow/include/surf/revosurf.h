
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
 
#ifndef SURF_REVOSURF_H
#define SURF_REVOSURF_H

#include "surface.h"
#include "curve.h"

/** Surface of revolution.

  This definition of a surface of revolution is modeled after the
  IGES entity 120.

  \ingroup geometry
  \sa Surface, LinearSurf
  */
class RevoSurf : public Surface
{
public:

  /// create undefined surface
  RevoSurf(const std::string & s = "RevoSurf")
    : Surface(s), startAngle(0.0), termAngle(2*PI) {}

  /// evaluate surface
  Vct3 eval(Real u, Real v) const;

  /// evaluate derivatives
  Vct3 derive(Real u, Real v, uint du, uint dv) const;

  /// evaluate linear approximation
  void plane(Real u, Real v, Vct3 &S, Vct3 &Su, Vct3 &Sv) const;

  /// append to IGES file and return the directory entry index, if implemented
  int toIges(IgesFile & file, int tfi = 0) const;

  /// extract surface of revolution from IGES file
  bool fromIges(const IgesFile & file, const IgesDirEntry & dir);

  /// generate a clone
  RevoSurf *clone() const;

  /// create XML representation
  XmlElement toXml(bool share) const;

  /// recover from XML representation
  void fromXml(const XmlElement &xe);

  /// apply transformation
  void apply();

protected:

  /// reconstruct 90 degree rotation from axis
  void buildRotation();

protected:

  /// two points define axis of revolution
  Vct3 pax1, pax2;

  /// generatrix curve
  CurvePtr genCurve;

  /// start and end angles
  Real startAngle, termAngle;

  /// helper : rotation by 90 degree about axis
  Mtx33 rot90;
};

#endif // REVOSURF_H
