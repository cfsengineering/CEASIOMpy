
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
 
#ifndef SURF_MULTISURFPROJECTOR_H
#define SURF_MULTISURFPROJECTOR_H

#include "surface.h"
#include <genua/transformation.h>
#include <genua/boxsearchtree.h>
#include <boost/shared_ptr.hpp>

/** Project point onto nearest of multiple surfaces.

  MultiSurfProjector is a search data structure which allows to find the
  projection of a 3D point onto one of multiple surfaces which have been
  discretized before.

  \ingroup geometry
  \sa Surface
  */
class MultiSurfProjector
{
public:

  /// construct projector
  MultiSurfProjector();

  /// undefined/empty projector
  bool empty() const {return surfaces.empty();}

  /// number of surfaces attached
  uint size() const {return surfaces.size();}

  /// set transformation
  void transformation(const Trafo3d & t);

  /// append a surface patch to search structure
  void append(SurfacePtr psf, const PointList<2> & uv);

  /// append a surface and use the default grid pattern
  void append(SurfacePtr psf);

  /// construct vertex search tree
  void buildTree();

  /// clear stored data
  void clear();

  /// compute projected point on surface
  Vct3 project(const Vct3 & p) const;

protected:

  /// transformation mapping discretized surfaces to model space
  Mtx44 c2s, s2c;

  /// continuous surfaces
  std::vector<SurfacePtr> surfaces;

  /// list of parametric locations (u,v)
  PointList<2> parpos;

  /// surface index for each node
  Indices surfidx;

  /// vertex search tree
  BSearchTree btree;

  /// projection tolerance in 3D and uv-space
  Real pjtol, uvtol;
};

typedef boost::shared_ptr<MultiSurfProjector> MultiSurfProjectorPtr;

#endif // MULTISURFPROJECTOR_H
