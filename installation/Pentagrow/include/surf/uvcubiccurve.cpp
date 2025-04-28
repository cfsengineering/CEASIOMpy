
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
 #include "uvcubiccurve.h"

UvCubicCurve *UvCubicCurve::clone() const
{
  return (new UvCubicCurve(*this));
}


AbstractUvCurvePair UvCubicCurve::split(Real t) const
{
  UvCubicCurve *plo = new UvCubicCurve(*this);
  UvCubicCurve *phi = new UvCubicCurve(m_psf);
  plo->splitSpline(t, *phi);

  AbstractUvCurvePair pair;
  pair.first.reset(plo);
  pair.second.reset(phi);

  return pair;
}

XmlElement UvCubicCurve::toXml(bool share) const
{
  XmlElement xe("UvCubicCurve");
  xe.append( m_basis.toXml(share) );

  XmlElement xcp("ControlPoints");
  xcp["count"] = str(m_uvc.size());
  xcp.asBinary( 2*m_uvc.size(), m_uvc.pointer(), share );
  xe.append( std::move(xcp) );

  return xe;
}

void UvCubicCurve::fromXml(const XmlElement &xe)
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

