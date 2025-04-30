
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
#include <genua/strutils.h>
#include "eggframe.h"

using namespace std;

void EggFrame::init(const Vct3 & pzl, const Vct3 & pzu, const Vct3 & pys)
{
  zl = pzl;
  zu = pzu;
  ys = pys;
  
  Vct3 zmid = 0.5*(zl + zu);
  Vct3 rup = 0.5*(zu - zl);
  Real lrup = norm(rup);

  Vct3 zs, rside, zp;
  Line<3> zline(zl, zu);
  zs = zline.foot(ys);
  rside = ys - zs;

  // create n points along the half sector, i.e. 0 < alpha < PI
  // parametrization starts at the lower point, that is u = 0 -> alpha = PI
  const uint n(16);
  PointList<3> pts(n);
  Real alpha, beta, sa, ca;
  for (uint i=0; i<n; ++i) {
    alpha = PI* (1.0 - Real(i)/(n-1));
    sincosine(alpha, sa, ca);
    zp = zmid + rup*ca;
    beta = atan(lrup*sa/norm(zp - zs));
    pts[i] = zp + rside*sin(beta);
  }

  SymFrame::init(pts);
}
    
XmlElement EggFrame::toXml(bool) const
{
  XmlElement xe("EggFrame");
  xe.attribute("name") = Curve::ids;

  // store defining points
  XmlElement xl("Lower");
  xl.text() = str(zl);
  xe.append(std::move(xl));

  XmlElement xu("Upper");
  xu.text() = str(zu);
  xe.append(std::move(xu));

  XmlElement xs("Side");
  xs.text() = str(ys);
  xe.append(std::move(xs));

  // add transformation sequence data
  xe.append(Curve::trafoToXml());
  
  return xe;
}
    
void EggFrame::fromXml(const XmlElement & xe)
{
  Vct3 pzl, pzu, pys;

  if (xe.name() != "EggFrame")
    throw Error("Incompatible XML representation for EggFrame: "+xe.name());

  rename(xe.attribute("name"));

  // identify definition points
  XmlElement::const_iterator itr;
  itr = xe.findChild("Lower");
  if (itr == xe.end())
    throw Error("EggFrame definition requires xml element <Lower> x y z </Lower>.");
  else
    fromString(itr->text(), pzl);

  itr = xe.findChild("Upper");
  if (itr == xe.end())
    throw Error("EggFrame definition requires xml element <Upper> x y z </Upper>.");
  else
    fromString(itr->text(), pzu);

  itr = xe.findChild("Side");
  if (itr == xe.end())
    throw Error("EggFrame definition requires xml element <Side> x y z </Side>.");
  else
    fromString(itr->text(), pys);

  // create spline curve
  init(pzl, pzu, pys);

  // apply transformation if present
  itr = xe.findChild("TrafoSequence");
  if (itr != xe.end())
    Curve::applyFromXml(*itr);
}

EggFrame *EggFrame::clone() const
{
  return new EggFrame(*this);
}
