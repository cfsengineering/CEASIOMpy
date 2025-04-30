#ifndef SURF_BEZIERSEGMENT_H
#define SURF_BEZIERSEGMENT_H

#include "abstractcurve.h"

/** Single cubic Bezier segment.
 *
 * Object representing a single cubic Bezier segment. This is not particularly
 * useful in itself, but will be as a building block for other curves.
 *
 * \ingroup geometry
 */
class BezierSegment : public AbstractCurve
{
public:

  /// undefined segment
  explicit BezierSegment(const std::string &s = "") : AbstractCurve(s) {}

  /// segment defined by two points and two tangents
  explicit BezierSegment(const Vct3 &p0, const Vct3 &t0,
                         const Vct3 &p1, const Vct3 &t1) : AbstractCurve("")
  {
    byTangents(p0, t0, p1, t1);
  }

  /// create a clone
  virtual BezierSegment *clone() const;

  /// construct a Bezier segment from points and tangents
  void byTangents(const Vct3 &p0, const Vct3 &t0,
                  const Vct3 &p1, const Vct3 &t1);

  /// access the array of 4 control points
  const Vct3 *controls() const {return m_cp;}

  /// evaluate spline curve
  Vct3 eval(Real t) const {
    return ( 1 - cb(t) ) * m_cp[0]
        +  3*sq(1 - t)*t * m_cp[1]
        +  3*(1-t)*sq(t) * m_cp[2]
        +  cb(t)         * m_cp[3];
  }

  /// compute kth derivative
  Vct3 derive(Real t, uint k) const;

  /// apply hard transformation
  void apply();

protected:

  /// four control points
  Vct3 m_cp[4];
};

#endif // BEZIERSEGMENT_H
