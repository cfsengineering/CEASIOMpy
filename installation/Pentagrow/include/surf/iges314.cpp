/* Copyright (C) 2015 David Eller <david@larosterna.com>
 *
 * This program is free software; you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free Software
 * Foundation; either version 2 of the License, or (at your option) any later
 * version. This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details. You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
 */

#include "iges314.h"
#include "igesfile.h"
#include "igessection.h"

void IgesColorDefinition::definition(IgesFile & file)
{
  IgesParameterSection & par(file.parameters());

  // color component are specified in percent, not fractions
  double f = 100.0 / 255.0;
  par.addFloatParameter( f*m_rgb.red() );
  par.addFloatParameter( f*m_rgb.green() );
  par.addFloatParameter( f*m_rgb.blue() );

  if (not m_cname.empty())
    par.addParameter( m_cname );
}

uint IgesColorDefinition::parse(const std::string & pds, const Indices & vpos)
{
  if (vpos.size() < 3)
    return 0;

  uint n(3);
  const char *s = pds.c_str();

  // color component are specified in percent, not fractions
  float red = asDouble(s, vpos[0]);
  float green = asDouble(s, vpos[1]);
  float blue = asDouble(s, vpos[2]);
  m_rgb.assign(0.01f*red, 0.01f*green, 0.01f*blue);

  if (vpos.size() > 4) {
    fromHollerith( pds.substr(vpos[3], vpos[4]), m_cname );
    ++n;
  }

  return n;
}
