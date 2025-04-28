
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
 
#ifndef SURF_IGES110_H
#define SURF_IGES110_H

#include "forward.h"
#include "igesentity.h"

/** IGES 110 : Line.

  \b Spec : IGES 5.3 page 119

  A line is a bounded, connected portion of a straight line which has distinct
  start and terminate points. A line is defined by its end points. Each end point
  is specified relative to definition space by triple coordinates. With respect to
  definition space, a direction is associated with the line by considering the
  start point to be listed first and the terminate point second.

  The direction of the line with respect to model space is determined by the
  original direction of the line within definition space, in conjunction with the
  action of the transformation matrix on the line.

  \ingroup interop
  \sa IgesEntity, IgesFile
  */
class IgesLineEntity : public IgesEntity
{
  public:

    /// create line entity
    IgesLineEntity() : IgesEntity(110) {}

    /// create line entity from available points
    IgesLineEntity(const Vct3 &a, const Vct3 &b);

    /// copy data from provider
    void setup(const double a[], const double b[]) {
      for (int k=0; k<3; ++k) {
        p1[k] = a[k]; p2[k] = b[k];
      }
    }

    /// access point 1
    const double *point1() const {return p1;}

    /// access point 2
    const double *point2() const {return p2;}

    /// assemble definition
    void definition(IgesFile & file);

    /// parse entity data
    uint parse(const std::string & pds, const Indices & vpos);

  private:

    /// defined by two points
    double p1[3], p2[3];
};


#endif // IGES110_H
