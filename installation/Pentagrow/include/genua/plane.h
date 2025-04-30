
/* Copyright (C) 2019 David Eller <david@larosterna.com>
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

#ifndef GENUA_PLANE_H
#define GENUA_PLANE_H

#include "point.h"
#include "line.h"
#include "xmlelement.h"

struct PlnIts
{
  bool pierces;
  Real parm;
  Vct3 pt;
};

/** A plane in three dimensions.

  Can be initialized by a normal and distance from origin, or by
  two tangent vectors and a point in the plane. To create a plane
  from three points, use
  \begin{verbatim}
  Vct3 a,b,c;
  Plane pl((a-b), (a-c), a);
  \end{verbatim}
  Plane supports computation of point distance and projections.

  \ingroup geometry
  */
class Plane
{
  
public:
  
  enum CartesianPlaneType { XPlus, XMinus, YPlus, YMinus, ZPlus, ZMinus };

  /// empty construction
  Plane() : m_dist(0) {}

  /// construct a plane aligned with coordinate axes
  Plane(CartesianPlaneType cartp, Real dst = 0.0);

  /// build from normal and distance from origin
  Plane(const Vct3 & n, Real d);

  /// build from two vectors in plane and a point
  Plane(const Vct3 & a, const Vct3 & b, const Vct3 & p);

  /// project point onto plane
  Vct3 project(const Vct3 & p) const {return p-distance(p)*m_normal;}

  /// return the mirror image of a point with respect to plane
  Vct3 reflection(const Vct3 &p) const {
    Vct3 pjp = this->project(p);
    return p + 2.0*(pjp - p);
  }

  /// calculate signed distance
  Real distance(const Vct3 & p) const {return dot(m_normal, p)-m_dist;}

  /// is *this parallel to pl
  bool parallel(const Plane & pl) const {
    return norm(cross(m_normal, pl.m_normal)) < gmepsilon;
  }

  /// compute intersection line
  Line<3> intersection(const Plane & pl) const;

  /// compute line parameter where line pierces plane
  PlnIts pierce(const Line<3> & ln) const;

  /// compute line parameter where line pierces plane
  PlnIts pierce(const Vct3 & p1, const Vct3 & p2) const;

  /// return normal
  const Vct3 & vector() const {return m_normal;}

  /// return offset (distance from origin)
  Real offset() const {return m_dist;}

  /** determine a normal vector so that the plane through origin
    minimizes the sum of squared distances for the points in pts */
  const Vct3 & fitNormal(const Vct3 & origin, const PointList<3> & pts);

  /// return XML representation
  XmlElement toXml(bool share) const;

  /// recover from XML representation
  void fromXml(const XmlElement &xe);

private:

  /// normal vector
  Vct3 m_normal;

  /// distance from origin
  Real m_dist;
};


#endif
