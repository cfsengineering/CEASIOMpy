
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
 
#include <cstring>
#include "naca6generator.h"

Naca6Generator::Naca6Generator() 
{
  clear();
}
    
int Naca6Generator::addMeanLine(double cli, double a)
{
  if (mncmbl < 10) {
    mcli[mncmbl] = cli;
    ma[mncmbl] = a;
    ++mncmbl;
    return mncmbl;
  } else {
    return NACA6_TOOMANYLINES;
  }
}
    
int Naca6Generator::generate(int iprof, int icamb, double toc) 
{
  int status = naca6(iprof, icamb, toc, 
                     mncmbl, mcli, ma,
                     &mnout, mxyout);
  if (status == NACA6_SUCCESS)
    return 2*mnout;
  else
    return status;
}
    
int Naca6Generator::generate(int iprof, int icamb, double toc, double cli, double a)
{
  clear();
  mncmbl = 1;
  mcli[0] = cli;
  ma[0] = a;
  return generate(iprof, icamb, toc);
}
    
void Naca6Generator::copyCoordinates(double cx[], double cy[]) const
{
  if (mnout == 0)
    return;
  
  memcpy(&cx[0], &mxyout[0], 2*mnout*sizeof(double));
  memcpy(&cy[0], &mxyout[2*mnout], 2*mnout*sizeof(double));
}
    
void Naca6Generator::clear()
{
  memset(mxyout, 0, sizeof(mxyout));
  memset(mcli, 0, sizeof(mcli));
  memset(ma, 0, sizeof(ma));
  mncmbl = mnout = 0;
}
