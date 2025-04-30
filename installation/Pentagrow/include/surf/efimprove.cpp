
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
 
#include "edgefaceisec.h"
#include "meshpatch.h"
#include "efimprove.h"

using namespace std;

// index tables for edges and faces
static const uint efi_edges[2][2] = { {0,1},{1,2}};
static const uint efi_faces[4][3] =
  { {0,1,5},
    {1,2,3},
    {1,3,5},
    {3,4,5}
  };

// ----------------------------------------------------------------------------
  
EfImprove::EfImprove(const EdgeFaceIsec & is)
{
  // fetch spline surfaces
  const TriEdge & edge(is.segment());
  const TriFace & face(is.triangle());

  const MeshPatch *mpe(0);
  mpe = dynamic_cast<const MeshPatch*>( edge.mesh() );
  assert(mpe != 0);
  const MeshPatch *mpf(0);
  mpf = dynamic_cast<const MeshPatch*>( face.mesh() );
  assert(mpf != 0);

  esf = mpe->surface();
  fsf = mpf->surface();

  // initial edge
  Vct2 e[2], ed;
  e[0] = mpe->parameter(edge.source());
  e[1] = mpe->parameter(edge.target());
  ed = e[1] - e[0];
  qe = is.eparameter();
  Real t = norm(qe-e[0]) / norm(ed);
  if (t < 0.3)
    e[0] -= 0.5*ed;
  else if (t > 0.7)
    e[1] += 0.5*ed;

  limit(e[0]);
  limit(e[1]);

  const uint *vi(face.vertices());
  Vct2 shift, f[3];
  qf = is.fparameter();
  f[0] = mpf->parameter(vi[0]);
  f[1] = mpf->parameter(vi[1]);
  f[2] = mpf->parameter(vi[2]);
  shift = qf - (f[0]+f[1]+f[2])/3.0;
  for (uint i=0; i<3; ++i) {
    f[i] += shift;
    limit(f[i]);
  }

  // compute corresponding 3D points
  init(e, f);
  
  // mark
  si = sj = NotFound;
}

void EfImprove::init(const Vct2 e[2], const Vct2 f[3])
{
  // three edge vertices
  eq[0] = e[0];
  eq[1] = 0.5*(e[0]+e[1]);
  eq[2] = e[1];

  for (uint i=0; i<3; ++i)
    ep[i] = esf->eval(eq[i][0], eq[i][1]);

  // six face vertices
  fq[0] = f[0];
  fq[1] = 0.5*(f[0]+f[1]);
  fq[2] = f[1];
  fq[3] = 0.5*(f[1]+f[2]);
  fq[4] = f[2];
  fq[5] = 0.5*(f[0]+f[2]);

  for (uint i=0; i<6; ++i)
    fp[i] = fsf->eval(fq[i][0], fq[i][1]);
}

Real EfImprove::refine(Real tol, uint maxit)
{
  bool found;
  uint rci(0);
  Real err(huge), t;
  Vct2 e[2], f[3], r, qe, qf, ed;

  // 120deg rotation matrix
  Mtx22 m;
  m(0,0) = m(1,1) = -0.5;
  m(0,1) = -0.5*sqrt(3.0);
  m(1,0) = 0.5*sqrt(3.0);

  while (rci < maxit and err > tol) {
    found = false;
    for (uint i=0; i<2 and !found; ++i)
      for (uint j=0; j<4 and !found; ++j)
        found = intersects(i,j);

    // makes no sense to search any further
    if (!found)
      break;
    
    // evaluate precision
    qe = eparameter();
    qf = fparameter();
    err = norm(esf->eval(qe[0], qe[1]) - fsf->eval(qf[0],qf[1]));

    if (err < tol)
      break;

    // compute new edge segments
    e[0] = eq[efi_edges[si][0]];
    e[1] = eq[efi_edges[si][1]];

    // extend edge if necessary
    ed = e[1] - e[0];
    t = norm(qe-e[0]) / norm(ed);
    if (t < 0.3)
      e[0] -= 0.5*ed;
    else if (t > 0.7)
      e[1] += 0.5*ed;
    
    // limit coordinates
    limit(e[0]);
    limit(e[1]);

    // compute new base triangle
    f[0] = fq[efi_faces[sj][0]];
    f[1] = fq[efi_faces[sj][1]];
    f[2] = fq[efi_faces[sj][2]];

    Vct2 shift = qf - (f[0]+f[1]+f[2])/3.0;
    for (uint i=0; i<3; ++i) {
      f[i] += shift;
      limit(f[i]);
    }

    // prepare next iteration
    init(e, f);

    ++rci;
  }

  return err;
}

Real EfImprove::gap() const
{
  Vct2 qe, qf;
  qe = eparameter();
  qf = fparameter();

  Vct3 pte, ptf;
  pte = esf->eval(qe[0], qe[1]);
  ptf = fsf->eval(qf[0], qf[1]);

  return norm(pte-ptf);
}

Vct2 EfImprove::eparameter() const
{
  if (si == NotFound)
    return qe;
  
  Real t;
  t = uvt[2];
  Vct2 p1, p2;
  p1 = eq[efi_edges[si][0]];
  p2 = eq[efi_edges[si][1]];
  return (1-t)*p1 + t*p2;
}

Vct2 EfImprove::fparameter() const
{
  if (sj == NotFound)
    return qf;
  
  Real u, v, w;
  u = uvt[0];
  v = uvt[1];
  w = 1 - u - v;

  Vct2 p1, p2, p3;
  p1 = fq[efi_faces[sj][0]];
  p2 = fq[efi_faces[sj][1]];
  p3 = fq[efi_faces[sj][2]];
  return w*p1 + u*p2 + v*p3;
}

bool EfImprove::intersects(uint i, uint j)
{
  // edge end vertices
  Vct3 q1 = EfImprove::project(j, ep[efi_edges[i][0]]);
  Vct3 q2 = EfImprove::project(j, ep[efi_edges[i][1]]);

  if ( fabs(q1[2]-q2[2]) > gmepsilon ) {
    Real t = q1[2]/(q1[2] - q2[2]);
    if (t < 0 or t > 1)
      return false;

    Real u = q1[0] + t*(q2[0] - q1[0]);
    if (u < 0 or u > 1)
      return false;

    Real v = q1[1] + t*(q2[1] - q1[1]);
    if (v < 0 or v > 1)
      return false;

    Real w = 1 - u - v;
    if (w < 0 or w > 1)
      return false;
    else {
      uvt[0] = u;
      uvt[1] = v;
      uvt[2] = t;
      si = i;
      sj = j;
      return true;
    }
  } else
    return false;
}

Vct3 EfImprove::project(uint j, const Vct3 & pt) const
{
  const Vct3 & p1(fp[efi_faces[j][0]]);
  const Vct3 & p2(fp[efi_faces[j][1]]);
  const Vct3 & p3(fp[efi_faces[j][2]]);

  Vct3 nrm, va, vb, vXi, vEta;
  va = p2 - p1;
  vb = p3 - p1;
  nrm = cross(va,vb).normalized();
  vXi = va - vb*(dot(va,vb)/dot(vb,vb));
  vEta = vb - va*(dot(va,vb)/dot(va,va));

  Vct3 s;
  s[0] = dot(pt-p1, vXi) / dot(vXi,vXi);
  s[1] = dot(pt-p1, vEta) / dot(vEta,vEta);
  s[2] = dot(pt,nrm) - dot(p1,nrm);

  return s;
}

void EfImprove::limit(Vct2 & p) const
{
  p[0] = min(1.0, max(0.0, p[0]));
  p[1] = min(1.0, max(0.0, p[1]));
}
