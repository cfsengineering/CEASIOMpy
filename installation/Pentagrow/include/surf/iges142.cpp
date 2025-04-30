
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
 
#include "igesfile.h"
#include "igessection.h"
#include "iges142.h"

using namespace std;

void IgesCurveOnSurface::prefer(Preference p)
{
  switch (p) {
  case Unspecified:
    pref = 0;
    entry.useflag = 0;
    break;
  case Parametric:
    pref = 1;
    entry.useflag = 5;
    break;
  case Spatial:
    pref = 2;
    entry.useflag = 0;
    break;
  case Any:
    pref = 3;
    entry.useflag = 0;
    break;
  }
}

IgesCurveOnSurface::Preference IgesCurveOnSurface::prefer() const
{
  switch (pref) {
  case 0:
    return Unspecified;
  case 1:
    return Parametric;
  case 2:
    return Spatial;
  case 3:
    return Any;
  default:
    return Unspecified;
  }
}

void IgesCurveOnSurface::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());
  par.addIntParameter(crtn);
  par.addIntParameter(sptr);
  par.addIntParameter(bptr);
  par.addIntParameter(cptr);
  par.addIntParameter(pref);
}

uint IgesCurveOnSurface::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 5)
    return 0;

  const char *s = pds.c_str();
  crtn = asInt(s, vpos[0]);
  sptr = asInt(s, vpos[1]);
  bptr = asInt(s, vpos[2]);
  cptr = asInt(s, vpos[3]);
  pref = asInt(s, vpos[4]);

  return 5;
}

