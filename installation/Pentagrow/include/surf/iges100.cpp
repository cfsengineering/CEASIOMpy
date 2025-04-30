
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
 
#include "iges100.h"
#include "igessection.h"
#include "igesfile.h"

void IgesCircularArc::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());

  par.addFloatParameter( center[2] );
  par.addFloatParameter( center[0] );
  par.addFloatParameter( center[1] );
  par.addFloatParameter( startPoint[0] );
  par.addFloatParameter( startPoint[1] );
  par.addFloatParameter( endPoint[0] );
  par.addFloatParameter( endPoint[1] );
}

uint IgesCircularArc::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 7)
    return 0;

  const char *s = pds.c_str();
  center[2] = IgesEntity::asDouble( s, vpos[0] );
  for (int k=0; k<2; ++k)
    center[k] = IgesEntity::asDouble( s, vpos[1+k] );
  for (int k=0; k<2; ++k)
    startPoint[k] = IgesEntity::asDouble( s, vpos[3+k] );
  for (int k=0; k<2; ++k)
    endPoint[k] = IgesEntity::asDouble( s, vpos[5+k] );

  return 7;
}
