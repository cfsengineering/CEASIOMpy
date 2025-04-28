
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

#include "uvpolyline.h"

UvPolyline::UvPolyline(SurfacePtr psf, const PointList<2> &pts)
  : UvSplineCurve<1>(psf)
{
  UvSplineCurve<1>::interpolate(pts);
}

UvPolyline::UvPolyline(SurfacePtr psf, const Vector &u, const PointList<2> &pts)
  : UvSplineCurve<1>(psf)
{
  UvSplineCurve<1>::interpolate(u, pts);
}

UvPolyline::UvPolyline(SurfacePtr psf, const Vct2 &a, const Vct2 &b)
  : UvSplineCurve<1>(psf)
{
  interpolate(a, b);
}

UvPolyline *UvPolyline::clone() const
{
  return (new UvPolyline(*this));
}

void UvPolyline::interpolate(const Vct2 &a, const Vct2 &b)
{
  m_uvc.resize(2);
  m_uvc[0] = a;
  m_uvc[1] = b;

  Vector u(2);
  u[0] = 0.0;
  u[1] = 1.0;
  m_basis.init(1, u);
}

const Vector &UvPolyline::uBoundary(Real u, const Vector &v, bool flip)
{
  const size_t n = v.size();
  PointList2d pts(n);
  for (size_t i=0; i<n; ++i)
    pts[i] = Vct2(u, v[i]);
  if (flip)
    std::reverse(pts.begin(), pts.end());
  return interpolate(pts);
}

const Vector &UvPolyline::vBoundary(Real v, const Vector &u, bool flip)
{
  const size_t n = u.size();
  PointList2d pts(n);
  for (size_t i=0; i<n; ++i)
    pts[i] = Vct2(u[i], v);
  if (flip)
    std::reverse(pts.begin(), pts.end());
  return interpolate(pts);
}

AbstractUvCurvePair UvPolyline::split(Real t) const
{
  UvPolyline *plo = new UvPolyline(*this);
  UvPolyline *phi = new UvPolyline(m_psf);
  plo->splitSpline(t, *phi);

  AbstractUvCurvePair pair;
  pair.first.reset(plo);
  pair.second.reset(phi);

  return pair;
}

XmlElement UvPolyline::toXml(bool share) const
{
  XmlElement xe("UvPolyline");
  xe.append( m_basis.toXml(share) );

  XmlElement xcp("ControlPoints");
  xcp["count"] = str(m_uvc.size());
  xcp.asBinary( 2*m_uvc.size(), m_uvc.pointer(), share );
  xe.append( std::move(xcp) );

  return xe;
}

void UvPolyline::fromXml(const XmlElement &xe)
{
  XmlElement::const_iterator itr, last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "SplineBasis") {
      m_basis.fromXml(*itr);
    } else if (itr->name() == "ControlPoints") {
      m_uvc.resize( Int(itr->attribute("count")) );
      itr->fetch( 2*m_uvc.size(), m_uvc.pointer() );
    }
  }
}
