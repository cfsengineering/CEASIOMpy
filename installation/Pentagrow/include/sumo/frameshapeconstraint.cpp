/* ------------------------------------------------------------------------
 * file:       frameshapeconstraint.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Fit body section to special shape function 
 * ------------------------------------------------------------------------ */

#include "bodyframe.h"
#include "frameshapeconstraint.h"

using namespace std;

// ------------------------------- FrameShapeConstraint --------------------

ShapeConstraintPtr FrameShapeConstraint::createFromXml(const XmlElement & xe)
{
  ShapeConstraintPtr fcp;
  if (xe.name() == "EllipticShapeConstraint") {
    fcp = ShapeConstraintPtr(new EllipticShapeConstraint);
    fcp->fromXml(xe);
  } else if (xe.name() == "HuegelschaefferConstraint") {
    fcp = ShapeConstraintPtr(new HuegelschaefferConstraint);
    fcp->fromXml(xe);
  } else if (xe.name() == "CircularShapeConstraint") {
    fcp = ShapeConstraintPtr(new CircularShapeConstraint);
    fcp->fromXml(xe);
  } else if (xe.name() == "DoubleEllipticConstraint") {
    fcp = ShapeConstraintPtr(new DoubleEllipticConstraint);
    fcp->fromXml(xe);
  } else if (xe.name() == "IsikverenShapeConstraint") {
    fcp = ShapeConstraintPtr(new IsikverenShapeConstraint);
    fcp->fromXml(xe);
  }
  return fcp;
}

// ------------------------------- CircularShapeConstraint -----------------

void CircularShapeConstraint::constrain(BodyFrame & bf) const
{
  PointList<2> rpts(nip);
  Real sphi, cphi;
  for (int i=0; i<nip; ++i) {
    sincosine(i*PI/(nip-1), sphi, cphi);
    rpts[i][0] =  sphi;
    rpts[i][1] = -cphi;
  }
  bf.setFrameHeight( rds );
  bf.setFrameWidth( rds );
  bf.riPoints() = rpts;
  bf.interpolate();
}
    
XmlElement CircularShapeConstraint::toXml() const
{
  XmlElement xe("CircularShapeConstraint");
  xe["npoints"] = str(nip);
  xe["radius"] = str(rds);
  return xe;
}
    
void CircularShapeConstraint::fromXml(const XmlElement & xe)
{
  assert(xe.name() == "CircularShapeConstraint");
  nip = xe.attr2int("npoints", nip);
  rds = xe.attr2float("radius", rds);
}

// ------------------------------- EllipticShapeConstraint -----------------

void EllipticShapeConstraint::constrain(BodyFrame & bf) const
{
  Real rx = 1.0; // bf.frameWidth() / bf.frameHeight();
  Real ry = 1.0;
  PointList<2> rpts(nip);
  Real sphi, cphi, p = 2.0/xpn;
  for (int i=0; i<nip; ++i) {
    sincosine(i*PI/(nip-1), sphi, cphi);
    rpts[i][0] =  rx*pow(fabs(sphi), p)*sign(sphi);
    rpts[i][1] = -ry*pow(fabs(cphi), p)*sign(cphi);
  }
  bf.riPoints() = rpts;
  bf.interpolate();
}
    
XmlElement EllipticShapeConstraint::toXml() const
{
  XmlElement xe("EllipticShapeConstraint");
  xe["npoints"] = str(nip);
  xe["exponent"] = str(xpn);
  return xe;
}
    
void EllipticShapeConstraint::fromXml(const XmlElement & xe)
{
  assert(xe.name() == "EllipticShapeConstraint");
  nip = xe.attr2int("npoints", nip);
  xpn = xe.attr2float("exponent", xpn);
}

// ------------------------------- DoubleEllipticConstraint -----------------

void DoubleEllipticConstraint::constrain(BodyFrame & bf) const
{
  Real rx = 1.0; 
  Real ry = 1.0;
  PointList<2> rpts(nip);
  
  // absolute excentricity
  Real dry = ry*rxc;
  Real phi, sphi, cphi, dphi = PI/(nip-1);
  for (int i=0; i<nip; ++i) {
    phi = i*dphi;
    sincosine(phi, sphi, cphi);
    rpts[i][0] = rx*sphi;
    if (phi < 0.5*PI)
      rpts[i][1] = dry - (ry + dry) * cphi;    
    else
      rpts[i][1] = dry - (ry - dry) * cphi;
  }
  
  bf.riPoints() = rpts;
  bf.interpolate();
}
    
XmlElement DoubleEllipticConstraint::toXml() const
{
  XmlElement xe("DoubleEllipticConstraint");
  xe["npoints"] = str(nip);
  xe["offset"] = str(rxc);
  return xe;
}
    
void DoubleEllipticConstraint::fromXml(const XmlElement & xe)
{
  assert(xe.name() == "DoubleEllipticConstraint");
  nip = xe.attr2int("npoints", nip);
  rxc = xe.attr2float("offset", rxc);
}

// ------------------------------- HuegelschaefferConstraint-----------------

void HuegelschaefferConstraint::constrain(BodyFrame & bf) const
{
  Real rx = 1.0; // bf.frameWidth() / bf.frameHeight();
  Real ry = 1.0;
  PointList<2> rpts(nip);
  Real beta, sphi, cphi;
  for (int i=0; i<nip; ++i) {
    sincosine(PI - (i*PI/(nip-1)), sphi, cphi);
    beta = atan2(sphi, cphi-a);
    rpts[i][0] =  rx*sin(beta);
    rpts[i][1] =  ry*cphi;
  }
  bf.riPoints() = rpts;
  bf.interpolate();
}
    
XmlElement HuegelschaefferConstraint::toXml() const
{
  XmlElement xe("HuegelschaefferConstraint");
  xe["npoints"] = str(nip);
  xe["distortion"] = str(a);
  return xe;
}
    
void HuegelschaefferConstraint::fromXml(const XmlElement & xe)
{
  assert(xe.name() == "HuegelschaefferConstraint");
  nip = xe.attr2int("npoints", nip);
  a = xe.attr2float("distortion", a);
}

// ------------------------------- IsikverenShapeConstraint -----------------

void IsikverenShapeConstraint::constrain(BodyFrame & bf) const
{
  PointList<2> rpts(nip);
  
  Real t, phi, sp, cp, r;
  for (int i=0; i<nip; ++i) {
    t = Real(i) / (nip-1);
    phi = PI * ( t - 0.5 );
    sincosine(phi, sp, cp);
    r = a0 + a1*cos(2.*phi) + b1*sp;
    rpts[i][0] = r*cp;
    rpts[i][1] = zp + r*sp;
  }
  
  bf.setFrameHeight( 1.0 );
  bf.setFrameWidth( 1.0 );
  bf.riPoints() = rpts;
  bf.normalize();
  bf.interpolate();
}
    
XmlElement IsikverenShapeConstraint::toXml() const
{
  XmlElement xe("IsikverenShapeConstraint");
  xe["npoints"] = str(nip);
  xe["zp"] = str(zp);
  xe["a0"] = str(a0);
  xe["a1"] = str(a1);
  xe["b1"] = str(b1);
  return xe;
}
    
void IsikverenShapeConstraint::fromXml(const XmlElement & xe)
{
  assert(xe.name() == "IsikverenShapeConstraint");
  nip = xe.attr2int("npoints", nip);
  zp = xe.attr2float("zp", zp);
  a0 = xe.attr2float("a0", a0);
  a1 = xe.attr2float("a1", a1);
  b1 = xe.attr2float("b1", b1);
}


