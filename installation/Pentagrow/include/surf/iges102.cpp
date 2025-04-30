
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
 
#include "iges102.h"
#include "igessection.h"
#include "igesfile.h"

void IgesCompositeCurve::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());

  const int n = curves.size();
  par.addIntParameter( n );
  for (int i=0; i<n; ++i)
    par.addIntParameter( curves[i] );
}

uint IgesCompositeCurve::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 2)
    return 0;

  const char *s = pds.c_str();
  const uint n = asInt(s, vpos[0]);
  if (n < 1 or vpos.size() < n+1)
    return 0;

  curves.resize(n);
  for (uint i=0; i<n; ++i)
    curves[i] = asInt(s, vpos[i+1]);

  return n+1;
}
