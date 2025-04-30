
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
 
#ifndef SURF_PRODUCTTREE_H
#define SURF_PRODUCTTREE_H

#include "instance.h"
#include "forward.h"
#include <genua/cgmesh.h>
#include <genua/mxmesh.h>
#include <boost/shared_ptr.hpp>
#include <vector>

/** Tree structure for geometric instances.

  Base class for a memory representation of a hierarchical product structure.

  \ingroup geometry
  \sa Instance, CgMesh
 */
class ProductTree : public Instance
{
public:

  /// create empty tree
  ProductTree() : m_etype(NotFound) {}

  /// base class
  virtual ~ProductTree() {}

  /// number of child nodes
  uint nchildren() const {return m_siblings.size();}

  /// leaf node?
  bool leafNode() const {return (nchildren() == 0);}

  /// compute tree depth
  uint depth() const;

  /// append sibling node
  void append(ProductTreePtr p) { m_siblings.push_back(p); }

  /// access child node
  ProductTreePtr child(uint k) const {
    assert(k < nchildren());
    return m_siblings[k];
  }

  /// access CG representation
  CgMeshPtr cgRep() const {return m_cgr;}

  /// access CG representation
  void cgRep(const CgMeshPtr & cgr) {m_cgr = cgr;}

  /// whether this node is a surface object
  bool isSurface() const {return (m_psf.get() != 0);}

  /// whether this node is a curve object
  bool isCurve() const {return (m_pcv.get() != 0);}

  /// access surface
  SurfacePtr surface() const {return m_psf;}

  /// set surface pointer
  void surface(const SurfacePtr & psf) {m_psf = psf;}

  /// access curve (may be nil)
  AbstractCurvePtr curve() const {return m_pcv;}

  /// set curve pointer
  void curve(const AbstractCurvePtr & pcv) {m_pcv = pcv;}

  /// assign a sequence of IDs to the complete tree
  void enumerate(uint & offset);

  /// merge sibling tesselations into *this
  void mergeNodeCg();

  /// pull up child CgMesh representations
  void mergeCg(bool clearChildren);

  /// collapse mesh in parallel
  void collapseMesh();

  /// compute the number of triangles in the CG representation
  uint ntriangles() const;

  /// generate a section in MxMesh
  void toMxSection(MxMesh & mx) const;

  /// store as xml
  virtual XmlElement toXml(bool share) const;

  /// recover from xml
  virtual void fromXml(const XmlElement & xe);

  /// read as a flat object from IGES file
  bool fromIges(const IgesFile & file, uint ide, int importScope);

  /// clear all data
  virtual void clear();

  /// write out text representation (debugging)
  void print(int indent=0) const;

  /// reconnect parent nodes recursively
  static void connectParents(ProductTreePtr node);

protected:

  /// parent node
  ProductTreePtr m_parent;

  /// sibling nodes
  ProductArray m_siblings;

  /// surface pointer associated with this node, if any
  SurfacePtr m_psf;

  /// curve pointer associated with node, if any
  AbstractCurvePtr m_pcv;

  /// graphical representation (may be zero)
  CgMeshPtr m_cgr;

  /// IGES entity type
  uint m_etype;
};

//inline bool operator< (const ProductTreePtr & a, const ProductTreePtr & b)
//{
//  return a->id() < b.id();
//}

#endif // PRODUCTTREE_H
