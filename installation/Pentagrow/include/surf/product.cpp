
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
 
#include "product.h"
#include "igesfile.h"
#include "igesdirentry.h"
#include "iges144.h"
#include "stepfile.h"
#include "step_ap203.h"
#include "trimmedsurf.h"
#include "polysplinesurf.h"
#include <genua/mxmesh.h>
#include <genua/trimesh.h>
#include <genua/dbprint.h>
#include <genua/parallel_loop.h>
#include <genua/atomicop.h>
#include <iostream>

using namespace std;

void Product::fromSTL(const StringArray &files)
{
  clear();

  // import surfaces from files and build tree
  // which can be at most be three deep
  const int nfile = files.size();

  // load STL files in parallel -- cleanup, fixate, estimateNormals
  // is quite compute-intensive to construct as STL does not store that data
  std::vector<TriMesh> tms(nfile);
#pragma omp parallel for schedule(dynamic)
  for (int i=0; i<nfile; ++i) {
    tms[i].readSTL(files[i]);
    tms[i].cleanup(1e-6);
    tms[i].fixate(true);
    tms[i].estimateNormals();
  }

  for (int i=0; i<nfile; ++i) {

    // create a tree node for each STL file
    // set tree node name from filename
    ProductTreePtr fileNode(new ProductTree);
    string::size_type p1, p2, pa, pb, nc;
    p1 = files[i].find_last_of('/');
    p2 = files[i].find_last_of('\\');
    pb = files[i].find_last_of('.');
    pa = std::min(p1, p2);
    if (pa == string::npos)
      pa = 0;
    else
      ++pa;
    nc = std::min(pb-pa, files[i].size());
    fileNode->rename( files[i].substr(pa, pb-pa) );
    m_ptree->append( fileNode );

    int fileID = m_entities.size() + 1;

    const TriMesh & tm(tms[i]);
    Indices tags;
    tm.allTags(tags);
    const int nt = tags.size();
    if (nt < 2) {

      // if there is only a single solid in the STL file,
      // attach the cgr to the file node directly
      CgMeshPtr cgr(new CgMesh);
      cgr->importMesh(tm);
      cgr->detectEdges(gmepsilon, rad(44.0f));
      insert(fileID, cgr);
      fileNode->id( fileID );
      fileNode->cgRep( cgr );

    } else {

      const uint nv = tm.nvertices();

      for (int j=0; j<nt; ++j) {

        Indices vix;
        const int nf = tm.nfaces();
        for (int k=0; k<nf; ++k) {
          const TriFace & f( tm.face(k) );
          if ( uint(f.tag()) == tags[j]) {
            const uint *vi = f.vertices();
            vix.insert(vix.end(), vi, vi+3);
          }
        }

        const uint nt = vix.size()/3;
        CgMeshPtr cgr(new CgMesh);
        cgr->importMesh( nv, tm.vertices().pointer(),
                         tm.normals().pointer(), nt, &vix[0] );
        cgr->dropUnusedVertices();

        int solidID = m_entities.size() + 1;
        insert(solidID, cgr, Referenced | MeshOnly);

        // generate a tree node for each solid
        ProductTreePtr solidNode(new ProductTree);
        solidNode->rename(fileNode->name() + "Solid" + str(j+1));
        solidNode->id( solidID );
        solidNode->cgRep( cgr );
        fileNode->append( solidNode );
      }
    }
  }
}

void Product::fromIges(const IgesFile &file, int importScope)
{
  clear();

  // keep track of trimmed surface entries
  Indices dirTrimmedSurf, dirTrimmedCurve;

  // create all surfaces which are not trimmed surfaces
  IgesDirEntry entry;
  const int ndir = file.nDirEntries();
  dbprint(ndir, "entries found in IGES file, scope ", importScope);
  for (int i=0; i<ndir; ++i) {
    file.dirEntry(2*i+1, entry);
    int eClass = IgesEntity::classOf(entry.etype);
    dbprint("Entry ", 2*i+1, " type ", entry.etype, " class ", eClass);
    if (entry.etype == 408) {
      ProductTreePtr subtree = boost::make_shared<ProductTree>();
      if (subtree->fromIges(file, 2*i+1, importScope)) {
        if (subtree->name().empty())
          subtree->rename("DE"+str(2*i+1));
        m_ptree->append( subtree );
      }
    } else if ( (eClass & importScope) == 0 ) {
      continue;
    } else if ( eClass & IgesEntity::SurfaceClass ) {
      if (entry.etype != 144) {
        // surface, but not trimmed
        SurfacePtr psf = Surface::createFromIges(file, entry);
        if (psf) {
          if (psf->name().empty())
            psf->rename("DE"+str(2*i+1)+" IGES"+str(entry.etype));
          insert(2*i+1, psf);
        }
      } else {
        // trimmed surface
        dirTrimmedSurf.push_back(2*i+1);
      }
    } else if ( eClass & (IgesEntity::CurveClass | IgesEntity::LineClass) ) {
      if (entry.etype != 142) {
        // curve, but not trimmed
        AbstractCurvePtr psf = AbstractCurve::createFromIges(file, entry);
        if (psf) {
          if (psf->name().empty())
            psf->rename("DE"+str(2*i+1)+" IGES"+str(entry.etype));
          insert(2*i+1, psf);
        }
      } else {
        // trimmed curve, not processed yet
        dirTrimmedCurve.push_back(2*i+1);
      }
    } else {
      dbprint("Will not generate instance for entry ",2*i+1," type ",entry.etype);
    }
  }

  // now, create trimmed surfaces which re-use existing surface objects
  const int ntrim = dirTrimmedSurf.size();
  for (int i=0; i<ntrim; ++i) {
    file.dirEntry(dirTrimmedSurf[i], entry);
    IgesTrimmedSurface e144;
    if (not file.createEntity(entry, e144))
      continue;
    EntityMap::iterator pos = m_entities.find(e144.pts);
    if (pos == m_entities.end())
      continue;
    pos->second.status |= BaseSurface;
    SurfacePtr baseSurf = pos->second.psf;
    if (not baseSurf)
      continue;
    TrimmedSurf *ptrim = new TrimmedSurf;
    if (ptrim->fromIges(file, entry, baseSurf)) {
      if (ptrim->name().empty())
        ptrim->rename("DE"+str(dirTrimmedSurf[i])+" IGES144");
      insert(dirTrimmedSurf[i], SurfacePtr(ptrim));
    }
  }

  // finally, associate product tree leaf nodes with surfaces
  assignSurfaces(m_ptree);

  // create product tree entries for top-level surfaces
  size_t nsf(0), ncv(0);
  EntityMap::iterator itr, last = m_entities.end();
  for (itr = m_entities.begin(); itr != last; ++itr) {
    if (itr->second.status == TopLevel) {
      ProductTreePtr leaf( new ProductTree );
      leaf->id( itr->first );
      SurfacePtr psf = itr->second.psf;
      if (psf) {
        leaf->rename( psf->name() );
        leaf->surface( psf );
        ++nsf;
      }
      AbstractCurvePtr pcv = itr->second.pcv;
      if (pcv) {
        leaf->rename( pcv->name() );
        leaf->curve( pcv );
        ++ncv;
      }
      leaf->cgRep( itr->second.cgr );
      m_ptree->append(leaf);
    }
  }

  ProductTree::connectParents(m_ptree);

  dbprint("IGES product: ",nsf,"surfaces",ncv,"curves.");
}

void Product::fromStep(const StepFile &file)
{
  // shorter notation
  typedef StepBSplineSurfaceWithKnots StepPolySrf;

  clear();

  StepFile::const_iterator itr, last;
  last = file.end();
  for (itr = file.begin(); itr != last; ++itr) {
    const StepEntityPtr & eptr( *itr );
    const StepPolySrf *sps = dynamic_cast<const StepPolySrf*>( eptr.get() );
    if (sps != 0) {
      PolySplineSurfPtr pss(new PolySplineSurf);
      if ( pss->fromStep( file, sps ) ) {
        if (pss->name().empty())
          pss->rename("STEP"+str(eptr->eid));
        CgMeshPtr cgr = insert(eptr->eid, pss);
        ProductTreePtr treeNode( new ProductTree );
        treeNode->id( eptr->eid );
        treeNode->surface( pss );
        treeNode->cgRep( cgr );
        treeNode->rename( pss->name() );
        m_ptree->append( treeNode );
      }
    }
  }
}

void Product::assignSurfaces(ProductTreePtr subtree)
{
  const int nchild = subtree->nchildren();
  for (int i=0; i<nchild; ++i) {
    const ProductTreePtr & child( subtree->child(i) );
    EntityMap::iterator pos = m_entities.find(child->id());
    if (pos != m_entities.end()) {
      child->surface( pos->second.psf );
      child->curve( pos->second.pcv );
      child->cgRep( pos->second.cgr );
    }
    if (child->leafNode()) {
      if (pos != m_entities.end())
        pos->second.status |= Referenced;
    } else {
      assignSurfaces(child);
    }
  }
}

uint Product::tessellate(uint maxtri)
{
  const int n = m_entities.size();
  Vector surfaceArea(n);
  Real areaSum = 0.0;

  BEGIN_PARLOOP_CHUNK(0, n, 32)
  for (int i=a; i<b; ++i) {
    EntityMap::iterator itr = m_entities.begin();
    std::advance(itr, i);
    EntityIndex & idx(itr->second);
    if ( (not (idx.status & BaseSurface)) and (idx.psf) ) {
      Surface::DimStat tStat;
      idx.psf->dimStats(tStat);
      surfaceArea[i] = tStat.area;
      atomic_add(areaSum, tStat.area);
    }
  }
  END_PARLOOP_CHUNK

  BEGIN_PARLOOP(0, n)
  for (int i=a; i<b; ++i) {
    EntityMap::iterator itr = m_entities.begin();
    std::advance(itr, i);
    EntityIndex & idx(itr->second);

    if (idx.psf and ((idx.status & BaseSurface) == 0) ) {

      // assign triangle count according to estimated surface area
      // not optimal for trimmed surfaces

      // assign at least 0.1% of total triangle budget to each surface
      Real areaFraction = std::max(0.001, surfaceArea[i]/areaSum);

      // assign at least a maximum of 4000 triangles
      uint ntri = std::max(4000u, uint(areaFraction*maxtri));
      idx.tesselate(ntri);

    } else if (idx.pcv) {
      idx.tesselate();
    }
  }
  END_PARLOOP

  return m_ptree->ntriangles();
}

void Product::collapseMesh()
{
  // m_ptree->mergeCg(true);
  m_ptree->collapseMesh();
}

void Product::toMx(MxMesh &mx) const
{
  mx.clear();

  const int m = m_ptree->nchildren();
  for (int i=0; i<m; ++i)
    m_ptree->child(i)->toMxSection(mx);
}

void Product::fromMx(const MxMesh &mx)
{
  clear();

  int ivi[48];
  uint lvi[48];
  Indices tri;
  const int nsec = mx.nsections();
  const int nboc = mx.nbocos();

  // first, look for farfield bocos. if any are found, import
  // elements by bocos, otherwise, by sections
  bool haveFarfield = false;
  for (int i=0; i<nboc; ++i)
    haveFarfield |= ( mx.boco(i).bocoType() == Mx::BcFarfield )
        or ( mx.boco(i).bocoType() == Mx::BcWakeSurface );

  if (haveFarfield) {

    Indices elements;
    for (int i=0; i<nboc; ++i) {

      const MxMeshBoco & bc( mx.boco(i) );
      if ((bc.bocoType() == Mx::BcFarfield) or
          (mx.boco(i).bocoType() == Mx::BcWakeSurface))
        continue;

      tri.clear();
      bc.elements(elements);
      const int ne = elements.size();
      uint isec, nv;
      for (int j=0; j<ne; ++j) {
        const uint *vix = mx.globalElement(elements[j], nv, isec);
        int ntv = 3*mx.section(isec).triangleVertices(ivi);
        for (int k=0; k<ntv; ++k)
          lvi[k] = vix[ivi[k]];
        tri.insert(tri.end(), lvi, lvi+ntv);
      }

      importElements(i, bc.name(), mx.nodes(), tri);
    }

  } else {

    // no farfield bocos, import by section instead

    for (int i=0; i<nsec; ++i) {

      // ignore anything which is not a surface section
      const MxMeshSection & sec( mx.section(i) );
      if (not sec.surfaceElements())
        continue;

      // discretize surface sections using triangles
      tri.clear();
      sec.toTriangles(tri);
      //      const int ntv = 3*sec.triangleVertices(ivi);
      //      const int ne = sec.nelements();
      //      for (int j=0; j<ne; ++j) {
      //        const uint *vix = sec.element(j);
      //        for (int k=0; k<ntv; ++k)
      //          lvi[k] = vix[ivi[k]];
      //        tri.insert(tri.end(), lvi, lvi+ntv);
      //      }

      importElements(i, sec.name(), mx.nodes(), tri);
    }

  } // no farfield
}

void Product::importElements(int id, const string &meshName,
                             const PointList<3> &vtx, const Indices &tri)
{
  CgMeshPtr cgr(new CgMesh);
  const int ntri = tri.size() / 3;
  cgr->importMesh( vtx.size(), vtx.pointer(), (const double * ) 0,
                   ntri, &tri[0] );
  // cgr->dropUnusedVertices();

  insert(id, cgr);

  // generate tree node
  ProductTreePtr treeNode(new ProductTree);
  treeNode->rename( meshName );
  treeNode->id( id );
  treeNode->cgRep( cgr );
  m_ptree->append(treeNode);
}

void Product::clear()
{
  m_entities.clear();
  m_ptree.reset(new ProductTree);
  m_ptree->id(0);
  m_ptree->rename("Product");
}

void Product::print() const
{
  const int ns = m_entities.size();
  cout << ns << " Surfaces:" << endl;
  EntityMap::const_iterator itr, last = m_entities.end();
  for (itr = m_entities.begin(); itr != last; ++itr) {
    const EntityIndex & idx( itr->second );
    cout << "Key " << itr->first
         << " Status: " << idx.status;
    if (idx.psf)
      cout << " Name: " << idx.psf->name();
    if (idx.cgr)
      cout << " Triangles: " << idx.cgr->ntriangles()
           << " Lines: " << idx.cgr->nlines();
    cout << endl;
  }

  cout << "Structure:" << endl;
  m_ptree->print(0);
}

XmlElement Product::toXml(bool share) const
{
  XmlElement xp("Product");

  EntityMap::const_iterator itr, last = m_entities.end();
  for (itr = m_entities.begin(); itr != last; ++itr) {
    XmlElement xsi( itr->second.toXml(share) );
    xsi["id"] = str(itr->first);
    xp.append(xsi);
  }

  if (m_ptree)
    xp.append(m_ptree->toXml(share));

  return xp;
}

void Product::fromXml(const XmlElement &xe)
{
  if (xe.name() == "MxMesh") {
    MxMesh mx;
    mx.fromXml(xe);
    fromMx(mx);
    return;
  }

  // load surfaces
  m_entities.clear();
  XmlElement::const_iterator itr, last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "Part") {
      EntityIndex part;
      part.fromXml(*itr);
      uint key = Int( itr->attribute("id") );
      m_entities.insert(  make_pair(key, part) );
    } else if (itr->name() == "ProductTree") {
      m_ptree.reset(new ProductTree);
      m_ptree->fromXml(*itr);
    }
  }

  if (m_ptree)
    assignSurfaces(m_ptree);
}

// ---------------- embedded class SurfaceIndex -----------------------------

XmlElement Product::EntityIndex::toXml(bool share) const
{
  XmlElement xsi("Part");
  xsi["status"] = str(status);
  if (cgr)
    xsi.append( cgr->toXml(share) );
  if (psf)
    xsi.append( psf->toXml(share) );
  return xsi;
}

void Product::EntityIndex::fromXml(const XmlElement &xe)
{
  cgr.reset();
  psf.reset();
  status = xe.attr2int("status", 0);
  XmlElement::const_iterator itr, last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "CgMesh") {
      cgr.reset(new CgMesh);
      cgr->fromXml(*itr);
    } else {
      psf = Surface::createFromXml(*itr);
    }
  }
}

