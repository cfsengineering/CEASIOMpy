
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
 
#ifndef SURF_INSTANCESURF_H
#define SURF_INSTANCESURF_H

#include "forward.h"
#include "surface.h"
#include <genua/smatrix.h>
#include <genua/transformation.h>

/** Associative copy of another surface.
 *
 *
 * \ingroup geometry
 * \sa Surface, TopoPart
 */
class InstanceSurf : public Surface
{
public:

  /// undefined instance
  InstanceSurf() {}

  /// create instance from parent and transformation matrix
  InstanceSurf(SurfacePtr parent, const Mtx44 &tfm = Mtx44::identity())
    : Surface("InstanceOf"+parent->name()),
      m_parent(parent), m_tfm(tfm), m_uo(0), m_du(1), m_vo(0), m_dv(1),
      m_parent_id(0) {}

  /// change instance transformation
  void transform(const Trafo3d &t);

  /// change instance transformation
  void transform(const Mtx44 &t);

  /// switch u-parametrization direction
  void uswap(bool flag);

  /// switch v-parametrization direction
  void vswap(bool flag);

  /// define a general mapping of the u-coordinate
  void mapU(Real offset, Real scale) { m_uo = offset; m_du = scale; }

  /// define a general mapping of the v-coordinate
  void mapV(Real offset, Real scale) { m_vo = offset; m_dv = scale; }

  /// evaluate surface
  Vct3 eval(Real u, Real v) const;

  /// compute derivative
  Vct3 derive(Real u, Real v, uint ku, uint kv) const;

  /// compute point and tangent derivatives at (u,v), for efficiency
  void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const;

  /// coordinate transformation
  void apply();

  /// XML output
  XmlElement toXml(bool share=false) const;

  /// XML input
  void fromXml(const XmlElement & xe);

  /// generate a clone
  InstanceSurf *clone() const;

private:

  /// map (u,v) coordinate to internal space
  void map(Real &u, Real &v) const {
    u = m_uo + u*m_du;
    v = m_vo + v*m_dv;
  }

private:

  /// original, master surface
  SurfacePtr m_parent;

  /// transformation matrix
  Mtx44 m_tfm;

  /// linear transformation of u-parameter
  Real m_uo, m_du;

  /// linear transformation of v-parameter
  Real m_vo, m_dv;

  /// for recovery from xml
  uint m_parent_id;
};

#endif // INSTANCESURF_H
