
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
 
#include <iostream>

#include <genua/defines.h>
#include <genua/xcept.h>
#include <genua/plane.h>
#include <genua/line.h>
#include <genua/pattern.h>
#include "linearsurf.h"
#include "wingletblend.h"

using namespace std;

void WingletBlend::init(const Curve & a, const Curve & b)
{
  // store *copies* of the original curves
  c0 = CurvePtr(new Curve(a));
  c1 = CurvePtr(new Curve(b));
  initRotation();
}

void WingletBlend::initRotation()
{
  // fit plane through first and last section
  Vct3 pmid;
  Plane pl1, pl2;
  const uint n(32);
  PointList<3> pts(n);
  for (uint i=0; i<n; ++i) {
    pts[i] = c0->eval( Real(i)/(n-1) );
    pmid += pts[i];
  }
  pmid /= Real(n);
  pl1.fitNormal(pmid, pts);
  
  pmid = 0.0;
  for (uint i=0; i<n; ++i) {
    pts[i] = c1->eval( Real(i)/(n-1) );
    pmid += pts[i];
  }
  pmid /= Real(n);
  pl2.fitNormal(pmid, pts);
  
  // construct axis of rotation
  Line<3> rline = pl1.intersection(pl2);
  lp = rline.eval(0.0);
  ldir = rline.direction();
  
  // reference axis : downward
  Vct3 rax;
  rax[2] = -1.0;
  
  // compute angles
  Vct3 r0, r1;
  r0 = c0->eval(0.0) - lp;
  r1 = c1->eval(0.0) - lp;
  
  r0 -= dot(r0,ldir) * ldir;
  r1 -= dot(r1,ldir) * ldir;
  
  theta0 = arg(rax, r0);
  theta1 = arg(rax, r1);
  
  // transformation matrix
  Real st0, ct0, st1, ct1;
  sincosine(theta0, st0, ct0);
  sincosine(theta1, st1, ct1);
  Mtx22 m;
  m(0,0) = ct0;
  m(1,0) = ct1;
  m(0,1) = st0;
  m(1,1) = st1;
  inverse(m, csm);
}
    
Vct3 WingletBlend::eval(Real u, Real v) const 
{
  // evaluate interface curves
  Vct3 p0 = c0->eval(u) - lp;
  Vct3 p1 = c1->eval(u) - lp;
  
  // transform into orthogonal control points 
  Vct3 ca, cb;
  for (uint k=0; k<3; ++k) {
    ca[k] = csm(0,0) * p0[k] + csm(0,1) * p1[k];
    cb[k] = csm(1,0) * p0[k] + csm(1,1) * p1[k];
  }
  
  // substract component along the axis of rotation
  ca -= dot(ca,ldir)*ldir;
  cb -= dot(cb,ldir)*ldir;
  
  // component along the axis of rotation
  Vct3 b(ldir);
  b *= (1-v)*dot(p0,ldir) + v*dot(p1,ldir);
  
  // angle for elliptic arc
  Real phi, sphi, cphi;
  phi = theta0 + v*(theta1 - theta0);
  sincosine(phi, sphi, cphi);
 
  return lp + b + ca*cphi + cb*sphi;
}

void WingletBlend::plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const
{
  Vct3 p0, t0, p1, t1;
  c0->tgline(u, p0, t0);
  c1->tgline(u, p1, t1);
  
  p0 -= lp;
  p1 -= lp;
  
  Vct3 ca, cb, cadu, cbdu;
  for (uint k=0; k<3; ++k) {
    ca[k] = csm(0,0) * p0[k] + csm(0,1) * p1[k];
    cadu[k] = csm(0,0) * t0[k] + csm(0,1) * t1[k];
    cb[k] = csm(1,0) * p0[k] + csm(1,1) * p1[k];
    cbdu[k] = csm(1,0) * t0[k] + csm(1,1) * t1[k];
  }
  ca -= dot(ca,ldir)*ldir;
  cb -= dot(cb,ldir)*ldir;
  cadu -= dot(cadu,ldir)*ldir;
  cbdu -= dot(cbdu,ldir)*ldir;
  
  Vct3 b(ldir), bdu(ldir), bdv(ldir);
  b *= (1-v)*dot(p0,ldir) + v*dot(p1,ldir);
  bdu *= (1-v)*dot(t0,ldir) + v*dot(t1,ldir);
  bdv *= dot(p1,ldir) - dot(p0,ldir);
  
  Real phi, sphi, cphi, dtheta;
  phi = theta0 + v*(theta1 - theta0);
  dtheta = theta1 - theta0;
  sincosine(phi, sphi, cphi);
  
  S = lp + b + ca*cphi + cb*sphi;
  Su = bdu + cadu*cphi + cbdu*sphi;
  Sv = bdv + cb * (cphi*dtheta) - ca * (sphi*dtheta);
}
    
Vct3 WingletBlend::normal(Real u, Real v) const
{
  Vct3 S, Su, Sv, nrm;
  plane(u, v, S, Su, Sv);
  nrm = cross(Su, Sv);
  normalize(nrm);
  return nrm;
}
    
Vct3 WingletBlend::derive(Real u, Real v, uint du, uint dv) const
{
  if (du == 0 and dv == 0) 
    return eval(u, v);
    
  Vct3 p0, p1, ca, cb;
  if (du < 1) {
    p0 = c0->eval(u) - lp;
    p1 = c1->eval(u) - lp;
    for (uint k=0; k<3; ++k) {
      ca[k] = csm(0,0) * p0[k] + csm(0,1) * p1[k];
      cb[k] = csm(1,0) * p0[k] + csm(1,1) * p1[k];
    }
  } else {
    p0 = c0->derive(u, du);
    p1 = c1->derive(u, du);
    for (uint k=0; k<3; ++k) {
      ca[k] = csm(0,0) * p0[k] + csm(0,1) * p1[k];
      cb[k] = csm(1,0) * p0[k] + csm(1,1) * p1[k];
    }
  }
  ca -= dot(ca,ldir)*ldir;
  cb -= dot(cb,ldir)*ldir;
 
  Vct3 b(ldir);
  if (dv == 0)
    b *= (1-v)*dot(p0,ldir) + v*dot(p1,ldir);
  else if (dv == 1)
    b *= dot(p1,ldir) - dot(p0,ldir);
  else
    b = 0.0;
  
  Real phi, sphi, cphi, dtheta;
  phi = theta0 + v*(theta1 - theta0);
  dtheta = pow(theta1 - theta0, Real(dv));
  sincosine(phi, sphi, cphi);
  sphi *= dtheta;
  cphi *= dtheta;
  
  switch (dv%4) {
    case 0:
      return b + ca*cphi + cb*sphi;  
    case 1:
      return b - ca*sphi + cb*cphi;  
    case 2:
      return b - ca*cphi - cb*sphi;  
    case 3:
      return b + ca*sphi - cb*cphi;  
  }
  
  // never reached
  return b + ca*cphi + cb*sphi;
}

void WingletBlend::apply()
{
  c0->setTrafoMatrix(RFrame::trafoMatrix());
  c0->apply();
  c1->setTrafoMatrix(RFrame::trafoMatrix());
  c1->apply();
  RFrame::clear();
  
  // must recompute angles and rotation axis after transform
  initRotation();
}
        
XmlElement WingletBlend::toXml(bool) const
{
  XmlElement xe("WingletBlend");
  if (c0 and c1) {
    xe.append(c0->toXml());
    xe.append(c1->toXml());
  }
  return xe;
}
    
void WingletBlend::fromXml(const XmlElement & xe)
{
  if (xe.name() != "WingletBlend")
    throw Error("WingletBlend: Incompatible XML representation: "+xe.name());
  
  XmlElement::const_iterator itr;
  itr = xe.begin();
  if (itr != xe.end()) {
    c0 = Curve::createFromXml(*itr);
    ++itr;
    assert(itr != xe.end());
    c1 = Curve::createFromXml(*itr);
    initRotation();
  } 
}

void WingletBlend::initGridPattern(Vector & up, Vector & vp) const
{
  up = cosine_pattern(21, 4*PI, 0.0, 0.8);
  vp = equi_pattern(7);
}
    
void WingletBlend::isSymmetric(bool & usym, bool & vsym) const
{
  usym = false;
  vsym = false;
}
