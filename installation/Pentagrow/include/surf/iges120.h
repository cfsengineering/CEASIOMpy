
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
 
#ifndef SURF_IGES120_H
#define SURF_IGES120_H

#include "igesentity.h"

/** IGES 120 : Surface of revolution.

  \b Spec : IGES 5.3 page 136

  A surface of revolution is defined by an axis of rotation (which shall be
  a Line Entity), a generatrix, and start and terminate rotation angles.
  The surface is created by rotating the generatrix about the axis of
  rotation through the start and terminating angles. Since the axis of
  rotation is a Line Entity (Type 110), it contains in its parameter data
  section the coordinates of its start point first, followed by the
  coordinates of its terminate point. The angles of rotation are measured
  counterclockwise from the terminate point of the Line Entity defining the
  axis of revolution while looking in the direction of the start point of
  this line. The generatrix curve may be any curve entity to which a
  parameterization has been assigned.

  \ingroup interop
  \sa IgesEntity, IgesFile
  */
class IgesRevolutionSurface : public IgesEntity
{
  public:

    /// create line entity
    IgesRevolutionSurface() : IgesEntity(120) {}

    /// assemble definition
    void definition(IgesFile & file);

    /// parse entity data
    uint parse(const std::string & pds, const Indices & vpos);

  public:

    /// points to directory entry for axis of revolution
    uint pAxis;

    /// points to directory entry for generatrix curve
    uint pGenCurve;

    /// start and terminate angles in radian
    double sa, ta;
};


#endif // IGES110_H
