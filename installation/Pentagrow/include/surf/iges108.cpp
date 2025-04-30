
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
 
#include "iges108.h"
#include "igesfile.h"

void IgesPlane::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());
  for (int k=0; k<3; ++k)
    par.addFloatParameter( normal[k] );
  par.addFloatParameter( distance );
  par.addIntParameter( ideBoundary );
  for (int k=0; k<3; ++k)
    par.addFloatParameter( marker[k] );
  par.addFloatParameter( markerSize );
}

uint IgesPlane::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 9)
    return false;

  const char *s = pds.c_str();
  for (int k=0; k<3; ++k)
    normal[k] = asDouble(s, vpos[k]);
  distance = asDouble(s, vpos[3]);
  ideBoundary = asInt(s, vpos[4]);
  for (int k=0; k<3; ++k)
    marker[k] = asDouble(s, vpos[5+k]);
  markerSize = asDouble(s, vpos[8]);

  return 9;
}
