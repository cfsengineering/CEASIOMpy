
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
 
#include "xcept.h"
#include "plane.h"

Plane::Plane(Plane::CartesianPlaneType cartp, Real dst) : m_dist(dst)
{
  switch (cartp) {
  case XPlus:
    m_normal = Vct3(1, 0, 0);
    break;
  case XMinus:
    m_normal = Vct3(-1, 0, 0);
    break;
  case YPlus:
    m_normal = Vct3(0, 1, 0);
    break;
  case YMinus:
    m_normal = Vct3(0, -1, 0);
    break;
  case ZPlus:
    m_normal = Vct3(0, 0, 1);
    break;
  case ZMinus:
    m_normal = Vct3(0, 0, -1);
    break;
  }
}

Plane::Plane(const Vct3 & n, Real d) : m_normal(n.normalized()), m_dist(d)
{
  if (m_dist < 0) {
    m_normal = -1.*m_normal;
    m_dist = -m_dist;
  }
}

Plane::Plane(const Vct3 & a, const Vct3 & b, const Vct3 & p)
{
  m_normal = cross(a,b).normalized();
  m_dist = dot(m_normal,p);
  if (m_dist < 0) {
    m_normal = -1.*m_normal;
    m_dist = -m_dist;
  }
}

Line<3> Plane::intersection(const Plane & pl) const
{
  // compute intersection line
  if ( parallel(pl) )
    throw Error("Planes are parallel - no intersection.");

  Vct3 k( cross(m_normal, pl.m_normal) );
  Vct3 t1( m_dist*m_normal );
  Vct3 t2( pl.m_dist*pl.m_normal );
  
  Line<3> l1(t1, t1+cross(k, m_normal) );
  Line<3> l2(t2, t2+cross(k, pl.m_normal) );
  
  LnIts<3> its = l1.intersection( l2 );
  if (not its.hit)
    throw Error("Planes do not intersect.");
  
  return Line<3>(its.pt, its.pt+k);
  
//   Vct3 p1, d, a, p1, pk;
//   p1 = dist*normal;
//   a = cross(normal, k);
//   d = pl.project(p1) - p1;
//   pk = p1 + norm(d) / dot(a,d) * a;
//   return Line<3>(pk, pk+k);
}

PlnIts Plane::pierce(const Vct3 & p1, const Vct3 & p2) const
{
  Vct3 le = p2 - p1;
  PlnIts its;
  its.pierces = false;
  its.parm = 0.0;
  if ( fabs(dot(le,m_normal)) < gmepsilon*norm(le) )
    return its;
  
  Real t = (m_dist - dot(m_normal,p1)) / (dot(m_normal,p2) - dot(m_normal,p1));
  its.pierces = true;
  its.parm = t;
  its.pt = (1-t)*p1 + t*p2;
  
  return its;      
}

PlnIts Plane::pierce(const Line<3> & ln) const
{
  return pierce(ln.eval(0.0), ln.eval(1.0));
}
       
XmlElement Plane::toXml(bool) const
{
  XmlElement xe("Plane");
  xe["normal"] = str( m_normal );
  xe["distance"] = str(m_dist);
  return xe;
}

void Plane::fromXml(const XmlElement &xe)
{
  fromString(xe.attribute("normal"), m_normal);
  m_dist = xe.attr2float("distance", 0.0);
}


// Plane::fitNormal() moved to separate source file to break
// dependency of plane.o (and most that includes plane.h) from LAPACK
// which is not always available on win32/msvc (but everywhere else)


