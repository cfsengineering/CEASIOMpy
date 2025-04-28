
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
#include "iges308.h"

using namespace std;

void IgesSubfigure::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());

  par.addIntParameter(depth);
  par.addParameter(id);

  const int n = deps.size();
  par.addIntParameter(n);
  for (int k=0; k<n; ++k)
    par.addIntParameter(deps[k]);
}

uint IgesSubfigure::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 3)
    return 0;

  const char *s = pds.c_str();
  depth = asInt(s, vpos[0]);
  fromHollerith( pds.substr(vpos[1], vpos[2]), id );
  int n = asInt(s, vpos[2]);

  deps.resize(n);
  for (int i=0; i<n; ++i)
    deps[i] = asInt(s, vpos[3+i]);

  return 3+n;
}
