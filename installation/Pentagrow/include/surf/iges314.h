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

#ifndef SURF_IGES314_H
#define SURF_IGES314_H

#include "igesentity.h"
#include <genua/color.h>
#include <string>

/** IGES Entity 314: Color definition.

  Defines a RGB color and an optional color name.

  \ingroup interop
  \sa IgesEntity
*/
class IgesColorDefinition : public IgesEntity
{
public:

  /// create empty entry
  IgesColorDefinition() : IgesEntity(314) {}

  /// create from color
  explicit IgesColorDefinition(const Color &c) : IgesEntity(314), m_rgb(c) {}

  /// set color components
  void setRGB(float r, float g, float b) {
    m_rgb.assign(r, g, b);
  }

  /// access color object
  const Color & color() const {return m_rgb;}

  /// access color object
  void color(const Color & c) {m_rgb = c;}

  /// assemble definition
  void definition(IgesFile & file);

  /// extract from file
  uint parse(const std::string & pds, const Indices & vpos);

private:

  /// color components
  Color m_rgb;

  /// optional color name
  std::string m_cname;
};

#endif
