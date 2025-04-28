
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
 
#include <iostream>
#include <genua/mvop.h>
#include "nstcoordsys.h"

using namespace std;

void NstCoordSys::axes(const Vct3 & ax, const Vct3 & ay, const Vct3 & az)
{
  for (int i=0; i<3; ++i) {
    xyz(0,i) = ax[i];
    xyz(1,i) = ay[i];
    xyz(2,i) = az[i];
  }
}

void NstCoordSys::fromCord2r(const Vct3 & a, const Vct3 & b, const Vct3 & c)
{
  org = a;
  Vct3 zax(b - a);
  normalize(zax);
  Vct3 xax(c - a);
  xax -= zax*dot(xax,zax);
  normalize(xax);
  Vct3 yax = cross(zax,xax);
  for (int k=0; k<3; ++k) {
    xyz(k,0) = xax[k];
    xyz(k,1) = yax[k];
    xyz(k,2) = zax[k];
  }
}

void NstCoordSys::toGlobal(uint i, Matrix & z) const
{
  Vct3 dx, dr;
  for (int k=0; k<3; ++k) {
    dx[k] = z(i,k);
    dr[k] = z(i,k+3);
  }
  dx = xyz*dx;
  dr = xyz*dr;
  for (int k=0; k<3; ++k) {
    z(i,k) = dx[k];
    z(i,k+3) = dr[k];
  }
}

