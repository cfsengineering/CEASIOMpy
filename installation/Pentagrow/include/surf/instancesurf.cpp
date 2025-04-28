
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
 
#include "instancesurf.h"
#include <genua/transformation.h>

void InstanceSurf::transform(const Trafo3d &t)
{
  t.matrix(m_tfm);
}

void InstanceSurf::transform(const Mtx44 &t)
{
  m_tfm = t;
}

void InstanceSurf::uswap(bool flag)
{
  if (flag) {
    m_uo =  1.0;
    m_du = -1.0;
  } else {
    m_uo =  0.0;
    m_du =  1.0;
  }
}

void InstanceSurf::vswap(bool flag)
{
  if (flag) {
    m_vo =  1.0;
    m_dv = -1.0;
  } else {
    m_vo =  0.0;
    m_dv =  1.0;
  }
}

Vct3 InstanceSurf::eval(Real u, Real v) const
{
  assert(m_parent != nullptr);
  this->map(u, v);
  Vct3 p = m_parent->eval(u,v);
  Trafo3d::transformPoint(m_tfm, p);
  return p;
}

Vct3 InstanceSurf::derive(Real u, Real v, uint ku, uint kv) const
{
  assert(m_parent != nullptr);
  this->map(u, v);
  Real f = std::pow(m_du, Real(ku)) * std::pow(m_dv, Real(kv));

  Vct3 p = m_parent->derive(u, v, ku, kv);
  Trafo3d::transformPoint(m_tfm, p);

  return f*p;
}

void InstanceSurf::plane(Real u, Real v, Vct3 &S, Vct3 &Su, Vct3 &Sv) const
{
  assert(m_parent != nullptr);
  this->map(u, v);
  m_parent->plane(u, v, S, Su, Sv);
  Trafo3d::transformPoint(m_tfm, S);
  Trafo3d::transformPoint(m_tfm, Su);
  Trafo3d::transformPoint(m_tfm, Sv);

  Su *= m_du;
  Sv *= m_dv;
}

void InstanceSurf::apply()
{
  m_tfm = RFrame::trafoMatrix() * m_tfm;
  RFrame::clear();
}

XmlElement InstanceSurf::toXml(bool share) const
{
  XmlElement xe("InstanceSurf");
  xe["parent_id"] = str(m_parent->objid());
  if (m_uo != 0)
    xe["origin_u"] = str(m_uo);
  if (m_vo != 0)
    xe["origin_v"] = str(m_vo);
  if (m_du != 1)
    xe["scale_u"] = str(m_du);
  if (m_dv != 1)
    xe["scale_v"] = str(m_dv);
  xe.asBinary(16, m_tfm.pointer(), share);
  return xe;
}

void InstanceSurf::fromXml(const XmlElement &xe)
{
  m_parent.reset();
  fromString(xe.attribute("parent_id"), m_parent_id);
  m_uo = xe.attr2float("origin_u", 0.0);
  m_vo = xe.attr2float("origin_v", 0.0);
  m_du = xe.attr2float("scale_u", 1.0);
  m_dv = xe.attr2float("scale_v", 1.0);
  xe.fetch(16, m_tfm.pointer());
}

InstanceSurf *InstanceSurf::clone() const
{
  return (new InstanceSurf(*this));
}
