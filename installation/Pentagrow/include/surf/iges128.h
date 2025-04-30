
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
 
#ifndef SURF_IGES128_H
#define SURF_IGES128_H

#include "igesentity.h"
#include <genua/dvector.h>
#include <genua/point.h>

/** IGES 128 : Rational spline surface.

  This class represents general rational spline surface (NURBS surafces) in IGES
  files. Note that some CAD systems misuse this object to write simple entities
  such as planes and cylinders without setting the corresponding
  form attribute in the directory entry.

  \b Spec : IGES 5.3 page 155

  \ingroup interop
  \sa IgesEntity, IgesFile
*/
class IgesSplineSurface : public IgesEntity
{
  public:

    /// create undefined
    IgesSplineSurface() : IgesEntity(128), uclosed(0), vclosed(0),
                          polynomial(1), uperiodic(0), vperiodic(0),
                          ustart(0.0), uend(1.0), vstart(0.0), vend(1.0) {}

    /// pass data for polynomial spline curve
    void setup(int ncpu, int ncpv, int udegree, int vdegree,
               const double ukts[], const double vkts[], const double cp[]);

    /// pass data for rational spline curve
    void setup(int ncpu, int ncpv, int udegree, int vdegree,
               const double ukts[], const double vkts[],
               const double wgt[], const double cp[]);

    /// change closed flag
    void flagClosed(bool ucl, bool vcl) {
      uclosed = ucl ? 1 : 0;
      vclosed = vcl ? 1 : 0;
    }

    /// assemble definition
    void definition(IgesFile & file);

    /// parse entity data
    uint parse(const std::string & pds, const Indices & vpos);

  public:

    /// number of control points minus one, degree
    int ku, kv, mu, mv;

    /// shape flags
    int uclosed, vclosed, polynomial, uperiodic, vperiodic;

    /// pointers to knots, weights and control points
    Vector uknots, vknots;

    /// weights, if surface is rational, else empty
    Matrix weights;

    /// control points
    PointGrid<3> cpoints;

    /// domain for parameter values
    double ustart, uend, vstart, vend;
};

#endif // IGES128_H
