
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
 
#include "ringcapsurf.h"
#include "paver.h"
#include "dnmesh.h"
#include "dnrefine.h"
#include <genua/pattern.h>
#include <genua/lu.h>

#ifndef NDEBUG
#include <genua/mxmesh.h>
#endif

using namespace std;

void RingCapSurf::init(const Surface & srf,
                       const PointList<2> & qts, Real h)
{
  if (h == 0) {
    initFlat(srf, qts);
  } else {
    initDome(srf, qts, h);
  }
}

void RingCapSurf::initFlat(const Surface & srf, const PointList<2> & qts)
{
  // extract boundary points (to be matched) and inward normals
  const int nu = qts.size();
  PointList<3> bp0(nu), ni0(nu);
  for (int i=0; i<nu; ++i) {
    uint k = nu-1-i;  // reverse direction
    bp0[i] =  srf.eval( qts[k][0], qts[k][1] );
    ni0[i] = -srf.normal( qts[k][0], qts[k][1] );
  }


  // generate arclength parametrization for u-direction
  // and determine straight segment center
  Vct3 ctr;
  Vector up(nu);
  for (int i=1; i<nu; ++i) {
    Real slen = norm(bp0[i] - bp0[i-1]);
    up[i] = up[i-1] + slen;
    ctr += slen*0.5*(bp0[i] + bp0[i-1]);
  }
  Real ccf = up.back();
  ctr /= ccf;
  up /= ccf;

  // mean boundary plane normal
  Vct3 pn = meanNormal(ctr, bp0);

  // scale normals appropriately (local radius)
  for (int i=0; i<nu; ++i) {
    ni0[i] -= dot(pn,ni0[i])*pn;
    ni0[i] *= norm(bp0[i] - ctr) / norm(ni0[i]);
  }

  // manufacture regularly distributed radial normal vectors
  // pointing into ctr at v == 1
  PointList<3> ni1(ni0);
  flatNormals(pn, up, ni1);

  // make inner normals equally long
  for (int i=0; i<nu; ++i)
    ni1[i] *= ccf / (2*PI*norm(ni1[i]));

  // set up spline surface bases
  ub.init(3, up);
  Vector vknots(8);
  for (int i=0; i<4; ++i) {
    vknots[i] = 0.0;
    vknots[4+i] = 1.0;
  }
  vb = SplineBasis(3, vknots);

  // interpolation problem: match given boundary points and
  // inward normals at up, v = 0; match center point and assigned
  // radial direction at up, v = 1
  SMatrix<2,4> bu, bv;
  Matrix a(4*nu,4*nu), rhs(4*nu,3);

  // assume that control points are stored in column-major
  // with u in rows as in
  //  for (uint i=0; i<4; ++i)
  //    for (uint j=0; j<4; ++j)
  //      pt += bu[i] * bv[j] * cp(uspan-3+i,vspan-3+j);

  for (int i=0; i<nu; ++i) {
    int uspan = ub.derive(up[i], bu);

    // C0 match condition at v == 0
    int vspan = vb.derive(0.0, bv);
    for (int ki=0; ki<4; ++ki) {
      for (int kj=0; kj<4; ++kj) {
        int col = (uspan-3+ki) + nu*( vspan-3+kj );
        a(4*i+0, col) = bu(0,ki)*bv(0,kj);
      }
    }
    for (int k=0; k<3; ++k)
      rhs(4*i+0,k) = bp0[i][k];

    // C1 match condition at v == 0
    for (int ki=0; ki<4; ++ki) {
      for (int kj=0; kj<4; ++kj) {
        int col = (uspan-3+ki) + nu*( vspan-3+kj );
        a(4*i+1, col) = bu(0,ki)*bv(1,kj);
      }
    }
    for (int k=0; k<3; ++k)
      rhs(4*i+1,k) = ni0[i][k];

    // C0 match condition at v == 1
    vspan = vb.derive(1.0, bv);
    for (int ki=0; ki<4; ++ki) {
      for (int kj=0; kj<4; ++kj) {
        int col = (uspan-3+ki) + nu*( vspan-3+kj );
        a(4*i+2, col) = bu(0,ki)*bv(0,kj);
      }
    }
    for (int k=0; k<3; ++k)
      rhs(4*i+2,k) = ctr[k];

    // C1 match condition at v == 1
    for (int ki=0; ki<4; ++ki) {
      for (int kj=0; kj<4; ++kj) {
        int col = (uspan-3+ki) + nu*( vspan-3+kj );
        a(4*i+3, col) = bu(0,ki)*bv(1,kj);
      }
    }
    for (int k=0; k<3; ++k)
      rhs(4*i+3,k) = ni1[i][k];
  }

  // compute control points
  lu_solve(a, rhs);
  cp.resize(nu,4);

  // copy results
  for (int j=0; j<4; ++j) {
    for (int i=0; i<nu; ++i)
      for (int k=0; k<3; ++k)
        cp(i,j)[k] = rhs(j*nu+i,k);
  }

  // make sure that the seam (u=0,u=1) is closed
  for (int j=0; j<4; ++j) {
    cp(0,j) = cp(nu-1,j) = 0.5*(cp(0,j) + cp(nu-1,j));
  }

  // store boundary points
  m_bnq.resize(nu);
  for (int i=0; i<nu; ++i)
    m_bnq[i] = vct(up[i], 0.0);

  // avoid self-intersections
  smoothCpGrid(3);

  dump();
}

Vct3 RingCapSurf::meanNormal(const Vct3 & ctr,
                             const PointList<3> & bp) const
{
  const uint n = bp.size();
  Vct3 mn;
  for (uint i=1; i<n; ++i) {
    Vct3 r1 = bp[i-1] - ctr;
    Vct3 r2 = bp[i] - ctr;
    mn += cross(r1, r2);
  }
  return mn.normalized();
}

void RingCapSurf::flatNormals(const Vct3 & pn, const Vector & up,
                              PointList<3> & ni) const
{
  // precondition : ni is set to outer normals
  const int n = ni.size();

  // axes
  Vct3 xax(ni.front()), yax;
  xax -= dot(xax,pn)*pn;
  normalize(xax);
  yax = cross(pn,xax).normalized();

  if (dot(yax, ni[n/4]) < 0)
    yax = -yax;

  // generate directions
  Real sphi, cphi;
  for (int i=0; i<n; ++i) {
    sincosine(2*PI*up[i], sphi, cphi);
    ni[i] = cphi*xax + sphi*yax;
  }
}

void RingCapSurf::smooth(PointList<3> & ni, int npass) const
{
  const int nu = ni.size();
  PointList<3> work(ni);
  for (int j=0; j<npass; ++j) {
    for (int i=1; i<nu-1; ++i) {
      const Vct3 & npre = ni[i-1];
      const Vct3 & npost = ni[i+1];
      work[i] = 0.5*ni[i] + 0.25*(npre + npost);
    }
    work.front() = work.back() = 0.5*(work.front() + work.back());
    work.swap(ni);
  }
}

void RingCapSurf::initDome(const Surface & srf,
                           const PointList<2> & qts, Real h)
{
  // extract boundary points (to be matched) and local slope
  Vct3 ni0mean;
  const int nu = qts.size();
  PointList<3> bp0(nu), ni0(nu);
  for (int i=0; i<nu; ++i) {
    uint k = nu-1-i;  // reverse direction
    bp0[i] =  srf.eval(qts[k][0], qts[k][1]);
    ni0[i] =  srf.derive(qts[k][0], qts[k][1], 0, 1);
    ni0mean += ni0[i];
  }
  normalize(ni0mean);

  // generate arclength parametrization for u-direction
  // and determine straight segment center
  Vct3 ctr;
  Vector up(nu);
  for (int i=1; i<nu; ++i) {
    Real slen = norm(bp0[i] - bp0[i-1]);
    up[i] = up[i-1] + slen;
    ctr += slen*0.5*(bp0[i] + bp0[i-1]);
  }
  Real ccf = up.back();
  ctr /= ccf;
  up /= ccf;

  // mean boundary plane normal
  Vct3 pn = meanNormal(ctr, bp0);

  // check whether normals need to be inverted
  if ( dot(ni0mean, pn) < 0 ) {
    for (int i=0; i<nu; ++i)
      ni0[i] = -ni0[i];
  }

  // h is a relative height; scale by min radius
  Real minrad; // mrad = ccf / (2*PI);
  minrad = huge;
  for (int i=0; i<nu; ++i)
    minrad = std::min(minrad, norm(bp0[i] - ctr));

  Real stdf = stdFactor(pn, ni0);
  stdf *= stdf;
  h *= minrad * stdf;

  // shift center away from plane
  ctr += h * pn;

  // scale normals appropriately (local radius)
  // and create inner normals
  PointList<3> ni1(nu);
  for (int i=0; i<nu; ++i) {
    Real lrad = norm(bp0[i] - ctr);
    lrad = sqrt(sq(lrad) + sq(h));
    ni0[i] *= lrad  / norm(ni0[i]);
    ni1[i]  = ni0[i] - dot(ni0[i],pn)*pn;
    ni1[i] *= lrad / norm(ni1[i]);
  }

  // set up spline surface bases
  ub.init(3, up);
  Vector vknots(8);
  for (int i=0; i<4; ++i) {
    vknots[i] = 0.0;
    vknots[4+i] = 1.0;
  }
  vb = SplineBasis(3, vknots);

  // interpolation problem: match given boundary points and
  // inward normals at (up, v = 0); match center point and assigned
  // radial direction at (up, v = 1)
  SMatrix<2,4> bu, bv;
  Matrix a(4*nu,4*nu), rhs(4*nu,3);

  // assume that control points are stored in column-major
  // with u in rows as in
  //  for (uint i=0; i<4; ++i)
  //    for (uint j=0; j<4; ++j)
  //      pt += bu[i] * bv[j] * cp(uspan-3+i,vspan-3+j);

  for (int i=0; i<nu; ++i) {
    int uspan = ub.derive(up[i], bu);

    // C0 match condition at v == 0
    int vspan = vb.derive(0.0, bv);
    for (int ki=0; ki<4; ++ki) {
      for (int kj=0; kj<4; ++kj) {
        int col = (uspan-3+ki) + nu*( vspan-3+kj );
        a(4*i+0, col) = bu(0,ki)*bv(0,kj);
      }
    }
    for (int k=0; k<3; ++k)
      rhs(4*i+0,k) = bp0[i][k];

    // C1 match condition at v == 0
    for (int ki=0; ki<4; ++ki) {
      for (int kj=0; kj<4; ++kj) {
        int col = (uspan-3+ki) + nu*( vspan-3+kj );
        a(4*i+1, col) = bu(0,ki)*bv(1,kj);
      }
    }
    for (int k=0; k<3; ++k)
      rhs(4*i+1,k) = ni0[i][k];

    // C0 match condition at v == 1
    vspan = vb.derive(1.0, bv);
    for (int ki=0; ki<4; ++ki) {
      for (int kj=0; kj<4; ++kj) {
        int col = (uspan-3+ki) + nu*( vspan-3+kj );
        a(4*i+2, col) = bu(0,ki)*bv(0,kj);
      }
    }
    for (int k=0; k<3; ++k)
      rhs(4*i+2,k) = ctr[k];

    // C1 match condition at v == 1
    for (int ki=0; ki<4; ++ki) {
      for (int kj=0; kj<4; ++kj) {
        int col = (uspan-3+ki) + nu*( vspan-3+kj );
        a(4*i+3, col) = bu(0,ki)*bv(1,kj);
      }
    }
    for (int k=0; k<3; ++k)
      rhs(4*i+3,k) = ni1[i][k];
  }

  // compute control points
  lu_solve(a, rhs);
  cp.resize(nu,4);

  // copy results
  for (int j=0; j<4; ++j) {
    for (int i=0; i<nu; ++i)
      for (int k=0; k<3; ++k)
        cp(i,j)[k] = rhs(j*nu+i,k);
  }

  // make sure that the seam (u=0,u=1) is closed
  for (int j=0; j<4; ++j) {
    cp(0,j) = cp(nu-1,j) = 0.5*(cp(0,j) + cp(nu-1,j));
  }

  // store boundary points
  m_bnq.resize(nu);
  for (int i=0; i<nu; ++i)
    m_bnq[i] = Vct2(up[i], 0.0);

  // avoid self-intersections
  // smoothCpGrid(1, 0.2);

  dump();
}

Real RingCapSurf::stdFactor(const Vct3 & pn,
                            const PointList<3> & nout) const
{
  const int n = nout.size();
  Real sf = 0.0;
  for (int i=0; i<n; ++i) {
    sf += cosarg(nout[i], pn);
  }
  return sf/n;
}

void RingCapSurf::initMesh(const DnRefineCriterion &,
                           DnMesh & gnr) const
{
  PointList<2> pts;
  Indices tri;
  pavedMesh(pts, tri);
  gnr.importMesh(pts, tri);
  gnr.smooth(2, 0.3);
}

XmlElement RingCapSurf::toXml(bool share) const
{
  XmlElement xe("RingCapSurf");

  {
    XmlElement xb("BoundaryPoints");
    xb["count"] = m_bnq.size();
    xb.asBinary(2*m_bnq.size(), m_bnq.pointer(), share);
    xe.append(std::move(xb));
  }

  xe.append( TranSurf::toXml(share) );

  return xe;
}

void RingCapSurf::fromXml(const XmlElement & xe)
{
  if (xe.name() != "RingCapSurf")
    throw Error("Incompatible XML representation of RingCapSurf.");

  XmlElement::const_iterator itr, ilast;
  ilast = xe.end();
  for (itr = xe.begin(); itr != ilast; ++itr) {
    if (itr->name() == "BoundaryPoints") {
      m_bnq.resize( Int(itr->attribute("count")) );
      xe.fetch(2*m_bnq.size(), m_bnq.pointer());
    } else if (itr->name() == "TranSurf") {
      TranSurf::fromXml(*itr);
    }
  }
}

void RingCapSurf::pavedMesh(PointList<2> &pts, Indices &tri) const
{
  // start at the outer boundary
  Paver paver(*this);
  paver.nextRow(m_bnq);

  // extract circumferential pattern
  const int nu = m_bnq.size();
  Vector up(nu), uj;
  for (int i=0; i<nu; ++i)
    up[i] = m_bnq[i][0];

  // and proceed inward
  const int nir = int(sqrt(float(nu)));
  Real dv = 1.0 / (nir+1);
  int dn = nu/(nir+1), nj = nu;
  for (int j=0; j<nir; ++j) {
    nj = max(6, nj - dn);
    interpolate_pattern(up, nj, uj);
    paver.nextVRow((j+1)*dv, uj);
  }

  // finally, create central triangle fan
  paver.fan(Vct2(0.0, 1.0));
  pts = paver.vertices();
  tri = paver.triangles();
}

void RingCapSurf::smoothCpGrid(int npass, Real omg)
{
  // smooth along u
  const int nu = TranSurf::cp.nrows();
  const int nv = TranSurf::cp.ncols();
  PointGrid<3> work(cp);
  for (int k=0; k<npass; ++k) {
    for (int j=1; j<nv-1; ++j) {
      for (int i=0; i<nu; ++i) {
        int iprv = (i > 0) ? i-1 : nu-1;
        int inxt = (i < nu-1) ? i+1 : 0;
        work(i,j) = (1-omg)*cp(i,j) + 0.25*omg*(cp(iprv,j-1) + cp(inxt,j-1)
                                              + cp(iprv,j+1) + cp(inxt,j+1));
      }
      work(0,j) = work(nu-1,j) = 0.5*(work(0,j) + work(nu-1,j));
    }
    work.swap(cp);
  }
}

void RingCapSurf::dump()
{
#ifndef NDEBUG
  MxMesh mx;
  mx.appendSection(TranSurf::cp);
  mx.toXml(true).write(name() + "Cp.xml", XmlElement::ZippedXml);
#endif
}
