
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
#include "uvmapping.h"
#include "surface.h"
#include <genua/pattern.h>
#include <genua/lls.h>
#include <genua/dbprint.h>
#include <genua/mxmesh.h>

#ifdef HAVE_SPQR
#include <genua/csrmatrix.h>
#include <genua/sparseqr.h>
#endif

#include <iostream>

using namespace std;

uint UvMapping::s_max_neval(64);

UvMapping::UvMapping(const Surface &srf, const Vector &up, const Vector &vp)
{
  init(srf, up, vp);
}

void UvMapping::boundaries(Real &tmin, Real &tmax) const
{
  tmin = std::numeric_limits<Real>::max();
  tmax = -tmin;
  const int ncp = m_ctp.size();
  for (int i=0; i<ncp; ++i) {
    tmin = std::min(tmin, m_ctp[i]);
    tmax = std::max(tmax, m_ctp[i]);
  }
}

void UvMapping::downSample(const Vector &upp, Vector &up)
{
  uint npmax = up.empty() ? s_max_neval : up.size();
  if (upp.size() > npmax)
    interpolate_pattern(upp, npmax, up);
  else if (upp.size() < 4)
    interpolate_pattern(upp, 4, up);
  else
    up = upp;

  // smooth spacing
  const int n = up.size();
  Vector tmp(up);
  for (int i=1; i<n-1; ++i)
    up[i] = 0.5*tmp[i] + 0.25*(tmp[i-1] + tmp[i+1]);
  up.swap(tmp);
}

void UvMapping::upSample(const Vector &knots, Vector &p)
{
  const int m(2);
  assert(m > 0);

  p.clear();
  p.push_back(knots.front());

  const int nk = knots.size();
  for (int i=1; i<nk; ++i) {
    Real ki = knots[i];
    if ( ki == p.back() )
      continue;
    Real dk = (ki - p.back()) / m;
    Real back = p.back();
    for (int j=1; j<=m; ++j)
      p.push_back(back + j*dk);
  }
}

void UvMapping::init(const Surface &srf, const Vector &upp, const Vector &vpp)
{
  const uint max_ntot = 1024;
  const uint max_npar = s_max_neval;
  const uint npp = upp.size() * vpp.size();

  // knot count scaling
  Real fu(1.0), fv(1.0), ft(1.0);
  fu = std::min(1.0, Real(max_npar) / upp.size());
  fv = std::min(1.0, Real(max_npar) / vpp.size());
  ft = std::min(1.0, Real(max_ntot) / (fu*fv*npp));
  fu = std::min(fu, ft);
  fv = std::min(fv, ft);

  Vector up, vp;
  if (fu < 1.0) {
    up.resize( std::max(4, int(fu*upp.size()) ) );
    downSample(upp, up);
  } else {
    up = upp;
  }
  if (fv < 1.0) {
    vp.resize( std::max(4, int(fv*vpp.size()) ) );
    downSample(vpp, vp);
  } else {
    vp = vpp;
  }

  //  // debug
  //  cout << "up values: " << upp << endl
  //       << " up param: " << up << endl;
  //  cout << "vp values: " << vpp << endl
  //       << " vp param: " << vp << endl;

  m_ubas.init(SDEG, up);
  m_vbas.init(SDEG, vp);

  fitSpline(srf);
  buildLookupTable();
}

void UvMapping::fitSpline(const Surface &srf)
{
  bool fitted = false;

#ifdef HAVE_SPQR
  fitted = sparseFitSpline(srf);
#else
  fitted = denseFitSpline(srf);
#endif

  if (not fitted)
    fitted = lengthRatioMapping(srf);

  if (not fitted)
    throw Error("UvMapping::fitSpline() - Degenerate surface "+srf.name());
}

bool UvMapping::denseFitSpline(const Surface &srf)
{
  // generate grid of (u,v) points where skew and stretch will be matched
  Vector up, vp;
  upSample(m_ubas.getKnots(), up);
  upSample(m_vbas.getKnots(), vp);

  // number of equations
  const int npu = up.size();
  const int npv = vp.size();
  const int neq = 2*npu*npv+1;

  cout << "Fitting spline surface: " << m_ubas.ncontrol()
       << " x " << m_vbas.ncontrol() << ", equations: " << neq << endl;

  // number of control points
  const int ncu = m_ubas.ncontrol();
  const int ncv = m_vbas.ncontrol();
  const int ncp = ncu*ncv;

  SMatrix<2,SDEG+1> bu, bv;
  Vct3 S, Su, Sv;
  Matrix A(neq, ncp);
  Vector b(neq);
  for (int j=0; j<npv; ++j) {
    const Real v = vp[j];
    const int vspan = m_vbas.derive(v, bv);
    for (int i=0; i<npu; ++i) {
      const Real u = up[i];
      srf.plane(u, v, S, Su, Sv);
      Real squ = sq(Su);
      Real sqv = sq(Sv);
      Real c1 = sqv / squ;
      Real t1 = dot(Su,Sv);
      Real c2 = sq(t1) / (squ*sqv);
      Real fu = (t1 != 0.0) ? (sign(t1) * sqrt(c2 / (1-c2))) : 0.0;  // fu
      Real fv = sqrt(c1 / (1-c2));                   // fv

      if (c1 <= 0 or c2 >= 1)
        return false;

      const uint row = 2*(j*npu + i);
      b[row+0] = fu;
      b[row+1] = fv;

      const int uspan = m_ubas.derive(u, bu);
      for (int ki=0; ki<SDEG+1; ++ki) {
        for (int kj=0; kj<SDEG+1; ++kj) {
          const int col = (vspan+kj-SDEG)*ncu + (uspan+ki-SDEG);
          A(row+0, col) += bu(1,ki) * bv(0,kj);  // fu
          A(row+1, col) += bu(0,ki) * bv(1,kj);  // fv
        }
      }
    }
  }

  //  // apply weighting
  //  Real meanfu(0.0), meanfv(0.0);
  //  const int nrow = b.size();
  //  for (int i=0; i<nrow/2; ++i) {
  //    meanfu += fabs( b[2*i+0] );
  //    meanfv += fabs( b[2*i+1] );
  //  }
  //  meanfu /= 0.5*nrow;
  //  meanfv /= 0.5*nrow;

  const int nrow = b.size();
  const int ncol = A.ncols();
  for (int i=0; i<nrow/2; ++i) {
    Real fv = b[2*i+1];
    b[2*i+0] *= fv;
    //    b[2*i+1] *= imfv;
    for (int j=0; j<ncol; ++j) {
      A(2*i+0,j) *= fv;
      //  A(2*i+1,j) *= imfv;
    }
  }

  // last equation : t(0,0) = 0
  SVector<SDEG+1> cu, cv;
  const int uspan = m_ubas.eval(0.0, cu);
  const int vspan = m_vbas.eval(0.0, cv);
  for (int ki=0; ki<SDEG+1; ++ki) {
    for (int kj=0; kj<SDEG+1; ++kj) {
      const int col = (vspan+kj-SDEG)*ncu + (uspan+ki-SDEG);
      A(neq-1, col) += cu(ki) * cv(kj);
    }
  }
  b[neq-1] = 0.0;

  // solve least-squares problem
  lls_solve(A, b);

  m_ctp.resize(ncu, ncv);
  std::copy(b.begin(), b.end(), m_ctp.begin());

  return true;
}

bool UvMapping::lengthRatioMapping(const Surface &srf)
{
  // create single spline patch
  const int npu = SDEG+1;
  const int npv = npu;
  Vector up(npu), vp(npv);
  for (int i=0; i<npu; ++i)
    up[i] = vp[i] = Real(i+1) / (npu+1);

  m_ubas.init(SDEG, up);
  m_vbas.init(SDEG, vp);

  // number of control points
  const int ncu = m_ubas.ncontrol();
  const int ncv = m_vbas.ncontrol();
  const int ncp = npu * npv;

  SVector<SDEG+1> bu, bv;
  Vct3 S, Su, Sv;
  Matrix A(ncp, ncp);
  Vector b(ncp);
  for (int j=0; j<npv; ++j) {
    const Real v = vp[j];
    const int vspan = m_vbas.eval(v, bv);
    for (int i=0; i<npu; ++i) {
      const Real u = up[i];
      srf.plane(u, v, S, Su, Sv);
      Real lv = norm(Sv);
      Real lu = norm(Su);

      const uint row = (j*npu + i);
      if (lu > 0)
        b[row] = lv/lu * v;
      else
        b[row] = v;

      const int uspan = m_ubas.eval(u, bu);
      for (int ki=0; ki<SDEG+1; ++ki) {
        for (int kj=0; kj<SDEG+1; ++kj) {
          const int col = (vspan+kj-SDEG)*ncu + (uspan+ki-SDEG);
          A(row, col) += bu[ki] * bv[kj];
        }
      }
    }
  }
  lu_solve(A, b);

  m_ctp.resize(ncu, ncv);
  std::copy(b.begin(), b.end(), m_ctp.begin());

  return true;
}

void UvMapping::buildLookupTable()
{
  const int nup = m_ctp.nrows();
  const int nvp = m_ctp.ncols();
  m_ucol = resize_pattern(m_ubas.getKnots(), nup);
  m_vrow = resize_pattern(m_vbas.getKnots(), nvp);

  m_tval.resize(nvp, nup);
  for (int j=0; j<nup; ++j)
    for (int i=0; i<nvp; ++i)
      m_tval(i,j) = eval(m_ucol[j], m_vrow[i]);
}

Real UvMapping::vlookup(Real t, uint jcol) const
{
  const Real *cbeg = m_tval.colpointer(jcol);
  const Real *cend = cbeg + m_tval.nrows();
  const Real *pos = std::lower_bound(cbeg, cend, t);
  if (pos == cend)
    return 1.0;
  else if (pos == cbeg)
    return 0.0;

  Real tlo = *(pos - 1);
  Real thi = *pos;
  Real p = (t - tlo) / (thi - tlo);
  size_t ipos = std::distance(cbeg, pos);
  return (1.0 - p)*m_vrow[ipos-1] + p*m_vrow[ipos];
}

Vct2 UvMapping::lookup(const Vct2 &st) const
{
  Vector::const_iterator pos;
  pos = std::lower_bound(m_ucol.begin(), m_ucol.end(), st[0]);
  if (pos == m_ucol.begin())
    return Vct2(st[0], vlookup(st[1], 0));
  else if (pos == m_ucol.end())
    return Vct2(st[0], vlookup(st[1], m_tval.ncols()-1));

  size_t jcol = std::distance(m_ucol.begin(), pos);
  Real p = (st[0] - m_ucol[jcol-1]) / (m_ucol[jcol] - m_ucol[jcol-1]);
  Real vlo = vlookup(st[1], jcol-1);
  Real vhi = vlookup(st[1], jcol);
  return Vct2(st[0], (1.0 - p)*vlo + p*vhi);
}

Vct2 UvMapping::invert(const Vct2 &st, Real tol) const
{
  Vct2 uv, uvg = lookup(st);
  uv = uvg;
  if ( invert(st, uv, tol) )
    return uv;

  // invert failed; return the better of the two
  if ( fabs(st[1] - eval(uv[0], uv[1])) < fabs(st[1] - eval(uvg[0], uvg[1])) )
    return uv;
  else
    return uvg;
}

bool UvMapping::invert(const Vct2 &st, Vct2 &uv, Real tol) const
{
  uv[0] = st[0];
  Real r = st[1] - eval(uv[0], uv[1]);
  if (std::fabs(r) < tol)
    return true;

  // TODO: If this function turns up in profiling, optimize call
  // to gradient since u is constant and only tv is used
  for (int i=0; i<16; ++i) {
    Vct2 g = gradient(uv[0], uv[1]);
    uv[1] += r / g[1];
    uv[1] = clamp(uv[1], 0.0, 1.0);
    r = st[1] - eval(uv[0], uv[1]);
    if (std::fabs(r) < tol)
      return true;
  }
  return false;
}

void UvMapping::plane(const Surface &srf, Real u, Real v,
                      Vct3 &Ss, Vct3 &St) const
{
  Vct3 S, Su, Sv;
  srf.plane(u, v, S, Su, Sv);

  SMatrix<3,2> G1;
  G1.assignColumn(0, Su);
  G1.assignColumn(1, Sv);

  SMatrix<2,2> G2;
  G2.assignColumn(0, uvStep(Vct2(u,v), Vct2(1,0)));
  G2.assignColumn(1, uvStep(Vct2(u,v), Vct2(0,1)));

  G1 = G1 * G2;
  Ss = G1.column(0);
  St = G1.column(1);
}

#ifdef HAVE_SPQR

bool UvMapping::sparseFitSpline(const Surface &srf)
{
  // generate grid of (u,v) points where skew and stretch will be matched
  Vector up, vp;
  upSample(m_ubas.getKnots(), up);
  upSample(m_vbas.getKnots(), vp);

  // number of equations
  const int npu = up.size();
  const int npv = vp.size();
  const int neq = 2*npu*npv+1;

  cout << "Fitting spline surface: " << m_ubas.ncontrol()
       << " x " << m_vbas.ncontrol() << ", equations: " << neq << endl;

  // number of control points
  const int ncu = m_ubas.ncontrol();
  const int ncv = m_vbas.ncontrol();
  const int ncp = ncu*ncv;

  // assemble sparse coefficient matrix
  CsrMatrix<double,1> A(neq, ncp);
  {
    ConnectMap spty;
    spty.beginCount(neq);
    for (int j=0; j<npv; ++j) {
      for (int i=0; i<npu; ++i) {
        const uint row = 2*(j*npu + i);
        spty.incCount(row+0, (SDEG+1)*(SDEG+1));
        spty.incCount(row+1, (SDEG+1)*(SDEG+1));
      }
    }
    spty.incCount(neq-1, (SDEG+1)*(SDEG+1));
    spty.endCount();
    for (int j=0; j<npv; ++j) {
      const int vspan = m_vbas.findSpan(vp[j]);
      for (int i=0; i<npu; ++i) {
        const uint row = 2*(j*npu + i);
        const int uspan = m_ubas.findSpan(up[i]);
        for (int ki=0; ki<SDEG+1; ++ki) {
          for (int kj=0; kj<SDEG+1; ++kj) {
            const int col = (vspan+kj-SDEG)*ncu + (uspan+ki-SDEG);
            spty.append(row+0, col);
            spty.append(row+1, col);
          }
        }
      }
    }
    const int uspan = m_ubas.findSpan(0.0);
    const int vspan = m_vbas.findSpan(0.0);
    for (int ki=0; ki<SDEG+1; ++ki) {
      for (int kj=0; kj<SDEG+1; ++kj) {
        const int col = (vspan+kj-SDEG)*ncu + (uspan+ki-SDEG);
        spty.append(neq-1, col);
      }
    }
    spty.compress();
    A.swap(spty, ncp);
  }

  SMatrix<2,SDEG+1> bu, bv;
  Vct3 S, Su, Sv;
  Vector b(neq);
  for (int j=0; j<npv; ++j) {
    const Real v = vp[j];
    const int vspan = m_vbas.derive(v, bv);
    for (int i=0; i<npu; ++i) {
      const Real u = up[i];
      srf.plane(u, v, S, Su, Sv);
      Real squ = sq(Su);
      Real sqv = sq(Sv);
      Real c1 = sqv / squ;
      Real t1 = dot(Su,Sv);
      Real c2 = sq(t1) / (squ*sqv);
      Real fu = (t1 != 0.0) ? (sign(t1) * sqrt(c2 / (1-c2))) : 0.0;  // fu
      Real fv = sqrt(c1 / (1-c2));                   // fv

      if (c1 <= 0 or c2 >= 1)
        return false;

      const uint row = 2*(j*npu + i);
      b[row+0] = fu;
      b[row+1] = fv;

      const int uspan = m_ubas.derive(u, bu);
      for (int ki=0; ki<SDEG+1; ++ki) {
        for (int kj=0; kj<SDEG+1; ++kj) {
          const int col = (vspan+kj-SDEG)*ncu + (uspan+ki-SDEG);
          uint lix0 = A.lindex(row+0, col);
          uint lix1 = A.lindex(row+1, col);
          A.value(lix0, 0) += bu(1,ki) * bv(0,kj);  // fu
          A.value(lix1, 0) += bu(0,ki) * bv(1,kj);  // fv
        }
      }
    }
  }

  // apply weighting
  const int nrow = b.size();
  for (int i=0; i<nrow/2; ++i) {
    Real fv = b[2*i+1];
    b[2*i+0] *= fv;
    A.scaleRow(2*i+0, fv);
  }

  // last equation : t(0,0) = 0
  SVector<SDEG+1> cu, cv;
  const int uspan = m_ubas.eval(0.0, cu);
  const int vspan = m_vbas.eval(0.0, cv);
  for (int ki=0; ki<SDEG+1; ++ki) {
    for (int kj=0; kj<SDEG+1; ++kj) {
      const int col = (vspan+kj-SDEG)*ncu + (uspan+ki-SDEG);
      const uint lix = A.lindex(neq-1, col);
      A.value(lix,0) += cu(ki) * cv(kj);
    }
  }
  b[neq-1] = 0.0;

  // solve least-squares problem
  Vector x;
  SparseQR<double> spqr;
  spqr.solve(&A, b, x);

  m_ctp.resize(ncu, ncv);
  std::copy(x.begin(), x.end(), m_ctp.begin());

  return true;
}

#else // no SparseQR

bool UvMapping::sparseFitSpline(const Surface &) {return false;}

#endif // HAVE_SPQR


void UvMapping::dump(const string &fname) const
{
  // visualization of the mapping [u,v] -> [s,t]
  // map the (u,v) grid [0,1]^2 to the [s,t] domain and write out as
  // a quad mesh to observe stretch and skew factors

  const int nu = 3*m_ctp.nrows();
  const int nv = 3*m_ctp.ncols();
  PointGrid<3> pts(nu, nv);
  for (int j=0; j<nv; ++j) {
    Real v = Real(j) / (nv-1);
    for (int i=0; i<nu; ++i) {
      Real u = Real(i) / (nu-1);
      Real t = eval(u,v);
      pts(i,j) = vct(u, v, t);  // s == u
    }
  }

  MxMesh mx;
  mx.appendSection(pts);
  mx.toXml(true).zwrite(fname);
}



void UvMapping::clear()
{
  m_ctp.clear();
}
