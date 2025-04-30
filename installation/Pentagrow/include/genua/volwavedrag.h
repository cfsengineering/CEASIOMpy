
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
 
#ifndef GENUA_VOLWAVEDRAG_H
#define GENUA_VOLWAVEDRAG_H

#include "dvector.h"
#include "point.h"

class TriMesh;
class MxMesh;

/** Utility class for wave drag estimation.

  This class implements a classical method for the estimation of the
  zero-lift component of the wave drag, based on an integral formula for
  equivalent body of revolution:
  \f[
    C_{Dw} = \frac{-1}{2 \pi A L^2} \int_0^1 \int_0^1
          \frac{\partial^2 S}{\partial \eta_1^2}
          \frac{\partial^2 S}{\partial \eta_2^2} \log |\eta_1 - \eta_2|
          d \eta_1 d \eta_2
  \f]
  where \f$ S(\eta) \f$ is the cross section area as a function of the
  nondimensional longitudinal coordinate, \f$A\f$ is the reference area and
  \f$L\f$ the body length. For efficiency, the cross section area distribution
  is expanded as a sine series with 48 terms for which the above integral is
  stored precomputed to high accuracy.

  \ingroup numerics
  */
class VolWaveDrag
{
public:

  /// empty object
  VolWaveDrag() {}

  /// initialize with TriMesh
  VolWaveDrag(const TriMesh & tm);

  /// initialize with all wall surface mesh sections of mx
  VolWaveDrag(const MxMesh & mx);

  /// compute angular-averaged area distribution for specific Mach number
  void meanAreaDistribution(const Vct3 & pn, Real Mach, int nsec, int nphi,
                            Vector & x, Vector & S) const;

  /// intermediate : compute area distribution
  void areaDistribution(const Vct3 & pn, int n, Vector & x, Vector & S) const;

  /// return drag coefficient for known area distribution
  static Real dragCoefficient(Real Sref, const Vector & x, const Vector & S,
                              Real Scutoff = 0.01);

private:

  /// initialize bounding box
  void initBox();

  /// compute distances of all nodes from plane through origin
  void planeDistance(const Vct3 & pn, Vector & dst,
                     Real & dmin, Real & dmax) const;

  /// determine triangles which intersect plane with offset dp
  void intersectingTriangles(const Vector & dst, Real dp, Indices & itri) const;

  /// cross section area contribution of triangle jt
  Real areaContribution(const Vct3 & pn, Real dp, uint jt) const;

  /// determine sine series coefficients
  static void sineSeries(const Vector & eta, const Vector & S,
                         Vector & ak);

  /// compute wave drag from series coeffiecients
  static Real dragCoefficient(Real Sref, Real L, const Vector & ak);

private:

  /// all surface triangles as point triples
  PointList<3> vtri;

  /// bounding box edges
  Vct3 bbp1, bbp2;
};

#endif // VOLWAVEDRAG_H
