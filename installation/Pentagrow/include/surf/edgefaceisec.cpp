
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
 
#include <utility>
#include <genua/triangulation.h>
#include <genua/lu.h>
#include <genua/algo.h>
#include "meshpatch.h"
#include "efimprove.h"
#include "edgefaceisec.h"

using namespace std;

EdgeFaceIsec::EdgeFaceIsec(const TriFace & t, const TriEdge & s) : 
    f(t), e(s), refined(false)
{
  const TriMesh & m(*e.mesh());
  uvt = t.pierce(m.vertex(e.source()), m.vertex(e.target()));
}

bool EdgeFaceIsec::operator< (const EdgeFaceIsec & rhs) const
{
  const TriMesh *srf, *rsf;
  srf = f.mesh();
  rsf = rhs.f.mesh();

  if (srf < rsf)
    return true;
  else if (srf > rsf)
    return false;

  if (f < rhs.f)
    return true;
  else if (not (f == rhs.f))
    return false;

  if (e < rhs.e)
    return true;
  else
    return false;
}

bool EdgeFaceIsec::valid(bool disjoint) const
{
  if (uvt[0] == huge)
    return false;
  
  Real u, v, w, t;
  u = uvt[0];
  v = uvt[1];
  w = 1 - u - v;
  t = uvt[2];

  // trap NaN
  assert(u == u);
  assert(v == v);
  assert(t == t);
  if (u < 0 or u > 1)
    return false;
  else if (v < 0 or v > 1)
    return false;
  else if (w < 0 or w > 1)
    return false;
  else if (t < 0 or t > 1)
    return false;
  else if (disjoint)
    return true;
  else {

    // edge and face are not allowed to share any vertex,
    // if they are on the same surface
    if (f.mesh() != e.mesh())
      return true;

    uint s = e.source();
    uint t = e.target();
    const uint *vf = f.vertices();
    if (s == vf[0] or s == vf[1] or s == vf[2])
      return false;
    else if (t == vf[0] or t == vf[1] or t == vf[2])
      return false;
    else
      return true;
  }
}

bool EdgeFaceIsec::touching(Real threshold) const
{
  // does not make sense if edge and face are on different surfaces
  if (f.mesh() != e.mesh())
    return false;
  
  threshold = fabs(threshold);
  if (fabs(uvt[0]) <= threshold or fabs(uvt[0]-1) <= threshold)
    return true;
  if (fabs(uvt[1]) <= threshold or fabs(uvt[1]-1) <= threshold)
    return true;
  if (fabs(uvt[2]) <= threshold or fabs(uvt[2]-1) <= threshold)
    return true;
  else
    return false;
}

Vct3 EdgeFaceIsec::eval() const
{
  if (refined)
    return rpt;
  else {
    const TriMesh *srf(e.mesh());
    Real t(uvt[2]);
    return (1-t)*srf->vertex(e.source()) + t*srf->vertex(e.target());
  }
}

Vct2 EdgeFaceIsec::fparameter() const
{
  if (refined)
    return rqf;
  else {
    const TriMesh *srf(f.mesh());
    const MeshPatch *pp(0);
    pp = dynamic_cast<const MeshPatch *>(srf);
    assert(pp != 0);
    const MeshPatch & mp(*pp);
    const uint *vi(f.vertices());
    Real u, v, w;
    u = uvt[0];
    v = uvt[1];
    w = 1 - u - v;
    return w*mp.parameter(vi[0]) + u*mp.parameter(vi[1]) + v*mp.parameter(vi[2]);
  }
}

Vct2 EdgeFaceIsec::eparameter() const
{
  if (refined)
    return rqe;
  else {
    const TriMesh *srf(e.mesh());
    const MeshPatch *pp(0);
    pp = dynamic_cast<const MeshPatch *>(srf);
    assert(pp != 0);
    const MeshPatch & mp(*pp);
    Real t = uvt[2];
    return (1-t)*mp.parameter(e.source()) + t*mp.parameter(e.target());
  }
}

Vct3 EdgeFaceIsec::tangent() const
{
  if (refined)
    return rtg;
  else {
    const TriMesh *sf = f.mesh();
    const TriMesh *se = e.mesh();

    const MeshPatch *ppf(0), *ppe(0);
    ppf = dynamic_cast<const MeshPatch *>(sf);
    assert(ppf != 0);
    ppe = dynamic_cast<const MeshPatch *>(se);
    assert(ppe != 0);
    const MeshPatch & mf(*ppf);
    const MeshPatch & me(*ppe);

    Vct2 pf = fparameter();
    Vct2 pe = eparameter();

    Vct3 nf = mf.normal(pf[0], pf[1]);
    Vct3 ne = me.normal(pe[0], pe[1]);
    Vct3 t = cross(nf,ne);
    assert(norm(t) != 0);

    if (ppf > ppe)
      t /= -norm(t);
    else
      t /= norm(t);
    return t;
  }
}

// void EdgeFaceIsec::writeOogl(std::ostream & os) const
// {
//   Real r = 0.1*sqrt(0.5*norm(f.normal()));
//   os << "{ SPHERE " << endl;
//   os << r << endl;
//   os << eval() << endl;
//   os << "}" << endl;
// }

Vct2 EdgeFaceIsec::parameter(const MeshPatch *mp) const
{
  const TriMesh *sf = f.mesh();
  const TriMesh *se = e.mesh();

  const MeshPatch *ppf(0), *ppe(0);
  ppf = dynamic_cast<const MeshPatch *>(sf);
  assert(ppf != 0);
  ppe = dynamic_cast<const MeshPatch *>(se);
  assert(ppe != 0);

  if (ppf == mp)
    return fparameter();
  else if (ppe == mp)
    return eparameter();
  else
    throw Error("EdgeFaceIsec not connected to this patch.");
}

Vct3 EdgeFaceIsec::midpoint() const
{
  if (refined)
    return rpt;
  else {
    const TriMesh *sf = f.mesh();
    // const TriMesh *se = e.mesh();

    const MeshPatch *ppf(0); // *ppe(0);
    ppf = dynamic_cast<const MeshPatch *>(sf);
    assert(ppf != 0);
    // ppe = dynamic_cast<const MeshPatch *>(se);
    // assert(ppe != 0);

    Vct2 pf, pe;
    pf = fparameter();
    pe = eparameter();

    Vct3 qf, qe;
    qf = ppf->eval(pf[0], pf[1]);
    qe = ppf->eval(pe[0], pe[1]);

    return 0.5*(qf+qe);
  }
}

Real EdgeFaceIsec::refine(Real tol, uint maxit)
{
  Real pregap(0), postgap(huge);
  EfImprove efi(*this);
  pregap = efi.gap();
  efi.refine(tol, maxit);
  postgap = efi.gap();

  if (postgap < pregap) {

    rqe = efi.eparameter();
    rqf = efi.fparameter();

    const TriMesh *sf = f.mesh();
    const TriMesh *se = e.mesh();
    const MeshPatch *ppf(0), *ppe(0);
    ppf = dynamic_cast<const MeshPatch *>(sf);
    assert(ppf != 0);
    ppe = dynamic_cast<const MeshPatch *>(se);
    assert(ppe != 0);

    Vct3 pe, pf;
    pe = ppe->eval(rqe[0], rqe[1]);
    pf = ppf->eval(rqf[0], rqf[1]);
    rpt = 0.5*(pe + pf);
    pe = ppe->normal(rqe[0], rqe[1]);
    pf = ppf->normal(rqf[0], rqf[1]);
    if (ppf < ppe)
      rtg = cross(pf, pe).normalized();
    else
      rtg = cross(pe, pf).normalized();
    refined = true;
    return postgap;
  } else {
    rqe = eparameter();
    rqf = fparameter();
    rpt = midpoint();
    rtg = tangent();
    refined = true;
    return pregap;
  }
}

Real EdgeFaceIsec::erefine(Real tol, uint maxit)
{
  // identify patches belonging to edge and face  
  const MeshPatch *ppf(0), *ppe(0);
  ppf = dynamic_cast<const MeshPatch *>(f.mesh());
  assert(ppf != 0);
  ppe = dynamic_cast<const MeshPatch *>(e.mesh());
  assert(ppe != 0);
  const MeshPatch & mf(*ppf);
  const MeshPatch & me(*ppe);
  
  // construct initial values for Newton iteration
  Vct3 x;  
  x[0] = uvt[2];
  Real us, ut, vs, vt;
  const Vct2 & eq0( me.parameter(e.source()) );
  const Vct2 & eq1( me.parameter(e.target()) );
  us = eq0[0];
  vs = eq0[1];
  ut = eq1[0];
  vt = eq1[1];
  
  Real uf, vf, wf;
  uf = uvt[0];
  vf = uvt[1];
  wf = 1 - uf - vf;
  const uint *vi(f.vertices());
  const Vct2 & fq0( mf.parameter(vi[0]) );
  const Vct2 & fq1( mf.parameter(vi[1]) );
  const Vct2 & fq2( mf.parameter(vi[2]) );
  x[1] = wf*fq0[0] + uf*fq1[0] + vf*fq2[0];
  x[2] = wf*fq0[1] + uf*fq1[1] + vf*fq2[1];
  
  // determine limits for x[0]
  Real edu, edv, tmin(-huge), tmax(huge);  
  edu = ut - us;
  edv = vt - vs;
  if (edu > 0.0) {
    tmin = max(tmin, -us/edu);
    tmax = min(tmax, (1.0-us)/edu);
  } else if (edu < 0.0) {
    tmin = max(tmin, (1.0-us)/edu);
    tmax = min(tmax, -us/edu);
  }
  if (edv > 0.0) {
    tmin = max(tmin, -vs/edv);
    tmax = min(tmax, (1.0-vs)/edv);
  } else if (edv < 0.0) {
    tmin = max(tmin, (1.0-vs)/edv);
    tmax = min(tmax, -vs/edv);
  }
  assert(std::isfinite(tmin));
  assert(std::isfinite(tmax));
  assert(tmin < tmax);
  
  // Newton iteration
  Mtx33 Jac;
  Vct3 dst, Se, Seu, Sev, Sf, Sfu, Sfv, dx;
  
  Real ue, ve, pregap(huge), gap(huge), pgap(huge);  
  ue = us + edu*x[0];
  ve = vs + edv*x[0];
  
  for (uint iter=0; iter < maxit; ++iter) {
    
    // evaluate surfaces
    me.surface()->plane(ue, ve, Se, Seu, Sev);
    mf.surface()->plane(x[1], x[2], Sf, Sfu, Sfv);    
    dst = Se - Sf;
    pgap = gap;
    gap = norm(dst);
    
    if (iter == 0)
      pregap = gap;    
    if (gap < tol or gap == pgap)
      break;
    
    // construct Jacobian
    for (uint i=0; i<3; ++i) {
      Jac(i,0) = Seu[i] * (ut - us) + Sev[i] * (vt - vs);
      Jac(i,1) = -Sfu[i];
      Jac(i,2) = -Sfv[i];
    }
    
    // compute and apply step
    dx = lu_solve_copy(Jac, -dst);
    x += dx;
    
    // limit to valid parameter range    
    x[0] = min(tmax, max(tmin, x[0]));
    x[1] = min(1.0, max(0.0, x[1]));
    x[2] = min(1.0, max(0.0, x[2]));
    
    // due to rounding errors, ue and ve can end up at -1e-16 ...
    ue = min(1.0, max(0.0, us + edu*x[0]));
    ve = min(1.0, max(0.0, vs + edv*x[0]));
  }
  
  // determine if refinement was successfull
  if (gap < pregap) {

    rqe[0] = ue;
    rqe[1] = ve;
    rqf[0] = x[1];
    rqf[1] = x[2];

    // midpoint
    rpt = 0.5*(Se + Sf);
     
    // intersection line tangent
    Vct3 nre( cross(Seu, Sev).normalized() );
    Vct3 nrf( cross(Sfu, Sfv).normalized() );
    if (ppf < ppe)
      rtg = cross(nrf, nre);
    else
      rtg = cross(nre, nrf);        
    
    refined = true;
    return gap;
    
  } else {
    
    // failed - return values from discrete intersection
    rqe = eparameter();
    rqf = fparameter();
    rpt = midpoint();
    rtg = tangent();
    refined = true;
    return pregap;
  }
}

Real EdgeFaceIsec::localSize() const
{
  // compute triangle area
  const PointList<3> & fv(f.mesh()->vertices());
  const uint *vi(f.vertices());
  const Vct3 & p1( fv[vi[0]] );
  const Vct3 & p2( fv[vi[1]] );
  const Vct3 & p3( fv[vi[2]] );
  Real area = norm(cross(p2-p1, p3-p1));
    
  // compute edge lengths
  Real len1 = norm(p2-p1);
  Real len2 = norm(p3-p1);
  Real len3 = norm(p3-p2);
  Real alen = min(len1, min(len2, len3));
  alen = min(alen, 2.3094*sqrt(area));
  
  // compute edge length
  const PointList<3> & ev(e.mesh()->vertices());
  const Vct3 & ps( ev[e.source()] );
  const Vct3 & pt( ev[e.target()] );
  Real elen = norm(pt-ps);
  
  return min(elen, alen);
}

Real EdgeFaceIsec::sizeRatio() const
{
  // compute triangle edge length
  const PointList<3> & fv(f.mesh()->vertices());
  const uint *vi(f.vertices());
  const Vct3 & p1( fv[vi[0]] );
  const Vct3 & p2( fv[vi[1]] );
  const Vct3 & p3( fv[vi[2]] );
  Real area = norm(cross(p2-p1, p3-p1));
  Real tlen = 2.3094*sqrt(area);
  
  // compute edge length
  const PointList<3> & ev(e.mesh()->vertices());
  const Vct3 & ps( ev[e.source()] );
  const Vct3 & pt( ev[e.target()] );
  Real elen = norm(pt-ps);
  
  return tlen/elen;
}

side_t EdgeFaceIsec::onBoundary(Real tol) const
{
  Vct2 ep( eparameter() );
  side_t se = whichside(ep[0], ep[1], tol);
  if (se != none)
    return se;
  Vct2 fp( fparameter() );
  return whichside(fp[0], fp[1], tol);
}

void EdgeFaceIsec::forceToBoundary(Real tol)
{
  if (rqe[0] < tol)
    rqe[0] = 0.0;
  else if (rqe[0] > 1.0-tol)
    rqe[0] = 1.0;
  if (rqe[1] < tol)
    rqe[1] = 0.0;
  else if (rqe[1] > 1.0-tol)
    rqe[1] = 1.0; 
  
  if (rqf[0] < tol)
    rqf[0] = 0.0;
  else if (rqf[0] > 1.0-tol)
    rqf[0] = 1.0;
  if (rqf[1] < tol)
    rqf[1] = 0.0;
  else if (rqf[1] > 1.0-tol)
    rqf[1] = 1.0;
}

bool EdgeFaceIsec::fakeOpposedPoint(Real ptol, EdgeFaceIsec & fop) const
{
  if (not refined)
    return false;
  
  if (rqe[0] < ptol or 1.0-rqe[0] < ptol) {
    fop.rqe[0] = rqe[0] < ptol ? 0.0 : 1.0;
    fop.rqe[1] = rqe[1];
    fop.rqf = rqf;
    fop.rpt = rpt;
    fop.rtg = rtg;
    fop.e = e;
    fop.f = f;
    fop.refined = true;
    return true;
  } else if (rqf[0] < ptol or 1.0-rqf[0] < ptol) {
    fop.rqf[0] = rqf[0] < ptol ? 0.0 : 1.0;
    fop.rqf[1] = rqf[1];
    fop.rqe = rqe;
    fop.rpt = rpt;
    fop.rtg = rtg; 
    fop.e = e;
    fop.f = f;
    fop.refined = true;
    return true;
  }
  
  return false;
}
