
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
 
#ifndef SURF_BASICPART_H
#define SURF_BASICPART_H

#include "forward.h"
#include "topopart.h"

/** Single-surface part.
 *
 * A simple topological component which contains only a single surface, and,
 * optionally, can generate simple cap surfaces. The main purpose of this
 * class is to make importing legacy geometry as straightforward as possible,
 * because this pattern maps directly to the special case of all body components
 * in smx 2.x
 *
 * \ingroup meshgen
 * \sa TopoPart, WingPart
 */
class BasicPart : public TopoPart
{
public:

  /// create empty part
  BasicPart(const std::string &s);

  /// base class
  virtual ~BasicPart();

  /// set surface and mesh criterion
  void surface(SurfacePtr psf, DcMeshCritBasePtr mcrit);

  /// access main surface, w/o caps
  const SurfacePtr &mainSurface() const {return m_surface;}

  /// assign mesh biasing (nose and tail)
  void meshBias(Real noseRefine, Real tailRefine);

  /// set boundary condition type to write into mesh for main surface
  void mainBocoType(uint bc) { m_bocoface[0] = bc; }

  /// set boundary condition type to write into mesh for main surface
  void capBocoType(uint side, uint bc);

  /// insert this part into the topology object
  virtual void inject(Topology &topo);

  /// generate a flat cap surface on boundary identified by side tag
  uint makeFlatCap(Topology &topo, uint sideTag);

  /// generate round cap, return face index
  uint makeRoundedCap(Topology &topo, uint sideTag, Real h=1.0);

  /// generate caps as defined in imported xml
  virtual void makeLegacyCaps(Topology &topo);

  /// append final face meshes to global (does no merge nodes)
  virtual void appendTo(const Topology &topo, MxMesh &mx, bool mergeBc=false);

  /// import legacy surface
  virtual void importLegacy(const XmlElement &xe);

private:

  /// the single surface
  SurfacePtr m_surface;

  /// mesh criterion for this surface
  DcMeshCritBasePtr m_mcrit;

  /// face index of the single surface and, optionally, the 4 caps
  uint m_iface[5];

  /// boundary conditions for faces; default is all walls
  uint m_bocoface[5];

  /// cap definitions found in smx file; negative means no cap
  Real m_capheight[4];

  /// surface periodicity
  bool m_uperiodic, m_vperiodic;

  /// refinement factors at nose (v=0) and tail
  Real m_noseRefine, m_tailRefine;
};

#endif // BASICPART_H
