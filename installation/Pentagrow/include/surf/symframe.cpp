
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
 
#include <genua/line.h>
#include <genua/lu.h>
#include "symframe.h"

using namespace std;

Vector SymFrame::init(const PointList<3> & pts)
{
  assert(pts.size() > 3);
  ipp = pts;
  
  // compute second set (mirror copy) of interpolation points
  // first, copy 'left side' interpolation points
  PointList<3> ipolpts(2*pts.size()-1);
  std::copy(pts.begin(), pts.end(), ipolpts.begin());

  // setup symmetry line
  Line<3> mirror(pts.front(), pts.back());

  // first point is last point
  ipolpts.back() = pts[0];

  // mirror all points in pts[] about line
  Vct3 pt_to_line;
  for (uint i=1; i<pts.size()-1; ++i) {
    pt_to_line = mirror.foot(pts[i]) - pts[i];
    ipolpts[ipolpts.size()-i-1] = pts[i] + 2.0*pt_to_line;
  }
  
  // compute first half of parameter values
  Vector u(ipolpts.size());
  for (uint i=1; i<pts.size(); ++i)
    u[i] = u[i-1] + norm(pts[i] - pts[i-1]);
  u /= 2*u[pts.size()-1];

  // mirror parameters (second half)
  for (uint i=pts.size(); i<u.size(); i++)
    u[i] = 1. - u[2*pts.size()-2-i];

  // compute knots:
  // fill knot vector, insert (degree+1) multiple start and end knot
  uint p(3); // always cubic
  uint n = u.size() - 1;
  uint m = n + p + 3;
  Vector knots(m+1);

  // knot placement by 'averaging' [Pie97] Eq. 9.9
  for (uint j=0; j<=n-p+1; j++)
    for (uint i=j; i<=j+p-1; i++)
      knots[j+p+1] += 1./p * u[i];

  for (uint i=n+3; i<=m; i++)
    knots[i] = 1.;

  // setup equations
  bas = SplineBasis(p,knots);
  Matrix cf(n+3,n+3), rhs(n+3,3);

  // first equation: slope continuity at parameters 0 and 1
  // the 'epsilons' should not be here, but without, nothing works:
  // basis function derivatives vanish on the last span for t=u[u.size()-1], 
  // but by definition,they cannot be zero there -- must be some floating 
  // point accuracy problem...
  Real first = u.front() + 0.125*gmepsilon;
  Real last = u.back() - 0.125*gmepsilon;
  for (uint i=0; i<=n+2; ++i)
    cf(0,i) = bas.derive(i,first,1) - bas.derive(i,last,1);

  // last equation: curvature continuity
  for (uint i=0; i<=n+2; ++i)
    cf(cf.nrows()-1,i) = bas.derive(i,first,2) - bas.derive(i,last,2);

  // interpolation conditions
  for (uint i=0; i<u.size(); ++i) {
    uint span = bas.findSpan(u[i]);
    for (uint j=span-p; j<=span; ++j)
      cf(i+1,j) = bas.eval(j,u[i]);
  }

  // interpolation points - rhs
  for (uint i=0; i<ipolpts.size(); ++i)
    for (uint k=0; k<3; ++k)
      rhs(i+1,k) = ipolpts[i][k];

  // solve for control points
  int stat = lu_solve(cf, rhs);
  if (stat != 0)
    throw Error("Multiple identical points in SymFrame interpolation: "
                + name());
  cp.resize(rhs.nrows());
  for (uint i=0; i<rhs.nrows(); ++i)
    for (uint j=0; j<3; ++j)
      cp[i][j] = rhs(i,j);

  // merge first and last control point to be identical 
  cp.front() = cp.back() = 0.5*(cp.front() + cp.back());
  
  return u;
}

XmlElement SymFrame::toXml(bool) const
{
  XmlElement xe("SymFrame");
  xe.attribute("name") = ids;
  
  XmlElement xp("InterpolationPoints");
  xp.attribute("count") = str(ipp.size());
  
  stringstream ss;
  for (uint i=0; i<ipp.size(); ++i)
    ss << ipp[i] << endl;
  xp.text() = ss.str();
  
  xe.append(std::move(xp));
  xe.append(Curve::trafoToXml());
  
  return xe;
}

void SymFrame::fromXml(const XmlElement & xe)
{
  if (xe.name() != "SymFrame")
    throw Error("Incompatible XML representation for SymFrame.");

  rename(xe.attribute("name"));
  XmlElement::const_iterator itr;
  itr = xe.findChild("InterpolationPoints");  
  if (itr == xe.end())
    throw Error("SymFrame XML representation requires interpolation points.");
        
  // read interpolation points
  uint np = Int(itr->attribute("count"));  
  ipp.resize(np);
  stringstream ss(itr->text());
  for (uint i=0; i<np; ++i)
    ss >> ipp[i];    
  
  init(ipp);
  
  itr = xe.findChild("TrafoSequence");
  if (itr != xe.end())
    Curve::applyFromXml(*itr);
}

SymFrame *SymFrame::clone() const
{
  return new SymFrame(*this);
}

