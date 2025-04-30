
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
 
#ifndef SURF_TRIMMEDSURF_H
#define SURF_TRIMMEDSURF_H

#include "forward.h"
#include "surface.h"
#include "abstractcurve.h"
#include <set>

/** Trimmed surface.

  \ingroup geometry
  \sa Surface, AbstractCurve
  */
class TrimmedSurf : public Surface
{
public:

  /// create undefined surface
  TrimmedSurf(const std::string & s = "") : Surface(s) {}

  /// return a clone of *this
  TrimmedSurf *clone() const;

  /// evaluation interface, will just evaluate untrimmed base surface
  Vct3 eval(Real u, Real v) const {
    assert(base);
    return base->eval(u,v);
  }

  /// derive at (u,v)
  Vct3 derive(Real u, Real v, uint du, uint dv) const {
    assert(base);
    return base->derive(u, v, du, dv);
  }

  /// first derivatives
  void plane(Real u, Real v, Vct3 &S, Vct3 &Su, Vct3 &Sv) const {
    assert(base);
    return base->plane(u, v, S, Su, Sv);
  }

  /// coordinate transformation
  void apply() {
    if (base)
      base->apply();
  }

  /// pass through tp base surface
  void initGridPattern(Vector &up, Vector &vp) const {
    if (base)
      base->initGridPattern(up, vp);
  }

  /// compute normal vector
  Vct3 normal(Real u, Real v) const {
    if (base)
      return base->normal(u, v);
    else
      return Vct3(0.0, 0.0, 0.0);
  }

  /// compute curvature along v at u
  Real vcurvature(Real u, Real v) const {
    if (base)
      return base->vcurvature(u, v);
    else
      return 0.0;
  }

  /// compute curvature along u at v
  Real ucurvature(Real u, Real v) const {
    if (base)
      return base->ucurvature(u, v);
    else
      return 0.0;
  }

  /// compute Gaussian curvature
  Real gaussianCurvature(Real u, Real v) const {
    if (base)
      return base->gaussianCurvature(u, v);
    else
      return 0.0;
  }

  /// find projection of pt on surface (needs a guess in q)
  bool project(const Vct3 & pt, Vct2 & q,
               Real tol=1e-6, Real dpmin=1e-6) const
  {
    if (base)
      return base->project(pt, q, tol, dpmin);
    else
      return false;
  }

  /// create an unconstrained point grid as initialization for mesh generator
  void initGrid(Real lmax, Real lmin, Real phimax, PointGrid<2> & pts) const {
    if (base)
      return base->initGrid(lmax, lmin, phimax, pts);
  }

  /// initialize mesh generator - default version uses initGrid
  void initMesh(const DnRefineCriterion & c, DnMesh & gnr) const {
    if (base)
      return base->initMesh(c, gnr);
  }

  /// generate visualization mesh
  void tessellate(CgMesh &cgm, uint maxtri = 60000) const;

  /// overload computation of surface statistics to cover only bounded range
  void dimStats(DimStat &stat) const;

  /// XML output
  XmlElement toXml(bool share=false) const;

  /// XML input
  void fromXml(const XmlElement & xe);

  /// append to IGES file and return the directory entry index, if implemented
  // int toIges(IgesFile & file, int tfi = 0) const;

  /// retrieve surface from IGES file
  bool fromIges(const IgesFile &file, const IgesDirEntry &entry,
                SurfacePtr baseSurf);

  /// retrieve surface from IGES file
  bool fromIges(const IgesFile &file, const IgesDirEntry &entry) {
    SurfacePtr noBase;
    return fromIges(file, entry, noBase);
  }

private:

  typedef NDPointTree<2,Real> PointTree;

  /// default discretization
  void meshCurves();

  /// determine bounding parameter rectangle for external boundary
  void curveBounds(const PointList<2> & bnd, Vct2 & plo, Vct2 & phi) const;

  /// produce representation using DnMesh
  void cgRepDN(CgMesh & cg) const;

  /// produce CG representation by trimming a grid
  void trimmedGrid(uint maxtri, PointList<2> & pg, Indices & tri) const;

  /// find boundary vertex indices from trimmed triangle set
  void findBoundaries(const Indices & tri, Indices & bv) const;

  /// refine trim curve discretization
  void refineCurve(PointList<2> & q) const;

  /// project constraint into patterns
  void projectConstraint(const PointList<2> & c,
                         std::set<Real> &uset, std::set<Real> &vset) const;

  /// insert existing points into constraint, where applicable
  uint insertPoints(const PointTree & ptree, PointList<2> & c) const;

  /// brute-force projection of point onto boundary
  Real pointToBoundary(const PointList<2> &bnd,
                       Vct2 &p, Real & dstmin) const;

  /// find corners in boundary, return whether there is a corner at bnd[0]
  bool findCorners(const PointList<2> & bnd,
                   Indices & cix, Vector & carc) const;

  /// create corner triangles
  void fillCorners(uint ibnd, const Indices &bv, const Vector &parc,
                   const Indices &ibound, PointList<2> &pg, Indices &tri) const;

  /// generate CG lines from discretized boundaries
  void linesFromBoundary(const PointList<2> & bnd, CgMesh & cgm) const;

  /// test whether p is in the 'kept' range of the trimming curves
  bool inside(const Vct2 & p) const;

  /// compute a set of hole marker candidates
  void addHole(const PointList<2> & poly,
               bool isHole, DnMesh & gnr) const;

  /// compute a set of hole marker candidates
  void addHole(const PointList<2> & poly,
               bool isHole, UvMapDelaunay & gnr) const;

private:

  /// underlying surface to be trimmed
  SurfacePtr base;

  /// external boundary (null if bounded by [0,1]x[0,1])
  AbstractCurvePtr extBound;

  /// internal boundaries, delimiting holes
  AbstractCurveArray intBound;

  /// discretization of external boundary (surface parameter space)
  PointList<2> extPoly;

  /// discretization of internal boundaries
  std::vector<PointList<2> > intPoly;
};

#endif // TRIMMEDSURF_H
