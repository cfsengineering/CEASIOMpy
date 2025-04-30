
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
 
#define _HAS_ITERATOR_DEBUGGING 0

#include "sectionplotter.h"
#include "plotprimitives.h"
#include <genua/mxmesh.h>
#include <genua/color.h>
#include <genua/basicedge.h>
#include <genua/basictriangle.h>
#include <genua/timing.h>
#include <genua/simdsupport.h>
#include "glew.h"

#include <iostream>
using namespace std;

Color SectionPlotter::s_edgeColor = Color(0.0f, 0.0f, 0.0f, 1.0f);
Color SectionPlotter::s_lineColor = Color(0.5f, 0.0f, 0.0f, 1.0f);

SectionPlotter::SectionPlotter() : m_isec(NotFound), m_idl(NotFound),
  m_showElements(true), m_showEdges(true), m_showNormals(false),
  m_splitElements(false), m_havePrimitives(false), m_bdefAllocated(false)
{
  std::fill(m_vbo, m_vbo+NBuf, NotFound);
}

SectionPlotter::~SectionPlotter()
{
  if (m_vbo[BVtx] != NotFound)
    glDeleteBuffers(NBuf, m_vbo);
  if (m_idl != NotFound)
    glDeleteLists(m_idl, 2);
}

bool SectionPlotter::showElements(const Indices &gix, bool flag)
{
  if ((not m_pmx) or (m_isec >= m_pmx->nsections()))
    return false;

  bool changed = false;
  const MxMeshSection & sec( m_pmx->section(m_isec) );
  const uint nel = sec.nelements();
  if (m_useElement.size() != sec.nelements()) {
    m_useElement.clear();
    m_useElement.resize( sec.nelements(), true );
    changed = true;
  }

  const int ng = gix.size();
  const uint offs = sec.indexOffset();
  for (int i=0; i<ng; ++i) {
    uint idx = gix[i];
    if (idx < offs)
      continue;
    idx -= offs;
    if (idx >= nel)
      continue;
    changed |= (m_useElement[idx] != flag);
    m_useElement[idx] = flag;
  }

  // re-create index set and element indices only when necessary; do not
  // change the sharedVertex status when doing so; in the case of volume
  // elements, the set of primitives must be re-created as well.
  if (changed) {
    if (m_cat == VolumeElements)
      gatherPrimitives(true);
    mapVisible( !m_splitElements );
  }

  return changed;
}

void SectionPlotter::showNormals(bool flag)
{
  if (not m_pmx)
    return;

  if ((m_showNormals == false) and (flag == true)) {
    if (m_hhp.nlines() != m_pmx->section(m_isec).nelements()) {
      m_hhp.plotNormals( *m_pmx, m_isec );
      m_hhp.build();
    }
  }
  m_showNormals = flag;
}

void SectionPlotter::solidColor(const Color &c)
{
  const int nv = m_vtx.size();
  if (m_vtxcol.size() != uint(nv))
    m_vtxcol.resize( nv );
  for (int i=0; i<nv; ++i)
    m_vtxcol[i] = c;
}

void SectionPlotter::draw() const
{
  if (GLEW_VERSION_1_5) {
    if (m_vbo[BVtx] != NotFound)
      renderBuffers();
  } else if (m_idl != NotFound) {
    if (m_showElements)
      glCallList(m_idl);
    if (m_showEdges)
      glCallList(m_idl+1);
  }

  if (m_showNormals and (m_hhp.nlines() > 0))
    m_hhp.draw();
}

void SectionPlotter::showEdges(bool flag) 
{
  if (m_showEdges or m_havePrimitives) {
    m_showEdges = flag;
  } else {
    gatherPrimitives( m_cat == VolumeElements );
    m_showEdges = flag;
  }
}

void SectionPlotter::showElements(bool flag)
{
  if (m_showElements or m_havePrimitives) {
    m_showElements = flag;
  } else {
    gatherPrimitives( m_cat == VolumeElements );
    m_showElements = flag;
  }
}

void SectionPlotter::assign(MxMeshPtr pmx, uint isec)
{
  Wallclock clk;
  clk.start();

  clear();
  m_pmx = pmx;
  m_isec = isec;
  m_havePrimitives = false;
  m_bdefAllocated = false;

  MxMeshSection & sec( m_pmx->section(m_isec) );
  if (sec.volumeElements()) {
    m_cat = VolumeElements;
    visible( sec.nelements() < maxShowVolElements / 8 );
  } else if (sec.surfaceElements()) {
    m_cat = SurfaceElements;
    visible(true);
  } else {
    m_cat = LineElements;
    visible(true);
  }

  // FIXME
  // for volume element sections, make sure that only primitives for
  // elements touching the volume boundaries are computed by default
  if (m_cat == VolumeElements) {
    // markBoundaryVolumes();

    // generate triangles for sections up to n elements
    m_useElement.clear();
    bool useVolElm = (sec.nelements() <= maxShowVolElements);
    m_useElement.resize( sec.nelements(), useVolElm );
  } else {
    m_useElement.clear();
    m_useElement.resize( sec.nelements(), true );
  }

  // if, initially, the section is determined to be invisible,
  // do not generate primitives (which is costly)
  if (visible()) {

    gatherPrimitives( false ); // m_cat == VolumeElements);

    // share vertices by default, but not for triangles which represent
    // volume elements because that makes volume elements look very ugly
    // along sharp, convex element edges (shared normals)
    mapVisible( m_cat != VolumeElements );
  }

  // use the stored display color unless it is the default grey; in this
  // case, assign a random color
  const Color grey(0.5f, 0.5f, 0.5f);
  if (sec.displayColor() == grey) {
    const int val = 160;
    const int sat = 90;
    const int hue = rand() % 360;
    sec.displayColor( Color::hsvColor(hue, sat, val) );
  }
  solidColor( sec.displayColor() );

  // setup for initial display
  build();

  clk.stop();

  // debug
  cerr << "Created " << m_pmx->section(m_isec).name() << ", "
       << m_triangles.size()/3 << " triangles, "
       << m_vtx.size() << " nodes, " << clk.elapsed() << "s." << endl;
}

void SectionPlotter::gatherPrimitives(bool useMask)
{
  const MxMeshSection & sec( m_pmx->section(m_isec) );
  const int ne = sec.nelements();

  int tmp[128], emp[32];
  const int tpe = triangleMap(tmp);
  const int lpe = sec.lineVertices(emp);

  if ((m_useElement.size() == uint(ne)) and useMask) {

    int nue = 0;
    for (int i=0; i<ne; ++i)
      nue += m_useElement[i];

    const int ntri = nue*tpe;
    const int nlin = nue*lpe;
    m_ptri.resize(ntri);
    m_pedg.resize(nlin);

    int toff(0), loff(0);
    for (int i=0; i<ne; ++i) {
      if (m_useElement[i]) {
        const uint *vi = sec.element(i);
        for (int j=0; j<tpe; ++j)
          m_ptri[toff++] = PlotTriangle(i, vi, tmp+3*j);
        for (int j=0; j<lpe; ++j)
          m_pedg[loff++] = PlotEdge(i, vi, emp+2*j);
      }
    }

  } else {

    const int ntri = ne*tpe;
    const int nlin = ne*lpe;
    m_ptri.resize(ntri);
    m_pedg.resize(nlin);

    // parallel?
    for (int i=0; i<ne; ++i) {
      const uint *vi = sec.element(i);
      for (int j=0; j<tpe; ++j)
        m_ptri[i*tpe+j] = PlotTriangle(i, vi, tmp+3*j);
      for (int j=0; j<lpe; ++j)
        m_pedg[i*lpe+j] = PlotEdge(i, vi, emp+2*j);
    }

  }

  // triangles generated from volume elements do not have a
  // specified direction -> eliminate about half of triangles
  if (sec.volumeElements()) {
    const size_t ntri = m_ptri.size();
    for (size_t i=0; i<ntri; ++i)
      m_ptri[i].sort();
  }

  sort_primitives(m_ptri);
  sort_primitives(m_pedg);
  m_havePrimitives = true;

  cout << m_ptri.size() << " tri, "
       << m_pedg.size() << " edg primitives for "
       << ne << " elements." << endl;
}

void SectionPlotter::mapVisible(bool shareVertices)
{
  Wallclock clk;
  clk.start();

  // collect primitives here unless already done
  if (not m_havePrimitives)
    gatherPrimitives(false);

  assert(m_pmx);
  assert(m_isec < m_pmx->nsections());
  const MxMeshSection & sec( m_pmx->section(m_isec) );

  // set all elements to visible unless specified otherwise
  if (m_useElement.size() != sec.nelements()) {
    m_useElement.clear();
    m_useElement.resize( sec.nelements(), true );
  }

  // count number of visible triangles and edges
  const int ntri = m_ptri.size();
  const int nedg = m_pedg.size();
  uint nvtri(0), nvedg(0);
  for (int i=0; i<ntri; ++i)
    nvtri += m_useElement[ m_ptri[i].eix ];
  for (int i=0; i<nedg; ++i)
    nvedg += m_useElement[ m_pedg[i].eix ];

  cout << sec.name() << ": " << nvtri << " visible triangles, "
       << nvedg << " visible edges." << endl;

  m_gnix.clear();
  if (shareVertices) {

    m_splitElements = false;

    // establish unique set of vertices if requested
    uint ntmp = 3*nvtri;
    if (m_cat == LineElements)
      ntmp += 2*nvedg;
    Indices tmp(ntmp);
    uint off(0);
    for (int i=0; i<ntri; ++i) {
      if (m_useElement[ m_ptri[i].eix] ) {
        for (int k=0; k<3; ++k)
          tmp[off+k] = m_ptri[i].vix[k];
        off += 3;
      }
    }

    // only in the case of line elements will m_pedg
    // reference other vertices than m_ptri does
    if (m_cat == LineElements) {
      for (int i=0; i<nedg; ++i) {
        if (m_useElement[ m_pedg[i].eix ]) {
          tmp[off+0] = m_pedg[i].src;
          tmp[off+1] = m_pedg[i].trg;
          off += 2;
        }
      }
    }
    assert(off == tmp.size());

    Indices::iterator last;
    std::sort(tmp.begin(), tmp.end());
    last = std::unique(tmp.begin(), tmp.end());
    m_gnix = Indices(tmp.begin(), last);

  } else {

    m_splitElements = true;

    // collect vertices as they appear in elements
    m_gnix.resize( 3*nvtri + 2*nvedg );
    uint off(0);
    for (int i=0; i<ntri; ++i) {
      if (m_useElement[ m_ptri[i].eix] ) {
        for (int k=0; k<3; ++k)
          m_gnix[off+k] = m_ptri[i].vix[k];
        off +=3;
      }
    }
    for (int i=0; i<nedg; ++i) {
      if (m_useElement[ m_pedg[i].eix ]) {
        m_gnix[off+0] = m_pedg[i].src;
        m_gnix[off+1] = m_pedg[i].trg;
        off += 2;
      }
    }
  }

  // fetch local vertex set
  CgMesh::clearMesh();
  const int nv = m_gnix.size();
  m_vtx.resize(nv);
  m_vtxcol.resize(nv, m_pmx->section(m_isec).displayColor());
  for (int i=0; i<nv; ++i) {
    m_vtx[i] = Vct3f( m_pmx->node(m_gnix[i]) );
  }

  // construct triangles
  CgMesh::m_triangles.resize(3*nvtri);
  m_gelix.resize(nvtri);
  uint off(0), v;
  const uint idox = sec.indexOffset();
  for (int i=0; i<ntri; ++i) {
    if (m_useElement[m_ptri[i].eix]) {
      m_gelix[off] = idox + m_ptri[i].eix;
      const uint *vix = m_ptri[i].vix;
      for (int k=0; k<3; ++k) {
        v = shareVertices ? sorted_index(m_gnix, vix[k]) : (3*off+k);
        assert(v != NotFound);
        CgMesh::m_triangles[3*off+k] =v ;
      }
      ++off;
    }
  }
  assert(off == nvtri);

  uint voff = 3*off;
  off = 0;
  if (m_cat != LineElements) {

    // construct lines to represent element edges
    m_edges.resize(2*nvedg);
    for (int i=0; i<nedg; ++i) {
      if (m_useElement[m_pedg[i].eix]) {
        v = shareVertices ? sorted_index(m_gnix, m_pedg[i].src) : (voff+0);
        assert(v != NotFound);
        m_edges[off+0] = v;
        v = shareVertices ? sorted_index(m_gnix, m_pedg[i].trg) : (voff+1);
        assert(v != NotFound);
        m_edges[off+1] = v;
        voff += 2;
        off += 2;
      }
    }
    assert(shareVertices or voff == m_gnix.size());

  } else {

    // construct line elements (not element edges)
    CgMesh::m_lines.resize(2*nvedg);
    for (int i=0; i<nedg; ++i) {
      if (m_useElement[m_pedg[i].eix]) {
        v = shareVertices ? sorted_index(m_gnix, m_pedg[i].src) : (voff+0);
        assert(v != NotFound);
        CgMesh::m_lines[off+0] = v;
        v = shareVertices ? sorted_index(m_gnix, m_pedg[i].trg) : (voff+1);
        assert(v != NotFound);
        CgMesh::m_lines[off+1] = v;
        voff += 2;
        off += 2;
      }
    }
    assert(shareVertices or voff == m_gnix.size());
  }

  clk.stop();
  cout << sec.name() << ": Index mapping: "<< clk.elapsed();
  clk.start();

  CgMesh::estimateNormals();

  clk.stop();
  cout << " normals: " << clk.elapsed() << endl;
}

void SectionPlotter::markBoundaryVolumes()
{
  assert(m_pmx);
  assert(m_isec < m_pmx->nsections());
  const MxMeshSection & sec( m_pmx->section(m_isec) );
  if (not sec.volumeElements())
    return;

  // this function requires vertex-to-element map
  if ( m_pmx->v2eMap().size() != m_pmx->nnodes() )
    m_pmx->fixate();

  // collect volume elements which share any node with another section
  // only these will be marked for rendering
  m_useElement.resize( sec.nelements(), false );

  Indices secNodes, jNodes, boundNodes;
  sec.usedNodes(secNodes);

  /*

  // preallocate reasonable amount
  boundNodes.reserve( secNodes.size() / 8 );

  for (uint j=0; j<m_pmx->nsections(); ++j) {
    if (j == m_isec)
      continue;

    jNodes.clear();
    m_pmx->section(j).usedNodes(jNodes);
    std::set_union( secNodes.begin(), secNodes.end(),
                    jNodes.begin(), jNodes.end(),
                    back_inserter(boundNodes) );

  }

  std::sort(boundNodes.begin(), boundNodes.end());
  boundNodes.erase( std::unique(boundNodes.begin(), boundNodes.end()),
                    boundNodes.end() );

  const int ne = sec.nelements();
  const int vpe = sec.nElementNodes();

  for (int i=0; i<ne; ++i) {
    const uint *vi = sec.element(i);
    for (int k=0; k<vpe; ++k) {
      if (binary_search(boundNodes.begin(), boundNodes.end(), vi[k])) {
        m_useElement[i] = true;
        break;
      }
    }
  }

  */


  const ConnectMap & v2e( m_pmx->v2eMap() );
  const int nun = secNodes.size();

  //#pragma omp parallel for schedule(dynamic, 256)
  for (int i=0; i<nun; ++i) {

    // test whether node is on section boundary
    bool anyOtherSec = false;
    ConnectMap::const_iterator itr, last = v2e.end(secNodes[i]);
    for (itr = v2e.begin(secNodes[i]); itr != last; ++itr) {
      uint nv, isec;
      m_pmx->globalElement(*itr, nv, isec);
      anyOtherSec |= (isec != m_isec);
    }

    // do not proceed with nodes which are not on a section boundary
    if (!anyOtherSec)
      continue;

    // mark all elements which share this node and are inside this section
    // as visible elements
    for (itr = v2e.begin(secNodes[i]); itr != last; ++itr) {
      uint nv, isec;
      m_pmx->globalElement(*itr, nv, isec);
      if (isec == m_isec) {
        uint lix = *itr - sec.indexOffset();
        //#pragma omp critical
        m_useElement[lix] = true;
      } // touched section matches *this
    } // elements which share secNodes[i]
  }

}

int SectionPlotter::triangleMap(int map[]) const
{
  const MxMeshSection & sec( m_pmx->section(m_isec) );
  int ntri = sec.triangleVertices(map);

  int qmap[64];
  int nquad = sec.quadVertices(qmap);
  int off = 3*ntri;
  for (int i=0; i<nquad; ++i) {
    map[off+0] = qmap[4*i+0];
    map[off+1] = qmap[4*i+1];
    map[off+2] = qmap[4*i+2];
    map[off+3] = qmap[4*i+2];
    map[off+4] = qmap[4*i+3];
    map[off+5] = qmap[4*i+0];
    off += 6;
    ntri += 2;
  }
  return ntri;
}

void SectionPlotter::build(bool dynamicDraw)
{
  if (GLEW_VERSION_1_5)
    transferBuffers(dynamicDraw);
  else
    compileLists();

  if (m_showNormals)
    m_hhp.build();
}

void SectionPlotter::compileLists()
{
  const int nlist = 2;
  if (m_idl != NotFound)
    glDeleteLists(m_idl, nlist);
  m_idl = glGenLists(nlist);

  // first list is for elements
  glNewList(m_idl, GL_COMPILE);
  drawElements();
  glEndList();

  glNewList(m_idl+1, GL_COMPILE);
  drawEdges();
  glEndList();
}

void SectionPlotter::drawElements()
{
  if (not m_vtx.empty()) {

    if (not m_triangles.empty()) {

      glEnableClientState( GL_VERTEX_ARRAY );
      glEnableClientState( GL_NORMAL_ARRAY );
      glEnableClientState( GL_COLOR_ARRAY );

      assert(m_nrm.size() == m_vtx.size());
      assert(m_vtxcol.size() == m_vtx.size());
      glVertexPointer( 3, GL_FLOAT, 0, m_vtx.pointer() );
      glNormalPointer( GL_FLOAT, 0, m_nrm.pointer() );
      glColorPointer( 4, GL_UNSIGNED_BYTE, 0, m_vtxcol.front().pointer() );

      glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
      glDrawElements( GL_TRIANGLES, m_triangles.size(),
                      GL_UNSIGNED_INT, &m_triangles[0] );

    } else if (not m_lines.empty()) {

      glEnableClientState( GL_VERTEX_ARRAY );
      glDisableClientState( GL_NORMAL_ARRAY );
      glDisableClientState( GL_COLOR_ARRAY );
      // glEnableClientState( GL_COLOR_ARRAY );

      glVertexPointer( 3, GL_FLOAT, 0, m_vtx.pointer() );
      // glColorPointer( 4, GL_UNSIGNED_BYTE, 0, m_vtxcol.front().pointer() );

      glLineWidth(1.0f);
      glColor4ubv( s_lineColor.pointer() );
      glDrawElements( GL_LINES, m_lines.size(),
                      GL_UNSIGNED_INT, &m_lines[0] );

    }
  }
}

void SectionPlotter::drawEdges()
{
  if (not m_edges.empty()) {

    glEnableClientState( GL_VERTEX_ARRAY );
    glDisableClientState( GL_NORMAL_ARRAY );
    glDisableClientState( GL_COLOR_ARRAY );

    glVertexPointer( 3, GL_FLOAT, 0, m_vtx.pointer() );

    glLineWidth(1.0f);
    glColor4ubv( s_edgeColor.pointer() );
    glDrawElements( GL_LINES, m_edges.size(),
                    GL_UNSIGNED_INT, &m_edges[0] );

  }
}

void SectionPlotter::transferBuffers(bool dynamicDraw)
{
  // VBO support requires OpenGL > 1.5
  assert(GLEW_VERSION_1_5);

  if (m_vbo[BVtx] == NotFound) {
    glGenBuffers( NBuf, m_vbo );
  }

  GLenum usage = dynamicDraw ? GL_STREAM_DRAW : GL_STATIC_DRAW;

  if (dynamicDraw) {
    transferDisplaced();
    return;
  } else if (not m_bdefAllocated) {
    // pre-allocate BDef buffer
    glBindBuffer(GL_ARRAY_BUFFER, m_vbo[BDef]);
    glBufferData(GL_ARRAY_BUFFER, sizeof(Vct3f)*m_vtx.size(),
                 0, usage);
    m_bdefAllocated = true;
  }

  if (not m_vtx.empty()) {
    glBindBuffer(GL_ARRAY_BUFFER, m_vbo[BVtx]);
    glBufferData(GL_ARRAY_BUFFER, sizeof(Vct3f)*m_vtx.size(),
                 m_vtx.pointer(), usage);
  }

  if (not m_nrm.empty()) {
    glBindBuffer(GL_ARRAY_BUFFER, m_vbo[BNrm]);
    glBufferData(GL_ARRAY_BUFFER, sizeof(Vct3f)*m_nrm.size(),
                 m_nrm.pointer(), usage);
  }

  if (not m_vtxcol.empty()) {
    glBindBuffer(GL_ARRAY_BUFFER, m_vbo[BClr]);
    glBufferData(GL_ARRAY_BUFFER, sizeof(Color)*m_vtxcol.size(),
                 m_vtxcol[0].pointer(), usage);
  }

  if (not m_triangles.empty()) {
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m_vbo[BTri]);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(uint)*m_triangles.size(),
                 &m_triangles[0], usage);
  }

  if (not m_lines.empty()) {
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m_vbo[BLns]);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(uint)*m_lines.size(),
                 &m_lines[0], usage);
  }

  if (not m_edges.empty()) {
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m_vbo[BEdg]);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(uint)*m_edges.size(),
                 &m_edges[0], usage);
  }

  glBindBuffer(GL_ARRAY_BUFFER, 0);
  glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
}

void SectionPlotter::transferDisplaced()
{
  if (m_vtx.empty())
    return;

  // always update BDef while drawing BVtx
  glBindBuffer(GL_ARRAY_BUFFER, m_vbo[BDef]);

  // right now, we only update dynamically to display moving vertices,
  // so it's enough to transfer the vertex buffer only
  glBufferSubData(GL_ARRAY_BUFFER, 0,
                  sizeof(Vct3f)*m_vtx.size(), m_vtx.pointer());
  glBindBuffer(GL_ARRAY_BUFFER, 0);
  swapDisplacedVertexBuffer();
}

void SectionPlotter::renderBuffers() const
{
  assert(GLEW_VERSION_1_5);
  if (m_vbo[BVtx] == NotFound)
    return;

  if (m_showElements) {

    if (not m_triangles.empty()) {

      glEnableClientState(GL_VERTEX_ARRAY);
      glEnableClientState(GL_NORMAL_ARRAY);
      glEnableClientState(GL_COLOR_ARRAY);

      glBindBuffer(GL_ARRAY_BUFFER, m_vbo[BVtx]);
      glVertexPointer(3, GL_FLOAT, 0, 0);
      glBindBuffer(GL_ARRAY_BUFFER, m_vbo[BNrm]);
      glNormalPointer(GL_FLOAT, 0, 0);
      glBindBuffer(GL_ARRAY_BUFFER, m_vbo[BClr]);
      glColorPointer(4, GL_UNSIGNED_BYTE, 0, 0);
      glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m_vbo[BTri]);
      glDrawElements(GL_TRIANGLES, m_triangles.size(), GL_UNSIGNED_INT, 0);
    }

  }

  if (m_showEdges) {

    if (not m_edges.empty()) {

      glEnableClientState(GL_VERTEX_ARRAY);
      glDisableClientState(GL_NORMAL_ARRAY);
      glDisableClientState(GL_COLOR_ARRAY);

      glLineWidth(1.0f);
      glColor4ubv( s_edgeColor.pointer() );
      glBindBuffer(GL_ARRAY_BUFFER, m_vbo[BVtx]);
      glVertexPointer(3, GL_FLOAT, 0, 0);
      glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m_vbo[BEdg]);
      glDrawElements(GL_LINES, m_edges.size(), GL_UNSIGNED_INT, 0);
    }
  }

  // this is repeated here because line elements should be drawn over
  // other elements' edges
  if (m_showElements) {

    if (not m_lines.empty()) {

      glEnableClientState(GL_VERTEX_ARRAY);
      glDisableClientState(GL_NORMAL_ARRAY);
      glDisableClientState(GL_COLOR_ARRAY);

      glLineWidth(2.0f);
      glColor4ubv( s_lineColor.pointer() );
      glBindBuffer(GL_ARRAY_BUFFER, m_vbo[BVtx]);
      glVertexPointer(3, GL_FLOAT, 0, 0);
      // glBindBuffer(GL_ARRAY_BUFFER, m_vbo[BClr]);
      // glColorPointer(4, GL_UNSIGNED_BYTE, 0, 0);
      glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m_vbo[BLns]);
      glDrawElements(GL_LINES, m_lines.size(), GL_UNSIGNED_INT, 0);

    }
  }

  glBindBuffer(GL_ARRAY_BUFFER, 0);
  glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
}

void SectionPlotter::updateColors(const MxMeshField &field,
                                  float blueLimit, float redLimit)
{
  if (not field.nodal())
    return;
  else if (not field.realField())
    return;
  else if (field.ndimension() != 1)
    return;

  const int nv = m_gnix.size();
  assert(m_vtx.size() == uint(nv));
  if (m_vtxcol.size() != uint(nv))
    m_vtxcol.resize(nv);

  for (int i=0; i<nv; ++i) {
    float x;
    field.scalar(m_gnix[i], x);
    m_vtxcol[i].map(blueLimit, redLimit, x);
  }
}

void SectionPlotter::updateColors(const DVector<float> &cf,
                                  float blueLimit, float redLimit)
{
  const int nv = m_gnix.size();
  assert(m_vtx.size() == uint(nv));
  if (m_vtxcol.size() != uint(nv))
    m_vtxcol.resize(nv);

  for (int i=0; i<nv; ++i) {
    assert(cf.size() > m_gnix[i]);
    m_vtxcol[i].map(blueLimit, redLimit, cf[m_gnix[i]]);
  }
}

bool SectionPlotter::updateColors(const ElementColorArray &ecl)
{
  if (not m_pmx)
    return false;
  if (m_triangles.empty())
    return false;
  if (ecl.empty())
    return false;

  const MxMeshSection & sec( m_pmx->section(m_isec) );

  // test whether ecl can have any overlap with elements in this section
  uint off = sec.indexOffset();
  uint nel = sec.nelements();

  // check if first element of this section is beyond ecl array
  if (off > ecl.back().gelix)
    return false;

  // check if last element is in front of ecl
  if (off+nel <= ecl.front().gelix)
    return false;

  // in order to allow element-based coloring, there must be one vertex
  // (and hence vertex color) per triangle vertex index
  if (not m_splitElements)
    mapVisible(false);

  // take into account that not all elements may be visible
  const uint nse = m_gelix.size();
  uint iel = 0;
  while (iel < nse) {
    uint eix = m_gelix[iel];              // global element index, first node
    uint vix = ::sorted_index(ecl, eix);  // lookup element color
    Color ec = (vix != NotFound) ? ecl[vix].color : sec.displayColor();
    do {
      for (int k=0; k<3; ++k)
        m_vtxcol[3*iel+k] = ec;
      ++iel;
    } while (m_gelix[iel] == eix);
  }

  return true;
}

void SectionPlotter::resetUndeformed()
{
  if ( hint_unlikely(m_pmx == nullptr or m_isec == NotFound) )
    return;
  if ( hint_unlikely(m_gnix.size() != m_vtx.size()) )
    m_vtx.resize( m_gnix.size() );

  cout << "Reset to undeformed configuration." << endl;

  const size_t n = m_gnix.size();
  for (size_t i=0; i<n; ++i)
    m_vtx[i] = Vct3f( m_pmx->node(m_gnix[i]) );

  // update only vtx buffer
  transferDisplaced();
}

void SectionPlotter::markAllElements(bool flag)
{
  m_useElement = std::vector<bool>( m_useElement.size(), flag );
  if ((m_cat == VolumeElements) and (not flag)) {
    m_ptri.clear();
    m_pedg.clear();
    m_edges.clear();
    m_gnix.clear();
    m_gelix.clear();
    CgMesh::clearMesh();
    build();
  }
}

bool SectionPlotter::cutVolumeElements(const std::vector<bool> &nodesBelowPlane)
{
  if ((not m_pmx) or (m_isec > m_pmx->nsections()))
    return false;

  const MxMeshSection & sec( m_pmx->section(m_isec) );
  if (not sec.volumeElements())
    return false;

  m_showEdges = m_showElements = true;
  const int ne = sec.nelements();
  const int vpe = sec.nElementNodes();
  int nsliced = 0;

  // parallelizing this is detrimental!
  for (int i=0; i<ne; ++i) {
    if (not m_useElement[i]) {
      const uint *vi = sec.element(i);
      bool firstside = nodesBelowPlane[vi[0]];
      bool sliced = false;
      for (int k=1; k<vpe; ++k)
        sliced |= (nodesBelowPlane[vi[k]] != firstside);
      m_useElement[i] = sliced;
      nsliced += (sliced ? 1 : 0);
    }
  }

  if (nsliced > 0) {
    gatherPrimitives(true);
    mapVisible(false);
    solidColor( Color(0.5f, 0.5f, 0.5f, 1.0f) );
    build();
  }

  return (nsliced != 0);
}

void SectionPlotter::updateVertices(const PointList<3,float> &pts)
{
  const int nv = m_gnix.size();
  if (m_vtx.size() != size_t(nv))
    m_vtx.resize(nv);

  // parallelization is counterproductive!
  for (int i=0; i<nv; ++i)
    m_vtx[i] = Vct3f( pts[m_gnix[i]] );

  // update normal directions
  // CgMesh::estimateNormals();
}

void SectionPlotter::setDeformationBasis(uint ifield, float scale)
{
  cout << this << " deformation basis: " << ifield << " scale: " << scale << endl;

  Vct3f dxi;
  const size_t n = m_gnix.size();
  m_vdefa.resize(n);
  const MxMeshField &field( m_pmx->field(ifield) );
  for (size_t i=0; i<n; ++i) {
    field.value( m_gnix[i], dxi );
    m_vdefa[i] = scale * dxi;
  }
}

void SectionPlotter::setDeformationBasis(const PointList<3,float> &gadef,
                                         const PointList<3,float> &gbdef)
{
  const size_t n = m_gnix.size();
  m_vdefa.resize(n);
  m_vdefb.resize(n);
  for (size_t i=0; i<n; ++i) {
    m_vdefa[i] = gadef[m_gnix[i]];
    m_vdefb[i] = gbdef[m_gnix[i]];
  }
}

void SectionPlotter::basisDeform(float dxa)
{
  // point optimization:
  // vectorized to improve load-store efficiency
  //
  // this should really be done by a vertex shader

  float16 sxa(dxa), v[3];
  const size_t n = m_vdefa.size();
  if (n == 0)
    return;

  const size_t nb = n / 16;
  float *pvtx = m_vtx.pointer();
  const float *pdefa = m_vdefa.pointer();
  for (size_t i=0; i<nb; ++i) {
    v[0].load( &pvtx[48*i] );
    v[1].load( &pvtx[48*i+16] );
    v[2].load( &pvtx[48*i+32] );
    v[0] += sxa * float16( &pdefa[i*48] );
    v[0].store( &pvtx[48*i] );
    v[1] += sxa * float16( &pdefa[i*48+16] );
    v[1].store( &pvtx[48*i+16] );
    v[2] += sxa * float16( &pdefa[i*48+32] );
    v[2].store( &pvtx[48*i+32] );
  }

  for (size_t i=16*nb; i<n; ++i) {
    m_vtx[i] += dxa * m_vdefa[i];
  }

  cout << this << " basisDeform, dxa = " << dxa << endl;
  transferDisplaced();
}

void SectionPlotter::basisDeform(float dxa, float dxb)
{
  // todo: vectorize, pointlist is aligned
  const size_t n = m_vdefb.size();
  float va = 1.0f - dxa - dxb;
  for (size_t i=0; i<n; ++i) {
    m_vtx[i] = va*m_vtx[i] + dxa * m_vdefa[i] + dxb * m_vdefb[i];
  }

  transferDisplaced();
}

void SectionPlotter::visibleNodes(Indices &idx) const
{
  Indices tmp;
  if (showElements()) {
    tmp.insert(tmp.end(), m_triangles.begin(), m_triangles.end());
    tmp.insert(tmp.end(), m_lines.begin(), m_lines.end());
  }
  if (showEdges()) {
    tmp.insert(tmp.end(), m_edges.begin(), m_edges.end());
  }

  if (tmp.empty())
    return;

  // de-duplicate local indices
  std::sort(tmp.begin(), tmp.end());
  tmp.erase( std::unique(tmp.begin(), tmp.end()), tmp.end() );

  // set of global indices
  const int nv = tmp.size();
  Indices gvi(nv);
  for (int i=0; i<nv; ++i)
    gvi[i] = m_gnix[tmp[i]];
  std::sort(gvi.begin(), gvi.end());

  // merge into idx
  if (idx.empty()) {
    idx.swap(gvi);
  } else {
    size_t mpos = idx.size();
    idx.insert( idx.end(), gvi.begin(), gvi.end() );
    std::inplace_merge( idx.begin(), idx.begin()+mpos, idx.end() );
    idx.erase( std::unique(idx.begin(), idx.end()), idx.end() );
  }
}

void SectionPlotter::visibleElements(Indices &idx) const
{
  idx.clear();
  idx.reserve( m_triangles.size() );
  const int ne = m_useElement.size();
  for (int i=0; i<ne; ++i) {
    if (m_useElement[i])
      idx.push_back( i );
  }
}

void SectionPlotter::clear()
{
  CgMesh::clearMesh();
  m_gnix.clear();
  m_gelix.clear();
  m_useElement.clear();
  m_edges.clear();
}
