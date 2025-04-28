
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
 
#ifndef SURF_IGES100_H
#define SURF_IGES100_H

#include "igesentity.h"
#include <genua/point.h>

/** IGES 100 : Circular arc

  A circular arc is a connected portion of a circle which has distinct start
  and terminate points. The definition space coordinate system is always
  chosen so that the circular arc lies in a plane either coincident with,
  or parallel to, the XT, YT plane.

  \b Spec : IGES 5.3 page 64

  \ingroup interop
  \sa IgesEntity, IgesFile
*/
class IgesCircularArc : public IgesEntity
{
public:

  /// construct undefined entity
  IgesCircularArc() : IgesEntity(100) {}

  /// assemble definition
  void definition(IgesFile & file);

  /// parse entity data
  uint parse(const std::string & pds, const Indices & vpos);

public:

  /// parent circle center
  Vct3 center;

  /// arc start point
  Vct2 startPoint;

  /// arc end point
  Vct2 endPoint;
};

#endif // IGES100_H
