
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
 
#ifndef SURF_RATIONALSPLINESURFACE_H
#define SURF_RATIONALSPLINESURFACE_H

#include "surface.h"
#include <genua/splinebasis.h>

class AbstractCurve;

/** NURBS surface.
 *
 * This is the most general representation of NURBS surfaces, with support for
 * runtime variable order and rational forms (i.e. non-unit weight values). This
 * flexibility also means that the evaluation and derivation is more expensive
 * than for simpler fixed-order objects.
 *
 * \ingroup geometry
 * \sa PolySplineSurf, RationalSplineCurve
 */
class RationalSplineSurf : public Surface
{
public:

  /// construct named spline surface
  RationalSplineSurf(const std::string & s = "") : Surface(s),
    ukfront(0.0), ukback(1.0), vkfront(0.0), vkback(1.0),
    ustart(0.0), uend(1.0), vstart(0.0), vend(1.0) {}

  /// evaluation interface
  Vct3 eval(Real u, Real v) const;

  /// derive at (u,v)
  Vct3 derive(Real u, Real v, uint du, uint dv) const;

  /// optimization for first derivatives
  void plane(Real u, Real v, Vct3 &S, Vct3 &Su, Vct3 &Sv) const;

  /// coordinate transformation
  void apply();

  /// overloaded grid pattern initialization
  void initGridPattern(Vector &up, Vector &vp) const;

  /// compute statistics
  void dimStats(DimStat &stat) const;

  /// utility for testing : create unit cylinder
  void createCylinder();

  /// XML output
  XmlElement toXml(bool share=false) const;

  /// XML input
  void fromXml(const XmlElement & xe);

  /// extract from IGES entity 128
  bool fromIges(const IgesFile & file, const IgesDirEntry & entry);

  /// append to IGES file and return the directory entry index, if implemented
  int toIges(IgesFile & file, int tfi = 0) const;

  /// generate a clone
  Surface *clone() const;

  /// transform a parameter-space curve read from IGES
  void knotScale(AbstractCurve & c) const;

protected:

  /// map u parameter to internal range
  Real umap(Real ux) const {
    return clamp(ustart + ux*(uend-ustart), 0.0, 1.0);
  }

  /// map v parameter to internal range
  Real vmap(Real vx) const {
    return clamp(vstart + vx*(vend-vstart), 0.0, 1.0);
  }

  /// first derivatives in mapped domain
  void mappedPlane(Real u, Real v, Vct3 &S, Vct3 &Su, Vct3 &Sv) const;

protected:

  /// spline bases in two directions
  SplineBasis ub, vb;

  /// control point grid
  PointGrid<4> cp;

  /// original range of knot values
  Real ukfront, ukback, vkfront, vkback;

  /// parameter region
  Real ustart, uend, vstart, vend;
};

#endif // SURF_RATIONALSPLINESURFACE_H
