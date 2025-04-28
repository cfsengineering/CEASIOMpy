
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
 
#include "pathplotter.h"
#include "glew.h"
#include <genua/mxmesh.h>
#include <genua/mxmeshdeform.h>

PathPlotter::~PathPlotter()
{
  if (m_idl != NotFound)
    glDeleteLists(m_idl, 1);
}

void PathPlotter::assign(const MxMesh &msh, uint idef,
                         const Vct3 &cog, Real width, Real scale)
{
  if (idef >= msh.ndeform())
    return;

  clear();
  const MxMeshDeform & mdf( msh.deform(idef) );
  if (not mdf.isFlightPath())
    return;

  // path centerline
  mdf.flightPath(cog, width, scale, m_vfpath);

  // postprocess : compute normals
  const int nfp = m_vfpath.size();
  const int nseg = nfp/2 - 1;

  PointList<3,float> segn(nseg);
  m_nfpath.resize(nfp);

#pragma omp parallel
  {

    // compute mean segment normals
#pragma omp for schedule(static,256)
    for (int i=0; i<nseg; ++i) {
      const Vct3f & a( m_vfpath[2*i+0] );
      const Vct3f & b( m_vfpath[2*i+1] );
      const Vct3f & c( m_vfpath[2*i+2] );
      const Vct3f & d( m_vfpath[2*i+3] );
      segn[i] = -cross(c-b, d-a);
      normalize(segn[i]);
    }

    // compute vertex normals from segments
#pragma omp for schedule(static,256)
    for (int i=1; i<nseg; ++i) {
      Vct3f vn = segn[i-1] + segn[i];
      normalize(vn);
      m_nfpath[2*i+0] = vn;
      m_nfpath[2*i+1] = vn;
    }
  }

  m_nfpath[0] = m_nfpath[1] = segn[0];
  m_nfpath[nfp-2] = m_nfpath[nfp-1] = segn[nseg-1];

  compileList();
}

void PathPlotter::draw() const
{
  if (not m_visible)
    return;
  if (m_vfpath.empty())
    return;

  if (m_idl != NotFound)
    glCallList(m_idl);
}

void PathPlotter::compileList()
{
  if (m_idl == NotFound)
    m_idl = glGenLists(1);

  const int nv = m_vfpath.size();
  const int nn = m_nfpath.size();
  if (nv > 0 and nv == nn) {

    // glEnable(GL_NORMALIZE);
    glEnableClientState( GL_VERTEX_ARRAY );
    glEnableClientState( GL_NORMAL_ARRAY );
    glDisableClientState(GL_COLOR_ARRAY);

    glVertexPointer( 3, GL_FLOAT, 0, m_vfpath.pointer() );
    glNormalPointer( GL_FLOAT, 0, m_nfpath.pointer() );
    glColor4ubv( m_fpcolor.pointer() );

    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
    glDrawArrays(GL_QUAD_STRIP, 0, nv);
  }
}

void PathPlotter::clear()
{
  m_vfpath.clear();
  m_nfpath.clear();
  if (m_idl != NotFound)
    glDeleteLists(m_idl, 1);
  m_idl = NotFound;
}
