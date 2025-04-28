
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
 
#include "dcspatialgeometry.h"
#include "delaunaycore.h"
#include <predicates/predicates.h>

bool DcSpatialGeometry::encroaches(const DelaunayCore &,
                                   const uint vf[], uint v) const
{
  const Vct3 & p0( m_vtx[vf[0]] );
  const Vct3 & p1( m_vtx[vf[1]] );
  const Vct3 & p2( m_vtx[vf[2]] );
  const Vct3 & pt( m_vtx[v] );

  Vct3 pcs;
  pointOnSphere(vf, pcs);

  // requires that p0, p1, p2 are in counterclockwise order
  double ict = jrsInSphere(p0, p1, p2, pcs, pt);
  return (ict <= 0.0);
}

bool DcSpatialGeometry::encroachesEdge(uint src, uint trg, uint v) const
{
  return DcGeometry::encroachesBall( m_vtx[src], m_vtx[trg], m_vtx[v] );
}

void DcSpatialGeometry::pointOnSphere(const uint vf[], Vct3 &pcs) const
{
  const Vct3 & p1(m_vtx[vf[0]]);
  const Vct3 & p2(m_vtx[vf[1]]);
  const Vct3 & p3(m_vtx[vf[2]]);

  // triangle normal and edge-normal directions
  Vct3 tn( cross(p2-p1,p3-p1) );
  Vct3 e1( cross(tn, p2-p1) );
  Vct3 e2( cross(tn, p3-p2) );

  // edge midpoints
  Vct3 m1( 0.5*(p1+p2) );
  Vct3 m2( 0.5*(p2+p3) );

  Real a11(0.0), a12(0.0), a21(0.0), a22(0.0);
  Real r1(0.0), r2(0.0);
  for (uint i=0; i<3; i++) {
    a11 +=  sq(e1[i]);
    a12 -= e1[i]*e2[i];
    a22 += sq(e2[i]);
    r1 -= (m1[i] - m2[i])*e1[i];
    r2 += (m1[i] - m2[i])*e2[i];
  }
  a21 = a12;

  // zero means lines are parallel
  Real det = a11*a22 - a12*a21;
  if (det == 0.0) {
    pcs = m1 + huge*e1;
  } else {
    Real s = (r1*a22 - r2*a12) / det;
    pcs = m1 + s*e1;
  }

  Real r = norm(pcs - p1);
  normalize(tn);
  pcs -= r*tn;
}
