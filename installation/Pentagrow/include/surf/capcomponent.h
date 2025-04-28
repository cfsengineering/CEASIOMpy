
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
 
#ifndef SURF_CAPCOMPONENT_H
#define SURF_CAPCOMPONENT_H

#include "meshcomponent.h"

/** MeshComponent holding an end cap surface.

  CapComponent overloads the MeshComponent interface to account for the
  mesh dependency between main (parent) surface and an explicitely meshed
  end cap. The specialized mesh generation stage for end caps is necessary
  because end cap surfaces usually contain parametrization singularities which
  makes them unsuitable for the regular mesh generation procedure.

  \ingroup meshgen
  \sa MeshComponent, LongCap, RingCap
*/
class CapComponent : public MeshComponent
{
public:

  /// use long (grid) or ring-shaped (polar) cap
  enum Shape {LongCap, RingCap};

  /// initialize cap surface
  CapComponent(MeshComponentPtr parent, side_t side, Shape shape, Real hgt=0);

  /// destroy
  virtual ~CapComponent() {}

  /// overloaded to call specialized mesh generation
  virtual void premesh(const PointGrid<2> & pgi = PointGrid<2>());

  /// overloaded to call specialized mesh generation
  virtual void premesh(const PointList<2> &, const Indices &);

  /// adapt to parent surface component
  virtual void adapt();

  /// generate cap surface from parameter set
  static SurfacePtr createCap(const MeshComponent *main,
                              side_t side, Shape shape, Real hgt);

private:

  /// which side of parent is closed by this cap?
  side_t m_mainside;

  /// cap shape
  Shape m_shape;

  /// cap height parameter
  Real m_height;
};

typedef boost::shared_ptr<CapComponent> CapComponentPtr;

#endif // CAPCOMPONENT_H
