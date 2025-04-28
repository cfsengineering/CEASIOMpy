
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
 
#ifndef SURF_ABSTRACTUVCURVE_H
#define SURF_ABSTRACTUVCURVE_H

#include "forward.h"
#include "abstractcurve.h"

/** Curve in (u,v) domain of parametric surface.
 *
 * This is an abstract interface used to describe a curve defined in the
 * (u,v) parameter space of a surface. Evaluating the curve for a given curve
 * parameter t yields a set of surface parameter values (u,v) from uveval(t),
 * for which the surface is then evaluated to yield a (x,y,z) point in 3D space.
 *
 * \ingroup geometry
 * \sa UvSplineCurve, UvPolyLine, UvCubicCurve, TopoEdge
 */
class AbstractUvCurve : public AbstractCurve
{
public:

  /// initialize with surface
  AbstractUvCurve(SurfacePtr psf = SurfacePtr())
    : AbstractCurve(), m_psf(psf) {}

  /// access surface on which this curve lies
  SurfacePtr surface() const {return m_psf;}

  /// evaluate spline curve
  virtual Vct3 eval(Real t) const;

  /// compute kth derivative
  virtual Vct3 derive(Real t, uint k) const;

  /// compute point and first derivative in one sweep
  virtual void tgline(Real t, Vct3 &c, Vct3 &dc) const;

  /// apply hard transformation (default implementation does nothing)
  virtual void apply();

  /// reverse evaluation direction, must be implemented
  virtual void reverse() = 0;

  /// split curve at t, create low and high curve
  virtual AbstractUvCurvePair split(Real t) const = 0;

  /// evaluate curve in (u,v) space
  virtual Vct2 uveval(Real t) const = 0;

  /// evaluate derivative in (u,v) space
  virtual Vct2 uvderive(Real t, uint k) const = 0;

  /// efficient evaluation of point and first derivative
  virtual void uvtgline(Real t, Vct2 &q, Vct2 &dq) const;

  /// discretized based on simple criteria
  virtual uint discretize(const DcMeshCritBase &mcrit, Vector &t) const;

protected:

  /// surface on which curve is defined
  SurfacePtr m_psf;
};

#endif // ABSTRACTUVCURVE_H
