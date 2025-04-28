
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
 
#ifndef SURF_CURVE_H
#define SURF_CURVE_H

#include "forward.h"
#include "abstractcurve.h"
#include <string>
#include <boost/shared_ptr.hpp>
#include <genua/point.h>
#include <genua/splinebasis.h>
#include <genua/trafo.h>

/** Cubic section curve.

  The cubic b-spline curve is the default curve representation used to model
  cross-sections and airfoils in libsurf. Child classes can be used in the
  assembly of surface objects which are very efficiently evaluated.

  \ingroup geometry
  \sa LinearSurf, SkinSurface
  */
class Curve : public AbstractCurve
{
public:

  /// default intialization
  explicit Curve(const std::string & name = "NoNameCurve");

  /// virtual destructor
  virtual ~Curve() {}

  /// initialize curve from knots and control points
  void initSpline(const Vector & knots, const PointList<3> & ctp);

  /// create curve passing through points a
  void interpolate(const PointList<3> &a);

  /// create curve passing through points a; makes parameter vector accessible
  void interpolate(const PointList<3> & a, Vector & u);

  /// create a cubic curve passing through points pts with tangents tng
  void interpolate(const PointList<3> &pts, const PointList<3> & tng,
                   Vector & u);

  /// approximate while passing through first/last points
  void approximate(const PointList<3> & pts, const Vector & uip);

  /// create a single cubic Bezier segment from four Bezier points
  void bezier(const Vct3 bp[]);

  /// create a single cubic Bezier segment from points and slopes
  void bezier(const Vct3 &p0, const Vct3 &t0,
              const Vct3 &p1, const Vct3 &t1);

  /// generate a closed curve using Akima interpolation
  void akima(const PointList<3> &pts);

  /// evaluate spline curve
  Vct3 eval(Real t) const;

  /// compute kth derivative
  Vct3 derive(Real t, uint k) const;

  /// compute point and first derivative in one sweep
  void tgline(Real t, Vct3 & c, Vct3 & dc) const;

  /// compute curvature at t
  Real curvature(Real t) const;

  /// default discretization
  void initGrid(Vector &t) const;

  /// compute line center of control points
  Vct3 center() const;

  /// access control points
  const PointList<3> & controls() const {return cp;}

  /// access control points
  PointList<3> & controls() {return cp;}

  /// access knot vector
  const Vector & knots() const {return bas.getKnots();}

  /// adapt to different knot vector
  void adapt(const Vector & nk);

  /// reverse parametrization direction
  void reverse();

  /// apply transformation to control points
  void apply();

  /// apply transformation as contained in Xml representation
  void applyFromXml(const XmlElement & xt);

  /// create xml representation for transformation sequence
  XmlElement trafoToXml() const;

  /// XML output
  virtual XmlElement toXml(bool share = false) const;

  /// XML input
  virtual void fromXml(const XmlElement & xe);

  /// create a clone
  virtual Curve *clone() const;

  /// write curve to iges file
  virtual int toIges(IgesFile & file, int tfi = 0) const;

  /// extract curve from iges file
  virtual bool fromIges(const IgesFile & file, const IgesDirEntry & dir);

  /// static factory function: create a CurvePtr from XML
  static CurvePtr createFromXml(const XmlElement & xe);

  /** Parametrization of curve sets.

    Compute the arc-length parametrization of a set of curves. Returns the
    number of curves which end up on the same position as their predecessor. */
  static uint arclenParamet(const CurvePtrArray & cpa, Vector & vp);

protected:

  /// DeBoor basis
  SplineBasis bas;

  /// control points
  PointList<3> cp;

  /// stores transformation sequence
  Mtx44 tfs;
};

inline Curve *new_clone(const Curve & c) 
{
  return c.clone();
}




#endif

