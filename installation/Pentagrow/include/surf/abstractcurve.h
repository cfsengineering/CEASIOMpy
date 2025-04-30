
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
 
#ifndef SURF_ABSTRACTCURVE_H
#define SURF_ABSTRACTCURVE_H

#include "forward.h"
#include <genua/trafo.h>
#include <genua/xmlelement.h>

/** Base class for all curve objects.

  AbstractCurve is the base class for all curve objects. The most
  important child class is Curve, which represents a cubic spline
  curve.

  \ingroup geometry

  */
class AbstractCurve : public RFrame
{
public:

  /// unamed curve
  explicit AbstractCurve(const std::string & s = "") : ids(s) {}

  /// virtual destructor
  virtual ~AbstractCurve() {}

  /// change name
  void rename(const std::string & s) {ids = s;}

  /// return name
  const std::string & name() const {return ids;}

  /// create a clone
  virtual AbstractCurve *clone() const = 0;

  /// evaluate spline curve
  virtual Vct3 eval(Real t) const = 0;

  /// compute kth derivative
  virtual Vct3 derive(Real t, uint k) const = 0;

  /// apply hard transformation
  virtual void apply() = 0;

  /// compute point and first derivative in one sweep
  virtual void tgline(Real t, Vct3 & c, Vct3 & dc) const;

  /// compute curvature at t
  virtual Real curvature(Real t) const;

  /// generate a reasonable discretization
  virtual void initGrid(Vector & t) const;

  /// discretization based on simple criteria
  virtual uint discretize(const DcMeshCritBase &mcrit, Vector &t) const;

  /// discretized for visualization based on default grid
  virtual void tessellate(CgMesh & cgr) const;

  /// project point onto curve, starting at t
  virtual bool project(const Vct3 &pt, Real & s,
                       Real stol=gmepsilon, Real ttol=1e-6) const;

  /// compute intersection of curve with plane (pn,dp), return success
  virtual bool pierce(const Vct3 &pn, Real dp, Real &s, Real stol=gmepsilon) const;

  /// XML output
  virtual XmlElement toXml(bool share = false) const;

  /// XML input
  virtual void fromXml(const XmlElement & xe);

  /// write curve to iges file
  virtual int toIges(IgesFile & file, int tfi = 0) const;

  /// extract curve from iges file
  virtual bool fromIges(const IgesFile & file, const IgesDirEntry & dir);

  /// create curve from any xml representation
  static AbstractCurvePtr createFromXml(const XmlElement & xe);

  /// create curve from IGES entity
  static AbstractCurvePtr createFromIges(const IgesFile & file,
                                         const IgesDirEntry & entry);

  /// discretization from spline knot vector
  static void gridFromKnots(uint n, const Vector & kts, Vector & t,
                            Real tstart=0.0, Real tend=1.0);

  /** Parametrization of curve sets.

    Compute the arc-length parametrization of a set of curves. Returns the
    number of curves which end up on the same position as their predecessor. */
  static uint arclenParamet(const AbstractCurveArray & cpa, Vector & vp);

  /// find curves that fit together and create a composite curve, decimate list
  //static AbstractCurvePtr joinCurves(AbstractCurveArray &crv);

protected:

  /// extract name from IGES entry, if any
  void setIgesName(const IgesFile & file, const IgesEntity & e);

  /// extract referenced transformation matrix from IGES file, apply
  void setIgesTransform(const IgesFile & file, const IgesDirEntry & entry);

protected:

  /// curve object name
  std::string ids;
};

#endif // ABSTRACTCURVE_H
