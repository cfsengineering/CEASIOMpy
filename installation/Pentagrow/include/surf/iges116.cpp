
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
 
#include "iges116.h"
#include "igesfile.h"
#include "igessection.h"

void IgesPoint::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());
  for (int k=0; k<3; ++k)
    par.addFloatParameter( pt[k] );
  par.addIntParameter(symbol);
}

uint IgesPoint::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 4)
    return 0;

  const char *s = pds.c_str();
  for (int k=0; k<3; ++k)
    pt[k] = asDouble(s, vpos[k]);

  symbol = asInt(s, vpos[3]);

  return 4;
}
