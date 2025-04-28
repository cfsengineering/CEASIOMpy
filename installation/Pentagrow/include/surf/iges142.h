
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
 
#ifndef SURF_IGES142_H
#define SURF_IGES142_H

#include "igesentity.h"
#include <genua/dvector.h>
#include <genua/point.h>

/** IGES 142 : Curve on surface.

  This is a pointer-only entity which declares a curve to lie on a surface. The
  curve can be specified either in the parameter space of the surface (in which
  case its (x,y) coordinates are mapped to (u,v) of the surface) or in the 3D
  model space (x,y,z), depending on the value of the preference flag.

  \b Spec : IGES 5.3 page 191

  \ingroup interop
  \sa IgesEntity, IgesFile
*/
class IgesCurveOnSurface : public IgesEntity
{
  public:

    /// used to clarify how the referenced curve is to be interpreted
    enum Preference {Unspecified=0, Parametric, Spatial, Any};

    /// create undefined
    IgesCurveOnSurface() : IgesEntity(142), crtn(0), sptr(0),
                           bptr(0), cptr(0), pref(0) {}

    /// change interpretation preference
    void prefer(Preference p);

    /// return preferred interpretation
    Preference prefer() const;

    /// assemble definition
    void definition(IgesFile & file);

    /// parse entity data
    uint parse(const std::string & pds, const Indices & vpos);

  public:

    /// the way the curve was created
    uint crtn;

    /// pointer to the DE of the surface entity
    uint sptr;

    /// pointer to the curve in parameter space
    uint bptr;

    /// pointer to a curve in model space
    uint cptr;

    /// flag to indicate which representation is preferred
    uint pref;
};

#endif // IGES128_H

