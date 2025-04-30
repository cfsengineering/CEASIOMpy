
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
 
#include "rationalsplinecurve.h"
#include "igesfile.h"
#include "iges126.h"
#include <genua/dbprint.h>
#include <boost/math/special_functions/binomial.hpp>

static inline Vct3 h2p( const Vct4 & pw )
{
  Real iw = 1.0 / pw[3];
  return Vct3( pw[0]*iw, pw[1]*iw, pw[2]*iw );
}

static inline Vct4 p2h( const Vct3 & p, Real w = 1.0)
{
  return Vct4( w*p[0], w*p[1], w*p[2], w );
}

void RationalSplineCurve::createCircle()
{
  const Real w = 0.5*std::sqrt(2.0);
  cp.resize(9);
  cp[0] = Vct4( 1.0,  0.0, 0.0, 1.0 );
  cp[1] = Vct4(   w,    w, 0.0, w );
  cp[2] = Vct4( 0.0,  1.0, 0.0, 1.0 );
  cp[3] = Vct4(  -w,    w, 0.0, w );
  cp[4] = Vct4(-1.0,  0.0, 0.0, 1.0 );
  cp[5] = Vct4(  -w,   -w, 0.0, w );
  cp[6] = Vct4( 0.0, -1.0, 0.0, 1.0 );
  cp[7] = Vct4(   w,   -w, 0.0, w );
  cp[8] = Vct4( 1.0,  0.0, 0.0, 1.0 );

  Vector kts(12);
  kts[0] = kts[1] = kts[2] = 0.0;
  kts[3] = kts[4] = 0.25;
  kts[5] = kts[6] = 0.5;
  kts[7] = kts[8] = 0.75;
  kts[9] = kts[10] = kts[11] = 1.0;

  ub = SplineBasis(2, kts);
}

void RationalSplineCurve::createCircle(const Vct3 &ctr,
                                       const Vct3 &pnrm, Real radius)
{
  createCircle();

  // transformation
  scale(radius);
  const Vct3 zax(0.0, 0.0, 1.0);
  Vct3 rotax = cross( zax, pnrm.normalized() );
  Real l = normalize(rotax);
  Real phi = arg(zax, pnrm);
  if (l > 0 and fabs(phi) > 0)
    rotate(rotax, phi);
  translate(ctr);

  apply();
}

Vct3 RationalSplineCurve::eval(Real u) const
{
  u = tmap(u);
  assert(u >= 0);
  assert(u <= 1);

  Real fu[8];
  const int uspan = ub.lleval(u, fu);

  Vct4 ptw;
  const int pu = ub.degree();
  for (int i=0; i<pu+1; ++i)
    ptw += fu[i] * cp[uspan-pu+i];

  return h2p(ptw);
}

Vct3 RationalSplineCurve::derive(Real u, uint ku) const
{
  if (ku == 0) {
    return eval(u);
  } else if (ku == 1) {

    // optimization for first derivative
    u = tmap(u);
    assert(u >= 0);
    assert(u <= 1);
    const int deg = ub.degree();
    Matrix fu(ku+1, deg+1);
    int uspan = ub.derive(u, ku, fu);

    Vct4 p, pu;
    for (int i=0; i<deg+1; ++i) {
      p  += fu(0,i) * cp[uspan-deg+i];
      pu += fu(1,i) * cp[uspan-deg+i];
    }

    Vct3 q;
    Real s1 = 1.0 / p[3];
    Real s2 = pu[3] * sq(s1);
    for (int k=0; k<3; ++k)
      q[k] = (tend - tstart) * ( pu[k]*s1 - p[k]*s2 );

    return q;
  } else {
    u = tmap(u);
    assert(u >= 0);
    assert(u <= 1);
    const int pu = ub.degree();
    Matrix fu(ku+1, pu+1);
    PointList<4> Cwp(ku+1);
    int uspan = ub.derive(u, ku, fu);
    for (int i=0; i<pu+1; ++i)
      for (uint j=0; j<ku+1; ++j)
        Cwp[j] += fu(j,i) * cp[uspan-pu+i];

    Vct3 p;
    for (uint k=0; k<=ku; ++k) {
      Vct3 v(Cwp[k][0], Cwp[k][1], Cwp[k][2]);
      for (uint i=1; i<=k; ++i)
        v -= boost::math::binomial_coefficient<Real>(k,i) * Cwp[k][3] * p;
      p = v / Cwp[0][3];
    }

    // inner derivative of tmap
    Real dtk = std::pow(tend - tstart, Real(ku));
    return dtk*p;
  }
}

void RationalSplineCurve::tgline(Real u, Vct3 &c, Vct3 &dc) const
{
  u = tmap(u);
  assert(u >= 0);
  assert(u <= 1);
  const int deg = ub.degree();
  Matrix fu(2, deg+1);
  int uspan = ub.derive(u, 1, fu);

  Vct4 p, pu;
  for (int i=0; i<deg+1; ++i) {
    p  += fu(0,i) * cp[uspan-deg+i];
    pu += fu(1,i) * cp[uspan-deg+i];
  }

  Real s1 = 1.0 / p[3];
  Real s2 = pu[3] * sq(s1);
  for (int k=0; k<3; ++k) {
    c[k]  = p[k] * s1;
    dc[k] = (tend - tstart) * ( pu[k]*s1 - p[k]*s2 );
  }
}

void RationalSplineCurve::apply()
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

void RationalSplineCurve::initGrid(Vector &t) const
{
  const int nps = std::max(2u, ub.degree() / 2);
  const int ntv = 2 + (cp.size()-1)*nps;
  AbstractCurve::gridFromKnots( ntv, ub.getKnots(), t, tstart, tend);
}

XmlElement RationalSplineCurve::toXml(bool share) const
{
  XmlElement xe("RationalSplineCurve");
  xe["name"] = name();
  xe["tstart"] = str(tstart);
  xe["tend"] = str(tend);
  xe["kfront"] = str(kfront);
  xe["kback"] = str(kback);
  xe.append(ub.toXml());

  XmlElement xcp("ControlPoints");
  xcp.attribute("count") = str(cp.size());
  xcp.asBinary(4*cp.size(), cp.pointer(), share);
  xe.append(std::move(xcp));

  return xe;
}

void RationalSplineCurve::fromXml(const XmlElement & xe)
{
  *this = RationalSplineCurve();

  assert(xe.name() == "RationalSplineCurve");
  tstart = xe.attr2float("tstart", 0.0);
  tend = xe.attr2float("tend", 1.0);
  kfront = xe.attr2float("kfront", 0.0);
  kback = xe.attr2float("kback", 1.0);
  rename( xe.attribute("name") );
  XmlElement::const_iterator itr, last;
  last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "SplineBasis") {
      ub.fromXml(*itr);
    } else if (itr->name() == "ControlPoints") {
      uint n = Int( itr->attribute("count") );
      cp.resize(n);
      itr->fetch(4*cp.size(), cp.pointer());
    }
  }
}

bool RationalSplineCurve::fromIges(const IgesFile & file,
                                   const IgesDirEntry & entry)
{
  if (entry.etype != 126)
    return false;

  *this = RationalSplineCurve();
  IgesEntityPtr eptr = file.createEntity(entry);
  IgesSplineCurve ssf;
  if (IgesEntity::as(eptr, ssf)) {

    // intercept case of too high polynomial order
    if (ssf.degree() > 7) {
      dbprint("Spline curve degree exceeds 7.");
      return false;
    }

    // normalize knot vector to range 0,1
    Vector knots( ssf.knotVector() );
    kfront = knots.front();
    kback = knots.back();
    knots -= kfront;
    knots /= kback - kfront;

    // subregion mapping, transformed to (0,1)
    tstart = (ssf.ustart - kfront) / (kback - kfront);
    tend = (ssf.uend - kfront) / (kback - kfront);

    assert(tstart >= 0.0);
    assert(tend <= 1.0);

    ub = SplineBasis(ssf.degree(), knots);

    const int ncp = ssf.cpoints.size();
    assert(ssf.weights.size() == uint(ncp));
    cp.resize(ncp);
    for (int i=0; i<ncp; ++i)
      cp[i] = p2h( ssf.cpoints[i], ssf.weights[i] );

  } else {
    return false;
  }

  setIgesName(file, ssf);
  setIgesTransform(file, entry);

  return true;
}

int RationalSplineCurve::toIges(IgesFile & file, int tfi) const
{
  const Vector & ukts(ub.getKnots());
  if (ukts.empty())
    return 0;

  // convert from homogeneous format to 3D points + weights
  const int ncp = cp.size();
  PointList<3> cpw(ncp);
  Vector wgt(ncp);
  for (int i=0; i<ncp; ++i) {
    wgt[i] = cp[i][3];
    cpw[i] = h2p( cp[i] );
  }

  IgesSplineCurve igs;
  igs.setup(cp.size(), ub.degree(), ukts.pointer(),
            wgt.pointer(), cpw.pointer());
  igs.trafoMatrix(tfi);

  igs.label("RSPL_CRV");
  return igs.append( file );
}

RationalSplineCurve *RationalSplineCurve::clone() const
{
  return (new RationalSplineCurve(*this));
}
