
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
 
#include "ellipframe.h"

using namespace std;

void EllipFrame::init(const Vct3 & ctr, Real radius)
{
  init(ctr, radius, radius, radius);  
}
    
void EllipFrame::init(const Vct3 & ctr, Real rz, Real ry)
{
  init(ctr, rz, rz, ry);  
}
    
void EllipFrame::init(const Vct3 & ctr, Real rzdown, Real rzup, Real ry)
{
  ectr = ctr;
  rlo = rzdown;
  rhi = rzup;
  rs = ry;
  
  // create seven interpolation points (30deg segments)   
  PointList<3> pts(7);
  Real phi, dphi = rad(30.0);
  for (uint i=0; i<7; ++i) {
    phi = i*dphi;
    pts[i] = ectr;
    pts[i][1] += rs*sin(phi);
    if (phi < rad(90.))
      pts[i][2] -= rlo*cos(phi);    
    else
      pts[i][2] -= rhi*cos(phi); 
  }
  
  SymFrame::init(pts);
}

XmlElement EllipFrame::toXml(bool) const
{
  XmlElement xe("EllipFrame");
  xe.attribute("name") = ids;
  
  XmlElement xc("Center");
  xc.text() = " " + str(ectr) + " ";
  
  XmlElement xr("Radius");
  xr.text() = " " + str(rlo) + " " + str(rhi) + " " + str(rs) + " ";

  xe.append(std::move(xc));
  xe.append(std::move(xr));
  xe.append(Curve::trafoToXml());
  
  return xe;
}

void EllipFrame::fromXml(const XmlElement & xe)
{
  if (xe.name() != "EllipFrame")
    throw Error("Incompatible XML representation for EllipFrame.");

  rename(xe.attribute("name"));
  
  rs = rlo = rhi = 0.0;
  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    if (itr->name() == "Center") {
      stringstream ss(itr->text());
      ss >> ectr;
    } else if (itr->name() == "Radius") {
      stringstream ss(itr->text());
      ss >> rlo >> rhi >> rs;
    } 
  }
  if ((rs*rlo*rhi) == 0)
    throw Error("EllipFrame::fromXml() : Cannot create frame with zero area.");
  
  init(ectr, rlo, rhi, rs);
  
  itr = xe.findChild("TrafoSequence");
  if (itr != xe.end())
    Curve::applyFromXml(*itr);
}

EllipFrame *EllipFrame::clone() const
{
  return new EllipFrame(*this);
}
