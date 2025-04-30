
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


#ifndef SURF_SRFPROJECTOR_H
#define SURF_SRFPROJECTOR_H

#include "forward.h"
#include <genua/defines.h>
#include <genua/svector.h>

class Surface;

/** Computes projection of a point onto a surface.

  *Note:* In rare cases, the Gauss-Newton method will report failure to converge
  when the surface normal at the computed projection point is parallel to the
  distance between projection and point. This should have resulted in termination
  as it is the (1st order) convergence criterion.

  \ingroup geometry
  \sa Surface
  */
class SrfProjector
{
public:

  /// initialize with surface reference
  SrfProjector(const Surface & s, Real tol=1e-6, Real dp=1e-8)
    : srf(s), tolsq(tol*tol), dpsq(dp*dp) {}

  /// return true if projection succeeded in decreasing distance
  bool project(const Vct3 & pt, Vct2 & q) const {
    assert(q[0] >= 0.0 and q[0] <= 1.0);
    assert(q[1] >= 0.0 and q[1] <= 1.0);
    if (gaussNewton(pt,q))
      return true;
    else if (coordSearch(pt,q))
      return true;
    else
      return compassSearch(pt,q);
  }

  /// iteratively find intersection of surface with curve
  bool intersect(const AbstractCurve &c, Vct2 &q, Real &t) const;

private:

  typedef enum {NONE=0, ULO=1, UHI=2, VLO=4, VHI=8} Constraint;

  /// advance, but not past boundary
  int advance(Vct2 & q, const Vct2 & step) const
  {
    Real u = q[0] + step[0];
    Real v = q[1] + step[1];
    Real t = 1.0;
    int c = SrfProjector::NONE;
    if (u < 0.0) {
      t = q[0] / fabs(step[0]);
      c |= ULO;
    }
    if (u > 1.0) {
      t = std::min(t, fabs(1.0 - q[0])/fabs(step[0]) );
      c |= UHI;
    }
    if (v < 0.0) {
      t = std::min(t, q[1] / fabs(step[1]));
      c |= VLO;
    }
    if (v > 1.0) {
      t = std::min(t, fabs(1.0 - q[1])/fabs(step[1]) );
      c |= VHI;
    }
    q[0] += t*step[0];
    q[1] += t*step[1];

    // handle rounding errors
    q[0] = std::min(1.0, std::max(0.0, q[0]));
    q[1] = std::min(1.0, std::max(0.0, q[1]));

    return c;
  }

  /// Standard Gauss-Newton with backtracking
  bool gaussNewton(const Vct3 & pt, Vct2 & q) const;

  /// compass-search method useful for discontinuous surfaces
  bool compassSearch(const Vct3 & pt, Vct2 & q) const;

  /// alternate coordinate search
  bool coordSearch(const Vct3 & pt, Vct2 & q) const;

  /// optional search to initialize the intersection problem
  Vct3 searchIntersection(int n, const AbstractCurve &c,
                          const Vct3 &lo, const Vct3 &hi) const;

private:

  /// surface to project upon
  const Surface & srf;

  /// convergence criteria
  Real tolsq, dpsq;
};

#endif // SRFPROJECTOR_H
