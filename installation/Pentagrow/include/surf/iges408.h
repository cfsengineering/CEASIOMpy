
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
 
#ifndef SURF_IGESSINGULARSUBFIGURE_H
#define SURF_IGESSINGULARSUBFIGURE_H

#include <genua/defines.h>
#include "igesentity.h"

/** Single instance of subfigure

  IGES entity 408, used in combination with entity 308 in order to
  represent (multiple) instantiation.

  \ingroup interop
  \sa IgesEntity, IgesSubfigure
*/
class IgesSingularSubfigure : public IgesEntity
{
  public:

    /// undefined subfigure
    IgesSingularSubfigure() : IgesEntity(408) {
      xyz[0] = xyz[1] = xyz[2] = 0;
      scl = 1.0;
    }

    /// subfigure reference
    uint subfigure() const {return sub;}

    /// subfigure reference
    void subfigure(uint isb) {sub = isb;}

    /// assemble definition
    void definition(IgesFile & file);

    /// parse entity data
    uint parse(const std::string & pds, const Indices & vpos);

  public:

    /// transformation values stored in this entry
    double xyz[3], scl;

    /// DE of subfigure
    int sub;
};

#endif // IGESSINGULARSUBFIGURE_H
