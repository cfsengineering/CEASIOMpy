
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
 
#ifndef SURF_SMBODYMESH_H
#define SURF_SMBODYMESH_H

#include "forward.h"
#include <surf/surface.h>
#include <genua/point.h>

/** Structural mesh on body segment.
 *
 * \ingroup structures
 * \sa SmWingMesh, SmRibMesh
 */
class SmBodyMesh
{
public:

  /// initialize with pointer to surface
  SmBodyMesh(SurfacePtr s) : m_psf(s) {}

  /// set pid to use for default surface elements
  void setMainPid(uint pid, uint mid=0) {m_pidmain = pid; m_mcid = mid;}

  /// place a longitudinal stiffener at u
  uint setLongeron(Real u, uint pidcap, uint pidweb=NotFound);

  /// place a circumferential stiffener at v
  uint setFrame(Real v, uint pidcap, uint pidweb=NotFound);

  /// register PID and MCID modification for rectangular box
  uint setBoxPid(const Vct2 & q1, const Vct2 & q2, uint pid, uint m_mcid);

  /// generate uv-space grid
  void grid(Real lmax, Real lmin, Real phimax);

  /// retrieve grid vertex
  const Vct3 & vertex(uint i, uint j) const {
    return m_pgrid(i,j);
  }

  /// generate grid, add quad elements to nastran mesh
  void addQuads(NstMesh & nst) const;

  /// access connection points (where stiffeners meet)
  const PointGrid<3> & findConnectors();

  /// connect to wing mesh at spanwise position vi
  uint rconnect(const SmWingMesh & wng, uint vi, NstMesh & nst) const;

private:

  /// pointer to fuselage
  SurfacePtr m_psf;

  /// uv-space mesh
  PointGrid<2> m_uvgrid;

  /// point grid for quad mesh, connection points
  PointGrid<3> m_pgrid, m_pcon;

  /// mean u/v values for grid lines
  Vector m_umean, m_vmean;

  /// property ids
  uint m_mcid, m_pidmain;

  /// stiffener pids
  Indices m_pidlongweb, m_pidlongcap, m_pidframeweb, m_pidframecap;

  /// indices for frame/longeron placement
  Indices m_ilong, m_jframe;

  /// register PID/MCID modifications on rectangular regions
  Indices m_ibox, m_jbox, m_boxpid, m_boxmcid;
};

#endif
