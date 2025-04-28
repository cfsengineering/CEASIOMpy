
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
 
#ifndef GENUA_LINE_H
#define GENUA_LINE_H

#include "smatrix.h"
#include "point.h"

// to hold line intersection information
template <uint N>
struct LnIts
{
  SVector<N> pt;
  Real self, other;
  bool hit;
  bool internal(Real tol = 0) const {
    if (hit and self > -tol and self < 1+tol and other > -tol and other < 1+tol)
      return true;
    else
      return false;
  }
};


/** Line in euclidian space.

  Line is constructed with two points. These points can be modified later
  using the setPoints() method. Parametric evaluation is defined so that
  parameter value 0 yields the first point, parameter 1 the second point.

  Lines are infinite: Parameters t can take any value.
  \[
    {\bf r} = {\bf p}_1 + t ({\bf p}_2 - {\bf p}_1)
  \]

  This class provides methods to find the projection of a point on the
  line (foot()), compute the intersection of lines and determine the
  parameter which belongs to a point lying on the line.

  \ingroup geometry
*/
template <uint N>
class Line
{
  public:

    /// default constructor
    Line() {}

    /// through two points
    template <typename FloatType>
    Line(const SVector<N,FloatType> & a,
         const SVector<N,FloatType> & b) : p1(a), p2(b) {}

    /// set new points
    void setPoints(const SVector<N> & a, const SVector<N> & b)
      {p1 = a; p2 = b;}

    /// returns point on line; t in (-infty, +infty)
    SVector<N> eval(Real t) const
      { return p1 + t*(p2-p1); }

    /// direction vector
    SVector<N> direction() const { return (p2-p1).normalized(); }

    /// true if lines are parallel
    bool isParallel(const Line<N> & ln) const
      {
        SVector<N> d1(p2-p1), d2(ln.p2-ln.p1);
        Real cosphi = dot(d1,d2)/(norm(d1)*norm(d2));
        return fsmall(fabs(cosphi) - 1.0);
      }

    /// returns the perpendicular projection of p on the line
    SVector<N> foot(const SVector<N> & p) const
      {
        SVector<N> d = (p2-p1).normalized();
        return p1 + dot( p-p1, d )*d;
      }

    /// parameter of the projection point
    Real footPar(const SVector<N> & p) const
      { return dot( p-p1, p2-p1 ) / dot(p2-p1, p2-p1); }

    /// calculates the minimum distance of p from line
    Real distance(const SVector<N> & p) const
      { return norm( p-foot(p) ); }

    /// parameters of intersection point
    LnIts<N> intersection(const Line<N> & ln) const
      {
        // minimize distance between lines, call it an intersection
        // if distance < gmepsilon
        LnIts<N> li;

        if (isParallel(ln)) {
          li.hit = false;
          return li;
        }

        SMatrix<2,2> a;
        SVector<2> b;
        SVector<N> r1 = p2-p1;
        SVector<N> r2 = ln.p2 - ln.p1;

        for (uint i=0; i<N; i++) {
          a(0,0) += sq(r1(i));
          a(0,1) += -r1(i)*r2(i);
          a(1,0) += -r1(i)*r2(i);
          a(1,1) += sq(r2(i));
          b(0) += -(p1(i) - ln.p1(i))*r1(i);
          b(1) += (p1(i) - ln.p1(i))*r2(i);
        }

        Real det = a(0,0)*a(1,1) - a(0,1)*a(1,0);
        li.self = (b(0)*a(1,1) - b(1)*a(0,1))/det;
        li.other = (a(0,0)*b(1) - a(1,0)*b(0))/det;

        SVector<N> p,q, d;
        p = eval(li.self);
        q = ln.eval(li.other);
        li.pt = 0.5*(p+q);

        d = p-q;
        if ( dot(d,d) < sq(gmepsilon) )
          li.hit = true;
        else
          li.hit = false;

        return li;
      }

  private:

    /// direction of positive parameters is p1->p2
    SVector<N> p1, p2;

};


/** Line segment.
  */
template <uint N>
class Segment
{
  public:

    /// construction with points
    Segment(const SVector<N> & a, const SVector<N> & b) : p1(a), p2(b) {}

    /// set new points
    void setPoints(const SVector<N> & a, const SVector<N> & b)
      {p1 = a; p2 = b;}

    /// returns point on line; t in (0, 1)
    SVector<N> eval(Real t) const
      {
      assert(t >= 0 and t <= 1);
        return p1 + t*(p2-p1);
      }

    /// project pt on segment
    SVector<N> foot(const SVector<N> & pt) const
      {
        Real par = dot(pt-p1, p2-p1) / dot(p2-p1, p2-p1);
        if (par < 0)
          return p1;
        else if (par > 1)
          return p2;
        else
          return p1 + par*(p2-p1);
      }

    /// parameter of the projection point
    Real footPar(const SVector<N> & p) const
      {
        Real par = dot( p-p1, p2-p1 ) / dot(p2-p1, p2-p1);
        if (par < 0)
          return 0;
        else if (par > 1)
          return 1;
        else
          return par;
      }

    /// calculates the minimum distance of p from segment
    Real distance(const SVector<N> & p) const
      { return norm( p-foot(p) ); }

    /// compute Intersection
    LnIts<N> intersection(const Segment<N> & seg) const
      {
        LnIts<N> li;
        Line<N> l1(p1, p2), l2(seg.p1, seg.p2);
        li = l1.intersection(l2);
        if (li.self < 0 or li.self > 1 or li.other < 0 or li.other > 1)
          li.hit = false;
        return li;
      }

  private:

    /// start and end point
    SVector<N> p1,p2;
};

#endif

