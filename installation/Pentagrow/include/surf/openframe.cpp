
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
 
#include <sstream>
#include <genua/lu.h>
#include <genua/xmlelement.h>
#include "openframe.h"
 
using namespace std;

Vector OpenFrame::init(const PointList<3> & a)
{
  assert(a.size() > 3);
  ipp = a;

  // always cubic
  uint p(3);
  Matrix cf(a.size(), a.size());

  // chord length parametrization
  Vector u(a.size());
  for (uint i=1; i<u.size(); ++i)
    u[i] = u[i-1] + norm(a[i] - a[i-1]);

  assert(u.back() != 0);
  u /= u.back();

  // construct basis
  bas.init(3, u);

  // set up linear system of equations
  for (uint i=0; i<a.size(); ++i) {
    uint span = bas.findSpan(u[i]);
    for (uint j=span-p; j<=span; ++j)
      cf(i,j) = bas.eval(j,u[i]);
  }

  // solve for control points
  Matrix rs(a.size(), 3);
  for (uint i=0; i<a.size(); ++i)
    for (uint j=0; j<3; ++j)
      rs(i,j) = a[i][j];

  try {
    rs = lu_solve_copy(cf,rs);
  } catch (Error & xcp) {
    stringstream ss;
    ss << "OpenFrame::init() - " << endl;
    ss << "Factorization failed with matrix for parameter vector:" << endl;
    ss << u << endl;
    throw Error(ss.str());
  }
  
  cp.resize(a.size());
  for (uint i=0; i<a.size(); ++i)
    for (uint j=0; j<3; ++j)
      cp[i][j] = rs(i,j);
  
  return u;
}

XmlElement OpenFrame::toXml(bool) const
{
  XmlElement xe("OpenFrame");
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

void OpenFrame::fromXml(const XmlElement & xe)
{
  if (xe.name() != "OpenFrame")
    throw Error("Incompatible XML representation for OpenFrame.");

  rename(xe.attribute("name"));
  
  XmlElement::const_iterator itr;
  itr = xe.findChild("InterpolationPoints");
  if (itr == xe.end())
    throw Error("OpenFrame XML representation requires interpolation points.");
  
  // read interpolation points
  uint np = Int(itr->attribute("count"));  
  ipp.resize(np);
  stringstream ss(itr->text());
  for (uint i=0; i<np; ++i)
    ss >> ipp[i];    
  init(ipp);
  
  // read transformation, if present
  itr = xe.findChild("TrafoSequence");
  if (itr != xe.end())
    Curve::applyFromXml(*itr);
}

OpenFrame *OpenFrame::clone() const
{
  return new OpenFrame(*this);
}


