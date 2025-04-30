
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
 
#ifndef SURF_AIRFOILFITTER_H
#define SURF_AIRFOILFITTER_H

#include "forward.h"
#include <genua/forward.h>
#include <genua/point.h>

/** Fit airfoil to cut through mesh/geometry.
 *
 * This is a very specialized object which serves to generate airfoil sections
 * of reasonable geometric quality from sectional cuts through discrete
 * geometry. The purpose is to reconstruct airfoil coordinates from structural
 * or CFD meshes or tessellations created for visualization.
 *
 * \ingroup geometry
 * \sa Airfoil
 */
class AirfoilFitter
{
public:

  /// prescribe approximate chord direction and plane normal (ordering!)
  void principalDirections(const Vct3 &pcd, const Vct3 &pn) {
    m_guide = pcd.normalized();
    m_pln = pn.normalized();
  }

  /// fit airfoil to segments
  AirfoilPtr fitSegments(const PointList<3> &segm);

  /// access computed chord
  Real chord() const {return m_chord;}

  /// access computed origin (leading edge point)
  const Vct3 & origin() const {return m_ple;}

  /// return rotation vector
  void rotation(Vct3 &rot) const;

  /// transform 2D point set to input coordinate system
  void transform(const PointList<2> &crd, PointList<3> &pts) const;

private:

  ///  estimate principal chord direction if not given
  void estimatePrincipal(const PointList<3> &pts);

  /// transform input points to local coordinates
  void toLocal(const PointList<3> &pts);

  /// linear search for nearest segment
  uint nearestSegment(const Vct2 &p, Vct2 &ps) const;

  /// project point on segment k
  Real project(uint k, const Vct2 &p, Vct2 &ps) const;

  /// normalize coordinates and adapt transformation
  void normalizeCoordinates();

  /// fix coordinate ordering
  void reorder(PointList<2> &pts);

private:

  /// basic coordinate system
  Vct3 m_xax, m_yax, m_zax;

  /// estimated/prescribed chord direction
  Vct3 m_guide;

  /// estimated/prescribed foil plane
  Vct3 m_pln;

  /// input point set in local coordinates
  PointList<2> m_crd;

  /// leading edge point (0,0)
  Vct3 m_ple;

  /// chord length, relative thickness estimate
  Real m_chord, m_tcest;

};

#endif // AIRFOILFITTER_H
