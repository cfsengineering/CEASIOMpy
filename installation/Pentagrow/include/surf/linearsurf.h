
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

#ifndef SURF_LINEARSURF_H
#define SURF_LINEARSURF_H

#include <boost/shared_ptr.hpp>
#include "surface.h"
#include "curve.h"

/** Ruled surface with multiple sections.

  LinearSurf implements a ruled surface defined as the linear
  interpolation between a set of curves, which need not have compatible
  knot vectors. A point at parameter value t on one curve is simply linearly
  connected to the point with the same parameter value on the next curve.
  Because of this, changing the t-parameterisation of a curve, which does not
  change the shape of the curve, can change the shape of a ruled surface
  defined by the curve.

  \ingroup geometry
  \sa SkinSurface
  */
class LinearSurf : public Surface
{
public:

  /// empty definition
  LinearSurf(const std::string & s = "NoNameLinearSurf") : Surface(s) {}

  /// copy surface, do not share curve objects
  LinearSurf(const LinearSurf & a);

  /// create from curve array, surface will modify curves when transformed
  Vector init(const CurvePtrArray & cv);

  /// convenience interface : construct from two curves (common case)
  Vector init(const CurvePtr &ca, const CurvePtr &cb);

  /// compute a surface point
  Vct3 eval(Real u, Real v) const;

  /// derivation with respect to parameters
  Vct3 derive(Real u, Real v, uint ku, uint kv) const;

  /// compute point and tangents in one sweep (more efficient)
  void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const;

  /// coordinate transformation
  void apply();

  /// initialize mesh generator (marks kink edges)
  void initMesh(const DnRefineCriterion & c, DnMesh & gnr) const;

  /// quadrilaterals for OpenGL display
  void simpleMesh(PointGrid<3,float> & pgrid,
                  PointGrid<3,float> & ngrid, uint pu=2, uint pv=2) const;

  /// XML output
  XmlElement toXml(bool share=false) const;

  /// XML input
  void fromXml(const XmlElement & xe);

  /// generate a clone
  LinearSurf *clone() const {return new LinearSurf(*this);}

  /// read access to parametric positions of sections
  const Vector & vsections() const {return vp;}

  /// generate multiple IGES entities 118
  int toIges(IgesFile & igfile, int tfi = 0) const;

  /// fetch data from IGES entity 118
  bool fromIges(const IgesFile & file, const IgesDirEntry & dir);

  /// find segment
  uint segment(Real v) const;

  /// compute statistics
  void dimStats(DimStat &stat) const;

  /// return an initial discretization pattern to start with
  void initGridPattern(Vector & upi, Vector & vpi) const;

  /// return if surface is symmetric in u- or v-direction
  void isSymmetric(bool & usym, bool & vsym) const;

private:

  /// curves which constitute sections between which to interpolate
  CurvePtrArray curves;

  /// the corresponding parameters in v-direction, [0,1]
  Vector vp;
};

typedef boost::shared_ptr<LinearSurf> LinearSurfPtr;

#endif

