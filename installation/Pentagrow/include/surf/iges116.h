
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
 
#ifndef SURF_IGES116_H
#define SURF_IGES116_H

#include "igesentity.h"
#include <genua/point.h>

/** IGES 116 : Point

  A point entity stores coordinates (accessible though operator[]) and
  a reference to a subfigure (entity type 308) which should be used to
  draw this point.

  \b Spec : IGES 5.3 page 131

  \ingroup interop
  \sa IgesEntity, IgesFile
*/
class IgesPoint : public IgesEntity
{
  public:

    /// create empty entity
    IgesPoint() : IgesEntity(116), symbol(0) {}

    /// create defined point
    IgesPoint(const Vct3 &p) : IgesEntity(116), pt(p), symbol(0) {}

    /// access coordinates
    const Real & operator[] (uint i) const {return pt[i];}

    /// access coordinates
    Real & operator[] (uint i) {return pt[i];}

    /// access location
    const Vct3 & location() const {return pt;}

    /// access the DE of the subfigure representing the symbol
    uint symbolSubfig() const {return symbol;}

    /// assemble definition
    void definition(IgesFile & file);

    /// parse entity data
    uint parse(const std::string & pds, const Indices & vpos);

  private:

    /// point coordinates
    Vct3 pt;

    /// pointer to subfigure indicating symbol used
    uint symbol;
};

#endif // IGES116_H
