
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
 
#ifndef SURF_SUBSURFACE_H
#define SURF_SUBSURFACE_H

#include "forward.h"
#include "surface.h"
#include <genua/bounds.h>

/** Rectangular parametric region of another surface.
 *
 * \ingroup geometry
 */
class SubSurface : public Surface
{
public:

  /// construct from mapping
  SubSurface(const Surface & s, const BndRect & br);

  /// construct from mapping
  SubSurface(const Surface & s, const Vct2 & plo, const Vct2 & phi);

  /// construct from mapping
  SubSurface(SurfacePtr p, const Vct2 & plo, const Vct2 & phi);

  /// evaluate surface
  Vct3 eval(Real u, Real v) const {
    return psf->eval(umap(u), vmap(v));
  }

  /// compute derivative
  Vct3 derive(Real u, Real v, uint ku, uint kv) const {
    Real f = pow(du,Real(ku))*pow(dv,Real(kv));
    return f*psf->derive(umap(u), vmap(v), ku, kv);
  }

  /// compute point and tangent derivatives at (u,v), for efficiency
  void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const {
    psf->plane(umap(u), vmap(v), S, Su, Sv);
    Su *= du;
    Sv *= dv;
  }

  /// compute normal vector
  Vct3 normal(Real u, Real v) const {
    return psf->normal(umap(u), vmap(v));
  }

  /// find projection of pt on surface (needs a guess in q)
  bool project(const Vct3 & pt, Vct2 & q, Real tol=1e-6, Real dpmin=1e-6) const;

  /// coordinate transformation cannot be performed
  void apply() {assert(!"Cannot transform SubSurface.");}

  /// XML output
  XmlElement toXml(bool share=false) const;

  /// XML input
  void fromXml(const XmlElement & xe);

  /// generate a clone
  SubSurface *clone() const;

  /// map global points to local coordinates
  void toLocal(PointList<2> & pts) const;

  /// map local points to global coordinates
  void toGlobal(PointList<2> & pts) const;

protected:

  /// initialize mapping
  void init(const Vct2 & plo, const Vct2 & phi) {
    uo = plo[0];
    du = phi[0]-plo[0];
    vo = plo[1];
    dv = phi[1]-plo[1];
  }

  /// map u value
  Real umap(Real t) const {return uo + t*du;}

  /// map v value
  Real vmap(Real t) const {return vo + t*dv;}

private:

  /// surface to evaluate
  SurfacePtr psf;

  /// region limits
  Real uo, du, vo, dv;
};

#endif
