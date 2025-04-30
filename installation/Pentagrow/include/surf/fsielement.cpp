
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
 
#include "fsielement.h"
#include "fsimesh.h"

using namespace std;

FsiElement::FsiElement(const FsiMesh & m, uint gix) : msh(m)
{
  vi = msh.structMesh().globalElement(gix, nv, isec);
  assert(vi != 0 and isec != NotFound);
  assert(nv > 0 and nv < max_nodes);
}

uint FsiElement::nearestFluidElement(Real u, Real v, Vct2 & fuv) const
{
  Real N[max_nodes];
  shapeFunction(u, v, N);

  // evaluation point
  Vct3 pep;
  for (uint i=0; i<nv; ++i)
    pep += N[i] * msh.structMesh().node( vi[i] );

  return msh.nearestFluidElement(pep, meanNormal, fuv);
}

void FsiElement::eval(const Vector & pf,
                      Real u, Real v, Real wgt, Vct3 npf[]) const
{
  Real N[max_nodes];
  Real detJ = shapeFunction(u, v, N);

  // evaluation point, psn is pressure times local normal
  Vct3 pep, psn;
  for (uint i=0; i<nv; ++i)
    pep += N[i] * msh.structMesh().node( vi[i] );

  Vct2 fuv;
  uint jfe = msh.nearestFluidElement(pep, meanNormal, fuv);
  if (jfe == NotFound)
    return;

  msh.evalPressure(pf, jfe, fuv, psn);

  // value of the force integrand
  for (uint i=0; i<nv; ++i)
    npf[i] += detJ * wgt * N[i] * psn;
}

void FsiElement::eval(const Vector & pf,
                      Real u, Real v, Real wgt, Vct6 npf[]) const
{
  Real N[max_nodes];
  Real detJ = shapeFunction(u, v, N);

  // evaluation point, psn is pressure times local normal
  Vct3 pep, psn;
  for (uint i=0; i<nv; ++i)
    pep += N[i] * msh.structMesh().node( vi[i] );

  Vct2 fuv;
  uint jfe = msh.nearestFluidElement(pep, meanNormal, fuv);
  if (jfe == NotFound)
    return;

  msh.evalPressure(pf, jfe, fuv, psn);

  // value of the force integrand
  for (uint i=0; i<nv; ++i) {
    const Vct3 & node( msh.structMesh().node( vi[i] ) );
    Vct3 epf = detJ * wgt * N[i] * psn;
    Vct3 epm = cross(pep - node, epf);
    for (int k=0; k<3; ++k) {
      npf[i][k+0] += epf[k];
      npf[i][k+3] += epm[k];
    }
  }
}

void FsiElement::eval(const Matrix & mpf, Real u, Real v, Real wgt,
                      PointList<3> & psn, PointGrid<6> & enf) const
{
  const int ncol = mpf.ncols();
  assert(enf.ncols() == size_t(ncol));
  assert(enf.nrows() >= nv);

  Real N[max_nodes];
  Real detJ = shapeFunction(u, v, N);

  // evaluation point
  Vct3 pep;
  for (uint i=0; i<nv; ++i)
    pep += N[i] * msh.structMesh().node( vi[i] );

  Vct2 fuv;
  uint jfe = msh.nearestFluidElement(pep, meanNormal, fuv);
  if (jfe == NotFound)
    return;

  msh.evalPressure(mpf, jfe, fuv, psn);

  // value of the force integrand
  for (int j=0; j<ncol; ++j) {
    for (uint i=0; i<nv; ++i) {
      const Vct3 & node( msh.structMesh().node( vi[i] ) );
      Vct3 pf = detJ * wgt * N[i] * psn[j];
      Vct3 pm = cross(pep - node, pf);
      Vct6 & fm( enf(i,j) );
      for (int k=0; k<3; ++k) {
        fm[k+0] += pf[k];
        fm[k+3] += pm[k];
      }
    }
  }
}

// nodal forces only

void FsiElement::integrate(const Vector & pf, uint nip,
                           const Real u[], const Real v[], const Real wgt[],
                           PointList<3> & gnf) const
{
  Vct3 enf[max_nodes];
  for (uint j=0; j<nip; ++j)
    eval(pf, u[j], v[j], wgt[j], enf);

  for (uint i=0; i<nv; ++i)
    msh.atomicUpdate<3>(vi[i], enf[i], gnf);
}

void FsiElement::tpIntegrate(const Vector & pf, uint nip, const Real u[],
                             const Real wgt[], PointList<3> & gnf) const
{
  Vct3 enf[max_nodes];
  for (uint j=0; j<nip; ++j)
    for (uint i=0; i<nip; ++i)
      eval(pf, u[i], u[j], wgt[i]*wgt[j], enf);

  for (uint i=0; i<nv; ++i)
    msh.atomicUpdate<3>(vi[i], enf[i], gnf);
}

// nodal forces and moments

void FsiElement::integrate(const Vector & pf, uint nip, const Real u[],
                           const Real v[], const Real wgt[],
                           PointList<6> & gnf) const
{
  Vct6 enf[max_nodes];
  for (uint j=0; j<nip; ++j)
    eval(pf, u[j], v[j], wgt[j], enf);

  for (uint i=0; i<nv; ++i)
    msh.atomicUpdate<6>(vi[i], enf[i], gnf);
}

void FsiElement::tpIntegrate(const Vector & pf, uint nip, const Real u[],
                             const Real wgt[], PointList<6> & gnf) const
{
  Vct6 enf[max_nodes];
  for (uint j=0; j<nip; ++j)
    for (uint i=0; i<nip; ++i)
      eval(pf, u[i], u[j], wgt[i]*wgt[j], enf);

  for (uint i=0; i<nv; ++i)
    msh.atomicUpdate<6>(vi[i], enf[i], gnf);
}

// multiple pressure fields

void FsiElement::integrate(uint nip, const Real u[], const Real v[],
                           const Real wgt[], const Matrix & mpf,
                           PointGrid<6> & gnf) const
{
  const uint nf = mpf.ncols();
  PointList<3> psn(nf);
  PointGrid<6> enf(nv, nf);

  // add contributions of integration points, process all
  // pressure fields in one pass (fluid element lookup is expensive)
  for (uint i=0; i<nip; ++i)
    eval(mpf, u[i], v[i], wgt[i], psn, enf);

  for (uint i=0; i<nv; ++i)
    for (uint j=0; j<nf; ++j)
      msh.atomicUpdate<6>(vi[i], enf(i,j), j, gnf);
}

// -------------------- FsiTri3 ----------------------------------

FsiTri3::FsiTri3(const FsiMesh & m, uint gix)
  : FsiElement(m, gix)
{
  const Vct3 & p1( msh.structMesh().node(vi[0]) );
  const Vct3 & p2( msh.structMesh().node(vi[1]) );
  const Vct3 & p3( msh.structMesh().node(vi[2]) );
  meanNormal = cross(p2-p1, p3-p1);
  detJ = normalize(meanNormal);
}

// ------------------- FsiQuad4 ----------------------------------

FsiQuad4::FsiQuad4(const FsiMesh & m, uint gix)
  : FsiElement(m, gix)
{
  const Vct3 & p1( msh.structMesh().node(vi[0]) );
  const Vct3 & p2( msh.structMesh().node(vi[1]) );
  const Vct3 & p3( msh.structMesh().node(vi[2]) );
  const Vct3 & p4( msh.structMesh().node(vi[3]) );
  meanNormal = cross(p3-p1, p4-p2).normalized();
  detJ  = norm(cross(p2-p1, p4-p1)) + norm(cross(p4-p3, p2-p3));
  detJ *= 0.5; // tensor product rule weights sum to 1.0
}
