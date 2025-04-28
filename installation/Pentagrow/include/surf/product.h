
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
 
#ifndef SURF_PRODUCT_H
#define SURF_PRODUCT_H

#include "forward.h"
#include "producttree.h"
#include "surface.h"
#include "abstractcurve.h"
#include "igesentity.h"

/** Structure, surface geometry and tessellation of surface model.

  \ingroup geometry
  \sa ProductTree, Instance
  */
class Product
{
public:

  enum SurfaceStatus {TopLevel = 0, BaseSurface = 1,
                      Referenced = 4, MeshOnly = 8};

  /// create empty product
  Product() {}

  /// insert a surface, detached from product structure
  CgMeshPtr insert(uint index, SurfacePtr psf) {
    EntityIndex idx;
    idx.psf = psf;
    idx.cgr = boost::make_shared<CgMesh>();
    m_entities.insert( std::make_pair(index,idx) );
    return idx.cgr;
  }

  /// insert a surface, detached from product structure
  CgMeshPtr insert(uint index, AbstractCurvePtr psf) {
    EntityIndex idx;
    idx.pcv = psf;
    idx.cgr = boost::make_shared<CgMesh>();
    m_entities.insert( std::make_pair(index,idx) );
    return idx.cgr;
  }

  /// insert a discrete surface, detached from product structure
  void insert(uint index, CgMeshPtr pcg, int status = MeshOnly) {
    EntityIndex idx;
    idx.cgr = pcg;
    idx.status = MeshOnly | status;
    m_entities.insert( std::make_pair(index,idx) );
  }

  /// number of referenced surfaces stored
  uint nsurfaces() const {return m_entities.size();}

  /// locate surface with key k
  SurfacePtr findSurface(uint k) const {
    EntityMap::const_iterator itr = m_entities.find(k);
    if (itr != m_entities.end())
      return itr->second.psf;
    else
      return SurfacePtr();
  }

  /// populate product tree by reading IGES file
  void fromIges(const IgesFile & file, int importScope = IgesEntity::AnyClass);

  /// populate product tree by reading STEP AP203 file (very limited support)
  void fromStep(const StepFile & file);

  /// (re-) generate all surface discretizations, return number of triangles
  uint tessellate(uint maxtri=2000000);

  /// import from multiple STL files
  void fromSTL(const StringArray & files);

  /// access root node
  ProductTreePtr rootNode() const {return m_ptree;}

  /// collapse complete discrete geometry into root node
  void collapseMesh();

  /// convert top-level tree nodes to MxMesh for visualization in scope
  void toMx(MxMesh & mx) const;

  /// import an MxMesh and create a tree node from each section
  void fromMx(const MxMesh & mx);

  /// iteration over each surface object
  template <class Functor>
  void foreachSurface(Functor & srfFunction) const {
    EntityMap::const_iterator itr, last = m_entities.end();
    for (itr = m_entities.begin(); itr != last; ++itr)
      srfFunction( itr->first, itr->second.psf );
  }

  /// iteration over each mesh object
  template <class Functor>
  void foreachMesh(Functor & cgmFunction) const {
    EntityMap::const_iterator itr, last = m_entities.end();
    for (itr = m_entities.begin(); itr != last; ++itr)
      cgmFunction( itr->first, itr->second.cgr );
  }

  /// generate an XML representation
  XmlElement toXml(bool share = false) const;

  /// recover from XML representation
  void fromXml(const XmlElement & xe);

  /// erase all data
  void clear();

  /// write out structure (debugging)
  void print() const;

protected:

  /// assign surfaces to children of subtree
  void assignSurfaces(ProductTreePtr subtree);

  /// utility used for mesh element import
  void importElements(int id, const std::string &meshName,
                      const PointList<3> &vtx, const Indices &tri);

protected:

  /** Internal entity data */
  struct EntityIndex {

    /// create default empty index
    EntityIndex() : status(TopLevel) {}

    /// update discretization
    void tesselate(uint maxtri=60000) {
      if  (psf and cgr)
        psf->tessellate(*cgr, maxtri);
      else if (pcv and cgr)
        pcv->tessellate(*cgr);
    }

    /// create XML representation
    XmlElement toXml(bool share) const;

    /// recover from XML representation
    void fromXml(const XmlElement &xe);

    /// pointer to surface
    SurfacePtr psf;

    /// pointer to curve
    AbstractCurvePtr pcv;

    /// tessellation (may be null)
    CgMeshPtr cgr;

    /// indicates how the surface is referenced
    int status;
  };

  typedef std::map<uint,EntityIndex> EntityMap;

  /// surface-to-index mapping
  EntityMap m_entities;

  /// tree structure
  ProductTreePtr m_ptree;
};

#endif // PRODUCT_H
