
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
#include "iges120.h"
#include <genua/xcept.h>

void IgesRevolutionSurface::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());
  par.addIntParameter(pAxis);
  par.addIntParameter(pGenCurve);
  par.addFloatParameter(sa);
  par.addFloatParameter(ta);
}

uint IgesRevolutionSurface::parse(const std::string & pds,
                                  const Indices & vpos)
{
  if (vpos.size() < 4)
    return 0;

  const char *s = pds.c_str();
  pAxis = asInt(s, vpos[0]);
  pGenCurve = asInt(s, vpos[1]);
  sa = asDouble(s, vpos[2]);
  ta = asDouble(s, vpos[3]);

  return 4;
}

