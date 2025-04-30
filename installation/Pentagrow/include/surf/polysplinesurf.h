
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
 
#ifndef SURF_POLYSPLINESURF_H
#define SURF_POLYSPLINESURF_H

#include <genua/splinebasis.h>
#include "surface.h"

class StepFile;
class StepEntity;
class StepBSplineSurfaceWithKnots;
class IgesFile;
struct IgesDirEntry;
class AbstractCurve;
class TriMesh;

/** Polynomial spline surface.

  This is a raw spline surface with variable degree (up to 7). Most geometric
  surfaces in libsurf are not built upon this class because a fixed degree 
  allows for considerable optimizations (no loops or allocations in eval() and
  plane()).

  \todo
  Update genua/splinebasis.cpp to allow for derivation w/o allocation

  \ingroup geometry
  \sa PolySplineCurve, RationalSplineSurf
*/
class PolySplineSurf : public Surface
{
public:

  /// control point grid compatibility
  enum GridCompat {Incompatible=0, North2South,
                   South2North, East2West, West2East};

  /// construct named spline surface
  PolySplineSurf(const std::string & s = "") : Surface(s),
    ukfront(0.0), ukback(1.0), vkfront(0.0), vkback(1.0),
    ustart(0.0), uend(1.0), vstart(0.0), vend(1.0) {}

  /// interpolate spline surface from grid
  void interpolate(const Vector &u, const Vector &v, const PointGrid<3> &grid,
                   int udeg=3, int vdeg=3);

  /// approximate spline surface from grid with a given control grid size
  void approximate(const Vector &u, const Vector &v, const PointGrid<3> &grid,
                   int ncu, int ncv, int udeg=3, int vdeg=3);

  /// evaluation interface
  Vct3 eval(Real u, Real v) const;

  /// derive at (u,v)
  Vct3 derive(Real u, Real v, uint du, uint dv) const;

  /// compute point and tangent derivatives at (u,v), for efficiency
  void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const;

  /// coordinate transformation
  void apply();

  /// overloaded grid pattern initialization
  void initGridPattern(Vector &up, Vector &vp) const;

  /// compute statistics
  void dimStats(DimStat &stat) const;

  /// create simple discretization for display purposes
  void simpleMesh(PointGrid<3,float> & pgrid,
                  PointGrid<3,float> & ngrid, uint pu=2, uint pv=2) const;

  /// dump simple discretization into global mesh
  void simpleMesh(TriMesh & msh, uint pu=2, uint pv=2, int tag=0) const;

  /// compute control point grid compatibility
  static GridCompat compatible(const PolySplineSurf & a,
                               const PolySplineSurf & b, Real tol=1e-6);

  /// XML output
  XmlElement toXml(bool share=false) const;

  /// XML input
  void fromXml(const XmlElement & xe);

  /// extract from STEP entity id
  bool fromStep(const StepFile & file, const StepBSplineSurfaceWithKnots *ep);

  /// extract from IGES entity 128
  bool fromIges(const IgesFile & file, const IgesDirEntry & entry);

  /// append to IGES file and return the directory entry index, if implemented
  int toIges(IgesFile & file, int tfi = 0) const;

  /// generate a clone
  Surface *clone() const;

  /// transform a parameter-space curve read from IGES
  void knotScale(AbstractCurve & c) const;

protected:

  /// evaluate spline bases on grid (interpolation/approximation)
  void evalBasisGrid(const Vector &u, const Vector &v, Matrix &A) const;

  /// recover control points from linear system solution
  void toControlGrid(int nu, int nv, const Matrix &b);

  /// map u parameter to internal range
  Real umap(Real ux) const {
    return clamp(ustart + ux*(uend-ustart), 0.0, 1.0);
  }

  /// map v parameter to internal range
  Real vmap(Real vx) const {
    return clamp(vstart + vx*(vend-vstart), 0.0, 1.0);
  }

  /// evaluate first derivatives in mapped domain [0,1]x[0,1]
  void mappedPlane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const;

protected:

  /// spline bases in two directions
  SplineBasis ub, vb;

  /// control point grid
  PointGrid<3> cp;

  /// original range of knot values
  Real ukfront, ukback, vkfront, vkback;

  /// parameter region
  Real ustart, uend, vstart, vend;
};

typedef boost::shared_ptr<PolySplineSurf> PolySplineSurfPtr;

#endif
