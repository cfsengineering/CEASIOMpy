
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

#ifndef SURF_CYLINDER_H
#define SURF_CYLINDER_H

#include "surface.h"

/** Cylinder surface.

  As might be expected, this implements the Surface interface for a simple
  spherical cylinder.

  \ingroup geometry
  */
class Cylinder : public Surface
{
public:

  /// empty initialization
  Cylinder(const std::string & s) : Surface(s) {}

  /// construct with two points and a vector
  Cylinder(const std::string & name, const Vct3 & pbot, const Vct3 & ptop, const Vct3 & vrad);

  /// evaluate at (u,v) - u is circumferential and v is axial coordinate
  Vct3 eval(Real u, Real v) const;

  /// compute derivatives
  Vct3 derive(Real u, Real v, uint du, uint dv) const;

  /// transformation
  void apply();

  /// XML output
  XmlElement toXml(bool share=false) const;

  /// XML input
  void fromXml(const XmlElement & xe);

  /// generate a clone
  Cylinder *clone() const {return new Cylinder(*this);}

  // protected:

  /// return an initial discretization pattern to start with
  void initGridPattern(Vector & up, Vector & vp) const;

  /// return if surface is symmetric in u- or v-direction
  void isSymmetric(bool & usym, bool & vsym) const;

private:

  /// bottom, top points and radius
  Vct3 bot, top, r1, r2;
};

#endif
