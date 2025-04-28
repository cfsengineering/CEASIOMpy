
/* Copyright (C) 2017 David Eller <david@larosterna.com>
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
 
#ifndef SURF_POLYSPLINECURVE_H
#define SURF_POLYSPLINECURVE_H

#include <genua/splinebasis.h>
#include "abstractcurve.h"

class StepFile;
class StepEntity;
class StepBSplineCurveWithKnots;
class IgesFile;
struct IgesDirEntry;

/** Polynomial spline curve.

  PolySplineCurve is a non-uniform polynomial (non-rational) spline (NUBS)
  curve as represented by IGES entity 126 or the STEP object
  BSplineCurveWithKnots.

  \ingroup geometry
  \sa IgesSplineCurve, StepBSplineCurveWithKnots, AbstractCurve, Curve
*/
class PolySplineCurve : public AbstractCurve
{
public:

  /// create empty spline curve
  PolySplineCurve(const std::string & s = "")
    : AbstractCurve(s), kfront(0.0), kback(1.0), tstart(0.0), tend(1.0) {}

  /// create a polyline (spline curve with order 1), return parameter vector
  Vector createPolyline(const PointList3d &pts);

  /// create a polyline (spline curve with order 1) for existing vector u
  void createPolyline(const Vector &upar, const PointList3d &pts);

  /// curve basis
  const SplineBasis &basis() const {return ub;}

  /// evaluation interface
  Vct3 eval(Real u) const;

  /// derive at (u,v)
  Vct3 derive(Real u, uint du) const;

  /// compute point and first derivative in one sweep
  void tgline(Real t, Vct3 & c, Vct3 & dc) const;

  /// coordinate transformation
  void apply();

  /// discretization
  void initGrid(Vector &t) const;

  /// XML output
  XmlElement toXml(bool share=false) const;

  /// XML input
  void fromXml(const XmlElement & xe);

  /// extract from STEP entity id
  bool fromStep(const StepFile & file, const StepBSplineCurveWithKnots *ep);

  /// extract from IGES entity 126
  bool fromIges(const IgesFile & file, const IgesDirEntry & entry);

  /// append to IGES file and return the directory entry index, if implemented
  int toIges(IgesFile & file, int tfi = 0) const;

  /// write NC blocks, return number of blocks written
  size_t writeGCode(std::ostream &os) const;

  /// generate a clone
  PolySplineCurve *clone() const;

protected:

  /// remap parameter value
  Real tmap(Real tx) const {return tstart + tx*(tend - tstart);}

protected:

  /// spline basis
  SplineBasis ub;

  /// control point list
  PointList<3> cp;

  /// original knot value range (defined by IGES import)
  Real kfront, kback;

  /// define knot region mapped by [0,1]
  Real tstart, tend;
};

#endif // POLYSPLINECURVE_H
