
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
 
#include "producttree.h"
#include "igesfile.h"
#include "igesdirentry.h"
#include "iges408.h"
#include "iges406.h"
#include "iges308.h"
#include "iges124.h"
#include <genua/dbprint.h>
#include <genua/trimesh.h>
#include <genua/parallel_loop.h>
#include <genua/synchron.h>
#include <boost/config.hpp>
#include <iostream>

using namespace std;

uint ProductTree::depth() const
{
  uint dep = 1;
  for (uint i=0; i<m_siblings.size(); ++i)
    dep = std::max(dep, m_siblings[i]->depth());
  return dep;
}

void ProductTree::enumerate(uint & offset)
{
  id( offset++ );
  const int nc = nchildren();
  for (int i=0; i<nc; ++i)
    m_siblings[i]->enumerate(offset);
}

XmlElement ProductTree::toXml(bool share) const
{
  XmlElement xe( Instance::toXml(share) );
  xe.rename("ProductTree");
  if (m_etype != NotFound)
    xe["entity_type"] = str(m_etype);
  const int nc = nchildren();
  xe["siblings"] = str(nc);
  for (int i=0; i<nc; ++i)
    xe.append( m_siblings[i]->toXml(share) );

  // if a parent node owns discrete geometry, it is a merged
  // representation of child node tesselations : save as well
  if (nc > 0 and m_cgr and m_cgr->ntriangles() > 0)
    xe.append( m_cgr->toXml(share) );

  return xe;
}

void ProductTree::fromXml(const XmlElement & xe)
{
  Instance::fromXml(xe);
  XmlElement::const_iterator ite, elast;
  elast = xe.end();
  for (ite = xe.begin(); ite != elast; ++ite) {
    if (ite->name() == "ProductTree") {
      ProductTree *p = new ProductTree;
      p->fromXml(*ite);
      m_siblings.push_back( ProductTreePtr(p) );
    } else if (ite->name() == "CgMesh") {
      m_cgr.reset(new CgMesh);
      m_cgr->fromXml( *ite );
    }
  }
}

bool ProductTree::fromIges(const IgesFile &file, uint ide, int importScope)
{
  clear();

  IgesDirEntry entry;
  file.dirEntry(ide, entry);
  if (not entry.valid())
    return false;

  id( ide );
  m_etype = entry.etype;
  if (not (IgesEntity::classOf(m_etype) & importScope))
    return false;

  IgesEntityPtr ep = file.createEntity(entry);
  if (not ep)
    return false;

  // default name is label
  rename( strip(std::string(entry.elabel, 8)) );

  // look for a name property
  IgesNameProperty nameProp;
  for (uint i=0; i<ep->nPropRef(); ++i) {
    if ( file.createEntity(ep->propRef(i), nameProp) ) {
      rename( nameProp.str() );
      break;
    }
  }

  // if name is empty, set name from IGES DE
  if (name().empty()) {
    rename( "DE"+str(ide)+" IGES"+str(m_etype) );
  }

  // extract transformation, if set
  IgesTrafoMatrix e124;
  int itf = ep->trafoMatrix();
  if (itf != 0) {
    IgesEntityPtr etp = file.createEntity(itf);
    if (IgesEntity::as(etp, e124)) {
      Mtx44 tfm;
      e124.toMatrix(tfm);
      Instance::m_placement.reconstruct(tfm);
    }
  }

  IgesSingularSubfigure e408;
  if (IgesEntity::as(ep, e408)) {

    if (itf == 0) {
      Instance::scale( e408.scl, e408.scl, e408.scl );
      Instance::translate( e408.xyz[0], e408.xyz[1], e408.xyz[2] );
    }

    // extract subfigure
    IgesSubfigure e308;
    if (file.createEntity(e408.subfigure(), e308)) {
      const Indices & esub( e308.subEntities() );
      rename( e308.name() );
      const int nsub = esub.size();
      //dbprint("Subfigure with", nsub, "entries:",e308.name());
      for (int j=0; j<nsub; ++j) {
        ProductTreePtr pchild = boost::make_shared<ProductTree>();
        pchild->m_parent = ProductTreePtr(this, null_deleter());
        if (pchild->fromIges(file, esub[j], importScope))
          m_siblings.push_back( pchild );
      }
    } else {
      dbprint("Subfigure not found.");
    }
  }

  return true;
}

void ProductTree::mergeNodeCg()
{
  // this is (optionally) called after tesselation only so that the discrete
  // geometry present at the leaf nodes is merged into the parent nodes of the
  // product tree hierarchy
  if (m_psf or m_pcv)
    return;

  const int n = m_siblings.size();
  if (n == 0) {
    m_cgr.reset();
    return;
  }

  m_cgr.reset(new CgMesh);
  for (int i=0; i<n; ++i) {
    ProductTree & child( *m_siblings[i] );
    child.mergeNodeCg();
    CgMeshPtr & ccg( child.m_cgr );
    if (ccg) {
      m_cgr->merge( *ccg );
    }
  }
}

void ProductTree::mergeCg(bool clearChildren)
{
  const int n = m_siblings.size();
  for (int i=0; i<n; ++i) {
    ProductTree & child( *m_siblings[i] );
    child.mergeCg(clearChildren);
    CgMeshPtr & ccg( child.m_cgr );
    if (ccg) {
      if (not m_cgr)
        m_cgr.reset(new CgMesh);
      Mtx44f tfm;
      child.currentTransform().matrix(tfm);
      m_cgr->merge( *ccg, tfm );
      if (clearChildren)
        ccg->clearMesh();
    }
  }
}

void ProductTree::collapseMesh()
{
  if (not m_cgr)
    m_cgr.reset(new CgMesh);



  // global counts
  size_t gnv, gnt, gnl;
  gnv = m_cgr->vertices().size();
  gnt = m_cgr->ntriangles();
  gnl = m_cgr->nlines();

  // descend tree and collect all CgMesh instances first
  // no point in parallelizing this - no real work done
  std::vector<ProductTree*> tomerge;
  {
    std::vector<ProductTree*> stack;
    stack.push_back(this);
    while (not stack.empty()) {
      ProductTree *p = stack.back();
      stack.pop_back();
      CgMesh *pcg = p->m_cgr.get();
      if ((pcg != 0) and (pcg->vertices().size() > 0)) {
        tomerge.push_back(p);
        gnv += pcg->vertices().size();
        gnt += pcg->ntriangles();
        gnl += pcg->nlines();
      } else {
        const int n = p->nchildren();
        for (int i=0; i<n; ++i)
          stack.push_back( p->child(i).get() );
      }
    }
  }

  // allocate space in global mesh before parallel tasks append
  m_cgr->reserve(gnv, gnt, gnl);

#ifndef BOOST_NO_CXX11_LAMBDAS

  Mutex guard;
  const size_t nm = tomerge.size();
  auto mergefun = [&] (size_t a, size_t b) {

    // to avoid unnecessary re-allocations, reserve space first
    CgMesh tmp;
    size_t nv(0), nt(0), nl(0);
    for (size_t i=a; i<b; ++i) {
      const CgMesh & cgi( *(tomerge[i]->m_cgr) );
      nv += cgi.vertices().size();
      nt += cgi.ntriangles();
      nl += cgi.nlines();
    }

    // actual work loop
    Mtx44 tfm;
    tmp.reserve(nv, nt, nl);
    for (size_t i=a; i<b; ++i) {
      ProductTree *p = tomerge[i];
      p->currentTransform().matrix(tfm);
      tmp.merge( *(p->m_cgr), tfm );
    }

    guard.lock();
    m_cgr->merge(tmp);
    guard.unlock();
  };
  parallel::block_loop(mergefun, size_t(0), size_t(nm));

#else // no c++11 lambda functions

  const size_t nm = tomerge.size();
  for (size_t i=0; i<nm; ++i) {
    Mtx44 tfm;
    ProductTree *p = tomerge[i];
    p->currentTransform().matrix(tfm);
    m_cgr->merge( *(p->m_cgr), tfm );
  }

#endif

  // at this point, reset all child meshes
  {
    std::vector<ProductTree*> stack;
    stack.push_back(this);
    while (not stack.empty()) {
      ProductTree *p = stack.back();
      stack.pop_back();
      CgMeshPtr ccg = p->cgRep();
      if ((ccg != nullptr) and (ccg->vertices().size() > 0)) {
        ccg.reset();
      } else {
        const int n = p->nchildren();
        for (int i=0; i<n; ++i)
          stack.push_back( p->child(i).get() );
      }
    }
  }

}

void ProductTree::toMxSection(MxMesh &mx) const
{
  if (not m_cgr)
    return;

  // generate a single section for this node
  uint rngBegin = mx.nelements();
  uint isec = mx.appendSection( *m_cgr );
  mx.section(isec).rename( name() );

  // and element groups for child nodes
  const int ns = m_siblings.size();
  for (int i=0; i<ns; ++i) {
    const CgMeshPtr & cgr( m_siblings[i]->cgRep() );
    if (not cgr)
      continue;
    uint ne = cgr->ntriangles();
    MxMeshBoco bc;
    bc.setRange(rngBegin, rngBegin+ne);
    bc.rename( m_siblings[i]->name() );
    mx.appendBoco(bc);
    rngBegin += ne;
  }
}

uint ProductTree::ntriangles() const
{
  if (m_cgr and m_cgr->ntriangles() > 0)
    return m_cgr->ntriangles();

  uint nt = 0;
  for (uint i=0; i<nchildren(); ++i)
    nt += m_siblings[i]->ntriangles();

  return nt;
}

void ProductTree::print(int indent) const
{
  string pre(indent, ' ');
  cout << pre << "ProductTree " << name() << ", id: " << m_iid;
  if (m_etype != NotFound)
    cout << ", IGES " << m_etype;
  const int n = m_siblings.size();
  if (n > 0)
    cout << ", siblings: " << m_siblings.size();
  cout << " cgr: " << m_cgr.get();
  const uint ntri = (m_cgr) ? m_cgr->ntriangles() : 0;
  const uint nlin = (m_cgr) ? m_cgr->nlines() : 0;
  if (ntri > 0)
    cout << ", triangles: " << ntri;
  if (nlin > 0)
    cout << ", lines: " << nlin;
  if ( (not m_psf) and (not m_pcv) )
    cout << " (discrete)";
  cout << endl;
  for (int i=0; i<n; ++i)
    m_siblings[i]->print(indent+2);
}

void ProductTree::connectParents(ProductTreePtr node)
{
  const size_t nsib = node->nchildren();
  for (size_t i=0; i<nsib; ++i) {
    node->child(i)->m_parent = node;
    ProductTree::connectParents( node->child(i) );
  }
}

void ProductTree::clear()
{
  m_siblings.clear();
  m_placement.identity();
}
