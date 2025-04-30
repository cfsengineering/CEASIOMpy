
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
 
#include "polysplinesurf.h"
#include "abstractcurve.h"
#include "igesfile.h"
#include "igesdirentry.h"
#include "iges128.h"
#include "stepfile.h"
#include "step_ap203.h"
#include <genua/piegl.h>
#include <genua/transformation.h>
#include <genua/pattern.h>
#include <genua/trimesh.h>
#include <genua/dbprint.h>
#include <genua/xcept.h>
#include <genua/lu.h>
#include <genua/lls.h>
#include <sstream>

using namespace std;

void PolySplineSurf::evalBasisGrid(const Vector &u,
                                   const Vector &v, Matrix &A) const
{
  const int nu = u.size();
  const int nv = v.size();
  const int pu = ub.degree();
  const int pv = vb.degree();
  assert(A.nrows() >= uint(nu*nv));

  Real fu[8], fv[8];
  for (int j=0; j<nv; ++j) {
    const int vspan = vb.lleval(v[j], fv);
    for (int i=0; i<nu; ++i) {
      int row = j*nu+i;
      const int uspan = ub.lleval(u[i], fu);
      for (int kj=0; kj<pv+1; ++kj) {
        for (int ki=0; ki<pu+1; ++ki) {
          int col = (uspan-pu+ki) + (vspan-pv+kj)*nu;
          A(row,col) = fu[ki]*fv[kj];
        }
      }
    }
  }
}

void PolySplineSurf::toControlGrid(int nu, int nv, const Matrix &b)
{
  assert(b.nrows() >= uint(nu*nv));
  assert(b.ncols() >= 3);
  cp.resize(nu,nv);
  for (int j=0; j<nv; ++j) {
    for (int i=0; i<nu; ++i) {
      int row = j*nu+i;
      cp(i,j) = Vct3( b(row,0), b(row,1), b(row,2) );
    }
  }
}

void PolySplineSurf::interpolate(const Vector &u, const Vector &v,
                                 const PointGrid<3> &grid,
                                 int udeg, int vdeg)
{
  if (u.size() < uint(udeg+1))
    throw Error("PolySplineSurf::interpolate() - "
                "Not enough points in u-direction for this degree.");
  if (v.size() < uint(vdeg+1))
    throw Error("PolySplineSurf::interpolate() - "
                "Not enough points in v-direction for this degree.");
  if (u.size() != grid.nrows())
    throw Error("PolySplineSurf::interpolate() - "
                "Number of u-parameter values does not match grid row count.");
  if (v.size() != grid.ncols())
    throw Error("PolySplineSurf::interpolate() - "
                "Number of v-parameter values does not match grid col count.");

  ub.init(udeg, u);
  vb.init(vdeg, v);

  const int nu = u.size();
  const int nv = v.size();
  const int ncp = nu*nv;
  Matrix A(ncp,ncp), b(ncp,3);
  evalBasisGrid(u, v, A);
  for (int j=0; j<nv; ++j) {
    for (int i=0; i<nu; ++i) {
      int row = j*nu+i;
      for (int k=0; k<3; ++k)
        b(row,k) = grid(i,j)[k];
    }
  }

  int stat = lu_solve(A, b);
  if (stat != 0)
    throw Error("PolySplineSurf::interpolate() - "
                "Interpolation matrix singular -- duplicate points?");

  toControlGrid(nu, nv, b);
}

void PolySplineSurf::approximate(const Vector &u, const Vector &v,
                                 const PointGrid<3> &grid,
                                 int ncu, int ncv, int udeg, int vdeg)
{
  if (u.size() < uint(udeg+1))
    throw Error("PolySplineSurf::approximate() - "
                "Not enough points in u-direction for this degree.");
  if (v.size() < uint(vdeg+1))
    throw Error("PolySplineSurf::approximate() - "
                "Not enough points in v-direction for this degree.");
  if (u.size() != grid.nrows())
    throw Error("PolySplineSurf::approximate() - "
                "Number of u-parameter values does not match grid row count.");
  if (v.size() != grid.ncols())
    throw Error("PolySplineSurf::approximate() - "
                "Number of v-parameter values does not match grid col count.");

  // create suitable parameter grid
  Vector uc, vc;
  if (uint(ncu) != u.size())
    interpolate_pattern(u, ncu, uc);
  else
    uc = u;
  if (uint(ncv) != v.size())
    interpolate_pattern(v, ncv, vc);
  else
    vc = v;

  // initialize basis
  ub.init(udeg, uc);
  vb.init(vdeg, vc);

  const int ncp = ncu*ncv;
  const int niu = u.size();
  const int niv = v.size();
  const int nip = niu*niv;
  Matrix A(nip,ncp), b(nip,3);
  evalBasisGrid(u, v, A);
  for (int j=0; j<niv; ++j) {
    for (int i=0; i<niu; ++i) {
      int row = j*niu + i;
      for (int k=0; k<3; ++k)
        b(row,k) = grid(i,j)[k];
    }
  }

  // LLS solution will fail if A has not full column rank, i.e. there are no
  // approximation points in (u,v) which span the interval of one cp
  int stat = lls_solve(A, b);
  if (stat != 0)
    throw Error("PolySplineSurf::approximate() - "
                "Least-squares solution failed; insufficient resolution.");

  toControlGrid(ncu, ncv, b);
}

void PolySplineSurf::dimStats(Surface::DimStat &stat) const
{
  Surface::dimStats(stat);
  stat.nControlU = cp.nrows();
  stat.nControlV = cp.ncols();
}

Vct3 PolySplineSurf::eval(Real u, Real v) const
{
  u = umap(u);
  v = vmap(v);
  assert(u >= 0);
  assert(u <= 1);
  assert(v >= 0);
  assert(v <= 1);
  
  Real fu[8], fv[8];
  const int uspan = ub.lleval(u, fu);
  const int vspan = vb.lleval(v, fv);
  
  Vct3 pt;
  const int pu = ub.degree();
  const int pv = vb.degree();
  for (int j=0; j<pv+1; ++j)
    for (int i=0; i<pu+1; ++i)
      pt += fu[i]*fv[j] * cp(uspan-pu+i,vspan-pv+j);
  
  return pt;
}

Vct3 PolySplineSurf::derive(Real u, Real v, uint ku, uint kv) const
{
  u = umap(u);
  v = vmap(v);
  assert(u >= 0);
  assert(u <= 1);
  assert(v >= 0);
  assert(v <= 1);

  Vct3 pt;
  int uspan, vspan;
  if (ku == 0 and kv == 0) {
    return eval(u, v);
  } else {
    const int pu = ub.degree();
    const int pv = vb.degree();
    Matrix fu(ku+1, pu+1), fv(kv+1, pv+1);
    uspan = ub.derive(u, ku, fu);
    vspan = vb.derive(v, kv, fv);
    for (int j=0; j<pv+1; ++j)
      for (int i=0; i<pu+1; ++i)
        pt += (fu(ku,i) * fv(kv,j)) * cp(uspan-pu+i, vspan-pv+j);
  }
  
  return pt;
}

void PolySplineSurf::plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const
{
  u = umap(u);
  v = vmap(v);

  // evaluate in mapped domain
  mappedPlane(u, v, S, Su, Sv);

  // some surfaces imported from IGES files have vanishing derivatives
  // at some of their outer boundaries - that is not acceptable.
  // a fairly robust solution is to replace the accurate derivatives with
  // finite differences near the boundaries. for triangular surfaces,
  // where the control point grid collapses into the apex, it is necessary
  // to back away from the surface in two directions
  Real ssu = sq(Su);
  Real ssv = sq(Sv);

  // replace partial derivatives with finite differences when
  // derivatives vanish
  Real mu(u), mv(v);
  Real deps = 2.0*std::numeric_limits<Real>::epsilon();
  while (ssu == 0) {
    Real u1 = std::max(0.0, u-deps);
    Real u2 = std::min(1.0, u+deps);
    if (v <= 0.0)
      mv += deps;
    else if (v >= 1.0)
      mv -= deps;
    Su = (eval(u2,mv) - eval(u1,mv)) / (u2 - u1);
    ssu = sq(Su);
    deps *= 2;
  }

  deps = 2.0*std::numeric_limits<Real>::epsilon();
  while (ssv == 0) {
    Real v1 = std::max(0.0, v-deps);
    Real v2 = std::min(1.0, v+deps);
    if (u <= 0.0)
      mu += deps;
    else if (u >= 1.0)
      mu -= deps;
    Sv = (eval(mu,v2) - eval(mu,v1)) / (v2 - v1);
    ssv = sq(Sv);
    deps *= 2;
  }

  //  Real mu(u), mv(v);
  //  while (ssu == 0 or ssv == 0) {
  //    const Real dt = 2.0*std::numeric_limits<Real>::epsilon();
  //    if (u <= 0.0)
  //      mu += dt;
  //    else if (u >= 1.0)
  //      mu -= dt;
  //    else if (v <= 0.0)
  //      mv += dt;
  //    else if (v >= 1.0)
  //      mv -= dt;

  //    Vct3 tmp;
  //    assert(mu != u or mv != v);
  //    mappedPlane(mu, mv, tmp, Su, Sv);
  //    ssu = sq(Su);
  //    ssv = sq(Sv);
  //  }

  assert(sq(Su) > 0);
  assert(sq(Sv) > 0);
} 

void PolySplineSurf::mappedPlane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const
{
  // compute basis function derivatives
  const int pu = ub.degree();
  const int pv = vb.degree();
  // Matrix fu(2,pu+1), fv(2,pv+1);
  const int NR = Piegl::MaxDegree;
  SMatrix<2,NR> fu, fv;

  const int uspan = ub.derive(u, 1, fu.nrows(), fu.pointer());
  const int vspan = vb.derive(v, 1, fv.nrows(), fv.pointer());

  // assemble surface point tangents
  S = 0.0;
  Su = 0.0;
  Sv = 0.0;
  for (int j=0; j<pv+1; ++j) {
    for (int i=0; i<pu+1; ++i) {
      const Vct3 & tp( cp(uspan-pu+i, vspan-pv+j) );
      S  += (fu(0,i) * fv(0,j)) * tp;
      Su += (fu(1,i) * fv(0,j)) * tp;
      Sv += (fu(0,i) * fv(1,j)) * tp;
    }
  }
}

void PolySplineSurf::apply()
{
  PointGrid<3>::iterator itr;
  for (itr = cp.begin(); itr != cp.end(); ++itr)
    *itr = RFrame::forward(*itr);
  RFrame::clear();
}

PolySplineSurf::GridCompat PolySplineSurf::compatible(const PolySplineSurf & a,
                                                      const PolySplineSurf & b,
                                                      Real tol)
{
  if (a.ub.degree() != b.ub.degree())
    return PolySplineSurf::Incompatible;
  if (a.vb.degree() != b.vb.degree())
    return PolySplineSurf::Incompatible;

  // try to match pairs of sides

  if (a.cp.nrows() == b.cp.nrows()) {

    const int nu = a.cp.nrows();
    const int ma = a.cp.ncols()-1;
    const int mb = b.cp.ncols()-1;
    Real n2s(0), s2n(0);
    for (int i=0; i<nu; ++i) {
      n2s += sq( a.cp(i,ma) - b.cp(i,0) );
      s2n += sq( a.cp(i,0) - b.cp(i,mb) );
    }
    n2s = std::sqrt(n2s);
    s2n = std::sqrt(s2n);

    if (n2s < tol)
      return PolySplineSurf::North2South;
    else if (s2n < tol)
      return PolySplineSurf::South2North;
  }

  if (a.cp.ncols() == b.cp.ncols()) {

    const int nv = a.cp.ncols();
    const int ma = a.cp.nrows()-1;
    const int mb = b.cp.nrows()-1;
    Real e2w(0), w2e(0);
    for (int i=0; i<nv; ++i) {
      e2w += sq( a.cp(ma,i) - b.cp(0,i) );
      w2e += sq( a.cp(0,i) - b.cp(mb,i) );
    }
    e2w = std::sqrt(e2w);
    w2e = std::sqrt(w2e);

    if (e2w < tol)
      return PolySplineSurf::East2West;
    else if (w2e < tol)
      return PolySplineSurf::West2East;
  }

  return PolySplineSurf::Incompatible;
}

XmlElement PolySplineSurf::toXml(bool share) const
{
  XmlElement xe("PolySplineSurf");
  xe.attribute("name") = name();
  xe["ustart"] = str(ustart);
  xe["uend"] = str(uend);
  xe["vstart"] = str(vstart);
  xe["vend"] = str(vend);
  xe["ukfront"] = str(ukfront);
  xe["ukback"] = str(ukback);
  xe["vkfront"] = str(vkfront);
  xe["vkback"] = str(vkback);

  XmlElement xub = ub.toXml();
  xub.attribute("direction") = "u";
  xe.append(std::move(xub));
  
  XmlElement xvb = vb.toXml();
  xvb.attribute("direction") = "v";
  xe.append(std::move(xvb));
  
  XmlElement xcp("ControlPoints");
  xcp.attribute("nrows") = str(cp.nrows());
  xcp.attribute("ncols") = str(cp.ncols());
  xcp.asBinary(3*cp.size(), cp.pointer(), share);
  xe.append(std::move(xcp));
  
  return xe;
}

void PolySplineSurf::fromXml(const XmlElement & xe)
{
  assert(xe.name() == "PolySplineSurf");
  rename( xe.attribute("name") );
  ustart = xe.attr2float("ustart", 0.0);
  uend = xe.attr2float("uend", 1.0);
  ukfront = xe.attr2float("ukfront", 0.0);
  ukback = xe.attr2float("ukback", 1.0);
  vstart = xe.attr2float("vstart", 0.0);
  vend = xe.attr2float("vend", 1.0);
  vkfront = xe.attr2float("vkfront", 0.0);
  vkback = xe.attr2float("vkback", 1.0);

  XmlElement::const_iterator itr, last;
  last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "SplineBasis") {
      if (itr->attribute("direction") == "u")
        ub.fromXml(*itr);
      else if (itr->attribute("direction") == "v")
        vb.fromXml(*itr);
    } else if (itr->name() == "ControlPoints") {
      uint nr = Int( itr->attribute("nrows") );
      uint nc = Int( itr->attribute("ncols") );
      cp.resize(nr, nc);
      itr->fetch(3*cp.size(), cp.pointer());
    }
  }
}

bool PolySplineSurf::fromIges(const IgesFile & file,
                              const IgesDirEntry & entry)
{
  if (entry.etype != 128)
    return false;

  IgesEntityPtr eptr = file.createEntity(entry);
  IgesSplineSurface ssf;
  if (IgesEntity::as(eptr, ssf)) {

    // intercept case of too high polynomial order
    if (ssf.mu > 7 or ssf.mv > 7) {
      dbprint("PolySplineSurf: IGES128 with order ", ssf.mu, ssf.mv);
      return false;
    }
    if (ssf.polynomial == 0) {
      dbprint("PolySplineSurf: IGES128, rational.", ssf.mu, ssf.mv);
      return false;
    }

    // knot vector normalization
    Vector uk( ssf.uknots ), vk( ssf.vknots );
    ukfront = uk.front();
    ukback = uk.back();
    vkfront = vk.front();
    vkback = vk.back();

    uk -= ukfront;
    uk /= ukback - ukfront;
    vk -= vkfront;
    vk /= vkback - vkfront;

    ustart = (ssf.ustart - ukfront) / (ukback - ukfront);
    uend = (ssf.uend - ukfront) / (ukback - ukfront);
    vstart = (ssf.vstart - vkfront) / (vkback - vkfront);
    vend = (ssf.vend - vkfront) / (vkback - vkfront);

    ub = SplineBasis(ssf.mu, uk);
    vb = SplineBasis(ssf.mv, vk);
    cp = ssf.cpoints;

    setIgesName(file, ssf);

  } else {
    return false;
  }

  return true;
}

void PolySplineSurf::knotScale(AbstractCurve & c) const
{
  c.translate( -ukfront, -vkfront, 0.0 );
  c.scale( 1.0/(ukback-ukfront), 1.0/(vkback-vkfront), 1.0 );
  c.apply();
}

int PolySplineSurf::toIges(IgesFile & file, int tfi) const
{
  const Vector & ukts(ub.getKnots());
  const Vector & vkts(vb.getKnots());
  if (ukts.empty() or vkts.empty())
    return 0;
  
  IgesSplineSurface igs;
  igs.setup(cp.nrows(), cp.ncols(), ub.degree(), vb.degree(),
            &ukts[0], &vkts[0], &cp[0][0]);
  igs.trafoMatrix(tfi);
  
  // determine if surface is closed
  Real ftol = file.modelTolerance();
  bool uclosed(true), vclosed(true);
  const int nr(cp.nrows());
  const int nc(cp.ncols());
  for (int i=0; i<nc; ++i) {
    const Vct3 & p1 = cp(0,i);
    const Vct3 & p2 = cp(nr-1,i);
    if (norm(p2-p1) > ftol) {
      uclosed = false;
      break;
    }
  }
  for (int i=0; i<nr; ++i) {
    const Vct3 & p1 = cp(i,0);
    const Vct3 & p2 = cp(i,nc-1);
    if (norm(p2-p1) > ftol) {
      vclosed = false;
      break;
    }
  }
  
  igs.label("PSPL_SRF");
  igs.flagClosed(uclosed, vclosed);
  return igs.append( file );
}

bool PolySplineSurf::fromStep(const StepFile & file,
                              const StepBSplineSurfaceWithKnots *ep)
{
  if ( ep->u_degree > 7 or ep->v_degree > 7 )
    return false;

  if (not ep->name.empty())
    rename( ep->name );

  // extract knot vectors, basis function spec
  assert(ep->u_knots.size() == ep->u_multiplicities.size());
  assert(ep->v_knots.size() == ep->v_multiplicities.size());
  ub.init( ep->u_degree, ep->u_knots.size(),
           &(ep->u_knots[0]), &(ep->u_multiplicities[0]) );
  vb.init( ep->v_degree, ep->v_knots.size(),
           &(ep->v_knots[0]), &(ep->v_multiplicities[0]) );

  // gather control points
  const StepCartesianPoint *pp = 0;
  const int nrow = ep->control_points_list.ncols();
  const int ncol = ep->control_points_list.nrows();
  cp.resize(nrow, ncol);
  for (int j=0; j<ncol; ++j) {
    for (int i=0; i<nrow; ++i) {
      bool ok = file.as( ep->control_points_list(j,i), &pp );
      if (not ok)
        return false;
      for (int k=0; k<3; ++k)
        cp(i,j)[k] = pp->coordinates[k];
    }
  }

  return true;
}

void PolySplineSurf::initGridPattern(Vector &up, Vector &vp) const
{
  const int npu = std::max( 2u, 1 + ub.degree()/2 );
  const int nu = (cp.nrows() - 1)*npu + 1;
  const int npv = std::max( 2u, 1 + vb.degree()/2 );
  const int nv = (cp.ncols() - 1)*npv + 1;

  AbstractCurve::gridFromKnots( nu, ub.getKnots(), up, ustart, uend );
  AbstractCurve::gridFromKnots( nv, vb.getKnots(), vp, vstart, vend );

  //  // interpolate knot pattern
  //  const int nu = (cp.nrows() - 1)*2 + 1;
  //  const int nv = (cp.ncols() - 1)*2 + 1;

  //  Vector k;
  //  up.resize(nu);
  //  vp.resize(nv);

  //  // used to eliminate multiple knots
  //  almost_equal<Real> pred(1e-4);

  //  k = ub.getKnots();
  //  sort(k.begin(), k.end());
  //  k.erase(std::unique(k.begin(), k.end(), pred), k.end());
  //  interpolate_pattern(k, nu, up);

  //  k = vb.getKnots();
  //  sort(k.begin(), k.end());
  //  k.erase(std::unique(k.begin(), k.end(), pred), k.end());
  //  interpolate_pattern(k, nv, vp);
}

void PolySplineSurf::simpleMesh(PointGrid<3,float> & pgrid,
                                PointGrid<3,float> & ngrid,
                                uint pu, uint pv) const
{
  pu = std::max(pu, 1u);
  pv = std::max(pv, 1u);
  const int nu = (cp.nrows() - 1)*pu + 1;
  const int nv = (cp.ncols() - 1)*pv + 1;

  // determine a suitable set of parameters
  almost_equal<Real> pred(1e-4);

  Vector k, up(nu), vp(nv);
  k = ub.getKnots();
  sort(k.begin(), k.end());
  k.erase(std::unique(k.begin(), k.end(), pred), k.end());
  interpolate_pattern(k, nu, up);
  k = vb.getKnots();
  sort(k.begin(), k.end());
  k.erase(std::unique(k.begin(), k.end(), pred), k.end());
  interpolate_pattern(k, nv, vp);

  // start with grid, then convert to trimesh
  pgrid.resize(nu, nv);
  ngrid.resize(nu, nv);
  Vct3 S, Su, Sv, pn;
  for (int j=0; j<nv; ++j) {
    for (int i=0; i<nu; ++i) {
      plane(up[i], vp[j], S, Su, Sv);
      pn = cross(Su, Sv).normalized();
      convert(S, pgrid(i,j));
      convert(pn, ngrid(i,j));
    }
  }
}

void PolySplineSurf::simpleMesh(TriMesh & msh, uint pu, uint pv, int tag) const
{
  pu = std::max(pu, 1u);
  pv = std::max(pv, 1u);
  const int nu = (cp.nrows() - 1)*pu + 1;
  const int nv = (cp.ncols() - 1)*pu + 1;

  // determine a suitable set of parameters
  almost_equal<Real> pred(1e-4);

  Vector k, up(nu), vp(nv);
  k = ub.getKnots();
  sort(k.begin(), k.end());
  k.erase(std::unique(k.begin(), k.end(), pred), k.end());
  interpolate_pattern(k, nu, up);
  k = vb.getKnots();
  sort(k.begin(), k.end());
  k.erase(std::unique(k.begin(), k.end(), pred), k.end());
  interpolate_pattern(k, nv, vp);

  // start with grid, then convert to trimesh
  PointGrid<3> pg(nu, nv);
  for (int j=0; j<nv; ++j)
    for (int i=0; i<nu; ++i)
      pg(i,j) = eval(up[i], vp[j]);

  msh.triangulate(pg);
  msh.faceTag(tag);
}

Surface *PolySplineSurf::clone() const
{
  return (new PolySplineSurf(*this));
}


