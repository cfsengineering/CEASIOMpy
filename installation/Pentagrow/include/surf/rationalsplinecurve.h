
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
 
#ifndef SURF_RATIONALSPLINECURVE_H
#define SURF_RATIONALSPLINECURVE_H

#include <genua/splinebasis.h>
#include "abstractcurve.h"

/** NURBS curve.
 *
 * This is the most general representation of NURBS curves, with support for
 * runtime variable order and rational forms (i.e. non-unit weight values). This
 * flexibility also means that the evaluation and derivation is more expensive
 * than for simpler fixed-order objects such as Curve.
 *
 * \ingroup geometry
 * \sa SplineBasis, PolySplineCurve, AbstractCurve
 */
class RationalSplineCurve : public AbstractCurve
{
public:

  /// create empty spline curve
  RationalSplineCurve(const std::string & s = "")
    : AbstractCurve(s), kfront(0.0), kback(1.0), tstart(0.0), tend(1.0) {}

  /// create unit circle in xy-plane
  void createCircle();

  /// create an exact circle from center, plane normal and radius
  void createCircle(const Vct3 & ctr, const Vct3 & pnrm, Real radius);

  /// evaluation interface
  Vct3 eval(Real u) const;

  /// derive at (u,v)
  Vct3 derive(Real u, uint du) const;

  /// optimization for common case
  void tgline(Real t, Vct3 & c, Vct3 & dc) const;

  /// coordinate transformation
  void apply();

  /// discretization
  void initGrid(Vector &t) const;

  /// XML output
  XmlElement toXml(bool share=false) const;

  /// XML input
  void fromXml(const XmlElement & xe);

  /// extract from IGES entity 128
  bool fromIges(const IgesFile & file, const IgesDirEntry & entry);

  /// append to IGES file and return the directory entry index, if implemented
  int toIges(IgesFile & file, int tfi = 0) const;

  /// generate a clone
  RationalSplineCurve *clone() const;

protected:

  /// remap parameter value
  Real tmap(Real tx) const {return tstart + tx*(tend - tstart);}

private:

  /// spline basis
  SplineBasis ub;

  /// control point list, homogeneous coordinates (x,y,z,w)
  PointList<4> cp;

  /// original knot value range (defined by IGES import)
  Real kfront, kback;

  /// define knot region mapped by [0,1]
  Real tstart, tend;
};

#endif // RATIONALSPLINECURVE_H
