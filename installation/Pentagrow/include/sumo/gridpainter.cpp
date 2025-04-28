
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
 
#include "glew.h"
#include "gridpainter.h"

GridPainter::GridPainter() : init(false)
{
  idispl = 0;
  memset(vbo, 0, sizeof(vbo));
  unity(vtf);
}

GridPainter::~GridPainter()
{
  if (useVbo) {
    const int nbuf = sizeof(vbo) / sizeof(uint);
    glDeleteBuffers(nbuf, vbo);
  } else {
    glDeleteLists(idispl, 1);
  }
}

void GridPainter::draw()
{
  // apply transformation
  glMatrixMode(GL_MODELVIEW);
  glPushMatrix();
  glMultMatrixf(vtf.pointer());

  glColor4fv(clr.pointer());

  if (useVbo)
    drawBuffers();
  else
    glCallList(idispl);

  glPopMatrix();
}

void GridPainter::use(const PointGrid<3> & vtx, const PointGrid<3> & nrm)
{
  // generate VBO if OpenGL 1.5 is supported
  if (not init) {
    if (GLEW_VERSION_1_5) {
      const int nbuf = sizeof(vbo) / sizeof(uint);
      std::fill(vbo, vbo+nbuf, 0);
      glGenBuffers(nbuf, vbo);
      useVbo = true;
    } else {
      useVbo = false;
      idispl = glGenLists(1);
    }
    init = true;
  }

  const int nr = vtx.nrows();
  const int nc = vtx.ncols();
  const int n = nr*nc;
  assert(nrm.nrows() == uint(nr));
  assert(nrm.ncols() == uint(nc));

  // convert geometry data to SP,
  // stored in column-major order in vf and nf
  vf.resize(n);
  nf.resize(n);
  for (int i=0; i<n; ++i) {
    for (int k=0; k<3; ++k) {
      vf[i][k] = (float) vtx[i][k];
      nf[i][k] = (float) nrm[i][k];
    }
  }

  // one quad strip between every two columns
  nstrips = nc - 1;
  striplen = 2*nr;
  strips.resize(nstrips * striplen);

  for (int j=0; j<nstrips; ++j) {
    const int ioff = nr*j;
    const int soff = striplen*j;
    for (int i=0; i<nr; ++i) {
      strips[soff + 2*i+0] = ioff + i;
      strips[soff + 2*i+1] = ioff + i + nr;
    }
  }

  if (useVbo)
    initBuffers();
  else
    initDisplayList();
}

void GridPainter::initBuffers()
{
  // construct pointer offsets
  poff.resize(nstrips);
  pcount.resize(nstrips);
  for (int i=0; i<nstrips; ++i) {
    pcount[i] = striplen;
    poff[i] = ((const char *) 0) + i*striplen*sizeof(uint);
  }

  // vertex buffers
  glBindBuffer(GL_ARRAY_BUFFER, vbo[0]);
  glBufferData(GL_ARRAY_BUFFER, sizeof(Vct3f)*vf.size(),
               vf.pointer(), GL_STATIC_DRAW);

  glBindBuffer(GL_ARRAY_BUFFER, vbo[1]);
  glBufferData(GL_ARRAY_BUFFER, sizeof(Vct3f)*nf.size(),
               nf.pointer(), GL_STATIC_DRAW);

  // quad strip indices
  glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo[2]);
  glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(uint)*strips.size(),
               &strips[0], GL_STATIC_DRAW);

  glBindBuffer(GL_ARRAY_BUFFER, 0);
}

void GridPainter::initDisplayList()
{
  glNewList(idispl, GL_COMPILE);

  for (int j=0; j<nstrips; ++j) {
    glBegin(GL_QUAD_STRIP);
    const uint *jstrip = &strips[j*striplen];
    for (int i=0; i<striplen; ++i) {
      glNormal3fv(nf[jstrip[i]].pointer());
      glVertex3fv(vf[jstrip[i]].pointer());
    }
    glEnd();
  }

  glEndList();
}

void GridPainter::drawBuffers()
{
  // draw using VBOs
  glEnableClientState(GL_VERTEX_ARRAY);
  glEnableClientState(GL_NORMAL_ARRAY);

  // identify buffers to use
  glBindBuffer(GL_ARRAY_BUFFER, vbo[0]);
  glVertexPointer(3, GL_FLOAT, 0, 0);
  glBindBuffer(GL_ARRAY_BUFFER, vbo[1]);
  glNormalPointer(GL_FLOAT, 0, 0);
  glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo[2]);

  // draw multiple quad strips at once
  glMultiDrawElements(GL_QUAD_STRIP, &pcount[0],
                      GL_UNSIGNED_INT, (const GLvoid **) &poff[0], nstrips);

  glDisableClientState(GL_NORMAL_ARRAY);
  glDisableClientState(GL_VERTEX_ARRAY);
}


