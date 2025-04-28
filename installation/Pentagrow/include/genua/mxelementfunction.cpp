
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
 
#include "mxelementfunction.h"
#include "mxmesh.h"
#include <predicates/predicates.h>

MxElementFunction::~MxElementFunction() {}

size_t MxElementFunction::inRange(Real minValue, Real maxValue,
                                  Indices &elx) const
{
  if (m_pmsh == 0)
    return 0;

  Indices tmp;
  Vector v;
  size_t ntested = 0;
  for (uint j=0; j<m_pmsh->nsections(); ++j) {
    const MxMeshSection &sec( m_pmsh->section(j) );
    const uint offset = sec.indexOffset();
    const size_t ne = sec.nelements();
    v.allocate(ne);
    if ( this->eval(j, v) ) {
      for (size_t i=0; i<ne; ++i) {
        if (v[i] >= minValue and v[i] <= maxValue)
          tmp.push_back(offset+i);
      }
      ntested += ne;
    }
  }

  if (elx.empty()) {
    elx.swap(tmp);
  } else {
    size_t mid = elx.size();
    elx.insert(elx.end(), tmp.begin(), tmp.end());
    std::inplace_merge(elx.begin(), elx.begin()+mid, elx.end());
    elx.erase(std::unique(elx.begin(), elx.end()), elx.end());
  }

  return ntested;
}

size_t MxElementFunction::elementsAbove(Real threshold, Indices &elx) const
{
  Real big = std::numeric_limits<Real>::max();
  return this->inRange(threshold, big, elx);
}

size_t MxElementFunction::elementsBelow(Real threshold, Indices &elx) const
{
  Real big = std::numeric_limits<Real>::max();
  return this->inRange(-big, threshold, elx);
}

size_t MxElementFunction::histogram(const Vector &thresholds, Indices &bins) const
{
  if (m_pmsh == 0)
    return 0;

  const int nbin = thresholds.size() + 1;
  bins = Indices(nbin, 0);

  Vector v;
  size_t ntested = 0;
  for (uint j=0; j<m_pmsh->nsections(); ++j) {
    const MxMeshSection &sec( m_pmsh->section(j) );
    const size_t ne = sec.nelements();
    v.allocate(ne);
    if ( this->eval(j, v) ) {
      for (size_t i=0; i<ne; ++i) {
        Real x = v[i];
        if (x >= thresholds.back()) {
          ++(bins.back());
        } else {
          for (int k=0; k<nbin-1; ++k) {
            if (x < thresholds[k]) {
              ++bins[k];
              break;
            }
          }
        }
      }
      ntested += ne;
    }
  }

  return ntested;
}

// -------------------------- MxTangledElement ---------------------------

bool MxTangledElement::eval(uint isec, Vector &val) const
{
  if (m_pmsh == 0)
    return false;

  const PointList<3> &vtx( m_pmsh->nodes() );
  const MxMeshSection &sec( m_pmsh->section(isec) );
  const size_t ne = sec.nelements();

  switch (sec.elementType()) {
  case Mx::Tet4:
  case Mx::Tet10:
    val.allocate( ne );
    for (size_t i=0; i<ne; ++i) {
      const uint *v = sec.element(i);
      Real ori = jrsOrient3d( vtx[v[0]], vtx[v[1]], vtx[v[2]], vtx[v[3]] );
      val[i] = (ori < 0.0) ? 1.0 : -1.0;
    }
    break;
  case Mx::Penta6:
  case Mx::Penta15:
  case Mx::Penta18:
    val.allocate( ne );
    for (size_t i=0; i<ne; ++i) {
      const uint *v = sec.element(i);
      bool pv = true;
      pv &= jrsOrient3d( vtx[v[0]], vtx[v[1]], vtx[v[2]], vtx[v[3]] ) < 0.0;
      pv &= jrsOrient3d( vtx[v[0]], vtx[v[1]], vtx[v[2]], vtx[v[4]] ) < 0.0;
      pv &= jrsOrient3d( vtx[v[0]], vtx[v[1]], vtx[v[2]], vtx[v[5]] ) < 0.0;
      val[i] = pv ? 1.0 : -1.0;
    }
    break;
  default:
    return false;
  }

  return true;
}

// -------------------------- tet dihedral angle ---------------------------

static inline void tet4_cosphi(const PointList<3> &vtx,
                               const uint v[], Real cphi[])
{
  // compute face normals
  Vct3 fn[4];
  const int tri[] = {0,2,1, 0,1,3, 0,3,2, 1,2,3};
  for (int k=0; k<4; ++k) {
    uint a = v[tri[3*k+0]];
    uint b = v[tri[3*k+1]];
    uint c = v[tri[3*k+2]];
    fn[k] = cross( vtx[b]-vtx[a], vtx[c]-vtx[a] );
  }

  cphi[0] = cosarg(fn[1], fn[0]); // front-bottom
  cphi[1] = cosarg(fn[1], fn[2]); // front-left
  cphi[2] = cosarg(fn[1], fn[3]); // front-right
  cphi[3] = cosarg(fn[2], fn[0]); // left-right
  cphi[4] = cosarg(fn[2], fn[3]); // left-bottom
  cphi[5] = cosarg(fn[3], fn[0]); // right-bottom
}

bool MxMinDihedralAngle::eval(uint isec, Vector &val) const
{
  if (m_pmsh == 0)
    return false;

  const MxMeshSection &sec( m_pmsh->section(isec) );
  int etype = sec.elementType();
  if (etype != Mx::Tet4 and etype != Mx::Tet10)
    return false;

  const size_t ne = sec.nelements();
  val.allocate( ne );
  for (size_t i=0; i<ne; ++i) {
    Real cphi[6];
    tet4_cosphi(m_pmsh->nodes(), sec.element(i), cphi);
    Real mincphi = 1.0;
    for (int k=0; k<6; ++k)
      mincphi = std::min(mincphi, cphi[k]);
    val[i] = M_PI - acos(mincphi);
  }

  return true;
}

bool MxMaxDihedralAngle::eval(uint isec, Vector &val) const
{
  if (m_pmsh == 0)
    return false;

  const MxMeshSection &sec( m_pmsh->section(isec) );
  int etype = sec.elementType();
  if (etype != Mx::Tet4 and etype != Mx::Tet10)
    return false;

  const size_t ne = sec.nelements();
  val.allocate( ne );
  for (size_t i=0; i<ne; ++i) {
    Real cphi[6];
    tet4_cosphi(m_pmsh->nodes(), sec.element(i), cphi);
    Real maxcphi = -1.0;
    for (int k=0; k<6; ++k)
      maxcphi = std::max(maxcphi, cphi[k]);
    val[i] = M_PI - acos(maxcphi);
  }

  return true;
}

// ---------------------- skew angle ------------------------------------------

// compute cosine of skew angles for quad elements
inline Real quad_skew_angles(const PointList<3> &vtx, const uint v[], Real cphi[])
{
  // these angles should be zero, i.e. cosphi = 1
  const Vct3 & p0( vtx[v[0]] );
  const Vct3 & p1( vtx[v[1]] );
  const Vct3 & p2( vtx[v[2]] );
  const Vct3 & p3( vtx[v[3]] );

  Real phimax = 0;
  cphi[0] = cosarg(p1-p0, p2-p3);
  cphi[1] = cosarg(p3-p0, p2-p1);
  phimax = fabs( acos( std::min(cphi[0], cphi[1]) ) );

  // these angles should be 90 deg, i.e. cosphi = 0
  cphi[2] = cosarg(p1-p0, p3-p0);
  cphi[3] = cosarg(p0-p1, p2-p1);
  cphi[4] = cosarg(p3-p2, p1-p2);
  cphi[5] = cosarg(p0-p3, p2-p3);

  Real cpm = 0;
  for (int i=2; i<6; ++i) {
    if (fabs(cphi[i]) > fabs(cpm))
      cpm = cphi[i];
  }

  Real betamax = fabs( acos(cpm) - M_PI );
  return std::max(phimax, betamax);
}

// compute cosine of skew angles for penta/hexa elements, return minimum
template <int N>
inline Real vol_skew_angles(const PointList<3> &vtx, const uint v[], Real cphi[])
{
  // determine N angles between base edges of opposing faces (torque)
  Real cpm = 1.0;
  for (int k=0; k<N; ++k) {
    uint s = v[k];
    uint t = v[(k+1)%N];
    Vct3 e1 = vtx[t] - vtx[s];
    Vct3 e2 = vtx[t+N] - vtx[s+N];
    cphi[k] = cosarg(e1, e2);
    cpm = std::min(cphi[k], cpm);
  }

  // determine N angles between edges connecting base faces (skew)
  for (int k=0; k<N; ++k) {
    uint l = (k+1)%N;
    Vct3 e1 = vtx[k+N] - vtx[k];
    Vct3 e2 = vtx[l+N] - vtx[l];
    cphi[N+k] = cosarg(e1, e2);
    cpm = std::min(cphi[N+k], cpm);
  }

  return cpm;
}

bool MxMaxSkewAngle::eval(uint isec, Vector &val) const
{
  if (m_pmsh == 0)
    return false;

  const MxMeshSection &sec( m_pmsh->section(isec) );
  const size_t ne = sec.nelements();
  val.allocate(ne);
  int etype = sec.elementType();

  // TODO: parallelize, make cphi private or drop it

  Real cphi[16];
  switch (etype) {
  case Mx::Quad4:
  case Mx::Quad8:
  case Mx::Quad9:
    for (size_t i=0; i<ne; ++i)
      val[i] = quad_skew_angles( m_pmsh->nodes(), sec.element(i), cphi );
    break;
  case Mx::Penta6:
  case Mx::Penta15:
  case Mx::Penta18:
    for (size_t i=0; i<ne; ++i) {
      Real cpm = vol_skew_angles<6>( m_pmsh->nodes(), sec.element(i), cphi );
      val[i] = acos(cpm);
    }
    break;
  case Mx::Hex8:
  case Mx::Hex20:
  case Mx::Hex27:
    for (size_t i=0; i<ne; ++i) {
      Real cpm = vol_skew_angles<8>( m_pmsh->nodes(), sec.element(i), cphi );
      val[i] = acos(cpm);
    }
    break;
  default:
    return false;
  };

  return true;
}




