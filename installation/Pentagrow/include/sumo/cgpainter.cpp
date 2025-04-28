
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
 
#include "cgpainter.h"
#include "glew.h"
#include <surf/producttree.h>
#include <genua/cgmesh.h>

#include <iostream>
using namespace std;

CgPainter::CgPainter()
{
  m_pgcolor = Color(0.5f, 0.5f, 0.5f);
  m_lncolor = Color(0.0f, 0.0f, 0.0f);
  m_drawpg = true;
  m_drawln = true;

  m_ntrivx = m_nlinevx = 0;

  // invalidate all buffer and list indices
  const int nvb = sizeof(m_vbo) / sizeof(m_vbo[0]);
  std::fill(m_vbo, m_vbo+nvb, NotFound);
  m_idl = NotFound;
}

CgPainter::~CgPainter()
{
  if (m_vbo[0] != NotFound) {
    const int nvb = sizeof(m_vbo) / sizeof(m_vbo[0]);
    glDeleteBuffers(nvb, m_vbo);
  } else if (m_idl != NotFound) {
    glDeleteLists(m_idl, 1);
  }
}

void CgPainter::init()
{
  if ( GLEW_VERSION_1_5 ) {
    const int nvb = sizeof(m_vbo) / sizeof(m_vbo[0]);
    std::fill(m_vbo, m_vbo+nvb, 0);
    glGenBuffers(nvb, m_vbo);
  } else {
    m_idl = glGenLists(1);
  }
}

void CgPainter::attach(CgMeshPtr cgr)
{
  m_cgr = cgr;
}

void CgPainter::build()
{
  if (not m_cgr)
    return;

  if (m_vbo[0] == NotFound and m_idl == NotFound)
    init();

  if (m_vbo[0] != NotFound)
    copyBuffers();
  else if (m_idl != NotFound)
    compileList();
  else
    assert(!"CgPainter not initialized.");
}

void CgPainter::copyBuffers()
{
  if (not m_cgr)
    return;
  const CgMesh & cgm(*m_cgr);
  const PointList<3,float> & vtx( cgm.vertices() );
  const PointList<3,float> & nrm( cgm.normals() );

  // copy buffers to GPU memory
  if (not vtx.empty()) {
    glBindBuffer(GL_ARRAY_BUFFER, m_vbo[0]);
    glBufferData(GL_ARRAY_BUFFER, sizeof(Vct3f)*vtx.size(),
                 vtx.pointer(), GL_STATIC_DRAW);
  }

  if (not nrm.empty()) {
    glBindBuffer(GL_ARRAY_BUFFER, m_vbo[1]);
    glBufferData(GL_ARRAY_BUFFER, sizeof(Vct3f)*nrm.size(),
                 nrm.pointer(), GL_STATIC_DRAW);
  }

  Indices idx;
  cgm.toTriangles(idx);
  m_ntrivx = idx.size();
  uint nbytes = sizeof(uint)*idx.size();
  if (nbytes > 0) {
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m_vbo[2]);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, nbytes,
                 &idx[0], GL_STATIC_DRAW);
  }

  // lines ...
  idx.clear();
  cgm.toLines(idx);
  m_nlinevx = idx.size();
  nbytes = sizeof(uint)*idx.size();
  if (nbytes > 0) {
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m_vbo[3]);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, nbytes,
                 &idx[0], GL_STATIC_DRAW);
  }

  // unbind buffers
  glBindBuffer(GL_ARRAY_BUFFER, 0);
  glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
}

void CgPainter::compileList()
{
  if (not m_cgr)
    return;

  const CgMesh & cgm(*m_cgr);
  if (cgm.vertices().empty())
    return;

  glNewList(m_idl, GL_COMPILE);

  glEnableClientState(GL_VERTEX_ARRAY);
  glEnableClientState(GL_NORMAL_ARRAY);

  glVertexPointer(3, GL_FLOAT, 0, cgm.vertices().pointer());
  glNormalPointer(GL_FLOAT, 0, cgm.normals().pointer());

  if (m_drawpg) {
    Indices idx;
    cgm.toTriangles(idx);
    m_ntrivx = idx.size();
    if (not idx.empty()) {
      glColor4ubv( m_pgcolor.pointer() );
      glDrawElements(GL_TRIANGLES, m_ntrivx,
                     GL_UNSIGNED_INT, &idx[0]);
    }
  }

  if (m_drawln) {
    Indices idx;
    cgm.toLines(idx);
    m_nlinevx = idx.size();
    if (not idx.empty()) {
      glColor4ubv( m_lncolor.pointer() );
      glDrawElements(GL_LINES, idx.size(),
                     GL_UNSIGNED_INT, &idx[0]);
    }
  }

  glDisableClientState(GL_VERTEX_ARRAY);
  glDisableClientState(GL_NORMAL_ARRAY);

  glEndList();
}

void CgPainter::draw() const
{
  if (m_vbo[0] != NotFound) {

    // draw using VBOs : enable arrays
    glDisableClientState(GL_COLOR_ARRAY);
    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_NORMAL_ARRAY);

    // bind vertex and normal buffers
    glBindBuffer(GL_ARRAY_BUFFER, m_vbo[0]);
    glVertexPointer(3, GL_FLOAT, 0, 0);
    glBindBuffer(GL_ARRAY_BUFFER, m_vbo[1]);
    glNormalPointer(GL_FLOAT, 0, 0);

    if (m_drawpg) {
      glColor4ubv(m_pgcolor.pointer());
      glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m_vbo[2]);
      glDrawElements(GL_TRIANGLES, m_ntrivx, GL_UNSIGNED_INT, 0);
    }
    glDisableClientState(GL_NORMAL_ARRAY);

    if (m_drawln) {
      glColor4ubv(m_lncolor.pointer());
      glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m_vbo[3]);
      glDrawElements(GL_LINES, m_nlinevx, GL_UNSIGNED_INT, 0);
    }
    glDisableClientState(GL_VERTEX_ARRAY);

  } else if (m_idl != NotFound) {
    glCallList(m_idl);
  }
}

void CgPainter::boundingBox(const Mtx44f &m, Vct3f &lo, Vct3f &hi) const
{
  if (not m_cgr)
    return;

  const PointList<3,float> & vtx( m_cgr->vertices() );
  const int n = vtx.size();
  for (int i=0; i<n; ++i) {
    const Vct3f & p(vtx[i]);
    for (int k=0; k<3; ++k) {
      float t = m(k,0)*p[0] + m(k,1)*p[1] + m(k,2)*p[2] + m(k,3);
      lo[k] = std::min(t, lo[k]);
      hi[k] = std::max(t, hi[k]);
    }
  }
}

// --------------- CgPainterInstance -------------------------------------


void CgInstancePainter::appendChild(CgInstancePainterPtr cgp)
{
  m_siblings.push_back( cgp );
}

void CgInstancePainter::draw() const
{
  if ( (not m_painter) and (m_siblings.empty()) )
    return;

  Mtx44f drawTfm;
  unity(drawTfm);
  if (m_node)
    m_node->currentTransform().matrix(drawTfm);

  // apply transformation
  glMatrixMode( GL_MODELVIEW );
  glPushMatrix();
  glMultMatrixf( drawTfm.pointer() );

  if (m_painter)
    m_painter->draw();

  for (uint i=0; i<m_siblings.size(); ++i)
    if (m_siblings[i])
      m_siblings[i]->draw();

  glPopMatrix();
}

void CgInstancePainter::boundingBox(const Mtx44f & dtf,
                                    Vct3f &lo, Vct3f &hi) const
{
  Mtx44f tfm;
  unity(tfm);
  if (m_node)
    m_node->currentTransform().matrix(tfm);

  tfm = dtf*tfm;

  if (m_painter)
    m_painter->boundingBox( tfm, lo, hi );

  int nc = m_siblings.size();
  for (int i=0; i<nc; ++i)
    m_siblings[i]->boundingBox(tfm, lo, hi);
}

void CgInstancePainter::clear()
{
  m_node.reset();
  m_painter.reset();
  m_siblings.clear();
}


