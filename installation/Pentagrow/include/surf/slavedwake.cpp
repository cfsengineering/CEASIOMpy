
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

#include "slavedwake.h"
#include "beziersegment.h"
#include "curve.h"
#include "linearsurf.h"
#include "uvpolyline.h"
#include <genua/dbprint.h>

void SlavedWake::initRuledBezier(SurfacePtr parent,
                                 const Vct3 &edgeDistance,
                                 const Vct3 &farTangent,
                                 Real compression)
{
  Real wlen = norm(edgeDistance);

  CurvePtr c0 = boost::make_shared<Curve>("WakeBoundary0");
  CurvePtr c1 = boost::make_shared<Curve>("WakeBoundary1");

  // boundary at u = 0.0
  Vct3 secp[3], secn;
  PointList3d pts(2), tng(2);
  Vector u{0.0, 1.0};
  pts[0]  = parent->eval(0.0, 0.0);
  pts[1]  = pts[0] + edgeDistance;
  tng[0]  = -parent->derive(0.0, 0.0, 1, 0) + parent->derive(1.0, 0.0, 1, 0);

  // project initial tangent into the plane of the surface v-section curve
  secp[0] = pts[0];
  secp[1] = parent->eval(1./3., 0.0);
  secp[2] = parent->eval(2./3., 0.0);
  secn = cross(secp[1] - secp[0], secp[2] - secp[0]).normalized();
  tng[0] -= dot(secn, tng[0]) * secn;

  tng[0] *= 2*compression*wlen / norm(tng[0]);
  tng[1]  = farTangent * ( 2.0*(1 - compression)*wlen / norm(farTangent) );
  c0->interpolate(pts, tng, u);

  // boundary at u = 1.0
  pts[0]  = parent->eval(0.0, 1.0);
  pts[1]  = pts[0] + edgeDistance;
  tng[0]  = -parent->derive(0.0, 1.0, 1, 0) + parent->derive(1.0, 1.0, 1, 0);
  secp[0] = pts[0];
  secp[1] = parent->eval(1./3., 1.0);
  secp[2] = parent->eval(2./3., 1.0);
  secn = cross(secp[1] - secp[0], secp[2] - secp[0]).normalized();
  tng[0] -= dot(secn, tng[0]) * secn;
  tng[0] *= 2*compression*wlen / norm(tng[0]);
  tng[1]  = farTangent * ( 2.0*(1 - compression)*wlen / norm(farTangent) );
  c1->interpolate(pts, tng, u);
  this->initRuled(parent, c0, c1);
}

void SlavedWake::initRuled(SurfacePtr parent, CurvePtr c0, CurvePtr c1)
{
  LinearSurfPtr psf = boost::make_shared<LinearSurf>("WakeSegment");
  psf->init(c0, c1);
  this->init(parent, psf);
}

Vct3 SlavedWake::derive(Real u, Real v, uint du, uint dv) const
{
  if (du == 0 and dv == 0)
    return eval(u,v);

  if (m_wplus == nullptr) {

    // simple linear extension
    if (dv == 0) {
      if (du == 1)
        return m_udr;
    } else if (du == 0) {
      return m_parent->derive(0.0, v, 0, dv);
    }

    return Vct3(0,0,0);

  } else {

    if (dv == 0) {
      return m_wplus->derive(u, v, du, 0);
    } else {
      Vct3 dshift = m_parent->derive(0.0, v, 0, dv)
          - m_wplus->derive(0.0, v, 0, dv);
      return m_wplus->derive(u, v, du, dv) + dshift;
    }

  }

  return Vct3(0.0, 0.0, 0.0);
}

void SlavedWake::plane(Real u, Real v, Vct3 &S, Vct3 &Su, Vct3 &Sv) const
{
  if (m_wplus == nullptr) {
    S = m_parent->eval(0.0, v) + u*m_udr;
    Su = m_udr;
    Sv = m_parent->derive(0.0, v, 0, 1);
  } else {

    Vct3 S1, S1v, dmy;
    m_parent->plane(0.0, v, S1, dmy, S1v);

    Vct3 S2, S2v;
    m_wplus->plane(0.0, v, S2, dmy, S2v);

    Vct3 S3, S3v;
    m_wplus->plane(u, v, S3, Su, S3v);

    S = S3 + (S1 - S2);
    Sv = S3v + (S1v - S2v);
  }
}

Vct3 SlavedWake::normal(Real u, Real v) const
{
  if (m_wplus == nullptr) {
    const Vct3 & Su(m_udr);
    Vct3 Sv( m_parent->derive(0.0, v, 0, 1) );
    return cross(Su, Sv);
  } else {
    Vct3 S, Su, Sv;
    this->plane(u, v, S, Su, Sv);
    return cross(Su, Sv);
  }
}

CurvePtr SlavedWake::guideCurve(SurfacePtr body, const Vct2 &uvi,
                                const Vct3 &panchor,
                                const Vct3 &edgeDistance,
                                const Vct3 &farTangent,
                                Real vend)
{
  // assumes body is symmetrical
  const Real u1 = uvi[0];
  const Real u2 = 1.0 - u1;

  // just use enough equidistant points for the part of the curve that is
  // inside the body
  const int nip = 64;
  const int nep = 32;
  const Real dt = 1.0 / (nip-1);
  const Real dv = (vend - uvi[1]) * dt;
  PointList3d pts(nip+nep);
  Vct3 pshift = panchor - 0.5*(body->eval(u1, uvi[1]) + body->eval(u2, uvi[1]));
  pts[0] = panchor;
  for (int i=1; i<nip; ++i) {
    Real ts = perlin_step(sq(1.0 - i*dt), 0.0, 1.0);
    Real v = uvi[1] + dv*i;
    pts[i] = 0.5*(body->eval(u1, v) + body->eval(u2, v)) + ts*pshift;
  }

  // to construct the part beyond the body, use a cubic segment which connects
  // with continuous slope to the end of the internal curve
  const Vct3 &p1 = pts[nip-1];
  Vct3 t1 = body->derive(u1, vend, 0, 1) + body->derive(u2, vend, 0, 1);

  Vct3 p2 = pts[0] + edgeDistance;
  Vct3 t2 = farTangent;

  // scale tangent lengths
  const Real clen = norm(p2 - p1);
  const Real compression = 0.5;
  t1 *= 2.0*compression*clen / norm(t1);
  t2 *= 2.0*(1.0 - compression)*clen / norm(t2);

  BezierSegment bz(p1, t1, p2, t2);
  for (int i=0; i<nep; ++i)
    pts[nip+i] = bz.eval( Real(i) / (nep-1) );

  Vector up;
  CurvePtr cp = boost::make_shared<Curve>("WakeGuideCurve");
  cp->interpolate(pts, up);
  return cp;
}

Vct3 SlavedWake::findIntersection(SurfacePtr wing, SurfacePtr body,
                                  Real vlo, Real vhi)
{
  // construct a curve along the trailing edge upper side
  UvPolyline tedge(wing, Vct2(0.0,vlo), Vct2(0.0,vhi));

  // solve the intersection problem,
  // start with tp < 0 to indicate initialization by search method is desired
  Vct2 uvp;
  Real tp(-1.0);
  body->intersect(tedge, uvp, tp);  // tp is actually tedge(tp), mind vlo/vhi
  return Vct3(uvp[0], uvp[1], (1-tp)*vlo + tp*vhi);
}

CurvePtr SlavedWake::cubicGuide(SurfacePtr parent, Real v,
                                const Vct3 &edgeDistance,
                                const Vct3 &farTangent, Real compression)
{
  Real wlen = norm(edgeDistance);
  Vct3 secp[3], secn;
  Vct3 pts[2], tng[2];
  pts[0]  = parent->eval(0.0, v);
  pts[1]  = pts[0] + edgeDistance;
  tng[0]  = -parent->derive(0.0, v, 1, 0) + parent->derive(1.0, v, 1, 0);

  // project initial tangent into the plane of the surface v-section curve
  secp[0] = pts[0];
  secp[1] = parent->eval(1./3., v);
  secp[2] = parent->eval(2./3., v);
  secn = cross(secp[1] - secp[0], secp[2] - secp[0]).normalized();
  tng[0] -= dot(secn, tng[0]) * secn;

  tng[0] *= 2*compression*wlen / norm(tng[0]);
  tng[1]  = farTangent * ( 2.0*(1 - compression)*wlen / norm(farTangent) );

  CurvePtr cp = boost::make_shared<Curve>("WakeBoundaryAt"+std::to_string(v));
  cp->bezier(pts[0], tng[0], pts[1], tng[1]);
  return cp;
}

void SlavedWake::apply()
{
  assert(!"Cannot transform slaved wake surface.");
}

XmlElement SlavedWake::toXml(bool) const
{
  assert(!"XML i/o not implemented.");
  return XmlElement("SlavedWake");
}

void SlavedWake::fromXml(const XmlElement &)
{
  assert(!"XML i/o not implemented.");
}

int SlavedWake::toIges(IgesFile &igfile, int tfi) const
{
  if (m_wplus != nullptr)
    return m_wplus->toIges(igfile, tfi);
  return 0;
}


