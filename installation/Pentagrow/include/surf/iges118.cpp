
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
 
#include "iges118.h"
#include "igesfile.h"

void IgesRuledSurface::definition(IgesFile & igfile)
{
  IgesParameterSection & par(igfile.parameters());

  // set curve parameters
  par.addIntParameter( cidx1 );
  par.addIntParameter( cidx2 );
  par.addIntParameter( dirflag );
  par.addIntParameter( devflag );
}

uint IgesRuledSurface::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 4)
    return 0;

  const char *s = pds.c_str();
  cidx1 = asInt(s, vpos[0]);
  cidx2 = asInt(s, vpos[1]);
  dirflag = asInt(s, vpos[2]);
  devflag = asInt(s, vpos[3]);

  return 4;
}
