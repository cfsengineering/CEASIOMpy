
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
 
#ifndef SURF_IGES102_H
#define SURF_IGES102_H

#include "igesentity.h"

/** IGES 102 : Composite Curve

  Curve defined by the concatenation of multiple other curves, which can not
  themselves be composite curves. When writing child curves, set the subordinate
  entity switch to indicate a physical dependency.

  \b Spec : IGES 5.3 page 97

  \ingroup interop
  \sa IgesEntity, IgesFile
*/
class IgesCompositeCurve : public IgesEntity
{
public:

  /// construct undefined entity
  IgesCompositeCurve() : IgesEntity(102) {}

  /// assemble definition
  void definition(IgesFile & file);

  /// parse entity data
  uint parse(const std::string & pds, const Indices & vpos);

public:

  /// directory entires of constituent curves / entities
  Indices curves;
};

#endif // IGES102_H
