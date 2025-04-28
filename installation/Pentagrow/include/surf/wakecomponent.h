
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
 
#ifndef SURF_WAKECOMPONENT_H
#define SURF_WAKECOMPONENT_H

#include "meshcomponent.h"
#include "wakesurf.h"

/** Manages surface mesh generation on wakes.

  Wakes are always connected to the trailing edge of lifting surfaces, which
  are a parametric surface boundary. To increase robustness, the connection of
  wake and wing mesh is not established by computed intersections, but rather
  by means of an explicit mesh dependency created by this class.

  Wakes are in general handled as unconstrained surfaces, they must therefore
  be explicitely registered as neighbors and children of the parent wing surface
  MeshComponent. WakeComponent implements/overloads the adapt() member which is
  called once after all other components have been refined, that is, after the
  wing mesh has reached its final shape. Then, the wake mesh is regenerated based
  on the current wing mesh, and wake-body intersections are introduced into the
  newly generated wake mesh.

  \ingroup geometry
  \sa MeshComponent, Surface
  */
class WakeComponent : public MeshComponent
{
public:

  /// initialize using surface alone
  WakeComponent(WakeSurfPtr wsp) : MeshComponent(wsp) {}

  /// initialize using surface and criterion
  WakeComponent(WakeSurfPtr wsp, const DnRefineCriterionPtr & pc) :
    MeshComponent(wsp, pc) {}

  /// destroy
  virtual ~WakeComponent() {}

  /// overloaded to call specialized mesh generation
  virtual void premesh(const PointGrid<2> & pgi = PointGrid<2>());

  /// overloaded to call specialized mesh generation
  virtual void premesh(const PointList<2> &, const Indices &);

  /// adapt to parent surface component
  virtual void adapt();

protected:

  /// modify vertex set to ensure merging of wing trailing-edge vertices
  virtual void transfer();

  /// evaluate parametric vertex
  Vct3 eval(uint k) const {
    return psf->eval( ppt[k][0], ppt[k][1] );
  }

private:

  /// create initial mesh for intersection computations
  void anyPremesh();

  /// transfer current component mesh to surface mesh generator (mg)
  void ppt2mg();

  /// generate a specialized mesh with expanding spacing
  void wakeMesh();

private:

  /// points along the parent surface boundary (u=0 boundary)
  Vector m_tedge, m_wedge;
};

typedef boost::shared_ptr<WakeComponent> WakeComponentPtr;

#endif // WAKECOMPONENT_H
