
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
 
#include "iges406.h"
#include "igesfile.h"

using namespace std;

void IgesNameProperty::definition(IgesFile & file)
{
  form(15);

  IgesParameterSection & par(file.parameters());

  par.addIntParameter(1);
  par.addParameter( name );
}

uint IgesNameProperty::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 2)
    return 0;

  // ignore entity if form is not 15 == name property
  if (entry.form == 15) {

    string::size_type nend = string::npos;
    if (vpos.size() > 2)
      nend = vpos[2];
    fromHollerith(pds.substr(vpos[1], nend), name);

    return 2;

  } else {
    return  0;
  }
}
