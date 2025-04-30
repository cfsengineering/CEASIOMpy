
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
 

#ifndef SURF_LINECURVE_H
#define SURF_LINECURVE_H

#include "abstractcurve.h"

/** Straight line segment with AbstractCurve interface.

  LineCurve is a curve object representing a simple straight line,
  but conforming to the AbstractCurve interface so that it can be used in
  composite curves. It is almost exclusively needed to support the use
  of straight line segments as trimming curves in TrimmedSurface objects
  recovered from IGES file.

  \ingroup geometry
  \sa IgesLineEntity, CompositeCurve
  */
class LineCurve : public AbstractCurve
{
public:

  /// create undefined curve
  LineCurve(const std::string & s = std::string()) : AbstractCurve(s) {}

  /// create a clone
  virtual LineCurve *clone() const {return (new LineCurve(*this));}

  /// evaluate spline curve
  Vct3 eval(Real t) const {
    assert(t >= 0 and t <= 1);
    return (1.0-t)*pStart + t*pEnd;
  }

  /// compute kth derivative
  Vct3 derive(Real t, uint k) const {
    if (k == 0)
      return eval(t);
    else if (k == 1)
      return pEnd - pStart;
    else
      return Vct3();
  }

  /// apply hard transformation
  void apply();

  /// compute point and first derivative in one sweep
  void tgline(Real t, Vct3 & c, Vct3 & dc) const {
    c = eval(t);
    dc = pEnd - pStart;
  }

  /// compute curvature at t
  Real curvature(Real) const {return 0.0;}

  /// generate a reasonable discretization
  void initGrid(Vector & t) const;

  /// XML output
  virtual XmlElement toXml(bool share = false) const;

  /// XML input
  virtual void fromXml(const XmlElement & xe);

  /// write curve to iges file
  virtual int toIges(IgesFile & file, int tfi = 0) const;

  /// extract curve from iges file
  virtual bool fromIges(const IgesFile & file, const IgesDirEntry & dir);

private:

  /// start point
  Vct3 pStart;

  /// end point
  Vct3 pEnd;
};

#endif // LINECURVE_H
