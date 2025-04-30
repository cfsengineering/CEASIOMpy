
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
 
#include "smwingmesh.h"
#include "nstmesh.h"
#include "symsurf.h"
#include <genua/pattern.h>
#include <iostream>

using namespace std;

uint SmWingMesh::setTrailingEdgeFlap(const SmControlSurf & cs)
{
  m_flaps.push_back( cs );
  return m_flaps.size()-1;
}

uint SmWingMesh::setTrailingEdgeFlap(Real v1, Real v2, Real hxc, uint pidshell,
                                     uint pidrib)
{
  m_flaps.push_back( SmControlSurf(v1, v2, hxc, pidshell, pidrib) );
  m_flaps.back().cmass = 0.0;
  m_flaps.back().cspring = 0.0;
  if (m_flaps.back().id.empty())
    m_flaps.back().id = m_psf->name() + "ControlSurf" + str(m_flaps.size());
  return m_flaps.size()-1;
}

void SmWingMesh::grid(uint nv, uint nle, uint nwb, uint nte, uint nweb)
{
  if (isMirrored()) {
    cout << m_psf->name() << " is mirrored." << endl;
  }
  
  m_vp = equi_pattern(nv);
  m_up.resize(nv);
  initLE();
  
  // leading edge pattern
  Vector lep = expand_pattern(nle+1, 1.1);
  
  // webs
  m_mweb.resize(nweb, nv);
  m_rweb.resize(nweb, nv);
  
  uint nu = 2*(nle+nwb+nte) + 1;
  for (uint j=0; j<nv; ++j) {
    
    m_up[j].resize(nu);
    int k = 0;
    
    // upper side
    Real uwb1 = findUpper(j, m_xbox1);
    Real uwb2 = findUpper(j, m_xbox2);
    for (uint i=0; i<nte+1; ++i)
      m_up[j][k+i] = uwb2*i/(nte);
    k += nte+1;
    m_giwb2_up = k;
    
    for (uint i=0; i<nwb; ++i)
      m_up[j][k+i] = uwb2 + (uwb1-uwb2)*(i+1)/nwb;
    k += nwb;
    m_giwb1_up = k;
    
    for (uint i=0; i<nle; ++i)
      m_up[j][k+i] = uwb1 + (m_ule[j]-uwb1)*(1.0 - lep[nle-1-i]);
    k += nle;
    
    // webs
    m_mweb(0,j) = m_psf->eval( uwb1, m_vp[j] );
    m_rweb(0,j) = m_psf->eval( uwb2, m_vp[j] );
    
    // lower side
    uwb1 = findLower(j, m_xbox1);
    uwb2 = findLower(j, m_xbox2);
    for (uint i=0; i<nle; ++i)
      m_up[j][k+i] = m_ule[j] + (uwb1 - m_ule[j])*lep[i+1];
    k += nle;
    m_giwb1_lo = k;
    
    for (uint i=0; i<nwb; ++i)
      m_up[j][k+i] = uwb1 + (uwb2-uwb1)*(i+1)/nwb;
    k += nwb;
    m_giwb2_lo = k;
    
    for (uint i=0; i<nte; ++i)
      m_up[j][k+i] = uwb2 + (1.0-uwb2)*(i+1)/nte;
    
    // webs
    m_mweb(nweb-1,j) = m_psf->eval( uwb1, m_vp[j] );
    m_rweb(nweb-1,j) = m_psf->eval( uwb2, m_vp[j] );
    
    for (uint i=1; i<nweb-1; ++i) {
      Real t = Real(i)/(nweb-1);
      m_mweb(i,j) = (1-t)*m_mweb(0,j) + t*m_mweb(nweb-1,j);
      m_rweb(i,j) = (1-t)*m_rweb(0,j) + t*m_rweb(nweb-1,j);
    }
  }
  
  m_pgrid.resize(nu,nv);
  m_umean.resize(nu);
  for (uint j=0; j<nv; ++j) {
    for (uint i=0; i<nu; ++i) {
      Real u = m_up[j][i];
      m_pgrid(i,j) = m_psf->eval(u, m_vp[j]);
      m_umean[i] += u;
    }
  }
  m_umean /= Real(nv);
  
  // locate control surface corner points
  const int nflap = m_flaps.size();
  for (int jf=0; jf<nflap; ++jf) {
    Real v1 = m_flaps[jf].vlo;
    Real v2 = m_flaps[jf].vhi;
    Real xc = m_flaps[jf].xc;

    // locate nearest grid lines
    uint iv1, iv2;
    iv1 = nearest_index(m_vp, v1);
    iv2 = nearest_index(m_vp, v2);
    
    Real utop, ubot;
    utop = 0.5*(findUpper(iv1, xc) + findUpper(iv2, xc));
    ubot = 0.5*(findLower(iv1, xc) + findLower(iv2, xc));
    
    m_flaps[jf].itop = nearest_index(m_umean, utop);
    m_flaps[jf].ibot = m_up[iv1].size() - m_flaps[jf].itop;
    m_flaps[jf].iv1 = iv1;
    m_flaps[jf].iv2 = iv2;
  }
}

void SmWingMesh::addQuads(NstMesh & nst)
{
  bool sym = isMirrored();
  uint nv = m_vp.size();
  uint nu = m_up[0].size();
  uint nvoff = nst.nvertices();
  
  uint gid = nst.nvertices()+1;
  for (uint j=0; j<nv; ++j)
    for (uint i=0; i<nu; ++i)
      nst.addVertex(m_pgrid(i,j), gid++ );
  
  // number of control surfaces
  const int nflap = m_flaps.size();
  
  // main wing shell
  DMatrix<uint> eix(nu-1,nv-1);
  for (uint j=1; j<nv; ++j) {

    // determine local CID
    uint lmcid = m_mcid;
    Vct3 Sv = m_pgrid(nu/2, j) - m_pgrid(nu/2, j-1);
    Real Svy = fabs(Sv[1]);
    Real Svz = fabs(Sv[2]);
    if (Svy >= Svz)
      lmcid = 1;
    else
      lmcid = 2;
    
    // PID to use for wingbox elements
    uint pid_wb = m_pid_wingbox.front();
    Real vmid = 0.5*(m_vp[j] + m_vp[j-1]);
    if (m_pid_wingbox.size() > 1) {
      uint jwb = 0;
      if (sym) {
        while ( 2*fabs(vmid-0.5) > m_pid_vlimits[jwb] and
                jwb < m_pid_vlimits.size()-1)
          ++jwb;
      } else {
        while (vmid > m_pid_vlimits[jwb] and jwb < m_pid_vlimits.size()-1)
          ++jwb;
      }
      pid_wb = m_pid_wingbox[jwb];
    }
    
    uint curflap = NotFound;
    for (int jf=0; jf<nflap; ++jf) {
      if (j > m_flaps[jf].iv1 and j <= m_flaps[jf].iv2) {
        curflap = jf;
        break;
      }
    }
    
    uint pid, a, b, c, d;
    for (uint i=1; i<nu; ++i) {

      if (curflap != NotFound and
          (i < m_flaps[curflap].itop or i > m_flaps[curflap].ibot) ) {
        continue;
      }
      
      if ( (i >= m_giwb2_up and i < m_giwb1_up) or
           (i >= m_giwb1_lo and i < m_giwb2_lo) )
        pid = pid_wb;
      else
        pid = m_pid_lete;
      
      a = nvoff + (j-1)*nu + i-1;
      b = nvoff + (j-1)*nu + i;
      c = nvoff + j*nu + i;
      d = nvoff + j*nu + i-1;
      NstQuadR *ep = new NstQuadR(&nst, a, b, c, d);
      ep->pid(pid);
      ep->mcid(lmcid);
      eix(i-1,j-1) = nst.addElement(ep);
    }
  }
  
  // generate wing spar elements
  nst.addQuads(m_mweb, NstCQUADR, m_pid_web, m_mcid);
  nst.addQuads(m_rweb, NstCQUADR, m_pid_web, m_mcid);

  // generate control surfaces
  addControlQuads(nst, 1e-3);
  connectFlaps(nst);
  
  // generate elements for ribs
  const int nr = m_ribs.size();
  for (int i=0; i<nr; ++i)
    m_ribs[i].addElements(nst);
}

uint SmWingMesh::createRib(uint vi, uint pid, uint mid)
{
  if (m_mweb.nrows() == 0)
    throw Error("Must call grid() before createRib().");

  // construct rib
  SmRibMesh nrib;
  
  // initialize with current settings
  nrib.pid(pid);
  nrib.mcid(mid);
  nrib.webPoints(m_mweb.nrows());
  
  // extract upper/lower rib boundary
  const Vector & upi(m_up[vi]);
  // uint nz = mweb.nrows();
  uint nu = upi.size();
  uint nx = (nu/2) - 1;

  // shorten ribs which collide with control surfaces
  uint joff(1);
  const int nflap = m_flaps.size();
  for (int jf = 0; jf < nflap; ++jf) {
    if (vi >= m_flaps[jf].iv1 and vi <= m_flaps[jf].iv2) {
      joff = m_flaps[jf].itop-1;
      break;
    }
  }
  nx -= joff;
  
  bool isweb(false);
  for (uint j=0; j<nx; ++j) {
    Vct3 top = m_psf->eval( upi[j+joff], m_vp[vi] );
    Vct3 bot = m_psf->eval( upi[nu-1-joff-j], m_vp[vi] );
    isweb = (j+joff == m_giwb1_up-1) or (j+joff == m_giwb2_up-1);
    nrib.bpoints(top, bot, isweb);
  }
  
  m_ribs.push_back(nrib);
  return m_ribs.size()-1;
}

void SmWingMesh::addControlQuads(NstMesh & nst, Real gap)
{
  const int nflap = m_flaps.size();
  PointGrid<3> pgt, pgb, pgr;
  for (int jf=0; jf<nflap; ++jf) {
    int nu = m_flaps[jf].itop;
    int nv = m_flaps[jf].iv2 - m_flaps[jf].iv1 + 1;
    int iv1 = m_flaps[jf].iv1;
    // int iv2 = flaps[jf].iv2;
    
    // generate top shell
    pgt.resize(nu, nv);
    for (int j=0; j<nv; ++j) {
      int jv = m_flaps[jf].iv1 + j;
      Real v = m_vp[jv];
      for (int i=0; i<nu; ++i) {
        Real u = m_up[jv][i];
        pgt(i,j) = m_psf->eval( u, v );
      }
    }
    
    // apply gap along hinge line
    for (int j=0; j<nv; ++j) {
      Vct3 & ph( pgt(nu-1,j) );
      const Vct3 & ps( pgt(nu-2,j) );
      ph += gap*(ps-ph).normalized();
    }
    
    // apply gap along sliding planes
    for (int i=0; i<nu; ++i) {
      Vct3 & ph( pgt(i,0) );
      const Vct3 & ps( pgt(i,1) );
      ph += gap*(ps-ph).normalized();
    }
    for (int i=0; i<nu; ++i) {
      Vct3 & ph( pgt(i,nv-1) );
      const Vct3 & ps( pgt(i,nv-2) );
      ph += gap*(ps-ph).normalized();
    }
    
    // modify points near hinge line to lie exactly on a line
    Line<3> hxl( pgt(nu-1, 0), pgt(nu-1, nv-1) );
    for (int j=0; j<nv; ++j)
      pgt(nu-1, j) = hxl.foot( pgt(nu-1, j) );
    
    // determine suitable MCID
    uint lmcid(m_mcid);
    Vct3 sv = pgt(nu/2, 1) - pgt(nu/2, 0);
    Real suy = fabs(sv[1]);
    Real suz = fabs(sv[2]);
    if (suy >= suz)
      lmcid = 1;
    else
      lmcid = 2;
    
    nst.addQuads(pgt, NstCQUADR, m_flaps[jf].pidshell, lmcid);
    
    uint ioff = m_flaps[jf].ibot;
    pgb.resize(nu, nv);
    for (int j=0; j<nv; ++j) {
      int jv = m_flaps[jf].iv1 + j;
      Real v = m_vp[jv];
      for (int i=0; i<nu; ++i) {
        Real u = m_up[jv][ioff+i];
        pgb(i,j) = m_psf->eval( u, v );
      }
    }
    
    // apply gap along hinge line
    for (int j=0; j<nv; ++j) {
      Vct3 & ph( pgb(0,j) );
      const Vct3 & ps( pgb(1,j) );
      ph += gap*(ps-ph).normalized();
    }
    
    // apply gap along sliding planes
    for (int i=0; i<nu; ++i) {
      Vct3 & ph( pgb(i,0) );
      const Vct3 & ps( pgb(i,1) );
      ph += gap*(ps-ph).normalized();
    }
    for (int i=0; i<nu; ++i) {
      Vct3 & ph( pgb(i,nv-1) );
      const Vct3 & ps( pgb(i,nv-2) );
      ph += gap*(ps-ph).normalized();
    }
    
    nst.addQuads(pgb, NstCQUADR, m_flaps[jf].pidshell, lmcid);
    
    // register actuator connection point
    int nwu = m_mweb.nrows();
    const Vct3 & p1( pgb(0,0) );
    const Vct3 & p2( pgb(0,nv-1) );
    Real yz1 = sq(p1[1]) + sq(p1[2]);
    Real yz2 = sq(p2[1]) + sq(p2[2]);
    if (yz1 < yz2) {
      m_flaps[jf].psact = p1;
      m_flaps[jf].pwact = m_rweb(nwu-1, m_flaps[jf].iv1);
    } else {
      m_flaps[jf].psact = p2;
      m_flaps[jf].pwact = m_rweb(nwu-1, m_flaps[jf].iv2);
    }
    
    // generate web along hinge line
    pgr.resize(nwu, nv);
    for (int j=0; j<nv; ++j) {
      const Vct3 & ptop = pgt(nu-1, j);
      const Vct3 & pbot = pgb(0, j);
      for (int i=0; i<nwu; ++i) {
        Real t = Real(i)/(nwu-1);
        pgr(i,j) = (1.0-t)*pbot + t*ptop;
      }
    }
    nst.addQuads(pgr, NstCQUADR, m_flaps[jf].pidshell, lmcid);
    
    // generate internal ribs
    const int nrib = m_flaps[jf].nhinge;
    const int nvrib = pgb.nrows() - 2;
    pgr.resize(nwu,nvrib);
    m_flaps[jf].phinge.resize(2*nrib);
    for (int krib=0; krib<nrib; ++krib) {
      int jpos = krib*(m_flaps[jf].iv2 - m_flaps[jf].iv1)/(nrib-1);
      for (int j=0; j<nvrib; ++j) {
        const Vct3 & ptop = pgt(nvrib+1-j, jpos);
        const Vct3 & pbot = pgb(j, jpos);
        for (int i=0; i<nwu; ++i) {
          Real t = Real(i)/(nwu-1);
          pgr(i,j) = (1.0-t)*pbot + t*ptop;
        }
      }
      nst.addQuads(pgr, NstCQUADR, m_flaps[jf].pidrib, 0);
      
      m_flaps[jf].phinge[2*krib] = pgr(nwu-1,0);
      m_flaps[jf].phinge[2*krib+1] =
          m_psf->eval( m_up[iv1+jpos][nu-1], m_vp[iv1+jpos] );
      
      // add the corresponding rib on the wing side
      if (m_flaps[jf].pidwingrib != 0)
        createRib(m_flaps[jf].iv1+jpos, 0, m_flaps[jf].pidwingrib);
    }
    
    m_flaps[jf].hax = m_flaps[jf].phinge.back() - m_flaps[jf].phinge.front();
    normalize(m_flaps[jf].hax);
  }
}

void SmWingMesh::connectFlaps(NstMesh & nst) const
{
  nst.fixate();
  
  // generate hinge elements
  int nflaps = m_flaps.size();
  uint gid = nst.nvertices()+1;
  for (int jf=0; jf<nflaps; ++jf) {
    
    // hinge axis line for projection
    int nrib = m_flaps[jf].phinge.size() / 2;
    assert(nrib >= 2);
    
    Vct3 ph1 = 0.5*(m_flaps[jf].phinge[0] + m_flaps[jf].phinge[1]);
    Vct3 ph2 = 0.5*(m_flaps[jf].phinge[2*(nrib-1)] +
        m_flaps[jf].phinge[2*(nrib-1)+1]);
    Line<3> hxl( ph1, ph2 );

    for (int i=0; i<nrib; ++i) {
      uint ps = nst.nearest( m_flaps[jf].phinge(2*i) );
      uint pw = nst.nearest( m_flaps[jf].phinge(2*i+1) );
      
      // introduce two points to place the joint
      Vct3 phg = hxl.foot( 0.5*(nst.vertex(ps) + nst.vertex(pw))  );
      uint pj = nst.addVertex(phg, gid++);
      
      // attach both hinge point to wing
      nst.rconnect(pw, pj);
      
      // introduce MPC between flap and hinge point
      nst.addJoint(pj, ps);
    }

    // actuator / attachment
    uint ps = nst.nearest( m_flaps[jf].psact );
    uint pw = nst.nearest( m_flaps[jf].pwact );
    NstSpring *celas;
    NstScalarMass *cmass;
    if ( m_flaps[jf].cspring > 0.0 ) {
      celas = new NstSpring(&nst, ps, pw);
      celas->dof( NstDof(1), NstDof(1) );
      celas->stiffness( m_flaps[jf].cspring );
      nst.addElement( celas );
    }
    if ( m_flaps[jf].cmass > 0.0 ) {
      cmass = new NstScalarMass(&nst, ps, pw);
      cmass->dof( NstDof(1), NstDof(1) );
      cmass->mass( m_flaps[jf].cmass );
      nst.addElement( cmass );
    }
  }
}

void SmWingMesh::initLE()
{
  Vct3 tg;
  const Real utol(0.001);
  const int nv = m_vp.size();
  m_ule.resize(nv);
  for (int i=0; i<nv; ++i) {
    Real u(0.5), ulo(0.4), uhi(0.6);
    while ( fabs(uhi-ulo) > utol ) {
      u = 0.5*(ulo + uhi);
      tg = m_psf->derive(u, m_vp[i], 1, 0);
      if (tg[0] < 0)
        ulo = u;
      else if (tg[0] > 0)
        uhi = u;
      else
        break;
    }
    m_ule[i] = u;
  }
}

void SmWingMesh::findConnectors(uint vi, PointList<3> & pcon) const
{
  pcon.resize(4);
  pcon[0] = m_pgrid( m_giwb1_up-1, vi );
  pcon[1] = m_pgrid( m_giwb1_lo-1, vi );
  pcon[2] = m_pgrid( m_giwb2_up-1, vi );
  pcon[3] = m_pgrid( m_giwb2_lo-1, vi );
}

void SmWingMesh::appendControls(XmlElement & xe) const
{
  string dof[3];
  dof[0] = "Rx";
  dof[1] = "Ry";
  dof[2] = "Rz";
  for (uint i=0; i<m_flaps.size(); ++i) {
    XmlElement xc("NoliComponent");
    xc.attribute("name") = m_flaps[i].id;
    xc.attribute("spring") = str(m_flaps[i].cspring);
    
    const Vct3 & ax( m_flaps[i].hax );
    for (int k=0; k<3; ++k) {
      XmlElement xna("Node");
      xna.attribute("coefficient") = str(ax[k]);
      xna.attribute("dof") = dof[k];
      xna.text( str(m_flaps[i].psact) );
      xc.append(xna);
      XmlElement xnb("Node");
      xnb.attribute("coefficient") = str(-ax[k]);
      xnb.attribute("dof") = dof[k];
      xnb.text( str(m_flaps[i].pwact) );
      xc.append(xnb);
    }
    
    xe.append(xc);
  }
}

Real SmWingMesh::findUpper(uint iv, Real xc, Real utol) const
{
  Vct3 p;
  Vct3 ple = m_psf->eval(m_ule[iv], m_vp[iv]);
  Vct3 pte = m_psf->eval(0.0, m_vp[iv]);
  
  Real xpos = (1.0-xc)*ple[0] + xc*pte[0];
  Real u(0.5), ulo(0.0), uhi(m_ule[iv]);
  while ( fabs(uhi-ulo) > utol ) {
    u = 0.5*(ulo + uhi);
    p = m_psf->eval(u, m_vp[iv]);
    if (p[0] < xpos)
      uhi = u;
    else if (p[0] > xpos)
      ulo = u;
    else
      return u;
  }
  return u;
}

Real SmWingMesh::findLower(uint iv, Real xc, Real utol) const
{
  Vct3 p;
  Vct3 ple = m_psf->eval(m_ule[iv], m_vp[iv]);
  Vct3 pte = m_psf->eval(1.0, m_vp[iv]);
  
  Real xpos = (1.0-xc)*ple[0] + xc*pte[0];
  Real u(0.5), uhi(1.0), ulo(m_ule[iv]);
  while ( fabs(uhi-ulo) > utol ) {
    u = 0.5*(ulo + uhi);
    p = m_psf->eval(u, m_vp[iv]);
    if (p[0] < xpos)
      ulo = u;
    else if (p[0] > xpos)
      uhi = u;
    else
      return u;
  }
  return u;
}

bool SmWingMesh::isMirrored() const
{
  Surface *ptr = m_psf.get();
  SymSurf *psym = dynamic_cast<SymSurf*>(ptr);
  if (psym)
    return true;
  else
    return false;
}
