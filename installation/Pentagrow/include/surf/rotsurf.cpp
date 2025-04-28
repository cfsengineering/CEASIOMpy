
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
#include "rotsurf.h"

using namespace std;

void RotSurf::init(const CurvePtr & c, const Vct3 & pa, const Vct3 & pb)
{
  org = pa;
  rax = pb - pa;
  corg = c;
  cva = cvb = *c;
  cva.translate(-1.0*pa);
  cva.apply();
  cva.rename("BaseCurve");

  cvb.translate(-1.0*pa);
  cvb.rotate(rax, 0.5*PI);
  cvb.apply();
  cvb.rename("OrthoCurve");
}

Vct3 RotSurf::eval(Real u, Real v) const
{
  Real phi(2*PI*u), cphi, sphi;
  Vct3 pa, pb, foot;
  pa = cva.eval(v);
  pb = cvb.eval(v);
  foot = org + dot(pa,rax)*rax;
  sincosine(phi, sphi, cphi);
  
  return foot + (pa-foot)*cphi + (pb-foot)*sphi;
}

Vct3 RotSurf::derive(Real u, Real v, uint ku, uint kv) const
{
  if (ku == 0 and kv == 0)
    return eval(u,v);

  Vct3 dpa, dpb, dfoot;
  dpa = cva.derive(v,kv);
  dpb = cvb.derive(v,kv);
  dfoot = dot(dpa,rax)*rax;

  Real sa(1.0), sb(1.0);
  if ( ((ku+1)/2)%2 != 0 )
    sa = -1.0;
  if ( (ku/2)%2 != 0 )
    sb = -1.0;
  Real a = pow(2*PI, Real(ku) );
  Real cpa, cpb, phi(2*PI*u);
  if (ku%2 == 0)
    sincosine(phi, cpb, cpa);
  else
    sincosine(phi, cpa, cpb);

  return dfoot + a*sa*cpa*(dpa - dfoot) + a*sb*cpb*(dpb - dfoot);
}

void RotSurf::apply()
{
  cva.setTrafoMatrix(RFrame::mat);
  cva.apply();
  cvb.setTrafoMatrix(RFrame::mat);
  cvb.apply();
  RFrame::clear();
}

XmlElement RotSurf::toXml(bool) const
{
  XmlElement xe("RotSurf");
  xe["name"] = ids;
  XmlElement xa("RotationAxis");
  stringstream ss;
  ss << org << endl;
  ss << rax << endl;
  xa.text(ss.str());
  xe.append(std::move(xa));
  xe.append(corg->toXml());
    
  return xe;
}
    
void RotSurf::fromXml(const XmlElement & xe)
{
  if (xe.name() != "RotSurf")
    throw Error("RotSurf: Incompatible XML representation: "+xe.name());

  rename(xe.attribute("name"));
  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    if (itr->name() == "RotationAxis") {
      stringstream ss;
      ss.str(itr->text());
      ss >> org;
      ss >> rax;
    } else {
      CurvePtr cp = Curve::createFromXml(*itr);
      if (cp)
        corg = cp;
    }
  }
  init(corg, org, org+rax);
}

void RotSurf::initGridPattern(Vector & up, Vector & vp) const
{
  up = equi_pattern(13);
  vp = equi_pattern(21);
}
    
void RotSurf::isSymmetric(bool & usym, bool & vsym) const
{
  usym = true;
  vsym = false;
}


