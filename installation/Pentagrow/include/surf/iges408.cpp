
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
#include "iges408.h"

void IgesSingularSubfigure::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());

  par.addIntParameter(sub);
  par.addFloatParameter(xyz[0]);
  par.addFloatParameter(xyz[1]);
  par.addFloatParameter(xyz[2]);
  par.addFloatParameter(scl);
}

uint IgesSingularSubfigure::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 5)
    return 0;

  const char *s = pds.c_str();
  sub = asInt(s, vpos[0]);
  xyz[0] = asDouble(s, vpos[1]);
  xyz[1] = asDouble(s, vpos[2]);
  xyz[2] = asDouble(s, vpos[3]);
  scl = asDouble(s, vpos[4]);

  return 5;
}
