
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
 
#include "smribmesh.h"
#include "dnmesh.h"
#include "dnrefine.h"
#include "nstmesh.h"
#include "nstelements.h"

using namespace std;

void SmRibMesh::punch(const PointList<3> & hole)
{
  if (m_quadmesh)
    initPlanarMesh();

  m_plm.punch(hole);
}

void SmRibMesh::addElements(NstMesh & nst) 
{
  if (m_quadmesh) {
    
    // no cutouts defined - use a structured mesh
    const int nt = m_ptop.size();
    PointGrid<3> pg(m_npweb,nt);
    for (int j=0; j<nt; ++j) {
      for (uint i=0; i<m_npweb; ++i) {
        Real t = Real(i) / (m_npweb-1);
        pg(i,j) = (1-t)*m_pbot[j] + t*m_ptop[j];
      }
    }
    nst.addQuads(pg, NstCQUADR, m_ipid, m_imcid);
    
  } else {
    
    // register constraints so that unstructured triangular mesh
    // will match spar web mesh nodes
    const int nc = m_iwebpos.size();
    PointList<3> wcon(m_npweb);
    for (int j=0; j<nc; ++j) {
      const Vct3 & top( m_ptop[m_iwebpos[j]] );
      const Vct3 & bot( m_pbot[m_iwebpos[j]] );
      for (uint i=0; i<m_npweb; ++i) {
        Real t = Real(i) / (m_npweb-1);
        wcon[i] = (1-t)*bot + t*top;
      }
      m_plm.enforce(wcon);
    }
    
    m_plm.delaunay(m_maxstretch, m_ndpass);
    nst.addTriangles(m_plm.mesh(), NstCTRIAR, m_ipid, m_imcid);
  }
}

void SmRibMesh::initPlanarMesh()
{
  m_quadmesh = false;
  
  // construct boundary points
  const int nt = m_ptop.size();
  PointList<3> cbound;
  cbound.resize(2*nt + 2*(m_npweb-2) + 1);

  int k(0);
  for (int i=0; i<nt; ++i)
    cbound[i] = m_ptop[i];
  k += nt;
  
  // append front spar web nodes
  for (uint i=1; i<m_npweb-1; ++i) {
    Real t = Real(i) / (m_npweb-1);
    Vct3 pw = (1-t)*m_ptop.back() + t*m_pbot.back();
    cbound[k+i-1] = pw;
  }
  k += m_npweb - 2;
  
  for (int i=0; i<nt; ++i)
    cbound[k+i] = m_pbot[nt-i-1];
  k += nt;
  
  // append rear spar web nodes
  for (uint i=1; i<m_npweb; ++i) {
    Real t = Real(i) / (m_npweb-1);
    Vct3 pw = (1-t)*m_pbot.front() + t*m_ptop.front();
    cbound[k+i-1] = pw;
  }
  
  m_plm.init(cbound);
}

