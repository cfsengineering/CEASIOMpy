
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
 
#include "productpainter.h"
#include "glew.h"
#include <genua/xcept.h>
#include <surf/product.h>
#include <surf/producttree.h>
#include <deque>
#include <iostream>

using namespace std;

ProductPainter::ProductPainter()
{
  // create empty dummy product to allow storing a transformation
  m_root.reset( new ProductTree );
}

void ProductPainter::drawPolygons(bool flag)
{
  PainterMap::const_iterator itr, last = m_painter.end();
  for (itr = m_painter.begin(); itr != last; ++itr)
    itr->second->drawPolygons(flag);
}

void ProductPainter::drawLines(bool flag)
{
  PainterMap::const_iterator itr, last = m_painter.end();
  for (itr = m_painter.begin(); itr != last; ++itr)
    itr->second->drawLines(flag);
}

const Trafo3d & ProductPainter::transformation() const
{
  assert(m_root);
  return m_root->currentTransform();
}

void ProductPainter::transformation(const Trafo3d &tf)
{
  if (not m_root)
    return;

  m_root->transform(tf);
}

void ProductPainter::init(const Product & prod)
{
  m_painter.clear();
  m_rootpainter.reset();
  m_root = prod.rootNode();
  if (not m_root)
    return;

  // if the mesh is already collapsed into the root node, just create a
  // single painter
  CgMeshPtr rootMesh( m_root->cgRep() );
  if (rootMesh)
    cout << "Root node has " << rootMesh->ntriangles() << endl;

  if (rootMesh and (rootMesh->ntriangles() > 0)) {

    CgPainterPtr rootPainter(new CgPainter);
    rootPainter->attach( rootMesh );
    rootPainter->polygonColor( Color(0.5f, 0.5f, 0.5f) );
    m_painter.insert( make_pair(0, rootPainter) );

    // m_instances.push_back( CgInstancePainter(rootPainter,
    //                                          m_root->currentTransform()) );
    m_rootpainter.reset( new CgInstancePainter(rootPainter, m_root) );

    return;
  }

  // create one mesh renderer for each part/surface in product
  PainterCreator creator(m_painter);
  prod.foreachMesh(creator);

  CgPainterPtr rootMeshPainter;
  PainterMap::const_iterator pos;
  pos = m_painter.find( m_root->id() );
  if (pos != m_painter.end())
    rootMeshPainter = pos->second;

  m_rootpainter.reset( new CgInstancePainter(rootMeshPainter, m_root) );
  buildPainterTree(m_rootpainter, m_root);


//  // create an instance for each tree node
//  std::deque<ProductTreePtr> queue;
//  queue.push_back(prod.rootNode());

//  while (not queue.empty()) {
//    ProductTreePtr node( queue.front() );
//    queue.pop_front();
//    const int nc = node->nchildren();
//    for (int i=0; i<nc; ++i)
//      queue.push_back(node->child(i));

//    PainterMap::const_iterator pos;
//    pos = m_painter.find( node->id() );
//    if (pos != m_painter.end())
//      m_instances.push_back( CgInstancePainter(pos->second,
//                                               node->currentTransform()) );
//  }
}

void ProductPainter::build()
{
  PainterMap::const_iterator itr, last = m_painter.end();
  for (itr = m_painter.begin(); itr != last; ++itr)
    itr->second->build();
}

void ProductPainter::buildPainterTree(CgInstancePainterPtr ip,
                                      ProductTreePtr pnode)
{
  if ( (not pnode) or (not ip) )
    return;

  const int nc = pnode->nchildren();
  for (int j=0; j<nc; ++j) {
    CgPainterPtr cgp;
    ProductTreePtr pchild = pnode->child(j);
    CgInstancePainterPtr ipj;
    if (not pchild) {
      ipj.reset( new CgInstancePainter(cgp, pchild) );
    } else {
      PainterMap::const_iterator pos;
      pos = m_painter.find( pchild->id() );
      if (pos != m_painter.end())
        cgp = pos->second;
      ipj.reset( new CgInstancePainter(cgp, pchild) );
      buildPainterTree( ipj, pchild );
    }
    ip->appendChild( ipj );
  }
}

void ProductPainter::draw() const
{
//  Mtx44f tfm;
//  transformation().matrix( tfm );

//  // apply transformation
//  glMatrixMode(GL_MODELVIEW);
//  glPushMatrix();
//  glMultMatrixf(tfm.pointer());

//  const int nip = m_instances.size();
//  for (int i=0; i<nip; ++i)
//    m_instances[i].draw();

  if (m_rootpainter)
    m_rootpainter->draw();

//  glPopMatrix();
}

void ProductPainter::boundingBox(Vct3f &lo, Vct3f &hi) const
{
  Mtx44f tfm;
  // transformation().matrix( tfm );
  unity(tfm);

//  const int nip = m_instances.size();
//  for (int i=0; i<nip; ++i)
//    m_instances[i].boundingBox(tfm, lo, hi);

  if (m_rootpainter)
    m_rootpainter->boundingBox(tfm, lo, hi);

  // debug
  cout << "ProductPainter t/bb: " << lo << hi << endl;
}

