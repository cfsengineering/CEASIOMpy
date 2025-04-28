
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
 
#include "iges110.h"
#include "igesfile.h"
#include <genua/svector.h>

IgesLineEntity::IgesLineEntity(const Vct3 &a, const Vct3 &b) : IgesEntity(110)
{
  setup(a.pointer(), b.pointer());
}

void IgesLineEntity::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());
  for (int k=0; k<3; ++k)
    par.addFloatParameter( p1[k] );
  for (int k=0; k<3; ++k)
    par.addFloatParameter( p2[k] );
}

uint IgesLineEntity::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 6)
    return false;

  const char *s = pds.c_str();
  for (int k=0; k<3; ++k)
    p1[k] = asDouble(s, vpos[k]);
  for (int k=0; k<3; ++k)
    p2[k] = asDouble(s, vpos[3+k]);

  return 6;
}


