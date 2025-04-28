
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
 
#ifndef SURF_SMRIBMESH_H
#define SURF_SMRIBMESH_H

#include "forward.h"
#include "planarmesh.h"

/** Structural mesh for ribs.
 *
 * \ingroup structures
 * \sa SmBodyMesh, SmWingMesh, NstMesh
 */
class SmRibMesh
{
public:

  /// initialize with default values
  SmRibMesh() : m_ipid(0), m_imcid(0), m_npweb(5), m_maxstretch(3.5), m_ndpass(1), m_quadmesh(true) {}

  /// set number of point divisions in vertical direction
  void webPoints(uint nw) {m_npweb = nw;}

  /// change property ID
  void pid(uint p) {m_ipid = p;}

  /// change material coordinate system ID
  void mcid(uint m) {m_imcid = m;}

  /// append boundary points to list
  void bpoints(const Vct3 & top, const Vct3 & bot, bool isweb = false) {
    m_ptop.push_back(top);
    m_pbot.push_back(bot);
    if (isweb)
      m_iwebpos.push_back(m_ptop.size()-1);
  }

  /// specify cutout
  void punch(const PointList<3> & hole);

  /// change triangle mesh generation parameters
  void delaunayParameters(Real maxratio, uint npass) {
    m_maxstretch = maxratio;
    m_ndpass = npass;
  }

  /// add elements to Nastran mesh
  void addElements(NstMesh & nst);

private:

  /// utility : assemble boundary points (before punch)
  void initPlanarMesh();

private:

  /// boundary points on top and bottom wing surface
  PointList<3> m_ptop, m_pbot;

  /// indices in ptop/pbot where to enforce constraints
  Indices m_iwebpos;

  /// planar triangular mesh used for ribs with cutouts
  PlanarMesh m_plm;

  /// PID and material coordinate system ID, number of web points
  uint m_ipid, m_imcid, m_npweb;

  /// maximum allowd stretch ratio for triangle meshing
  Real m_maxstretch;

  /// number of triangle mesh refinement passes
  uint m_ndpass;

  /// whether to use structured quad or unstructured mesh
  bool m_quadmesh;
};


#endif
