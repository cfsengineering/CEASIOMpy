
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

#ifndef SURF_PLANARMESH_H
#define SURF_PLANARMESH_H

#include <genua/trimesh.h>
#include "planesurface.h"

/** Planar triangular mesh with cutouts.

  This is a wrapper which hides the complexity of the DnMesh Delaunay
  surface mesh generator in order to provide a simpler interface suitable for
  plane mesh generation problems e.g. in structural modeling.

  \ingroup meshgen
  \sa TriMesh
  */
class PlanarMesh
{
public:

  /// construct from plane point set
  void init(const PointList<3> & pts);
  
  /// add hole contour
  uint punch(const PointList<3> & h);

  /// enforce points to be present in mesh
  uint enforce(const PointList<3> & h);

  /// generate a triangular mesh
  void delaunay(Real maxaspect = 4.0, int npass=1);

  /// access resulting triangular mesh
  const TriMesh & mesh() const {return msh;}

  /// change mesh tag
  void meshTag(int t) {msh.faceTag(t);}

private:

  /// set of bounding points and hole marker points
  PointList<2> cbound, holemarker;

  /// hole contours
  std::vector<PointList<2> > choles, cforce;

  /// plane surface on which cbound is defined
  PlaneSurfacePtr psf;

  /// triangular mesh
  TriMesh msh;
};

#endif
