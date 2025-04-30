
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
 
#ifndef SURF_COMPOSITECURVE_H
#define SURF_COMPOSITECURVE_H

#include "abstractcurve.h"

/** Composite curve.

  A curve which is composed of multiple segments that are simply
  concatenated. This class makes no guarantees that the curve segments
  which the user supplied are actually geometrically continuous in any
  way, it simply maps a common arclength parameter value to a set of
  curve segments.

  \ingroup geometry
  \sa AbstractCurve
  */
class CompositeCurve : public AbstractCurve
{
public:

  /// create undefined curve object
  CompositeCurve(const std::string & s = "") : AbstractCurve(s) {}

  /// initialize with a set of curves
  const Vector & init(const AbstractCurveArray & ca);

  /// create a clone
  virtual CompositeCurve *clone() const;

  /// evaluate spline curve
  virtual Vct3 eval(Real t) const;

  /// compute kth derivative
  virtual Vct3 derive(Real t, uint k) const;

  /// apply hard transformation
  virtual void apply();

  /// compute point and first derivative in one sweep
  virtual void tgline(Real t, Vct3 & c, Vct3 & dc) const;

  /// disctretization
  virtual void initGrid(Vector &t) const;

  /// number of curve segments
  uint nSegments() const {return m_curves.size();}

  /// low-level access to segment curves
  AbstractCurvePtr curveSegment(uint k) const {
    assert(k < m_curves.size());
    return m_curves[k];
  }

  /// XML output
  virtual XmlElement toXml(bool share = false) const;

  /// XML input
  virtual void fromXml(const XmlElement & xe);

  /// write curve to iges file
  virtual int toIges(IgesFile & file, int tfi = 0) const;

  /// extract curve from iges file
  virtual bool fromIges(const IgesFile & file, const IgesDirEntry & dir);

  /// keep segment ordering, but flip segments if needed (called by fromIges())
  void flipSegments();

  /// erase curve segments
  void clearSurface() {
    m_curves.clear();
    m_tbreak.clear();
  }

protected:

  /// compute segment for parameter t
  uint segment(Real t, Real & ti) const {
    size_t lb = std::distance(m_tbreak.begin(),
                            std::lower_bound(m_tbreak.begin(),
                                             m_tbreak.end(), t) );
    lb = std::max(size_t(1), std::min(lb, m_tbreak.size()-1) );
    ti = (t - m_tbreak[lb-1]) / (m_tbreak[lb] - m_tbreak[lb-1]);
    ti = clamp(ti, 0.0, 1.0);
    return lb;
  }

  /// establish break points based on arclength parametrization
  void breakPoints();

protected:

  /// constituent curves
  AbstractCurveArray m_curves;

  /// parameter space breakpoints
  Vector m_tbreak;
};

#endif // COMPOSITECURVE_H
