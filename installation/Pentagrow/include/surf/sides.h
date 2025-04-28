
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
 
#ifndef SURF_SIDES_H
#define SURF_SIDES_H

#include <genua/forward.h>
#include <genua/strutils.h>

typedef enum {west=0, north=1, east=2, south=3, none} side_t;

// problem : will only return one side for corner points
inline side_t whichside(Real u, Real v, Real tol = gmepsilon)
{
  if (u <= tol)
    return west;
  else if (u >= 1.0-tol)
    return east;
  else if (v <= tol)
    return south;
  else if (v >= 1.0-tol)
    return north;
  else
    return none;
}

inline side_t whichside(const Vct2 & p, Real tol = gmepsilon)
{
  return whichside(p[0], p[1], tol);
}

inline bool onside(Real u, Real v, side_t s, Real tol = gmepsilon)
{
  if (s == west and u <= tol)
    return true;
  else if (s == east and u >= 1.-tol)
    return true;
  else if (s == south and v <= tol)
    return true;
  else if (s == north and v >= 1.-tol)
    return true;
  else if (s == none and u > tol and u < 1.-tol and v > tol and v < 1.-tol)
    return true;
  else
    return false;
}

inline bool onside(const Vct2 & p, side_t s, Real tol = gmepsilon)
{
  return onside(p[0], p[1], s, tol);
}

inline void force2side(side_t s, Vct2 & p)
{
  switch (s) {
  case west:
    p[0] = 0.0;
    break;
  case north:
    p[1] = 1.0;
    break;
  case east:
    p[0] = 1.0;
    break;
  case south:
    p[1] = 0.0;
    break;
  case none:
  default:
    return;
  }
}

inline side_t forceNearBnd(Real maxdist, Vct2 & p)
{
  // compute distances from boundaries
  Real dst[4];
  dst[0] = std::max(0.0, p[0]);        // west
  dst[1] = std::max(0.0, 1.0-p[1]);    // north
  dst[2] = std::max(0.0, 1.0-p[0]);    // east
  dst[3] = std::max(0.0, p[1]);        // south
  int imin = std::distance(dst, std::min_element(dst, dst+4));
  if (dst[imin] > maxdist)
    return none;
  else {
    side_t s = side_t(imin);
    force2side(s, p);
    return s;
  }
}

inline side_t oppside(side_t s)
{
  switch (s) {
  case west:
    return east;
  case north:
    return south;
  case east:
    return west;
  case south:
    return north;
  case none:
    return none;
  }
  return none;
}

inline void fromString(const std::string & str, side_t & s)
{
  std::string lstr = toLower(str);
  if (lstr == "west")
    s = west;
  else if (lstr == "east")
    s = east;
  else if (lstr == "south")
    s = south;
  else if (lstr == "north")
    s = north;
  else
    s = none;
}

inline std::string str(side_t sd)
{
  switch (sd) {
  case west:
    return "west";
  case south:
    return "south";
  case east:
    return "east";
  case north:
    return "north";
  default:
    return "none";
  }
}

template <int c>
class BndCompare
{
public:
  BndCompare(const PointList<2> & pts) : ppt(pts) {}
  bool operator() (uint a, uint b) const {
    return ppt[a][c] < ppt[b][c];
  }
private:
  const PointList<2> & ppt;
};

/** Sort nodes along all boundaries, ccw order.
  */
class CcwCompare
{
public:
  CcwCompare(const PointList<2> & pts) : ppt(pts) {}
  bool operator() (uint a, uint b) const {
    const Vct2 & pa( ppt[a] );
    const Vct2 & pb( ppt[b] );
    side_t sa = whichside( pa );
    side_t sb = whichside( pb );
    if ( sa != sb ) {
      return sa > sb;
    }
    const int c[4] = {1, 0, 1, 0};
    const Real sgn[4] = {-1.0, -1.0, 1.0, 1.0};
    assert(int(sa) < 4 and int(sb) < 4);
    return sgn[sa]*pa[c[sa]] < sgn[sa]*pb[c[sa]];
  }
private:
  const PointList<2> & ppt;
};

class BoundaryFlag
{
public:

  /// bitmask used to identify boundaries
  enum {None=0, OnLoU = 1, OnHiU = 2, OnLoV = 4, OnHiV = 8};

  /// compute bitmask
  static int eval(const Vct2 & p, Real tol = gmepsilon) {
    int pBoundary = BoundaryFlag::None;
    if ( p[0] <= tol )
      pBoundary |= OnLoU;
    else if (p[0] >= 1.0-tol)
      pBoundary |= OnHiU;
    if ( p[1] <= tol )
      pBoundary |= OnLoV;
    else if (p[1] >= 1.0-tol)
      pBoundary |= OnHiV;
    return pBoundary;
  }

  /// determine whether two points are on the same boundary
  static bool share(int a, int b) {
    if (a == 0 and b != 0)
      return false;
    if ( (a & OnLoU) and (b & OnLoU) )
      return true;
    else if ( (a & OnHiU) and (b & OnHiU) )
      return true;
    if ( (a & OnLoV) and (b & OnLoV) )
      return true;
    else if ( (a & OnHiV) and (b & OnHiV) )
      return true;
    return false;
  }

  /// determine whether a is on a u boundary
  static bool onU(int a) {
    return (a & OnLoU) or (a & OnHiU);
  }

  /// determine whether a is on a v boundary
  static bool onV(int a) {
    return (a & OnLoV) or (a & OnHiV);
  }
};

#endif
