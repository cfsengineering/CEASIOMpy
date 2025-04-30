
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
 
#ifndef SURF_IGES118_H
#define SURF_IGES118_H

#include "igesentity.h"

/** IGES 118 : Ruled surface.

  \b Spec : IGES 5.3 page 133

  A ruled surface is formed by moving a line connecting points of equal relative
  arc length (Form 0 or equal relative parametric value (Form 1) on
  two parametric curves from a start point to a terminate point on the curves.
  The parametric curves may be points, lines, circles, conies, parametric splines,
  rational B-splines, composite curves, or any parametric curves defined in this
  Specification (both planar and non-planar).

  If DIRFLG=0, the first point of curve 1 is joined to the first point of curve 2,
  and the last point of curve 1 to last point of curve 2. If DIRFLG= 1, the first
  point of curve 1 is joined to the last point of curve 2, and the last point of
  curve 1 to the first point of curve 2.

  If DEVFLG=1, the surface is a developable surface; if DEVFLG=0, the surface may
  or may not be a developable surface.

  For the Ruled Surface Entity, the Form Numbers are as follows:
  - Form 0: DE1 and DE2 specify the defining rail curves, but their given
    parameterizations are not the ones used to generate the ruled surface.
    Instead, their arc length reparameterizations, C1 and C2 (respectively),
    are used.
  - Form 1: DE1 and DE2 specify the defining rail curves, C1 and C2 (respectively).
    Moreover, their given parameterizations are the ones used to generate the
    ruled surface.

  \ingroup interop
  \sa IgesEntity, IgesFile
*/
class IgesRuledSurface : public IgesEntity
{
  public:

    /// create undefined
    IgesRuledSurface() : IgesEntity(118), cidx1(0), cidx2(0),
                         dirflag(0), devflag(0) {}

    /// set curves by directory entry index
    void setup(int curve1, int curve2) {
      cidx1 = curve1;
      cidx2 = curve2;
    }

    /// access directory entry for curve 1
    int firstCurve() const {return cidx1;}

    /// access directory entry for curve 2
    int secondCurve() const {return cidx2;}

    /// change direction flag
    void direction(int d) {dirflag = d;}

    /// assemble definition
    void definition(IgesFile & igfile);

    /// parse entity data
    uint parse(const std::string & pds, const Indices & vpos);

  private:

    /// referenced curves, direction and development flag
    int cidx1, cidx2, dirflag, devflag;
};
#endif // IGES118_H
