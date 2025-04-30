
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
 
#include "hedgehogplotter.h"
#include "glew.h"
#include <genua/mxmesh.h>
#include <iostream>

using namespace std;

HedgehogPlotter::~HedgehogPlotter()
{
  if (m_vbo != NotFound)
    glDeleteBuffers(1, &m_vbo);
  if (m_idl != NotFound)
    glDeleteLists(m_idl, 1);
}

void HedgehogPlotter::nodalLengths(const MxMesh &mx, const Indices &nodeList)
{
  // gather elements shared by nodes in list
  const int nn = nodeList.size();
  const ConnectMap & v2e( mx.v2eMap() );
  m_nodalLength.resize(nn);
  DVector<int> nva(nn, 0);
  for (int i=0; i<nn; ++i) {
    int lmap[24], nl;
    const int inode = nodeList[i];
    const int nnb = v2e.size(inode);
    const uint *nbe = v2e.first(inode);
    for (int j=0; j<nnb; ++j) {
      uint nev, isec;
      const uint *v = mx.globalElement(nbe[j], nev, isec);
      nl = mx.section(isec).lineVertices(lmap);
      for (int k=0; k<nl; ++k) {
        uint src = v[lmap[2*k+0]];
        uint trg = v[lmap[2*k+1]];
        float len = norm( mx.node(src) - mx.node(trg) );
        uint sidx = sorted_index(nodeList, src);
        uint tidx = sorted_index(nodeList, trg);
        if (sidx != NotFound) {
          m_nodalLength[sidx] += len;
          ++nva[sidx];
        }
        if (tidx != NotFound) {
          m_nodalLength[tidx] += len;
          ++nva[tidx];
        }
      } // k, line
    } // j, nb element
  } // i, node

  for (int i=0; i<nn; ++i) {
    if (nva[i] != 0)
      m_nodalLength[i] /= nva[i];
  }
}

void HedgehogPlotter::plotField(const MxMesh &mx, uint ifield,
                                const Indices &nodeList,
                                int scaling, float scaleFactor)
{
  assert(mx.field(ifield).ndimension() >= 3);

  if ( (scaling == HedgehogPlotter::LocalLength) and
       (m_nodalLength.size() != nodeList.size()) ) {
    nodalLengths(mx, nodeList);
  }

  // elemental fields not supported yet
  if (not mx.field(ifield).nodal())
    return;

  Vct3f fv, p1, p2;
  const int nn = nodeList.size();
  for (int i=0; i<nn; ++i) {
    p2 = p1 = Vct3f( mx.node(nodeList[i]) );
    mx.field(ifield).value(nodeList[i], fv);
    if (scaling == HedgehogPlotter::ByMagnitude) {
      p2 += fv*scaleFactor;
    } else if (scaling == HedgehogPlotter::EqualLength) {
      float sql = sq(fv);
      if (sql > 0.0f)
        p2 += fv * (scaleFactor / std::sqrt(sql));
    } else if (scaling == HedgehogPlotter::LocalLength) {
      float sql = sq(fv);
      if (sql > 0.0f)
        p2 += fv * (m_nodalLength[i] / std::sqrt(sql));
    }

    m_vtx.push_back( p1 );
    m_vtx.push_back( p2 );
  }
}

void HedgehogPlotter::plotNormals(const MxMesh &mx, uint isection)
{
  m_vtx.clear();
  mx.section(isection).vizNormalPoints( m_vtx );
  cout << "HedgehogPlotter: " << nlines()
       << " normals for " << mx.section(isection).nelements()
       << " elements." << endl;

//  size_t n = m_vtx.size() / 2;
//  for (size_t i=0; i<n; ++i) {
//    cout << i << " : " << m_vtx[2*i+0] << " - " << m_vtx[2*i+1]
//         << " L " << norm(m_vtx[2*i+1] - m_vtx[2*i+0]) << endl;
//  }
}

void HedgehogPlotter::build(bool dynamicDraw)
{
  if (m_vtx.empty()) {
    if (m_idl != NotFound) {
      glDeleteLists(m_idl, 1);
      m_idl = NotFound;
    } else if (m_vbo != NotFound) {
      glDeleteBuffers(1, &m_vbo);
      m_vbo = NotFound;
    }
    return;
  }

  if (GLEW_VERSION_1_5) {

    if (m_vbo == NotFound)
      glGenBuffers( 1, &m_vbo );

    GLenum usage = dynamicDraw ? GL_STREAM_DRAW : GL_STATIC_DRAW;
    if (not m_vtx.empty()) {
      glBindBuffer(GL_ARRAY_BUFFER, m_vbo);
      glBufferData(GL_ARRAY_BUFFER, sizeof(Vct3f)*m_vtx.size(),
                   m_vtx.pointer(), usage);
    }

    glBindBuffer(GL_ARRAY_BUFFER, 0);

    cout << "Hedgehog plot with " << m_vtx.size()/2 << " lines. (VBO)" << endl;

  } else {

    if (m_idl == NotFound)
      m_idl = glGenLists(1);

    glNewList(m_idl, GL_COMPILE);

    glEnableClientState( GL_VERTEX_ARRAY );
    glDisableClientState( GL_NORMAL_ARRAY );
    glDisableClientState( GL_COLOR_ARRAY );
    glVertexPointer( 3, GL_FLOAT, 0, m_vtx.pointer() );
    glColor4ubv( m_lineColor.pointer() );
    glDrawArrays(GL_LINES, 0, m_vtx.size()/2);

    glEndList();

    cout << "Hedgehog plot with " << m_vtx.size()/2 << " lines. (DL)" << endl;
  }
}

void HedgehogPlotter::draw() const
{
  if (m_vtx.empty())
    return;

  if (m_idl != NotFound) {
    glCallList(m_idl);
  } else if (m_vbo != NotFound) {
    glEnableClientState(GL_VERTEX_ARRAY);
    glDisableClientState(GL_NORMAL_ARRAY);
    glDisableClientState(GL_COLOR_ARRAY);

    glLineWidth(1.0f);
    glColor4ubv( m_lineColor.pointer() );
    glBindBuffer(GL_ARRAY_BUFFER, m_vbo);
    glVertexPointer(3, GL_FLOAT, 0, 0);
    glDrawArrays(GL_LINES, 0, m_vtx.size());
    glBindBuffer(GL_ARRAY_BUFFER, 0);
  }
}

void HedgehogPlotter::clear()
{
  m_vtx.clear();
}
