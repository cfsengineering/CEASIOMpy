
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
 
#ifndef SURF_IGES126_H
#define SURF_IGES126_H

#include "igesentity.h"
#include <genua/point.h>
#include <genua/dvector.h>

/** IGES 126 : Rational spline curve.

  This class represents general rational spline curves (NURBS curves) in IGES
  files. Note that some CAD systems misuse this object to write plain lines
  (which should really be entity type 110) without setting the corresponding
  form attribute in the directory entry.

  \b Spec : IGES 5.3 page 152

  The rational B-spline curve may represent analytic curves of general interest.
  This information is important to both the sending and receiving systems.
  The Directory Entry Form Number Parameter is provided to communicate this
  information. For a brief description and a precise definition of rational
  B-spline curves, see Appendix B.

  If the rational B-spline curve represents a preferred curve type, the form number
  corresponds to the ECO630 most preferred type. The preference order is from 1
  through 5, followed by 0 For example, if the curve is a circle or circular arc,
  the form number shall be set to 2. If the curve is an ellipse with unequal major
  and minor axis lengths, the form number shall be set to 3. If the curve is not
  one of the preferred types, the form number shall be set to 0.

  If the curve lies entirely within a unique plane, the planar flag (PROP1) shall
  be set to 1; otherwise it shall be set to 0 If it is set to 1, the plane normal
  (Parameters 14+A+4*K through 16+A+4*K) shall contain a unit vector normal to the
  plane containing the curve. These fields shall exist but are ignored if the curve
  is non-planar.

  If the beginning and ending points on the curve, as defined by evaluating the
  curve at the starting and ending parameter values (i.e., V(0) and V(l)),
  are coincident, the curve is closed and PROP2 shall be set to 1. If they are not
  coincident, PROP2 shall be set to 0.

  If the curve is rational (does not have all weights equal), PROP3 shall be set to
  0 If all weights are ECO630 equal to each other, the curve is polynomial and
  PROP3 shall be set to 1. The curve is polynomial since in this case all weights
  cancel and the denominator reduces to one. (See Appendix B.) The weights shall be
  positive real numbers.

  If the curve is periodic with respect to its parametric variable, PROP4 shall be
  set to 1; otherwise, PROP4 shall be set to 0 The periodic flag is to be
  interpreted as purely informational; the curves which are flagged to be periodic
  are to be evaluated exactly the same as in the non-periodic case.

  Note that the control points are in the definition space of the curve.

  \ingroup interop
  \sa IgesEntity, IgesFile
*/
class IgesSplineCurve : public IgesEntity
{
  public:

    /// create undefined
    IgesSplineCurve() : IgesEntity(126), planar(0), closed(0),
                        polynomial(1), periodic(0) {}

    /// pass data for polynomial spline curve
    void setup(int ncp, int degree, const double kts[], const double cp[]);

    /// pass data for rational spline curve
    void setup(int ncp, int degree, const double kts[],
               const double wgt[], const double cp[]);

    /// change closed flag
    void flagClosed(bool f) { closed = (f ? 1 : 0); }

    /// access knot vector
    const Vector & knotVector() const {return knots;}

    /// access control points
    const PointList<3> & ctrlPoints() const {return cpoints;}

    /// is curve polynomial?
    bool isPolynomial() const {return (polynomial == 1);}

    /// degree
    int degree() const {return m;}

    /// assemble definition
    void definition(IgesFile & file);

    /// parse entity data
    uint parse(const std::string & pds, const Indices & vpos);

  public:

    /// pointers to knots, weights and control points
    Vector knots, weights;

    /// control points
    PointList<3,double> cpoints;

    /// number of control points minus one, degree
    int k, m, nknots;

    /// shape flags
    int planar, closed, polynomial, periodic;

    /// unit normal if curve is planar
    Vct3 nrm;

    /// starting and ending parameter value
    Real ustart, uend;
};

#endif // IGES126_H
