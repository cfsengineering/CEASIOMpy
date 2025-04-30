
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
 
#ifndef SURF_IGES108_H
#define SURF_IGES108_H

#include "igesentity.h"
#include <genua/svector.h>

/** IGES 108 : Plane.

  \b Spec : IGES 5.3 page 87

  The plane entity can be used to represent an unbounded plane, as well as a
  bounded portion of a plane. In either of the above cases, the plane is
  defined within definition space by means of the coefficients A, B, C, D,
  where at least one of A, B, and C is nonzero and A·XT + B·YT + C·ZT = D
  for each point lying in the plane, and having definition space coordinates
  (XT, YT, ZT). The definition space coordinates of a point, as well as a size
  parameter, can be specified in order to assist in defining a system-dependent
  display symbol. These values are parameter data entries six through nine,
  respectively. This information, together with the four coefficients defining
  the plane, provides sufficient information relative to definition space in
  order to be able to position the display symbol. (In the unbounded plane
  example of Figure 23, the curves and the crosshair together constitute the
  display symbol.) Defaulting, or setting the size parameter to zero, indicates
  that a display symbol is not intended. The case of a bounded portion of a
  fixed plane requires the existence of a pointer to a simple closed curve
  lying in the plane. This is parameter five. The only allowed coincident points
  for this curve are the start point and the terminate point. The case of an
  unbounded plane requires this pointer to be zero.

  \ingroup interop
  \sa IgesEntity, IgesFile
  */
class IgesPlane : public IgesEntity
{
public:

  /// create plane entity
  IgesPlane() : IgesEntity(108) {}

  /// assemble definition
  void definition(IgesFile & file);

  /// parse entity data
  uint parse(const std::string & pds, const Indices & vpos);

public:

  /// plane normal
  Vct3 normal;

  /// distance from origin
  Real distance;

  /// location of display marker
  Vct3 marker;

  /// size of marker
  Real markerSize;

  /// DE of bounding curve, or 0 if unbounded
  uint ideBoundary;
};

#endif // IGES108_H
