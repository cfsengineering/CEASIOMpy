
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
 
#ifndef DCSPATIALGEOMETRY_H
#define DCSPATIALGEOMETRY_H

#include "dcgeometry.h"
#include <genua/point.h>

/** Three-dimensional Delaunay criteria.
 *
 * DcSpatialGeometry implements a three-dimensional intepretation of the
 * Delaunay criterion using circumspheres in 3D instead of circumcircles in
 * 2D. This corresponds to the criterion used by the legacy mesh
 * generation kernel DnMesh.
 *
 * \ingroup meshgen
 * \sa DelaunayCore
 */
class DcSpatialGeometry : public DcGeometry
{
public:

  /// empty geometry object
  DcSpatialGeometry(Real stmin=-0.1, Real stmax=1.1)
    : DcGeometry(stmin, stmax) {}

  /// check whether edge (as,at) intersects (bs,bt)
  virtual int edgesIntersect(uint as, uint at, uint bs, uint bt) const;

  /// encroachment criterion
  virtual bool encroaches(const DelaunayCore &core,
                          const uint vf[], uint v) const;

  /// true if vertex encroaches ball around protected edge
  virtual bool encroachesEdge(uint src, uint trg, uint v) const;

private:

  /// compute point on circumsphere
  void pointOnSphere(const uint vf[], Vct3 & pcs) const;

private:

  /// vertex array
  PointList<3> m_vtx;
};

#endif // DCSPATIALGEOMETRY_H
