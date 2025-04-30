
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

#ifndef SURF_LONGCAPSURF_H
#define SURF_LONGCAPSURF_H

#include "forward.h"
#include "spline.h"
#include "surface.h"

/** Special tip cap surface.

  Semi-elliptic interpolation surface for long and narrow mesh holes.
  
  \ingroup geometry
  \sa AsyComponent
  */
class LongCapSurf : public Surface
{
public:

  /// undefined surface
  LongCapSurf(const std::string &s = std::string("")) : Surface(s) {}

  /// construct surface
  LongCapSurf(const PointList<3> & pts, Real rh);

  /// initialize with boundary points, return breakpoint
  uint init(const PointList<3> & bp, Real rh);

  /// access edge curve at u = 0
  const Vector & westEdge() const {return m_vplo;}

  /// access edge curve at u = 1
  const Vector & eastEdge() const {return m_vphi;}

  /// evaluate cap surface
  Vct3 eval(Real u, Real v) const;

  /// compute derivative
  Vct3 derive(Real u, Real v, uint ku, uint kv) const;

  /// apply coordinate transformation
  void apply();

  /// access stored boundary segments
  const PointList<2> & boundary() const {return m_bsegm;}

  /// generate initial mesh
  void initMesh(const DnRefineCriterion & crit, DnMesh & gnr) const;

  /// generate discrete mesh specific for tip caps
  bool fixedMesh(PointList2d &puv, PointList3d &pts,
                 PointList3d &nrm, Indices &tri) const;

  /// mesh and merge with tglob, return true on success
  bool merge(TriMesh & tglob) const;

  /// project point on boundary
  Vct2 boundaryProjection(const Vct3 & p) const;

  /// XML output (inactive)
  XmlElement toXml(bool share=false) const;

  /// XML input (inactive)
  void fromXml(const XmlElement & xe);

  /// generate clone
  LongCapSurf *clone() const {return new LongCapSurf(*this);}

  // debug: write a visualization to file
  void writeViz(const std::string & fname) const;

private:

  /// project point on spline
  Real bproject(const Spline<3> & spl, const Vct3 & p) const;

  /// initialize the mesh for a kinked cap topology (wing tip)
  //void initMeshKinked(const DnRefineCriterion & c, DnMesh & gnr) const;

  /// previously used mesh initialization (r1208)
  void initMeshStd(const DnRefineCriterion & c, DnMesh & gnr) const;

  /// select far pivot by distance
  uint pivotByDistance(const PointList<3> & pts) const;

  /// select far pivot by median direction
  uint pivotByMedian(const PointList<3> & pts) const;

private:

  /// cubic splines for the two boundary curves and spine
  Spline<3> m_clo, m_chi, m_cspine;

  /// mesh generation constraints
  PointList<2> m_bsegm;

  /// stored edge parameterization
  Vector m_vplo, m_vphi;

  /// mean normal
  Vct3 m_nmean;

  /// flag: has base surface a kink or not?
  bool m_bKink;
};

#endif

