
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
 
#ifndef SUMO_FRAMEPROJECTOR_H
#define SUMO_FRAMEPROJECTOR_H

#include "forward.h"
#include "tritree.h"
#include <genua/trimesh.h>
#include <genua/transformation.h>

/** Efficiently project points onto reference geometry/mesh.


  \sa WingSkeleton, BodySkeleton
  */
class FrameProjector
{
public:

  typedef PointList<3,float> SegmentArray;

  /// empty projector
  FrameProjector();

  /// configuration settings
  Real minCosNormal() const {return mincosphi;}

  /// configuration settings
  void minCosNormal(Real x) {mincosphi = x;}

  /// check whether projector is initialized
  bool empty() const {return trees.empty();}

  /// set transformation from mesh to model space
  void transformation(const Trafo3d & mtraf);

  /// initialize from tessellation or mesh
  void buildTree(const Product & m);

  /// compute segments where quasi-infinite plane pln intersects mesh
  bool intersect(const Plane & pln, SegmentArray & seg) const;

  /// compute intersections with a plane of limited size
  bool intersect(const Vct3 &po, const Vct3 &pu, const Vct3 &pv,
                 SegmentArray &seg) const;

  /// clear out all data
  void clear();

  /// linear search over segments to locate best projection (good enough)
  Vct3 lproject(const SegmentArray & seg, const Vct3 & pt) const;

  /// consider only projections which fulfill normal deviation criterion
  Vct3 lproject(const SegmentArray & seg,
                const Vct3 & pt, const Vct3 & pn) const;

  /// transform segments from mesh to model space
  void modelSpaceSegments(const SegmentArray & segments,
                          PointList<3> & pts) const;

private:

  typedef std::vector<TriTree> TriTreeArray;

  /// intersection acceleration structure
  TriTreeArray trees;

  /// model radius in mesh space
  Real mradius;

  /// transformation mapping discretized surfaces to model space
  Mtx44 c2s, s2c;

  /// projection settings
  Real mincosphi;
};

#endif // FRAMEPROJECTOR_H
