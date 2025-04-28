
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
 
#include "cascademesh.h"
#include <genua/dbprint.h>

using namespace std;

template <typename Type>
static inline Type ipow(Type x, uint y)
{
  Type t(1);
  for (uint i=0; i<y; ++i)
    t *= x;
  return t;
}

CascadeMesh::CascadeMesh(const Surface *srf, const PointGrid<2> & g)
  : m_psf(srf), m_maxkinsert(5)
{
  init(g);
}

void CascadeMesh::init(const PointGrid<2> & g)
{
  if (not m_psf)
    return;
  
  m_nrows = g.nrows();
  m_ncols = g.ncols();
  m_ppt.resize(m_nrows*m_ncols);
  m_vtx.resize(m_nrows*m_ncols);
  
  for (uint j=0; j<m_ncols; ++j) {
    for (uint i=0; i<m_nrows; ++i) {
      const Vct2 & q(g(i,j));
      m_ppt[j*m_nrows + i] = q;
      m_vtx[j*m_nrows + i] = m_psf->eval(q[0], q[1]);
    }
  }
}

void CascadeMesh::generate(Real stretchlimit, uint kmax, bool generateTriangles)
{
  m_gentris = generateTriangles;
  m_maxkinsert = kmax;
  for (uint j=0; j<m_ncols-1; ++j)
    processColumn(j, stretchlimit);
}

void CascadeMesh::exportMesh(PointList<2> & qts, Indices & tri) const
{
  assert(m_gentris);
  qts = m_ppt;
  tri = m_itri;
}

void CascadeMesh::exportMesh(PointList<2> & qts, PointList<3> & pts,
                             Indices & tri) const
{
  assert(m_gentris);
  qts = m_ppt;
  pts = m_vtx;
  tri = m_itri;
}

Real CascadeMesh::stretch(uint irow, uint jcol) const
{
  if (irow > 0 and irow < m_nrows-1) {
    Real s1 = stretchp(irow-1, jcol);
    Real s2 = stretchp(irow, jcol);
    return max(s1,s2);
  } else if (irow == 0) {
    return stretchp(irow, jcol);
  } else {
    return stretchp(irow-1, jcol);
  }
}

Real CascadeMesh::stretchp(uint irow, uint jcol) const
{
  Real rl1 = norm(pgrid(irow,jcol+1) - pgrid(irow,jcol));
  Real rl2 = norm(pgrid(irow+1,jcol+1) - pgrid(irow+1,jcol));
  Real cl1 = norm(pgrid(irow+1,jcol) - pgrid(irow,jcol));
  Real cl2 = norm(pgrid(irow+1,jcol+1) - pgrid(irow,jcol+1));
  return (rl1+rl2) / (cl1+cl2);
}

Real CascadeMesh::wrap(uint jcol) const
{
  const Vct3 & a1( pgrid(0,jcol) );
  const Vct3 & a2( pgrid(0,jcol+1) );
  const Vct3 & b1( pgrid(m_nrows-1,jcol) );
  const Vct3 & b2( pgrid(m_nrows-1,jcol+1) );
  Real d1 = norm(a1 - b1);
  Real d2 = norm(a2 - b2);
  return min(d1,d2);
}

void CascadeMesh::processColumn(uint jcol, Real mxst)
{
  // march through rows to determine refinement level
  Vector snow(m_nrows);
  Indices ksplit(m_nrows);
  fill(ksplit.begin(), ksplit.end(), 0);
  for (uint i=0; i<m_nrows; ++i) {
    Real s = stretch(i, jcol);
    snow[i] = s;
    uint k = (uint) max(0.0, ceil(log2(s/mxst)));
    ksplit[i] = min(k, m_maxkinsert);
  }
  
  // if surface is wrapped in u, that is if S(0,v) == S(1,v)
  // then we must enforce the same refinement level on the
  // first and the last row
  bool jwrap = wrap(jcol) < gmepsilon;
  if (jwrap) {
    uint kfront = ksplit.front();
    uint kback = ksplit.back();
    ksplit.front() = ksplit.back() = max(kfront, kback);
  }
  
  // negotiate suitable splitting level
  bool changed(true);
  while (changed) {
    changed = false;
    for (uint i=1; i<m_nrows-2; ++i) {
      int kprev = ksplit[i-1];
      int knext = ksplit[i+1];
      int k = ksplit[i];
      if (kprev > k+1) {
        k = kprev - 1;
        changed = true;
      }
      if (knext > k+1) {
        k = knext - 1;
        changed = true;
      }
      ksplit[i] = k;
    }
    
    if (jwrap) {
      uint kfront = ksplit.front();
      uint kback = ksplit.back();
      if (kfront != kback) {
        ksplit.front() = ksplit.back() = max(kfront, kback);
        changed = true;
      }
    }
  }
  
  // if cascading at this level would introduce cells with
  // too high stretch ratio in the opposite direction, we
  // must increase the allowed stretch ration
  Real tsmax(0.0);
  for (uint i=0; i<m_nrows; ++i) {
    int nsplit = ipow(2, ksplit[i]);
    Real ts = nsplit / snow[i];
    tsmax = max(ts, tsmax);
  }

  if (tsmax > mxst) {
    const Real maxtry = 20000;
    if (mxst >= maxtry) {
      dbprint("Cascading failed on grid column", jcol);
      fill(ksplit.begin(), ksplit.end(), 0);
    } else {
      dbprint("Cannot achieve this stretch ratio, increasing to", 2*mxst);
      processColumn(jcol, 2.0*mxst);
      return;
    }
  }

  // insert top points in first row
  Indices a, b;
  injectPoints(0, jcol, ksplit[0], a);
  
  // in each field, insert bottom points and generate triangles
  for (uint i=0; i<m_nrows-1; ++i) {
    
    // split level
    uint ktop = ksplit[i];
    uint kbot = ksplit[i+1];
    
    // insert bottom points
    injectPoints(i+1, jcol, kbot, b);
    
    if (m_gentris) {
      if (ktop == 0 and kbot == 0) {
        addBlock22( &a[0], &b[0] );
      } else {

        if (ktop < kbot) {
          uint nbox = ipow(2, ktop);
          for (uint ibox = 0; ibox < nbox; ++ibox)
            addBlock23( &a[ibox], &b[2*ibox] );
        } else if (ktop > kbot) {
          uint nbox = ipow(2, kbot);
          for (uint ibox = 0; ibox < nbox; ++ibox)
            addBlock23( &b[ibox], &a[2*ibox] );
        } else {
          uint nbox = ipow(2, ktop);
          for (uint ibox = 0; ibox < nbox; ++ibox)
            addBlock22( &a[ibox], &b[ibox] );
        }
      }

      // bottom of last row is top of next
      a.swap(b);

    } // m_gentris == true
  } // rows
}

void CascadeMesh::injectPoints(uint irow, uint jcol, uint k, Indices & a)
{
  if (m_gentris) {
    uint nins = ipow(2, k) - 1;
    Vct2 qleft( qgrid(irow,jcol) );
    Vct2 qright( qgrid(irow,jcol+1) );

    a.resize( 2 + nins );
    a[0] = jcol*m_nrows + irow;
    a[nins+1] = (jcol+1)*m_nrows + irow;
    for (uint m=0; m<nins; ++m) {
      Real t = Real(m+1) / (nins+1);
      a[m+1] = injectPoint( (1.-t)*qleft + t*qright );
    }
  } else {
    injectPoints(irow, jcol, k);
  }
}

void CascadeMesh::injectPoints(uint irow, uint jcol, uint k)
{
  uint nins = ipow(2, k) - 1;
  Vct2 qleft( qgrid(irow,jcol) );
  Vct2 qright( qgrid(irow,jcol+1) );
  for (uint m=0; m<nins; ++m) {
    Real t = Real(m+1) / (nins+1);
    injectPoint( (1.-t)*qleft + t*qright );
  }
}

void CascadeMesh::addTriangle(uint a, uint b, uint c)
{
  Vct2 qmid = (m_ppt[a] + m_ppt[b] + m_ppt[c]) / 3.0;
  Vct3 sn = m_psf->normal( qmid[0], qmid[1] );
  Vct3 fn = cross( m_vtx[b]-m_vtx[a], m_vtx[c]-m_vtx[a] );
  
  uint v[3];
  if (dot(sn,fn) > 0) {
    v[0] = a;
    v[1] = b;
    v[2] = c;
  } else {
    v[0] = a;
    v[1] = c;
    v[2] = b;
  }
  m_itri.insert(m_itri.end(), v, v+3);
}

void CascadeMesh::addBlock23(const uint a[2], const uint b[3])
{
  addTriangle( a[0], b[0], b[1] );
  addTriangle( a[0], b[1], a[1] );
  addTriangle( b[1], b[2], a[1] );
}

void CascadeMesh::addBlock22(const uint a[2], const uint b[2])
{
  Vct3 r1 = m_vtx[b[0]] - m_vtx[a[0]];
  Vct3 r2 = m_vtx[a[1]] - m_vtx[a[0]];
  Real cphi = cosarg(r1, r2);
  if (cphi > 0) {
    addTriangle( a[0], b[0], a[1] );
    addTriangle( b[0], b[1], a[1] );
  } else {
    addTriangle( a[0], b[1], a[1] );
    addTriangle( a[0], b[0], b[1] );
  }
}
