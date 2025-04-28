
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
#include "iges144.h"
#include <genua/xcept.h>

void IgesTrimmedSurface::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());
  par.addIntParameter(pts);
  par.addIntParameter(n1);
  par.addIntParameter(n2);
  par.addIntParameter(pto);

  for (uint i=0; i<pti.size(); ++i)
    par.addIntParameter(pti[i]);
}

uint IgesTrimmedSurface::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 4)
    return 0;

  const char *s = pds.c_str();
  pts = asInt(s, vpos[0]);
  n1 = asInt(s, vpos[1]);
  n2 = asInt(s, vpos[2]);
  pto = asInt(s, vpos[3]);

  if (vpos.size() < 4+n2)
    throw Error("Ill-defined IGES entity 144.");

  pti.resize(n2);
  for (uint i=0; i<n2; ++i)
    pti[i] = asInt(s, vpos[4+i]);

  return 4+n2;
}

