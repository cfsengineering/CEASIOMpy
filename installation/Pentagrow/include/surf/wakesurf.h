
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
 
#ifndef SURF_WAKESURF_H
#define SURF_WAKESURF_H

#include <boost/shared_ptr.hpp>
#include <genua/splinebasis.h>
#include "surface.h"
#include "curve.h"

class TriMesh;

/** Wake surface attached to wing trailing edge.

  WakeSurf is used to make a continuous wake surface available for
  interactive modelling in sumo. The wake surface is created to match the
  wing trailing edge geometrically, but may be parameterized differently.

  \ingroup geometry
  \sa Surface
*/
class WakeSurf : public Surface
{
public:

  enum ShapeFlag { Plain, Bump, Interpolate };

  /// create undefined surface
  WakeSurf(const std::string & s = "") : Surface(s),
    fwdScale(1.0), rearScale(1.0),
    bumpHeight(0.0), bumpWidth(0.0), bumpPos(0.5), shapeFlag(Plain) {}

  /// define tangent scale factors
  void defineTangent(const Vct3 & farTg, Real fscale=1.0, Real rscale=1.0) {
    farTangent = farTg;
    fwdScale = fscale;
    rearScale = rscale;
  }

  /// define central bump dimensions
  void defineBump(Real height, Real width, Real vpos = 0.5) {
    bumpHeight = height;
    bumpWidth = width;
    bumpPos = vpos;
    shapeFlag = Bump;
  }

  /// set point to interpolate instead of plain bump
  void interpolateBump(Real vpos, const Vct3 & p) {
    bumpPos = vpos;
    bumpWidth = - std::fabs(bumpWidth);
    bumpPoint = p;
    shapeFlag = Interpolate;
  }

  /// create wake geometry from wing surface
  void init(SurfacePtr wng);

  /// access farfield tangent
  const Vct3 & farfieldTangent() const {return farTangent;}

  /// evaluate spline surface
  Vct3 eval(Real u, Real v) const {
     assert(wakeGeo);
    return wakeGeo->eval(u,v);
  }

  /// derive spline surface
  Vct3 derive(Real u, Real v, uint ku, uint kv) const {
     assert(wakeGeo);
    return wakeGeo->derive(u, v, ku, kv);
  }

  /// compute surface point and tangent derivatives
  void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const {
    assert(wakeGeo);
    wakeGeo->plane(u, v, S, Su, Sv);
  }

  /// coordinate transformation
  void apply() {
    wakeGeo->apply();
  }

  /// access parent wing surface
  SurfacePtr parentWing() const {return wing;}

  /// convert spanwise parametrization
  void paramap(const Vector & vwing, Vector & vwake, Real tol=1e-6) const;

  /// XML output
  XmlElement toXml(bool share=false) const;

  /// XML input
  void fromXml(const XmlElement & xe);

  /// generate clone
  WakeSurf *clone() const {return new WakeSurf(*this);}

  /// create initial grid for meshing and visualization
  void initGridPattern(Vector &up, Vector &vp) const {
    assert(wakeGeo);
    wakeGeo->initGridPattern(up, vp);
  }

private:

  /// generate a streamwise curve at spanwise location v
  CurvePtr createStreamCurve(Real v, Real zShift,
                             Real fScale = 1.0, Real rScale = 1.0) const;

  /// streamwise curve on wake with zero curvature at downstream end
  CurvePtr createStreamCurveZC(Real v) const;

  /// streamwise curve on wake which passes through an interpolation point
  CurvePtr createStreamCurve(Real v, const Vct3 & Pip) const;

  /// generate a wake surface segment between v1 and v2
  SurfacePtr createSegment(const Vector & vbreak, uint iv1, uint iv2) const;

  /// streamwise curve blending
  CurvePtr blendCurve(const AbstractCurve & ca,
                      const AbstractCurve & cb, Real t, uint np=16) const;

  /// smoothly varying spanwise bump function
  Real bumpFactor(Real v) const {
    Real s = (v - bumpPos) / fabs(bumpWidth);
    return (fabs(s) < 1) ? sq(1.0 - sq(s)) : 0.0;
  }

private:

  /// parent wing surface
  SurfacePtr wing;

  /// geometry of the full wake surface
  SurfacePtr wakeGeo;

  /// geometry parameter : farfield tangent
  Vct3 farTangent;

  /// spanwise break points used in surface construction
  Vector breakPoints;

  /// tangent scaling factors
  Real fwdScale, rearScale;

  /// bump dimensions
  Real bumpHeight, bumpWidth, bumpPos;

  /// interpolated point
  Vct3 bumpPoint;

  /// indicate which wake shape pattern to use
  ShapeFlag shapeFlag;
};

typedef boost::shared_ptr<WakeSurf> WakeSurfPtr;

#endif // WAKESURFACE_H
