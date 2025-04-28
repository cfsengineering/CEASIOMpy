
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
 
#include "subsurface.h"

SubSurface::SubSurface(const Surface &s, const BndRect &br)
  : psf( SurfacePtr(s.clone()) ) {init(br.lower(),br.upper());}

SubSurface::SubSurface(const Surface &s, const Vct2 &plo, const Vct2 &phi)
  : psf( SurfacePtr(s.clone()) ) {init(plo,phi);}

SubSurface::SubSurface(SurfacePtr p, const Vct2 &plo, const Vct2 &phi)
  : psf(p) {init(plo,phi);}

bool SubSurface::project(const Vct3 & pt, Vct2 & q, Real tol, Real dpmin) const
{
  Vct2 qm;
  qm[0] = uo + q[0]*du;
  qm[1] = vo + q[1]*dv;
  bool stat = psf->project(pt, qm, tol, dpmin);
  q[0] = (qm[0] - uo)/du;
  q[1] = (qm[1] - vo)/dv;
  return stat;
}

XmlElement SubSurface::toXml(bool) const
{
  assert(!"Internal class SubSurface does not support i/o");
  return XmlElement();
}

void SubSurface::fromXml(const XmlElement &)
{
  assert(!"Internal class SubSurface does not support i/o");
}

SubSurface *SubSurface::clone() const
{
  SubSurface *cpy = new SubSurface( SurfacePtr(psf->clone()),
                                    vct(uo,vo), vct(uo+du,vo+dv));
  return cpy;
}

void SubSurface::toLocal(PointList<2> & pts) const
{
  const uint n(pts.size());
  for (uint i=0; i<n; ++i) {
    Vct2 & p(pts[i]);
    p[0] = (p[0] - uo)/du;
    p[1] = (p[1] - vo)/dv;
  }
}

void SubSurface::toGlobal(PointList<2> & pts) const
{
  const uint n(pts.size());
  for (uint i=0; i<n; ++i) {
    Vct2 & p(pts[i]);
    p[0] = uo + du*p[0];
    p[1] = vo + dv*p[1];
  }
}

