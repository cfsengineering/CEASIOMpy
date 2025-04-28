
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
 
#ifndef GENUA_ATMOSPHERE_H
#define GENUA_ATMOSPHERE_H

#include "defines.h"

/** Compute physical properties of the Standard Atmosphere.
 *
 * On construction, an object of this class computes atmospheric properties
 * for the altitude and temperature offset passed in the constructor. The
 * data members are all public.
 *
 *  \ingroup utility
 */
class Atmosphere
{
public:

  /// determine properties at altitude and ground temperature offset
  explicit Atmosphere(Real altm, Real dT=0.0) { update(altm, dT); }

  /// recompute properties at different conditions
  void update(Real altm, Real dT=0.0);

public:

  /// pressure
  Real p;

  /// temperature
  Real T;

  /// speed of sound
  Real Aoo;

  /// density
  Real Rho;

  /// dynamic viscosity
  Real Mu;

  /// kinematic viscosity
  Real Nu;
};

#endif // ATMOSPHERE_H
