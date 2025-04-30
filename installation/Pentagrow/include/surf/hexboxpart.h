
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
 
#ifndef SURF_HEXBOXPART_H
#define SURF_HEXBOXPART_H

#include "forward.h"
#include "topopart.h"
#include <genua/svector.h>
#include <genua/propmacro.h>
#include <genua/mxmeshtypes.h>

/** Hexahedral box.
 *
 * Intended for modeling farfield boxes and wind-tunnel walls, surfaces are
 * instantiated so that surface normal vectors point inward.
 *
 * \ingroup geometry
 * \sa WingPart, Topology
 */
class HexBoxPart : public TopoPart
{
public:

  enum SideType { LeftSide=0, TopSide, RightSide,
                  BottomSide, FrontSide, RearSide };

  /// create a default, axis-aligned box centered at (0,0,0)
  HexBoxPart(const std::string &s);

  /// leave directions as they are, but scale
  void rescale(Real l, Real w, Real h);

  /// set mesh quality criterion for all walls
  void meshQuality(DcMeshCritBasePtr crit) {m_mcrit = crit;}

  /// inject into topology
  virtual void inject(Topology &topo);

  /// access face index for side s (NotFound before initialized)
  uint faceIndex(SideType s) {
    return m_ifaces[int(s)];
  }

  /// set boundary condition on side s
  void boco(SideType s, Mx::BocoType b) {
    m_bctype[int(s)] = b;
  }

  /// imprint topological edge on side s
  void imprint(Topology &topo, uint eix, SideType s);

  /// once topo has meshed all faces, add triangle meshes to to mx
  virtual void appendTo(const Topology &topo, MxMesh &mx, bool mergeBc=false);

private:

  /// indices of my TopoFaces in global Topology object
  uint m_ifaces[6];

  /// indices of my mesh bocos in global MxMesh object
  uint m_ibocos[6];

  /// surface objects for the 6 sides
  PlaneSurfacePtr m_sides[6];

  /// mesh quality criterion assign to all faces
  DcMeshCritBasePtr m_mcrit;

  /// boundary conditions for the sides (default: all farfield)
  Mx::BocoType m_bctype[6];

  GENUA_PROP(Vct3, center)
  GENUA_PROP(Vct3, length)
  GENUA_PROP(Vct3, width)
  GENUA_PROP(Vct3, height)
  GENUA_PROP(std::string, name)
};

#endif // HEXBOXPART_H
