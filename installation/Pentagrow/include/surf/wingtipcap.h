
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

#ifndef SURF_WINGTIPCAP_H
#define SURF_WINGTIPCAP_H

#include <iosfwd>
#include <genua/point.h>

/** Mesh cap for open wing tips.

  \deprecated

  \ingroup geometry
  */
class WingtipCap
{
public:

  /// default construction (empty)
  WingtipCap() {}

  /// construction with boundary points
  WingtipCap(const PointList<3> & bnd);

  /// construct cylindrical cap
  const PointGrid<3> & makeCap(uint nv, Real rout = 1.0);

  /// output (debugging)
  void writeOogl(std::ostream & os) const;

private:

  /// boundary points
  PointList<3> upper, lower;

  /// rotation axis
  Vct3 ax;

  /// mini-mesh
  PointGrid<3> pg;
};

#endif

