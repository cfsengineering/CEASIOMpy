/* Copyright (C) 2017 David Eller <david@larosterna.com>
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
#include "iges402.h"

using namespace std;

bool IgesAssociativity::ordered() const
{
  int f = entry.form;
  return (f == 14 or f == 15);
}

bool IgesAssociativity::backpointers() const
{
  int f = entry.form;
  return (f == 1 or f == 14);
}

void IgesAssociativity::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());

  const int n = deps.size();
  par.addIntParameter(n);
  for (int k=0; k<n; ++k)
    par.addIntParameter(deps[k]);
}

uint IgesAssociativity::parse(const std::string &pds, const Indices & vpos)
{
  if (vpos.size() < 1)
    return 0;

  const char *s = pds.c_str();
  int n = asInt(s, vpos[0]);
  deps.resize(n);
  for (int i=0; i<n; ++i)
    deps[i] = asInt(s, vpos[1+i]);

  return 1+n;
}
