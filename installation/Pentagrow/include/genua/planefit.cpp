
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
 
// Plane::fitNormal() moved to separate source file to break
// dependency of plane.o (and most that includes plane.h) from LAPACK
// which is not always available on win32/msvc (but everywhere else)

#include "eig.h"
#include "plane.h"

const Vct3 & Plane::fitNormal(const Vct3 & origin, const PointList<3> & pts)
{
  // covariance matrix
  SMatrix<3,3> h;
  for (uint i=0; i<pts.size(); ++i) {
    Vct3 r = pts[i] - origin;
    for (uint j=0; j<3; ++j)
      for (uint k=0; k<3; ++k)
        h(j,k) += r[j]*r[k];
  }

  // compute principal directions
  Vct3 eval;
  sym_eig3(h, eval);

  // pick smallest axis
  Vct3 np;
  extract_eigenvector(h, eval[0], np);

  // adapt direction
  if (dot(m_normal,np) < 0)
    m_normal = -np/norm(np);
  else
    m_normal = np/norm(np);

  m_dist = dot(m_normal,origin);
  return m_normal;
}

