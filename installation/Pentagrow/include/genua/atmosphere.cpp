
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
 
#include "atmosphere.h"
#include <genua/xcept.h>

void Atmosphere::update(Real altm, Real dT)
{
  // earth radius (m)
  const Real radius(6356766.);

  // gas constants
  const Real Gamma = 1.4;
  const Real R(287.);
  const Real g(9.81);

  // for Sutherland's law
  const Real mu0(18.27e-6);
  const Real To(291.15);
  const Real C(120.);

  // Compute geopotential altitude
  Real h = altm*radius / (radius+altm);

  // reference conditions at sea level
  Real L0 = -6.5e-3;
  Real T0 = 288.16 + dT;
  Real p0 = 1.01325e5;

  // reference conditions at 11 000m
  Real T11 = T0 + 11000*L0;
  Real p11 = p0 * pow(T11/T0, -g/(L0*R));

  // lower stratosphere reference conditions
  Real L20 = +1.0e-3;
  Real p20 = p11 * exp( -g*(9000.0/(R*T11)) );

  // upper stratosphere reference conditions
  Real L32 = +2.8e-3;
  Real T32 = T11 + L20*12000.0;
  Real p32 = p20 * pow(T32/T11, -g/(L20*R));

  // stratopause reference conditions
  Real T47 = T32 + L32*15000.0;
  Real p47 = p32 * pow(T47/T32, -g/(L32*R));

  Real ho;
  if (h < 11000.0) {

    // troposphere: linear temperature gradient
    ho = 0;
    T = T0 + L0*(h - ho);
    p = p0 * pow(T/T0, -g/(L0*R));

  } else if (h < 20000.0) {

    // tropopause: constant temperature
    ho = 11000.0;
    T = T11;
    p = p11 * exp( -g*(h - ho)/(R*T) );

  } else if (h < 32000.0) {

    // lower stratosphere
    ho = 20000.0;
    T = T11 + L20*(h - ho);
    p = p20 * pow(T/T11, -g/(L20*R));

  } else if (h < 47000.0) {

    // upper stratosphere
    ho = 32000.0;
    T = T32 + L32*(h - ho);
    p = p32 * pow(T/T32, -g/(L32*R));

  } else if (h <= 51000.0) {

    // stratopause
    ho = 47000.0;
    T = T47;
    p = p47 * exp( -g*(h - ho)/(R*T) );

  } else {
    throw Error("Atmosphere - Altitude out of range (51km).");
  }

  // speed of sound
  Aoo = sqrt(Gamma*R*T);

  // compute density
  Rho = p/(R*T);

  // compute viscosity
  Mu = mu0 * (To + C)/(T + C) * pow(T/To, 1.5);
  Nu = Mu/Rho;
}
