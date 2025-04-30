
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

#ifndef SURF_SLAVEDWAKE_H
#define SURF_SLAVEDWAKE_H

#include "forward.h"
#include "surface.h"

/** A wake surface which autmatically attaches to a parent wing TE
 *
 * Parametrization: v of the wake matches v of the parent surface 1:1,
 * u of the wake increases from 0.0 at the trailing edge to 1 at the
 * downstream end.
 *
 * The simplest possible wake surface is one which is a linear extension
 * of the trailing edge along a constant downstream direction. Aletrnatively,
 * a wake surface can also be constructed from any other surface which is then
 * translated such that the (u=0, v) edge (i.e., the 'western' side) matches
 * the wing trailing edge at u=0 exactly.
 *
 * Note that if the trailing edge is not closed, then the wake will be attached
 * at the u = 0 edge of the wing, which is usually the upper side trailing edge.
 *
 * \ingroup geometry
 * \sa WingPart
 */
class SlavedWake : public Surface
{
public:

  /// undefined wake
  SlavedWake() : Surface() {}

  /// create simple wake surface
  SlavedWake(SurfacePtr parent, const Vct3 &udr)
    : Surface("SlavedWake-"+parent->name()), m_parent(parent), m_udr(udr) {}

  /// create a general wake surface defined by means of the added geometry
  SlavedWake(SurfacePtr parent, SurfacePtr wplus)
    : Surface("SlavedWake-"+parent->name()), m_parent(parent), m_wplus(wplus) {}

  /// virtual destruction
  virtual ~SlavedWake() {}

  /// initialize simple surface from parent surface and direction
  void init(SurfacePtr parent, const Vct3 &udr) {
    m_parent = parent;
    m_udr = udr;
    m_wplus.reset();
  }

  /// initialize complex wake surface
  void init(SurfacePtr parent, SurfacePtr wplus) {
    m_parent = parent;
    m_wplus = wplus;
  }

  /// construct a linear/cubic-Bezier-based wake surface
  void initRuledBezier(SurfacePtr parent,
                       const Vct3 &edgeDistance,
                       const Vct3 &farTangent,
                       Real compression = 0.2);

  /// construct a wake by defining two end curves which yield (0,0,0) at the TE
  void initRuled(SurfacePtr parent, CurvePtr c0, CurvePtr c1);

  /** Compute cubic wake guide.
    *
    * This guide curve starts on the surface at p = S(0.0, v) with the mean TE
    * tangent and ends in a point at a distance of edgeDistance from the
    * starting location. At the end point, the tangent is given by farTangent.
    */
  static CurvePtr cubicGuide(SurfacePtr parent, Real v,
                             const Vct3 &edgeDistance,
                             const Vct3 &farTangent,
                             Real compression = 0.2);

  /** Compute wake guide curve for tubular body.
   *
   * Returns a spline curve running along the centerline of the body between
   * two intersection points and following the body in the direction of
   * increasing v at constant u.
   */
  static CurvePtr guideCurve(SurfacePtr body, const Vct2 &uvi, const Vct3 &panchor,
                             const Vct3 &edgeDistance,
                             const Vct3 &farTangent, Real vend = 1.0);

  /// find approximate intersection of wing TE and body
  static Vct3 findIntersection(SurfacePtr wing, SurfacePtr body,
                               Real vlo = 0.0, Real vhi = 1.0);

  /// evaluate wake
  Vct3 eval(Real u, Real v) const {
    if (m_wplus == nullptr)
      return m_parent->eval(0.0, v) + u*m_udr;
    else {
      Vct3 shift = m_parent->eval(0.0, v) - m_wplus->eval(0.0, v);
      return shift + m_wplus->eval(u, v);
    }
  }

  /// derivatives
  Vct3 derive(Real u, Real v, uint du, uint dv) const;

  /// tangent plane
  void plane(Real u, Real v, Vct3 &S, Vct3 &Su, Vct3 &Sv) const;

  /// normal direction
  Vct3 normal(Real, Real v) const;

  /// coordinate transformation disabled
  void apply();

  /// clone object
  SlavedWake *clone() const {return new SlavedWake(*this);}

  /// XML import/export disabled
  XmlElement toXml(bool share) const;

  /// XML import/export disabled
  void fromXml(const XmlElement &xe);

  /// dump wake surface to iges when defined
  int toIges(IgesFile & igfile, int tfi = 0) const;

private:

  /// parent wing segment where wake is attached
  SurfacePtr m_parent;

  /// optionally, a more complex surface which is *added* to the parent's TE
  SurfacePtr m_wplus;

  /// default wake is just a straight segment
  Vct3 m_udr;
};

#endif // SLAVEDWAKE_H
