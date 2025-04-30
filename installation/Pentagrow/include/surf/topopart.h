
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
 
#ifndef SURF_TOPOPART_H
#define SURF_TOPOPART_H

#include "forward.h"
#include <genua/propmacro.h>

/** Base class for mesh generation components assembled from multiple surfaces.
 *
 * Each part can consist of one or multiple surfaces, where the topology among
 * those surfaces is established by the TopoPart subclass.
 *
 *
 * \ingroup meshgen
 * \sa WingPart
 */
class TopoPart
{
public:

  /// named initialization
  TopoPart(const std::string &s) : m_name(s) {}

  /// base class
  virtual ~TopoPart();

  /// change part-specific configuration settings
  virtual void configure(const ConfigParser &cfg);

  /// insert this part into the topology object
  virtual void inject(Topology &topo) = 0;

  /// append final face meshes to global (does no merge nodes)
  virtual void appendTo(const Topology &topo, MxMesh &mx, bool mergeBc=false) = 0;

  /// (optionally) load geometry from legacy format (sumo 2.x)
  virtual void importLegacy(const XmlElement &xe);

  /// (optionally) generate cap surfaces for legacy geometry
  virtual void makeLegacyCaps(Topology &topo);

protected:

  /// utility: create crude initial mesh criterion if nothing else available
  static DcMeshCritPtr basicCriterion(const Surface &srf, Real rfactor=1.0);

  /// utility: add a topological face to mx, tagging with Mx::BocoType btyp
  static uint appendWithBC(const TopoFace &face, int btyp, MxMesh &mx);

protected:

  /// part name
  GENUA_PROP(std::string, name)
};

#endif // TOPOPART_H
