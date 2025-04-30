
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
 
#include "edgecurve.h"

EdgeCurve::EdgeCurve(const Edge & e) : rev(false)
{
  // construct cubic curve from vertices and normals
  const Triangulation & srf( *(e.surface()) );
  uint v1, v2;
  Vct3 t1, t2, n1, n2, ev, p1, p2;
  
  v1 = e.source();
  v2 = e.target();  
  p1 = srf.vertex(v1);
  p2 = srf.vertex(v2);  
  n1 = srf.normal(v1);
  n2 = srf.normal(v2);
  ev = srf.vertex(v2) - srf.vertex(v1);

  // length factors
  Real lf1 = 1.0 - sq(dot(ev,n1)/norm(ev));
  Real lf2 = 1.0 - sq(dot(ev,n2)/norm(ev));

  t1 = lf1* cross( n1, cross(ev, n1) );
  t2 = lf2* cross( n2, cross(ev, n2) );

  // compute coefficients
  a0 = p1;
  a1 = t1;
  a2 = -3.0*p1 + 3.0*p2 - 2.0*t1 - t2;
  a3 = 2.0*p1 - 2.0*p2 + t1 + t2;
  defined = true;
}

Vct3 EdgeCurve::eval(Real t) const
{
  // evaluate curve
  assert(defined);
  assert(t >= 0.0);
  assert(t <= 1.0);
  
  if (rev)
    t = 1.0 - t;
    
  return a0 + a1*t + a2*sq(t) + a3*cb(t);
}


