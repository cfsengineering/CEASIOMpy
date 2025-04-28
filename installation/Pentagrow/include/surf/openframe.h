
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

#ifndef SURF_OPENFRAME_H
#define SURF_OPENFRAME_H

#include "curve.h"

/** Open spline curve.
 *
 * The simplest cross-section object: a plain, rational cubic spline without
 * any continuity conditions at the end points.
 *
 * \ingroup geometry
 */
class OpenFrame : public Curve
{
public:

  /// initialize with name
  explicit OpenFrame(const std::string & s = "") : Curve(s) {}

  /// interpolate points
  Vector init(const PointList<3> & pts);

  /// xml representation stores interpolation points
  virtual XmlElement toXml(bool share = false) const;

  /// construct from xml definition
  virtual void fromXml(const XmlElement & xe);

  /// generate a clone
  virtual OpenFrame *clone() const;

private:

  /// interpolation points
  PointList<3> ipp;
};

typedef boost::shared_ptr<OpenFrame> OpenFramePtr;

#endif

