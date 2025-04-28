
#include "streamlineplotter.h"
#include "meshplotter.h"
#include "glew.h"
#include <genua/surfacestreamlines.h>

#include <iostream>
using namespace std;

StreamlinePlotter::StreamlinePlotter() : m_vbuf(NotFound)
{
  visible(false);
  solidColor( Color(0.0f, 0.0f, 0.0f, 1.0f) );
}

StreamlinePlotter::~StreamlinePlotter()
{
  if (m_vbuf != NotFound)
    glDeleteBuffers(1, &m_vbuf);
}

void StreamlinePlotter::assign(const SurfaceStreamlines &ssf)
{
  const uint nl = ssf.size();
  m_lines.resize(nl);
  m_loffset.resize(nl+1);
  m_loffset[0] = 0;

  // count number of points in all lines
  uint npsum = 0;
  for (uint i=0; i<nl; ++i) {
    npsum += ssf[i].size();
    m_loffset[i+1] = npsum;
  }
  m_lines.resize(npsum);

  for (uint i=0; i<nl; ++i) {
    const PointList4d &pts = ssf[i];
    const uint np = pts.size();
    const uint loff = m_loffset[i];
    for (uint j=0; j<np; ++j)
      m_lines[loff+j] = Vct3f((float) pts[j][0], (float) pts[j][1], (float) pts[j][2]);
  }

  build();
}

void StreamlinePlotter::build(bool /*dynamicDraw*/)
{
  if (GLEW_VERSION_1_5) {

    if (m_vbuf == NotFound)
      glGenBuffers( 1, &m_vbuf );

    // GLenum usage = dynamicDraw ? GL_STREAM_DRAW : GL_STATIC_DRAW;
    const GLenum usage = GL_STATIC_DRAW;
    if (not m_lines.empty()) {
      glBindBuffer(GL_ARRAY_BUFFER, m_vbuf);
      glBufferData(GL_ARRAY_BUFFER, sizeof(Vct3f)*m_lines.size(),
                   m_lines.pointer(), usage);
    }

    glBindBuffer(GL_ARRAY_BUFFER, 0);
  }
}

void StreamlinePlotter::draw() const
{
  if (not visible())
    return;

  const uint nlines = m_loffset.size() - 1;
  if ((m_vbuf != NotFound) and (nlines > 0)) {

    glEnableClientState(GL_VERTEX_ARRAY);
    glDisableClientState(GL_NORMAL_ARRAY);
    glDisableClientState(GL_COLOR_ARRAY);

    glLineWidth(1.0f);
    glColor4ubv( m_solidColor.pointer() );
    glBindBuffer(GL_ARRAY_BUFFER, m_vbuf);
    glVertexPointer(3, GL_FLOAT, 0, 0);
    for (uint j=0; j<nlines; ++j) {
      GLint first = m_loffset[j];
      GLsizei count = m_loffset[j+1] - first;
      glDrawArrays(GL_LINE_STRIP, first, count);
    }
    glBindBuffer(GL_ARRAY_BUFFER, 0);
  }
}

