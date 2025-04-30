
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
#include <genua/pattern.h>
#include "cylinder.h"

using namespace std;

Cylinder::Cylinder(const std::string & s, const Vct3 & pbot,
                   const Vct3 & ptop, const Vct3 & vrad)
                   : Surface(s), bot(pbot), top(ptop), r1(vrad)
{
  r2 = cross(top-bot,r1);
  r2 *= norm(r1)/norm(r2);
  assert(norm(ptop-pbot) > 0);
  assert(norm(r1) > 0);
  assert(norm(r2) > 0);
}

Vct3 Cylinder::eval(Real u, Real v) const
{
  // evaluate cylinder equation
  Real s, c;
  sincosine(2*PI*u, s, c);
  return bot + v*(top-bot) + r1*c + r2*s;
}

Vct3 Cylinder::derive(Real u, Real v, uint du, uint dv) const
{
  // second derivatives not implemented!

  if (du == 0 and dv == 0)
    return eval(u,v);
  else if (du == 1 and dv == 0) {
    Real c,s;
    sincosine(2*PI*u, s, c);
    return 2*PI*(-r1*s + r2*c);
  } else if (du == 0 and dv == 1) {
    return top - bot;
  } else if ( (du == 1 and dv == 1) or dv > 1) {
    return vct(0.0, 0.0, 0.0);
  } else if (du == 2 and dv == 0) {
    Real c,s;
    sincosine(2*PI*u, s, c);
    return 2*PI*(-r1*c - r2*s);
  } else
    throw Error("Cylinder::derive() - Derivative not implemented.");
}

void Cylinder::apply()
{
  bot = RFrame::forward(bot);
  top = RFrame::forward(top);
  r1 = RFrame::forward(r1);
  r2 = RFrame::forward(r2);  
  RFrame::clear();
}

XmlElement Cylinder::toXml(bool) const
{
  XmlElement xe("Cylinder");
  xe["name"] = ids;

  stringstream ss;
  ss << bot << endl;
  ss << top << endl;
  ss << r1 << endl;
  ss << r2 << endl;
  xe.text(ss.str());
    
  return xe;
}
    
void Cylinder::fromXml(const XmlElement & xe)
{
  if (xe.name() != "Cylinder")
    throw Error("Cylinder: incompatible XML representation.");

  rename(xe.attribute("name"));
  stringstream ss;
  ss.str(xe.text());
  ss >> bot;
  ss >> top;
  ss >> r1;
  ss >> r2;
}

void Cylinder::initGridPattern(Vector & up, Vector & vp) const
{
  Real vlen = norm(top-bot);
  Real ulen = 0.5*(norm(r1) + norm(r2));
  
  uint nu = max(15, int(15*ulen/vlen));
  uint nv = max(9, int(9*vlen/ulen));
  up = equi_pattern(nu);
  vp = equi_pattern(nv);
}
    
void Cylinder::isSymmetric(bool & usym, bool & vsym) const
{
  usym = true;
  vsym = true;
}

