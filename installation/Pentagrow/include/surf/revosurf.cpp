
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
 
#include <genua/transformation.h>
#include "iges120.h"
#include "iges110.h"
#include "igesfile.h"
#include "revosurf.h"

Vct3 RevoSurf::eval(Real u, Real v) const
{
  assert(genCurve);

  // u-direction is the angular direction
  Real phi = (1.0-u)*startAngle + u*termAngle;

  // v-direction is the curve parameter
  Vct3 cp00 = genCurve->eval(v);
  Vct3 cp90 = rot90*cp00;

  Real sphi, cphi;
  sincosine(phi, sphi, cphi);
  return cphi*cp00 + sphi*cp90;
}

Vct3 RevoSurf::derive(Real u, Real v, uint du, uint dv) const
{
  if (du == 0 and dv == 0) {
    return eval(u,v);
  } else {
    assert(genCurve);
    Real phi = (1.0-u)*startAngle + u*termAngle;
    Real dpu = termAngle - startAngle;
    Real sp, cp;
    sincosine(phi, sp, cp);
    if (dv == 0) {
      Vct3 cp00 = genCurve->eval(v);
      Vct3 cp90 = rot90*cp00;
      if (du == 1)
        return dpu*( -sp*cp00 + cp*cp90 );
      else if (du == 2)
        return sq(dpu)*( -cp*cp00 - sp*cp90 );
      else
        throw Error("RevoSurf: Higher derivatives not implemented.");
    } else if (du == 0) {
      Vct3 cp00 = genCurve->derive(v, dv);
      Vct3 cp90 = rot90*cp00;
      return cp*cp00 + sp*cp90;
    } else {
      Vct3 cp00 = genCurve->derive(v, dv);
      Vct3 cp90 = rot90*cp00;
      if (du == 1)
        return dpu*( -sp*cp00 + cp*cp90 );
      else if (du == 2)
        return sq(dpu)*( -cp*cp00 - sp*cp90 );
      else
        throw Error("RevoSurf: Higher derivatives not implemented.");
    }
  }
}

void RevoSurf::plane(Real u, Real v, Vct3 &S, Vct3 &Su, Vct3 &Sv) const
{
  assert(genCurve);
  Real phi = (1.0-u)*startAngle + u*termAngle;
  Real dpu = termAngle - startAngle;
  Real sp, cp;
  sincosine(phi, sp, cp);

  Vct3 C, Cv;
  genCurve->tgline(v, C, Cv);

  Vct3 cp00 = C;
  Vct3 cp90 = rot90*cp00;

  S = cp*cp00 + sp*cp90;
  Su = dpu*( -sp*cp00 + cp*cp90 );

  cp00 = Cv;
  cp90 = rot90*cp00;
  Sv = cp*cp00 + sp*cp90;
}

int RevoSurf::toIges(IgesFile & file, int tfi) const
{
  // entity 120
  IgesRevolutionSurface irs;

  // axis of rotation
  IgesLineEntity iln;
  iln.setup( pax1.pointer(), pax2.pointer() );
  irs.pAxis = iln.append(file);

  // generatrix curve
  irs.pGenCurve = genCurve->toIges(file);

  // parameter
  irs.sa = startAngle;
  irs.ta = termAngle;

  irs.trafoMatrix(tfi);
  return irs.append(file);
}

bool RevoSurf::fromIges(const IgesFile & file, const IgesDirEntry & dir)
{
  if (dir.etype != 120)
    return false;

  IgesEntityPtr eptr = file.createEntity(dir);
  IgesRevolutionSurface irs;
  if (not IgesEntity::as(eptr, irs))
    return false;

  // extract generatrix curve
  IgesDirEntry dirCurve;
  file.dirEntry(irs.pGenCurve, dirCurve);

  genCurve.reset(new Curve("Generatrix"));
  if (not genCurve->fromIges(file, dirCurve))
    return false;

  // extract axis of rotation
  IgesLineEntity iln;
  eptr = file.createEntity(irs.pAxis);
  if (not IgesEntity::as(eptr, iln))
    return false;

  pax1 = Vct3( iln.point1() );
  pax2 = Vct3( iln.point2() );

  startAngle = irs.sa;
  termAngle = irs.ta;

  setIgesName(file, irs);
  applyIgesTrafo(file, dir);

  return true;
}

void RevoSurf::apply()
{
  pax1 = RFrame::forward(pax1);
  pax2 = RFrame::forward(pax2);
  genCurve->setTrafoMatrix( RFrame::trafoMatrix() );
  genCurve->apply();
  RFrame::clear();
}

RevoSurf *RevoSurf::clone() const
{
  return (new RevoSurf(*this));
}

void RevoSurf::buildRotation()
{
  Vct3 axis = (pax2 - pax1).normalized();
  Trafo3d::axis2matrix(0.5*PI, axis, rot90);
}

XmlElement RevoSurf::toXml(bool) const
{
  XmlElement xe("RevoSurf");
  xe["name"] = name();
  if (startAngle != 0)
    xe["startAngle"] = str(startAngle);
  if (termAngle != 2*PI)
    xe["termAngle"] = str(termAngle);
  xe["axisPoint1"] = str(pax1);
  xe["axisPoint2"] = str(pax2);
  xe.append( genCurve->toXml() );

  return xe;
}

void RevoSurf::fromXml(const XmlElement &xe)
{
  startAngle = xe.attr2float("startAngle", 0.0);
  termAngle = xe.attr2float("termAngle", 2*PI);

  fromString( xe.attribute("axisPoint1"), pax1 );
  fromString( xe.attribute("axisPoint2"), pax2 );
  buildRotation();

  XmlElement::const_iterator itr = xe.findChild("Curve");
  if (itr != xe.end())
    genCurve->fromXml(*itr);
  else
    throw Error("RevoSurf::fromXml: No generatrix found in XML rep.");
}
