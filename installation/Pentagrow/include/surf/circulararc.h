
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
 
#ifndef SURF_CIRCULARARC_H
#define SURF_CIRCULARARC_H

#include "abstractcurve.h"
#include <genua/point.h>

/** Exactly represented circular arc.
 *
 * An AbstractCurve which can represent a circular arc withut approximation.
 * This is mainly used in the import of CAD geometry from IGES.
 *
 * \ingroup geometry
 */
class CircularArc : public AbstractCurve
{
public:

  /// create undefined curve object
  CircularArc(const std::string & s = "") : AbstractCurve(s) {}

  /// create a clone
  virtual CircularArc *clone() const;

  /// evaluate spline curve
  virtual Vct3 eval(Real t) const;

  /// compute kth derivative
  virtual Vct3 derive(Real t, uint k) const;

  /// apply hard transformation
  virtual void apply();

  /// compute point and first derivative in one sweep
  virtual void tgline(Real t, Vct3 & c, Vct3 & dc) const;

  /// discretization
  virtual void initGrid(Vector &t) const;

  /// XML output
  virtual XmlElement toXml(bool share = false) const;

  /// XML input
  virtual void fromXml(const XmlElement &xe);

  /// write curve to iges file
  virtual int toIges(IgesFile &file, int tfi = 0) const;

  /// extract curve from iges file
  virtual bool fromIges(const IgesFile &file, const IgesDirEntry &entry);

protected:

  /// transformation matrix of circle plane from definition space
  Mtx44 m_cpltrafo;

  /// center point and z-offset of the plane
  Vct3 m_center;

  /// radius, start and end angle
  Real m_radius, m_tstart, m_tend;
};

#endif // CIRCULARARC_H
