
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
 
#include "iges124.h"
#include "igesfile.h"

void IgesTrafoMatrix::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());

  par.addFloatParameter( rp(0,0) );
  par.addFloatParameter( rp(0,1) );
  par.addFloatParameter( rp(0,2) );
  par.addFloatParameter( tp[0] );

  par.addFloatParameter( rp(1,0) );
  par.addFloatParameter( rp(1,1) );
  par.addFloatParameter( rp(1,2) );
  par.addFloatParameter( tp[1] );

  par.addFloatParameter( rp(2,0) );
  par.addFloatParameter( rp(2,1) );
  par.addFloatParameter( rp(2,2) );
  par.addFloatParameter( tp[2] );
}

uint IgesTrafoMatrix::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 12)
    return false;

  const char *s = pds.c_str();

  rp(0,0) = asDouble(s, vpos[0]);
  rp(0,1) = asDouble(s, vpos[1]);
  rp(0,2) = asDouble(s, vpos[2]);
  tp[0] = asDouble(s, vpos[3]);

  rp(1,0) = asDouble(s, vpos[4]);
  rp(1,1) = asDouble(s, vpos[5]);
  rp(1,2) = asDouble(s, vpos[6]);
  tp[1] = asDouble(s, vpos[7]);

  rp(2,0) = asDouble(s, vpos[8]);
  rp(2,1) = asDouble(s, vpos[9]);
  rp(2,2) = asDouble(s, vpos[10]);
  tp[2] = asDouble(s, vpos[11]);

  return 12;
}
