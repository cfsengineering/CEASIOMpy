
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
 
#include "circulararc.h"
#include "iges100.h"
#include "iges124.h"
#include "igesfile.h"
#include <genua/algo.h>
#include <genua/pattern.h>
#include <genua/xmlelement.h>
#include <genua/transformation.h>

CircularArc *CircularArc::clone() const
{
  return new CircularArc(*this);
}

Vct3 CircularArc::eval(Real t) const
{
  Real sphi, cphi, phi = m_tstart + t*(m_tend - m_tstart);
  sincosine(phi, sphi, cphi);

  Vct3 p(m_center);
  p[0] += m_radius*cphi;
  p[1] += m_radius*sphi;

  Trafo3d::transformPoint(m_cpltrafo, p);
  return p;
}

void CircularArc::tgline(Real t, Vct3 &c, Vct3 &dc) const
{
  Real sphi, cphi, phi = m_tstart + t*(m_tend - m_tstart);
  sincosine(phi, sphi, cphi);

  Vct3 p(m_center);
  p[0] += m_radius*cphi;
  p[1] += m_radius*sphi;

  Vct2 pd;
  pd[0] = -m_radius*sphi;
  pd[1] =  m_radius*cphi;

  // Trafo3d::transformPoint(m_cpltrafo, p);
  // Trafo3d::transformDirection(m_cpltrafo, pd);

  for (int k=0; k<3; ++k) {
    c[k] = m_cpltrafo(k,0)*p[0] + m_cpltrafo(k,1)*p[1]
        + m_cpltrafo(k,2)*p[2] + m_cpltrafo(k,3);
    dc[k] = m_cpltrafo(k,0)*pd[0] + m_cpltrafo(k,1)*pd[1];
  }

  // chain rule, dc is derivative wrt to t not phi
  dc *= (m_tend - m_tstart);
}

Vct3 CircularArc::derive(Real t, uint k) const
{
  assert(k < 4);
  if (k == 0)
    return eval(t);

  Real sphi, cphi, phi = m_tstart + t*(m_tend - m_tstart);
  sincosine(phi, sphi, cphi);

  Vct2 pd;

  if (k == 1) {
    pd[0] = -m_radius*sphi;
    pd[1] =  m_radius*cphi;
  } else if (k == 2) {
    pd[0] = -m_radius*cphi;
    pd[1] = -m_radius*sphi;
  } else if (k == 3) {
    pd[0] =  m_radius*sphi;
    pd[1] = -m_radius*cphi;
  }

  Vct3 dc;
  for (int j=0; j<3; ++j)
    dc[j] = m_cpltrafo(j,0)*pd[0] + m_cpltrafo(j,1)*pd[1];
  dc *= pow(m_tend - m_tstart, Real(k));
  return dc;
}

void CircularArc::apply()
{
  m_cpltrafo = this->trafoMatrix() * m_cpltrafo;
  RFrame::clear();
}

void CircularArc::initGrid(Vector &t) const
{
  t = equi_pattern(32);
}

XmlElement CircularArc::toXml(bool share) const
{
  XmlElement xe("CircularArc");
  xe["name"] = name();
  xe["center"] = str(m_center);
  xe["radius"] = str(m_radius);
  xe["start_angle"] = str(m_tstart);
  xe["end_angle"] = str(m_tend);
  if (m_cpltrafo != Mtx44::identity())
    xe.append("CplTrafo", 16, m_cpltrafo.pointer(), share);
  return xe;
}

void CircularArc::fromXml(const XmlElement & xe)
{
  if (xe.hasAttribute("name"))
    rename( xe.attribute("name") );
  fromString( xe.attribute("center"), m_center );
  fromString( xe.attribute("radius"), m_radius );
  fromString( xe.attribute("start_angle"), m_tstart );
  fromString( xe.attribute("end_angle"), m_tend );
  XmlElement::const_iterator itr = xe.findChild("CplTrafo");
  if (itr != xe.end())
    itr->fetch(16, m_cpltrafo.pointer());
  else
    m_cpltrafo = Mtx44::identity();
}

int CircularArc::toIges(IgesFile & file, int tfi) const
{
  // transformation
  IgesTrafoMatrix itrafo;
  for (int k=0; k<3; ++k) {
    for (int j=0; j<3; ++j)
      itrafo.rotation(k,j) = m_cpltrafo(k,j);
    itrafo.translation(k) = m_cpltrafo(k,3);
  }
  itrafo.trafoMatrix(tfi);
  int itf = itrafo.append(file);

  IgesCircularArc igs;
  igs.trafoMatrix(itf);
  igs.center = m_center;

  Real sphi, cphi;
  sincosine(m_tstart, sphi, cphi);
  igs.startPoint[0] = m_center[0] + m_radius*cphi;
  igs.startPoint[1] = m_center[1] + m_radius*sphi;

  sincosine(m_tend, sphi, cphi);
  igs.endPoint[0] = m_center[0] + m_radius*cphi;
  igs.endPoint[1] = m_center[1] + m_radius*sphi;

  return igs.append(file);
}

bool CircularArc::fromIges(const IgesFile & file, const IgesDirEntry & entry)
{
  if (entry.etype != 100)
    return false;

  // fetch parent entry
  IgesEntityPtr eptr = file.createEntity(entry);
  IgesCircularArc cce;
  if (not IgesEntity::as(eptr, cce))
    return false;

  m_center = cce.center;

  Vct2 rstart( cce.startPoint[0] - cce.center[0],
      cce.startPoint[1] - cce.center[1] );

  Vct2 rend( cce.endPoint[0] - cce.center[0],
      cce.endPoint[1] - cce.center[1] );

  m_tstart = std::atan2(rstart[1], rstart[0]);
  m_tend = std::atan2(rend[1], rend[0]);
  m_radius = std::sqrt(0.5*(sq(rstart) + sq(rend)));

  IgesTrafoMatrix itf;
  int tfi = entry.trafm;
  if ((tfi != 0) and file.createEntity(tfi, itf)) {
    itf.toMatrix(m_cpltrafo);
    IgesDirEntry tparent;
    file.dirEntry(tfi, tparent);
    if (tparent.valid())
      setIgesTransform(file, tparent);
  }

  // extract name tag if present
  setIgesName(file, cce);

  return true;
}
