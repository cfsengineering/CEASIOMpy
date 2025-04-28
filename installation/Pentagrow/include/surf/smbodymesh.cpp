
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

#include "smbodymesh.h"
#include "smwingmesh.h"
#include "surface.h"
#include "nstmesh.h"
#include "initgrid.h"
#include <genua/pattern.h>

using namespace std;

// ------------------ local ------------------------------------------------

int nearest_index(const Vector & a, Real b)
{
  const int n = a.size();
  int inear(0);
  Real dst, mindst(huge);
  for (int i=0; i<n; ++i) {
    dst = fabs(b-a[i]);
    if (dst < mindst) {
      mindst = dst;
      inear = i;
    }
  }
  return inear;
}

// ------------------ SmBodyMesh --------------------------------------------

void SmBodyMesh::grid(Real lmax, Real lmin, Real phimax)
{
  InitGrid ig(m_psf.get());
  ig.initPattern(equi_pattern(16), equi_pattern(24));
  ig.refine(lmax, lmin, phimax);
  ig.vsmooth(3);
  ig.enforceUSymmetry();
  ig.collect(m_uvgrid);
  
  const int nu = m_uvgrid.nrows();
  const int nv = m_uvgrid.ncols();
  Real u, v;
  m_pgrid.resize(nu, nv);
  m_umean.resize(nu);
  m_vmean.resize(nv);
  for (int j=0; j<nv; ++j) {
    for (int i=0; i<nu; ++i) {
      u = m_uvgrid(i,j)[0];
      v = m_uvgrid(i,j)[1];
      m_pgrid(i,j) = m_psf->eval(u, v);
      m_umean[i] += u;
      m_vmean[j] += v;
    }
  }
  
  m_umean /= Real(nv);
  m_vmean /= Real(nu);
  m_pcon.clear();
}

uint SmBodyMesh::setBoxPid(const Vct2 & q1, const Vct2 & q2, 
                           uint pid, uint bmcid)
{
  if (m_uvgrid.empty())
    throw Error("SmBodyMesh: Must call grid() before placing PID boxes.");
  
  uint ib[2], jb[2];
  const int nr(m_uvgrid.nrows());
  const int nc(m_uvgrid.ncols());
  
  Vector vp(nc);
  for (int j=0; j<nc; ++j)
    vp[j] = m_uvgrid(0,j)[1];
  jb[0] = nearest_index(vp, q1[1]);
  jb[1] = nearest_index(vp, q2[1]);
  
  Vector up(nr);
  for (int i=0; i<nr; ++i)
    up[i] = m_uvgrid(i,jb[0])[0];
  ib[0] = nearest_index(up, q1[0]);
  
  for (int i=0; i<nr; ++i)
    up[i] = m_uvgrid(i,jb[1])[0];
  ib[1] = nearest_index(up, q2[0]);
  
  m_ibox.insert(m_ibox.end(), ib, ib+2);
  m_jbox.insert(m_jbox.end(), jb, jb+2);
  m_boxpid.push_back(pid);
  m_boxmcid.push_back(bmcid);
  
  return m_boxpid.size()-1;
}

uint SmBodyMesh::setLongeron(Real u, uint pidcap, uint pidweb)
{
  if (m_uvgrid.empty())
    throw Error("SmBodyMesh: Must call grid() before placing stiffeners.");
  
  m_pcon.clear();
  m_pidlongcap.push_back(pidcap);
  m_pidlongweb.push_back(pidweb);
  m_ilong.push_back( nearest_index(m_umean, u) );
  return m_ilong.back();
}

uint SmBodyMesh::setFrame(Real v, uint pidcap, uint pidweb)
{
  if (m_uvgrid.empty())
    throw Error("SmBodyMesh: Must call grid() before placing stiffeners.");
  
  m_pcon.clear();
  m_pidframecap.push_back(pidcap);
  m_pidframeweb.push_back(pidweb);
  m_jframe.push_back( nearest_index(m_vmean, v) );
  return m_jframe.back();
}

const PointGrid<3> & SmBodyMesh::findConnectors()
{
  const uint nlong = m_ilong.size();
  const uint nframe = m_jframe.size();
  if ((m_pcon.nrows() != nlong) or (m_pcon.ncols() != nframe)) {
    m_pcon.resize(nlong, nframe);
    for (uint j=0; j<nframe; ++j)
      for (uint i=0; i<nlong; ++i)
        m_pcon(i,j) = m_pgrid(m_ilong[i], m_jframe[j]);
  }
  return m_pcon;
}

void SmBodyMesh::addQuads(NstMesh & nst) const
{
  const int eloff = nst.nelements();
  nst.addQuads( m_pgrid, NstCQUADR, m_pidmain, m_mcid );

  // modify PIDs for specified boxes
  const int nu = m_uvgrid.nrows();
  const int nv = m_uvgrid.ncols();
  //const int neu = nu-1;
  const int nev = nv-1;
  
  NstQuadR *ep;
  const int nbox = m_boxpid.size();
  for (int ibx=0; ibx<nbox; ++ibx) {
    int ib[2], jb[2];
    ib[0] = m_ibox[2*ibx+0];
    ib[1] = m_ibox[2*ibx+1];
    jb[0] = m_jbox[2*ibx+0];
    jb[1] = m_jbox[2*ibx+1];
    for (int j=jb[0]; j<jb[1]; ++j) {
      for (int i=ib[0]; i<ib[1]; ++i) {
        if ( nst.as(eloff + i*nev + j, &ep) ) {
          ep->pid( m_boxpid[ibx] );
          ep->mcid( m_boxmcid[ibx] );
        }
      }
    }
  }
  
  // determine where to place reinforcements
  PointList<3> bpt;
  bpt.resize(nv);
  for (uint ilg=0; ilg<m_ilong.size(); ++ilg) {
    int irow = m_ilong[ilg];
    for (int j=0; j<nv; ++j)
      bpt[j] = m_pgrid(irow, j);
    nst.addBeams(bpt, m_pidlongcap[ilg]);
  }
  bpt.resize(nu);
  for (uint jfr=0; jfr<m_jframe.size(); ++jfr) {
    int jcol = m_jframe[jfr];
    for (int i=0; i<nu; ++i)
      bpt[i] = m_pgrid(i,jcol);
    nst.addBeams(bpt, m_pidframecap[jfr]);
  }
}

uint SmBodyMesh::rconnect(const SmWingMesh & wng, uint vi, NstMesh & nst) const
{
  PointList<3> wcon;
  wng.findConnectors(vi, wcon);
  const int nw = wcon.size();
  const int nf = m_pcon.size();
  if (nf == 0)
    throw Error("Mesh for body "+m_psf->name()+" has no reinforced connection points.");
  
  int nc(0);
  for (int j=0; j<nw; ++j) {
    const Vct3 & pw(wcon[j]);
    Real dst, mindst(huge);
    int ibest = 0;
    for (int i=0; i<nf; ++i) {
      dst = norm(pw - m_pcon[i]);
      if (dst < mindst) {
        mindst = dst;
        ibest = i;
      }
    }
    int dep = nst.nearest(pw);
    int idep = nst.nearest(m_pcon[ibest]);
    nst.rconnect(dep, idep);
    ++nc;
  }
  
  return nc;
}
