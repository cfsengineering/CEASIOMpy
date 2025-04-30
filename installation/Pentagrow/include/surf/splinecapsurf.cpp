
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
 
#include <genua/pattern.h>
#include "curve.h"
#include "openframe.h"
#include "splinecapsurf.h"

using namespace std;

uint SplineCapSurf::iMaxKnots = numeric_limits<int>::max();

void SplineCapSurf::init(const Vector & tc, const Curve & c)
{
  Real tsplit(0.5), mindst(huge);
  const int nt = tc.size();
  for (int i=0; i<nt; ++i) {
    Real dst = fabs(tc[i] - 0.5);
    if (dst < mindst) {
      tsplit = tc[i];
      mindst = dst;
    }
  }  

  init(tsplit, c);
}
    
void SplineCapSurf::init(Real tsplit, const Curve & c)
{
  // build lateral curves by interpolation
  OpenFrame cu0, cu1;
  const int np = min(iMaxKnots-4, c.controls().size());
  PointList<3> pts(np);
  for (int i=0; i<np; ++i) 
    pts[i] = c.eval( i*tsplit/(np-1) );
  cu0.init(pts);
  for (int i=0; i<np; ++i) 
    pts[i] = c.eval( 1.0 - i*(1.0 - tsplit)/(np-1) );
  cu1.init(pts);
  
  // create compromise knot vector
  Vector knt = 0.5*(cu0.knots() + cu1.knots());
  
  // and adapt both curves to this one
  sort(knt.begin(), knt.end());
  cu0.adapt(knt);
  cu1.adapt(knt);
  
  // extract control points
  const PointList<3> & cplo( cu0.controls() );
  const PointList<3> & cphi( cu1.controls() );
  assert(cplo.size() == cphi.size());
  
  // setup spline surface linear in u and cubic in v
  Vector uknots(4);
  uknots[0] = uknots[1] = 0.0;
  uknots[2] = uknots[3] = 1.0;
  
  const int ncols = cplo.size();
  PolySplineSurf::ub = SplineBasis(1, uknots);
  PolySplineSurf::vb = SplineBasis(3, knt);
  PolySplineSurf::cp.resize(2, ncols);
  for (int j=0; j<ncols; ++j) {
    PolySplineSurf::cp(0,j) = cplo[j];
    PolySplineSurf::cp(1,j) = cphi[j];
  }
}

void SplineCapSurf::initGridPattern(Vector & up, Vector & vp) const
{
  up = equi_pattern(8);
  vp = cosine_pattern(30, 2*PI, 0.0, 0.8);
}

