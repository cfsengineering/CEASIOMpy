
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

#include "dcplanegeometry.h"
#include "dcface.h"
#include "delaunaycore.h"
#include <predicates/predicates.h>

#include <genua/dbprint.h>
#include <iostream>
#include <queue>

using namespace std;

// ------------------- local scope -------------------------------------------

class PolarCompare
{
public:
  PolarCompare(const PointList<2> & v, uint s, uint t) : vtx(v)
  {
    ps = vtx[s];
    xdir = (vtx[t] - ps).normalized();
    ydir[0] = +xdir[1];
    ydir[1] = -xdir[0];
  }

  bool operator() (uint a, uint b) const {
    Vct2 ra(vtx[a] - ps);
    Real ax = dot(ra, xdir);
    Real ay = dot(ra, ydir);
    int qa = quadrant(ax, ay);

    Vct2 rb(vtx[b] - ps);
    Real bx = dot(rb, xdir);
    Real by = dot(rb, ydir);
    int qb = quadrant(ax, ay);
    if (qa < qb)
      return true;
    else if (qa > qb)
      return false;
    else // same quadrant
      return ay*bx < ax*by;
  }

private:

  int quadrant(Real x, Real y) const {
    if (x >= 0 and y >= 0)
      return 0;
    else if (x < 0 and y >= 0)
      return 1;
    else if (x < 0 and y < 0)
      return 2;
    else
      return 3;
  }

private:
  Vct2 ps, xdir, ydir;
  const PointList<2> & vtx;
};

// ------------------- DcPlaneGeometry ---------------------------------------

void DcPlaneGeometry::sortPolar(const DcEdge *pe, Indices &c) const
{
  PolarCompare cmp(m_st, pe->source(), pe->target());
  std::sort(c.begin(), c.end(), cmp);
}

Vct2 DcPlaneGeometry::circumCenter(const PointList<2> &pts, const uint *vi)
{
  const Vct2 & q1(pts[vi[0]]);
  const Vct2 & q2(pts[vi[1]]);
  const Vct2 & q3(pts[vi[2]]);

  // compute edge-normal directions
  Vct2 e1( q2-q1 );
  Vct2 e2( q3-q2 );
  Vct2 n1, n2;
  if ( std::fabs(e1[1]) > std::fabs(e1[0]) ) {
    n1[0] = 1.0;
    n1[1] = -e1[0]/e1[1];
  } else {
    assert(e1[0] != 0.0);
    n1[0] = -e1[1]/e1[0];
    n1[1] = 1.0;
  }
  if ( std::fabs(e2[1]) > std::fabs(e2[0]) ) {
    n2[0] = 1.0;
    n2[1] = -e2[0]/e2[1];
  } else {
    assert(e2[0] != 0.0);
    n2[0] = -e2[1]/e2[0];
    n2[1] = 1.0;
  }

  // intersect lines through edge midpoints
  Vct2 m1( 0.5*(q1+q2) );
  Vct2 m2( 0.5*(q2+q3) );

  Real a11 = n1[0];
  Real a21 = n1[1];
  Real a12 = -n2[0];
  Real a22 = -n2[1];
  Real det = a11*a22 - a12*a21;
  if (det != 0.0) {

    Real r1 = m2[0] - m1[0];
    Real r2 = m2[1] - m1[1];

    // line through m1 is m1 + s*n1
    Real s = (r1*a22 - r2*a12) / det;
    return m1 + s*n1;

  } else {

    // det == 0 means e1 || e2, triangle with two parallel edges
    return 0.5*(m1 + m2);

  }
}

