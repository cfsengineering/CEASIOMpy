
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
 
#ifndef SURF_IGES144_H
#define SURF_IGES144_H

#include "igesentity.h"
#include <genua/dvector.h>
#include <genua/point.h>

/** IGES 144 : Trimmed surface.

  A pointer-only entity which relates a parametric surface to a set of boundary
  curves which define the outer boundary (first curve) and, optionally, internal
  holes. The part of the surface to use is the part of the surface
  enclosed by the first boundary, excluding the part enclosed by any of the
  following curves.

  Due to this definiton, all parameter-domain curves must be closed and
  represented by IgesCurveOnSurface (type 142) entities.

  \b Spec : IGES 5.3 page 196

  \ingroup interop
  \sa IgesEntity, IgesFile, IgesCurveOnSurface
*/
class IgesTrimmedSurface : public IgesEntity
{
public:

  /// create undefined
  IgesTrimmedSurface() : IgesEntity(144), pts(0), n1(0), n2(0), pto(0) {}

  /// assemble definition
  void definition(IgesFile & file);

  /// parse entity data
  uint parse(const std::string & pds, const Indices & vpos);

public:

  /// pointer to the parametric surface to be trimmed
  uint pts;

  /// zero if the outer boundary is the domain boundary of pts, otherwise one
  uint n1;

  /// number of internal boundaries (or zero)
  uint n2;

  /// pointer to the outer boundary curve, or zero if n1 == 0
  uint pto;

  /// pointer to inner boundaries, or empty
  Indices pti;
};

#endif // IGES128_H

