
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
 
#include <genua/pattern.h>
#include "surface.h"
#include "initgrid.h"

using namespace std;

void InitGrid::initPattern(const Vector & u, const Vector & v)
{
  const uint nv(v.size());
  vp = v;
  up.resize(nv);
  for (uint j=0; j<nv; ++j) 
    up[j] = u;
}

void InitGrid::initPattern(uint nu, uint nv)
{
  up.resize(nv);
  vp = equi_pattern(nv);
  Vector u(equi_pattern(nu));
  for (uint j=0; j<nv; ++j)
    up[j] = u;
}

void InitGrid::initPattern(const PointGrid<2> & pg)
{
  const uint nu(pg.nrows());
  const uint nv(pg.ncols());
  vp.resize(nv);
  up.resize(nv);
  for (uint j=0; j<nv; ++j) {
    up[j].resize(nu);
    vp[j] = 0.0;
    for (uint i=0; i<nu; ++i) {
      const Vct2 & q(pg(i,j));
      up[j][i] = q[0];
      vp[j] += q[1];
    }
    vp[j] /= nu;
  }
}

void InitGrid::refine(Real lmax, Real lmin, Real phimax)
{
  // maximum allowed stretch ratio
  const Real stmax(300.0);
  
  // this is supposed to be an initialization grid, therefore,
  // the degree of refinement is limited to these maxima 
  const uint numax(256);
  const uint nvmax(128);
  
  // coarse initialization
  uint nu(15), nv(9);
  if (vp.empty()) {
    nu = min(15, int(2*PI/phimax) );
    nu += 1 - nu%2; 
    initPattern(nu, nv);
  }
    
  // make sure that longitudinal distances are OK
  vRefineByLength(lmax);
  
  Real mxg(0.0);
  do {
    mxg = vRefineByGap( 0.125*lmax );
  } while (mxg > 0.5*lmax);
  
  nv = ncols();
  
  // adapt in u-direction and increase nu until criteria are
  // finally met (thus: use coarse criteria...) 
  Real worst;
  worst = uAdapt(lmax, lmin, phimax);
  while (worst > 1.0 and nu < numax) {
    nu += max(8u, nu/4);
    worst = uAdapt(lmax, lmin, phimax, nu);
  }
  
  // reduce stretch by inserting further frames where necessary
  do {
    nv += max(4u, nv/4);
    worst = vRefineByStretch(nv, 0.5*stmax);
  } while (worst > stmax and nv < nvmax);
  
  vsmooth(2);  
}

Real InitGrid::uAdapt(Real lmax, Real lmin, Real phimax, uint numax)
{
  // coarse initialization
  if (vp.empty()) {
    initPattern( min(15, int(2*PI/phimax)), 21 );
    vRefineByLength( lmax );
  }
  
  Real q, qworst(0.0);
  uint nu, nv = up.size();
  if (numax == 0)
    nu = up[0].size();
  else 
    nu = numax;
  for (uint i=0; i<nv; ++i) {
    q = adaptULine( i, nu, lmax, lmin, phimax );
    qworst = max(q, qworst);
  }
  
  return qworst;
}

void InitGrid::shift(uint j, Real cminphi, const Vector & cphi)
{  
  Vector & u(up[j]);
  const uint n(u.size());
  Real cp, c, cn;
  for (uint i=1; i<n-1; ++i) {
    cp = cphi[i-1];
    c = cphi[i];
    cn = cphi[i+1];
    if (c < cp and c < cn)
      continue;
    if (cp < cminphi and cp < cn) {
      u[i] = (2*u[i] + u[i-1]) / 3.;
    } else if (cn < cminphi and cn < cp) {
      u[i] = (2*u[i] + u[i+1]) / 3.;
    }
  }
}

void InitGrid::kinks(uint j, Vector & cphi) const
{
  const Vector & u(up[j]);
  const uint n(u.size());
  cphi.resize(n);
  PointList<3> pts(n);
  Real v = vp[j];
  for (uint i=0; i<n; ++i) 
    pts[i] = psf->eval(u[i], v);
  
  cphi.front() = cphi.back() = 1.0;
  for (uint i=1; i<n-1; ++i)
    cphi[i] = cosarg( pts[i+1]-pts[i], pts[i]-pts[i-1] );
}

void InitGrid::uRefineByLength(Real lmax)
{
  // check lengths along the u-direction
  bool insert;
  const uint nv(vp.size());
  for (uint j=0; j<nv; ++j) {
    Real v = vp[j];
    do {
      insert = false; 
      for (uint i=1; i<up[j].size(); ++i) {
        Real len = norm(psf->eval(up[j][i], v) - psf->eval(up[j][i-1], v));
        if (len > lmax) {
          insert = true;
          insertStringer( 0.5*(up[j][i] + up[j][i-1]) );
          ++i;
        }
      }
    } while (insert);  
    usmoothColumn(j, 1);
  }
}

void InitGrid::vRefineByLength(Real lmax)
{
  assert(not vp.empty());
  uint nu(up[0].size());
  
  // insert additional rows (frames) if distances are too large  
  bool insert;
  do {
    insert = false;
    for (uint j=1; j<vp.size(); ++j) {
      Real vmid = 0.5*(vp[j] + vp[j-1]);      
      
      // compute local circumference - distance between frames may not be 
      // larger than about 0.25*ccf. Otherwise, edge flips could result 
      // in degenerate geometries
      Real lsum(0), ccf(0);
      for (uint i=1; i<nu; ++i) 
        ccf += norm(psf->eval(up[j][i], vmid) - psf->eval(up[j][i-1], vmid));
      
      // compute distance between frames
      for (uint i=0; i<nu; ++i) 
        lsum += norm( psf->eval(up[j][i], vp[j]) - 
                      psf->eval(up[j-1][i], vp[j-1]) );
      lsum /= nu;
      if (lsum > lmax or lsum > 0.25*ccf) {
        
        // find position where to insert frame
        uint ipos = std::distance( vp.begin(), 
                                   lower_bound(vp.begin(), vp.end(), vmid) );
        vp.insert(vp.begin()+ipos, vmid);
        
        // compute frame to insert
        Vector iframe = 0.5*(up[j] + up[j-1]);
        up.insert(up.begin()+ipos, iframe);
        
        insert = true;
        ++j;
      }
    }
  } while (insert);
}

Real InitGrid::vRefineByAngle(Real maxphi)
{
  assert(not vp.empty());
  
  Real cpm(1.0);
  const uint nu(up[0].size());
  const Real cphimin( cos(maxphi) );
  PointList<3> ncur(nu), nprv(nu);
  for (uint i=0; i<nu; ++i)
    nprv[i] = psf->normal(up[0][i], vp[0]);
  for (uint j=1; j<vp.size(); ++j) {
    Real vmid = 0.5*(vp[j] + vp[j-1]);
    Real cphi(1.0);
    for (uint i=0; i<nu; ++i) {
      ncur[i] = psf->normal(up[j][i], vp[j]);
      cphi = min(cphi, cosarg(ncur[i], nprv[i]));
    } 
    nprv.swap(ncur);
    
    if (cphi < cphimin) {
      
      // find position where to insert frame
      uint ipos = std::distance( vp.begin(), 
                                  lower_bound(vp.begin(), vp.end(), vmid) );
      vp.insert(vp.begin()+ipos, vmid);
      
      // compute frame to insert
      Vector iframe = 0.5*(up[j] + up[j-1]);
      up.insert(up.begin()+ipos, iframe);
      ++j;
      
      cpm = min(cpm, 0.5*(1 + cphi));
    } else
      cpm = min(cpm, cphi);
  }
  
  return cpm;
}

Real InitGrid::vRefineByGap(Real maxgap)
{
  assert(not vp.empty());
  
  Vct3 ps, pd;
  const uint nu(up[0].size());
  PointList<3> pcur(nu), pprv(nu);
  for (uint i=0; i<nu; ++i)
    pprv[i] = psf->eval(up[0][i], vp[0]);
  
  Real mglob(0.0);
  for (uint j=1; j<vp.size(); ++j) {
    Real vmid = 0.5*(vp[j] + vp[j-1]);
    Real gap, mxg(0.0);
    for (uint i=0; i<nu; ++i) {
      pcur[i] = psf->eval(up[j][i], vp[j]);
      Real umid = 0.5*(up[j][i] + up[j-1][i]);
      ps = psf->eval(umid, vp[j]);
      pd = 0.5*(pcur[i] + pprv[i]);
      gap = norm(ps - pd);
      mxg = max(gap, mxg);
    } 
    pprv.swap(pcur);
    
    if (mxg > maxgap) {
      vp.insert(vp.begin()+j, vmid);
      Vector iframe = 0.5*(up[j] + up[j-1]);
      up.insert(up.begin()+j, iframe);
      ++j;
      
      mglob = max(mglob, 0.5*mxg);
    } else {
      mglob = max(mglob, mxg);
    }
  }
  
  return mglob;
}

Real InitGrid::vRefineByStretch(uint nvmax, Real smax)
{
  assert(not vp.empty());
  uint nu(up[0].size());
  
  // insert additional rows (frames) if stretch ratio is excessive 
  Vct3 p1, p2, p3;
  Real sworst(1.0);
  while (vp.size() < nvmax) {
    
    sworst = 1.0;
    uint jworst(1);
    for (uint j=1; j<vp.size(); ++j) {
      
      // determine maximum stretch ratio 
      Real s(1.0), is(1.0);
      for (uint i=1; i<nu; ++i) {
        p1 = psf->eval( up[j][i-1], vp[j] );
        p2 = psf->eval( up[j][i], vp[j] );
        p3 = psf->eval( up[j][i], vp[j-1] );
        Real du = norm(p2-p1);
        Real dv = norm(p2-p3);
        s = max(s, dv/du);
        is = max(is, du/dv);
      }
      
      // no point in refining if the result would be worse..
      if (2*is > smax)
        s = 1.0;
      
      if (s > sworst) {
        sworst = s;
        jworst = j;
      }
      
    }
      
    if (sworst > smax) {
      
      // find position where to insert frame
      Real vmid = 0.5*(vp[jworst] + vp[jworst-1]);
      uint ipos = std::distance(vp.begin(), lower_bound(vp.begin(), vp.end(), vmid));
      vp.insert(vp.begin()+ipos, vmid);
      
      // compute frame to insert
      Vector iframe = 0.5*(up[jworst] + up[jworst-1]);
      up.insert(up.begin()+ipos, iframe);
    } else {
      break;
    }
    
  }
  
  return sworst;
}

void InitGrid::uRefineByAngle(Real phimax, Real lmin)
{
  assert(not vp.empty());
  uint nv(vp.size());
  Real mincphi = cos(phimax);
  
  // check angles along the u-direction
  for (uint j=0; j<nv; ++j) {
    Real v = vp[j];
    bool insert;
    do {
      
      // insert if necessary
      insert = false;
      for (uint i=1; i<up[j].size()-1; ++i) {
        Vct3 r1 = psf->eval(up[j][i], v) - psf->eval(up[j][i-1], v);
        Vct3 r2 = psf->eval(up[j][i+1], v) - psf->eval(up[j][i], v);
        Real cphi = cosarg(r1,r2);
        if (cphi < mincphi) {
          Real len1 = norm(r1);
          Real len2 = norm(r2);
          if (len1 > len2 and len1 > lmin) {
            insert = true;
            insertStringer( 0.5*(up[j][i] + up[j][i-1]) );
            ++i;
          } else if (len2 > lmin) {
            insert = true;
            insertStringer( 0.5*(up[j][i+1] + up[j][i]) );
            ++i;
          }
        }
      }
    } while (insert);  
  }
}

void InitGrid::collect(PointGrid<2> & pts) const
{
  assert(not vp.empty());
  assert(up.size() == vp.size());
  const uint nv(vp.size());
  const uint nu(up[0].size());
  
  pts.resize(nu,nv);
  for (uint j=0; j<nv; ++j)
    for (uint i=0; i<nu; ++i)
      pts(i,j) = vct( up[j][i], vp[j] );
}

uint InitGrid::insertFrame(Real v, uint nu)
{
  Vector::iterator pos;
  pos = std::lower_bound(vp.begin(), vp.end(), v);
  uint ipos = std::distance(vp.begin(), pos);
  vp.insert(pos, v);
  up.insert(up.begin()+ipos, equi_pattern(nu));
  return ipos;
}
    
void InitGrid::insertStringer(Real u)
{
  Vector::iterator pos;
  const uint nf(up.size());
  for (uint j=0; j<nf; ++j) {
    pos = std::lower_bound(up[j].begin(), up[j].end(), u);
    up[j].insert(pos, u);
    usmoothColumn(j, 1);
  }
}

void InitGrid::usmooth(uint niter)
{
  const uint nc = vp.size();
  for (uint j=0; j<nc; ++j)
    usmoothColumn(j, niter);
}

void InitGrid::usmoothColumn(uint j, uint niter)
{
  assert(j < up.size());
  Vector u(up[j]);
  const uint n(u.size());
  for (uint k=0; k<niter; ++k)
    for (uint i=1; i<n-1; ++i) 
      u[i] = 0.5*u[i] + 0.25*(u[i-1] + u[i+1]);
}

Real InitGrid::adaptULine(uint i, uint nu, Real lmax, Real lmin, Real phimax)
{
  if (nu < 12)
    return 0.0;
  
  Real cpmin = cos(phimax);
  Real v = vp[i];
  bool iswing = not smoothSeam(v);
  uint nc = max(9u, nu/3);
  nc += 1 - nc%2;
  
  // recycle existing pattern if present 
  Vector u;
//   if (up[i].size() >= nc)
//     u = resize_pattern(up[i], nc);
//   else
    u = equi_pattern(nc);
  
  PointList<3> pts, nrm;
  pts.reserve(nu);
  pts.resize(nc);
  nrm.reserve(nu);
  nrm.resize(nc);
  
  // compute all points and normals
  Vct3 ptmp, Su, Sv;
  for (uint j=0; j<nc; ++j) {
    pts[j] = psf->eval(u[j], v);
    nrm[j] = psf->derive(u[j], v, 1, 0);
  }
  
  // compute average expected segment length
  Real ccf(0.0), lguide;
  for (uint j=1; j<nc; ++j)
    ccf += norm(pts[j] - pts[j-1]);
  lguide = ccf/(nu-1);
  
  // modify min length criterion for large frames
  lmin = max(lmin, lmin/lmax * lguide);
  
  // modify minimum length criterion for small frames
  lmin = min(lmin, lguide);
  
  // TE refinement parameters 
  const Real dute(0.16);
  const Real terf(1.6);
  
  Real cphi, len, qworst(0.0);
  while (nc < nu) {
    
    // locate worst segment 
    uint jworst(1);
    qworst = 0.0;
    for (uint j=1; j<nc; ++j) {
      Vct3 sgv(pts[j] - pts[j-1]);
      cphi = cosarg(nrm[j], nrm[j-1]);
      len = norm(sgv);
      Real qa = cb((1.0 + cpmin) / (1.0 + gmepsilon + cphi));
      Real ql = len/lmax;
      
      // modify ql near TE 
      if (iswing) {
        Real dte(0.0);
        if (u[j-1] < dute)
          dte = 1.0 - u[j-1]/dute;
        else if (u[j] > 1.0-dute)
          dte = 1.0 - (1.0 - u[j])/dute;
        ql *= (1.0 + terf*dte);
      }
      
      Real q = max(qa,ql);
      if (q > qworst and len > lmin) {
        jworst = j;
        qworst = q;
      }
    }

    // split segment jworst 
    Real umid = 0.5*(u[jworst] + u[jworst-1]);
    u.insert(u.begin()+jworst, umid);
    pts.insert(pts.begin()+jworst, psf->eval(umid, v));
    nrm.insert(nrm.begin()+jworst, psf->derive(umid, v, 1, 0));
    ++nc;
  }
  
  // swap-in refined vector 
  up[i].swap(u);
  
  // smoothing pass 
  usmoothColumn(i, 3);
  
  return qworst;
}

void InitGrid::vsmooth(uint niter)
{
  const uint nu(up.size());
  for (uint k=0; k<niter; ++k) {
    uint nv = up[0].size();
    for (uint j=0; j<nv; ++j) 
      up[0][j] = 0.5*up[0][j] + 0.5*up[1][j];
    for (uint i=1; i<nu-1; ++i) {
      nv = up[i].size();
      for (uint j=0; j<nv; ++j) {
        up[i][j] = 0.5*up[i][j] + 0.25*(up[i-1][j] + up[i+1][j]);
      }
    }
    nv = up[nu-1].size();
    for (uint j=0; j<nv; ++j) 
      up[nu-1][j] = 0.5*up[nu-1][j] + 0.5*up[nu-2][j];
  }
}

void InitGrid::enforceUSymmetry()
{
  const uint nv(vp.size());
  for (uint j=0; j<nv; ++j) {
    uint nu = up[j].size();
    for (uint i=0; i<nu/2; ++i) {
      Real u1 = up[j][i];
      Real u2 = 1.0 - up[j][nu-1-i];
      Real uc = 0.5*(u1 + u2);
      up[j][i] = uc;
      up[j][nu-1-i] = 1.0 - uc;
    }
    if (nu%2 == 1)
      up[j][nu/2] = 0.5;
  }
}

void InitGrid::enforceVSymmetry()
{
  const uint nv(vp.size());
  for (uint j=0; j<(nv/2); ++j) {
    Real v1 = vp[j];
    Real v2 = 1.0 - vp[nv-1-j];
    Real vc = 0.5*(v1 + v2);
    vp[j] = vc;
    vp[nv-1-j] = 1.0 - vc;
  }
  if (nv%2 == 1) {
    vp[nv/2] = 0.5;
  } else {
    Vector ins = 0.5*(up[nv/2-1] + up[nv/2]);
    vp.insert(vp.begin()+nv/2, 0.5);
    up.insert(up.begin()+nv/2, ins);
  }
}

void InitGrid::enforceColumns(const Vector & vpos)
{
  const int nc(vpos.size());
  const int nv(vp.size());
  for (int i=0; i<nc; ++i) {
    Real mindst = huge;
    int jnearest = 0;
    for (int j=0; j<nv; ++j) {
      Real dst = fabs(vp[j] - vpos[i]);
      if (dst < mindst) {
        mindst = dst;
        jnearest = j;
      }
    }
    vp[jnearest] = vpos[i];
  }
}

bool InitGrid::smoothSeam(Real v) const
{
  Vct3 n0 = psf->normal(0.0, v);
  Vct3 n1 = psf->normal(1.0, v);
  return (cosarg(n0,n1) > 0.8);
}
