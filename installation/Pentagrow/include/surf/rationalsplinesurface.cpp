
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
 
#include "rationalsplinesurface.h"
#include "abstractcurve.h"
#include "igesfile.h"
#include "igesdirentry.h"
#include "iges128.h"
#include <genua/transformation.h>
#include <genua/pattern.h>
#include <genua/dbprint.h>
#include <boost/math/special_functions/binomial.hpp>
#include <sstream>

using namespace std;

static inline Vct3 h2p( const Vct4 & pw )
{
  Real iw = 1.0 / pw[3];
  return Vct3( pw[0]*iw, pw[1]*iw, pw[2]*iw );
}

static inline Vct4 p2h( const Vct3 & p, Real w = 1.0)
{
  return Vct4( w*p[0], w*p[1], w*p[2], w );
}

static inline Real binCoef(uint a, uint b)
{
  return boost::math::binomial_coefficient<Real>(a,b);
}

void RationalSplineSurf::dimStats(Surface::DimStat &stat) const
{
  Surface::dimStats(stat);
  stat.nControlU = cp.nrows();
  stat.nControlV = cp.ncols();
}

Vct3 RationalSplineSurf::eval(Real u, Real v) const
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

  Vct4 pt;
  const int pu = ub.degree();
  const int pv = vb.degree();
  for (int j=0; j<pv+1; ++j)
    for (int i=0; i<pu+1; ++i)
      pt += fu[i]*fv[j] * cp(uspan-pu+i,vspan-pv+j);

  return h2p(pt);
}

Vct3 RationalSplineSurf::derive(Real u, Real v, uint ku, uint kv) const
{
  assert(u >= 0);
  assert(u <= 1);
  assert(v >= 0);
  assert(v <= 1);

  if (ku == 0 and kv == 0) {
    return eval(u, v);
  } else {

    u = umap(u);
    v = vmap(v);

    const int pu = ub.degree();
    const int pv = vb.degree();
    Matrix fu(ku+1, pu+1), fv(kv+1, pv+1);
    PointGrid<4> Sw(ku+1, kv+1);
    int uspan = ub.derive(u, ku, fu);
    int vspan = vb.derive(v, kv, fv);
    for (int iu=0; iu<pu+1; ++iu)
      for (uint ju=0; ju<ku+1; ++ju)
        for (int iv=0; iv<pv+1; ++iv)
          for (uint jv=0; jv<kv+1; ++jv)
            Sw(ju,jv) += fu(ju,iu) * fv(jv,iv) * cp(uspan-pu+iu, vspan-pv+iv);

    // Piegl/Tiller, equation 4.20
    Real w = Sw(0,0)[3];
    PointGrid<3> SKL(ku+1,kv+1);
    for (uint k=0; k<=ku; ++k) {
      for (uint l=0; l<=kv; ++l) {
        Vct3 vpp( Sw(k,l)[0], Sw(k,l)[1], Sw(k,l)[2] );   // A(k,l)
        for (uint i=1; i<=k; ++i)
          vpp -= binCoef(k,i) * Sw(i,0)[3] * SKL(k-i,l);
        for (uint j=1; j<=l; ++j)
          vpp -= binCoef(l,j) * Sw(0,j)[3] * SKL(k,l-j);
        for (uint i=1; i<=k; ++i)
          for (uint j=1; j<=l; ++j)
            vpp -= binCoef(k,i) * binCoef(l,j) * Sw(i,j)[3] * SKL(k-i,l-j);
        SKL(k,l) = vpp / w;
      }
    }

    // inner derivative of tmap
    Real dtu = std::pow(uend - ustart, Real(ku));
    Real dtv = std::pow(vend - vstart, Real(kv));
    return dtu * dtv * SKL(ku,kv);
  }

  // never reached
  return Vct3();
}

void RationalSplineSurf::plane(Real u, Real v, Vct3 &S,
                               Vct3 &Su, Vct3 &Sv) const
{
  u = umap(u);
  v = vmap(v);

  // evaluate in mapped domain
  mappedPlane(u, v, S, Su, Sv);

  // some surfaces imported from IGES files have vanishing derivatives
  // at some of their outer boundaries - that is not acceptable.
  Real ssu = sq(Su);
  Real ssv = sq(Sv);
  Real mu(u), mv(v);
  while (ssu == 0 or ssv == 0) {
    const Real dt = 2.0*std::numeric_limits<Real>::epsilon();
    if (u <= 0.0)
      mu += dt;
    else if (u >= 1.0)
      mu -= dt;
    else if (v <= 0.0)
      mv += dt;
    else if (v >= 1.0)
      mv -= dt;

    Vct3 tmp;
    assert(mu != u or mv != v);
    mappedPlane(mu, mv, tmp, Su, Sv);
    ssu = sq(Su);
    ssv = sq(Sv);
  }

  assert(sq(Su) > 0);
  assert(sq(Sv) > 0);
}

void RationalSplineSurf::mappedPlane(Real u, Real v, Vct3 &S,
                                     Vct3 &Su, Vct3 &Sv) const
{
  const int udeg = ub.degree();
  const int vdeg = vb.degree();
  // Matrix fu(2, udeg+1), fv(2, vdeg+1);

  SMatrix<2,Piegl::MaxDegree> fu, fv;
  int uspan = ub.derive(u, 1, fu.nrows(), fu.pointer());
  int vspan = vb.derive(v, 1, fv.nrows(), fv.pointer());

  Vct4 p, pu, pv;
  for (int i=0; i<udeg+1; ++i) {
    for (int j=0; j<vdeg+1; ++j) {
      const Vct4 & cpi( cp(uspan-udeg+i, vspan-vdeg+j) );
      p  += fu(0,i) * fv(0,j) * cpi;
      pu += fu(1,i) * fv(0,j) * cpi;
      pv += fu(0,i) * fv(1,j) * cpi;
    }
  }

  Real s1 = 1.0 / p[3];
  Real s2u = pu[3] * sq(s1);
  Real s2v = pv[3] * sq(s1);
  for (int k=0; k<3; ++k) {
    S[k]  = p[k] * s1;
    Su[k] = (uend - ustart) * ( pu[k]*s1 - p[k]*s2u );
    Sv[k] = (vend - vstart) * ( pv[k]*s1 - p[k]*s2v );
  }
}

void RationalSplineSurf::apply()
{
  const Mtx44 & m = RFrame::trafoMatrix();
  const int n = cp.size();
  for (int i=0; i<n; ++i) {
    Vct3 t, p = h2p( cp[i] );
    for (int k=0; k<3; ++k)
      t[k] = m(k,0)*p[0] + m(k,1)*p[1] + m(k,2)*p[2] + m(k,3);
    cp[i] = p2h(t, cp[i][3]);
  }
  RFrame::clear();
}

XmlElement RationalSplineSurf::toXml(bool share) const
{
  XmlElement xe("RationalSplineSurf");
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
  xcp.asBinary(4*cp.size(), cp.pointer(), share);
  xe.append(std::move(xcp));

  return xe;
}

void RationalSplineSurf::fromXml(const XmlElement & xe)
{
  assert(xe.name() == "RationalSplineSurf");
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
      itr->fetch(4*cp.size(), cp.pointer());
    }
  }
}

bool RationalSplineSurf::fromIges(const IgesFile & file,
                                  const IgesDirEntry & entry)
{
  if (entry.etype != 128)
    return false;

  IgesEntityPtr eptr = file.createEntity(entry);
  IgesSplineSurface ssf;
  if (IgesEntity::as(eptr, ssf)) {

    // intercept case of too high polynomial order
    if (ssf.mu > 7 or ssf.mv > 7) {
      dbprint("RationalSplineSurf: IGES128 with order ", ssf.mu, ssf.mv);
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

    const int nr = ssf.cpoints.nrows();
    const int nc = ssf.cpoints.ncols();
    const int ncp = nr*nc;
    cp.resize(nr, nc);
    for (int i=0; i<ncp; ++i)
      cp[i] = p2h( ssf.cpoints[i], ssf.weights[i] );

    setIgesName(file, ssf);

  } else {
    return false;
  }

  return true;
}

void RationalSplineSurf::knotScale(AbstractCurve & c) const
{
  c.translate( -ukfront, -vkfront, 0.0 );
  c.scale( 1.0/(ukback-ukfront), 1.0/(vkback-vkfront), 1.0 );
  c.apply();
}

int RationalSplineSurf::toIges(IgesFile & file, int tfi) const
{
  const Vector & ukts(ub.getKnots());
  const Vector & vkts(vb.getKnots());
  if (ukts.empty() or vkts.empty())
    return 0;

  IgesSplineSurface igs;

  const int nr = cp.nrows();
  const int nc = cp.ncols();
  const int ncp = nr*nc;
  Matrix wgts(nr,nc);
  PointGrid<3> cpp(nr,nc);
  for (int i=0; i<ncp; ++i) {
    wgts[i] = cp[i][3];
    cpp[i] = h2p( cp[i] );
  }

  igs.setup(cp.nrows(), cp.ncols(), ub.degree(), vb.degree(),
            &ukts[0], &vkts[0], wgts.pointer(), &cpp[0][0]);
  igs.trafoMatrix(tfi);

  // determine if surface is closed
  Real ftol = file.modelTolerance();
  bool uclosed(true), vclosed(true);
  for (int i=0; i<nc; ++i) {
    Vct3 p1 = h2p( cp(0,i) );
    Vct3 p2 = h2p( cp(nr-1,i) );
    if (sq(p2-p1) > sq(ftol)) {
      uclosed = false;
      break;
    }
  }
  for (int i=0; i<nr; ++i) {
    Vct3 p1 = h2p( cp(i,0) );
    Vct3 p2 = h2p( cp(i,nc-1) );
    if (sq(p2-p1) > sq(ftol)) {
      vclosed = false;
      break;
    }
  }

  igs.label("RSPL_SRF");
  igs.flagClosed(uclosed, vclosed);
  return igs.append( file );
}

void RationalSplineSurf::initGridPattern(Vector &up, Vector &vp) const
{
  const uint npmax = 64;
  const int npu = std::max( 2u, 1 + ub.degree()/2 );
  const int nu = std::min((cp.nrows() - 1)*npu + 1, npmax);
  const int npv = std::max( 2u, 1 + vb.degree()/2 );
  const int nv = std::min((cp.ncols() - 1)*npv + 1, npmax);

  AbstractCurve::gridFromKnots( nu, ub.getKnots(), up, ustart, uend );
  AbstractCurve::gridFromKnots( nv, vb.getKnots(), vp, vstart, vend );
}

Surface *RationalSplineSurf::clone() const
{
  return (new RationalSplineSurf(*this));
}

void RationalSplineSurf::createCylinder()
{
  const Real w = 0.5*std::sqrt(2.0);
  cp.resize(9,2);
  cp[0] = Vct4( 1.0,  0.0, 0.0, 1.0 );
  cp[1] = Vct4(   w,    w, 0.0, w );
  cp[2] = Vct4( 0.0,  1.0, 0.0, 1.0 );
  cp[3] = Vct4(  -w,    w, 0.0, w );
  cp[4] = Vct4(-1.0,  0.0, 0.0, 1.0 );
  cp[5] = Vct4(  -w,   -w, 0.0, w );
  cp[6] = Vct4( 0.0, -1.0, 0.0, 1.0 );
  cp[7] = Vct4(   w,   -w, 0.0, w );
  cp[8] = Vct4( 1.0,  0.0, 0.0, 1.0 );

  for (int i=0; i<9; ++i) {
    cp(i,1) = cp(i,0);
    cp(i,1)[2] = cp(i,0)[3];
  }

  Vector kts(12);
  kts[0] = kts[1] = kts[2] = 0.0;
  kts[3] = kts[4] = 0.25;
  kts[5] = kts[6] = 0.5;
  kts[7] = kts[8] = 0.75;
  kts[9] = kts[10] = kts[11] = 1.0;

  ub = SplineBasis(2, kts);

  Vector vk(4);
  vk[2] = vk[3] = 1.0;
  vb = SplineBasis(1, vk);
}
