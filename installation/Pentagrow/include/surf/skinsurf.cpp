
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
 
#include <set>
#include <sstream>
#include <genua/lu.h>
#include <genua/pattern.h>

#include "iges128.h"
#include "igesfile.h"
#include "initgrid.h"
#include "abstractcurve.h"
#include "skinsurf.h"

using namespace std;

struct margin_pred
{
  margin_pred(Real m) : margin(m) {}
  bool operator() (Real a, Real b) const {
    return fabs(a-b) < margin;
  }  
  Real margin;
};

// ----------------------- SkinSurf ------------------------------------------

Real SkinSurf::umergetol = 1e-6;
uint SkinSurf::iMaxKnots = numeric_limits<uint>::max() - 4;

Vct3 SkinSurf::eval(Real u, Real v) const
{
  assert(u >= 0);
  assert(u <= 1);
  assert(v >= 0);
  assert(v <= 1);

  // return the point at (u,v)
  Vct3 pt;
  Vct4 bu, bv;
  uint uspan = ub.eval(u, bu);
  uint vspan = vb.eval(v, bv);
  for (uint i=0; i<4; ++i)
    for (uint j=0; j<4; ++j)
      pt += bu[i] * bv[j] * cp(uspan-3+i,vspan-3+j);
  return pt;
}

Vct3 SkinSurf::derive(Real u, Real v, uint ku, uint kv) const
{
  assert(u >= 0);
  assert(u <= 1);
  assert(v >= 0);
  assert(v <= 1);  

  Vct3 pt;
  int uspan, vspan;
  if (ku == 0 and kv == 0) {
    return eval(u, v);
  } else {
    Matrix bu(ku+1, 4), bv(kv+1, 4);
    uspan = ub.derive(u, ku, bu);
    vspan = vb.derive(v, kv, bv);
    for (uint i=0; i<4; ++i)
      for (uint j=0; j<4; ++j)
        pt += (bu(ku,i) * bv(kv,j)) * cp(uspan-3+i, vspan-3+j);
  }
  
  return pt;
}

void SkinSurf::plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const
{
  // compute basis function derivatives
  SMatrix<2,4> bu, bv;
  uint uspan = ub.derive(u, bu);
  uint vspan = vb.derive(v, bv);
  
  // assemble surface point tangents
  S = 0.0;
  Su = 0.0;
  Sv = 0.0;
  for (uint i=0; i<4; ++i) {
    for (uint j=0; j<4; ++j) {
      const Vct3 & tp( cp(uspan-3+i, vspan-3+j) );
      S  += (bu(0,i) * bv(0,j)) * tp;
      Su += (bu(1,i) * bv(0,j)) * tp;
      Sv += (bu(0,i) * bv(1,j)) * tp;
    } 
  }
}

void SkinSurf::init(CurvePtrArray & cv, bool iplocal, bool akima)
{
  iploc = iplocal;
  ipakima = akima;
  
  const uint nc(cv.size());
  ipc.resize(nc);
  for (uint i=0; i<nc; ++i) 
    ipc[i] = CurvePtr(cv[i]->clone());
  
  if (iplocal)
    localIpol(cv, akima);
  else
    globalIpol(cv);
}

void SkinSurf::apply()
{
  PointGrid<3>::iterator itr;
  for (itr = cp.begin(); itr != cp.end(); ++itr)
    *itr = RFrame::forward(*itr);
  
  // transform curves as well
  SMatrix<4,4> tfm = RFrame::trafoMatrix();
  for (uint i=0; i<ipc.size(); ++i) {
    ipc[i]->setTrafoMatrix(tfm);
    ipc[i]->apply();
  }
  
  RFrame::clear();
}

uint SkinSurf::adaptCurves(CurvePtrArray & cv)
{
//   // merge knot vectors 
//   Vector tmp, common;
//   ctr.resize(cv.size());
//   for (uint i=0; i<cv.size(); ++i) {
//     
//     const Vector & ukvec(cv[i]->knots());
//     if (ukvec.size() > nkmax) {
//       nkmax = ukvec.size();
//       ukmax = ukvec;
//     }
//     common.resize(0);
//     std::set_union(ukvec.begin(), ukvec.end(), tmp.begin(), tmp.end(),
//                    back_inserter(common) );
//     tmp.swap(common);
//     
//     // find curve center
//     ctr[i] = cv[i]->center();
//   }
//   
//   // common now contains the unified knot vector
//   uint udeg(3);
//   Vector uknots, ukm;
//   margin_pred cmp(umergetol);
//   std::unique_copy(common.begin(), common.end(), back_inserter(ukm), cmp);
//   uknots.resize(ukm.size()+6);
//   std::copy(ukm.begin(), ukm.end(), uknots.begin()+3);
//   
//   for (uint i=0; i<4; ++i) 
//     uknots[uknots.size()-1-i] = 1.0;
  
  // collect all knot vectors, remember size of longest one
  Vector allknots;
  const int nc(cv.size());
  for (int i=0; i<nc; ++i) {
    const Vector & knots(cv[i]->knots());
    allknots.insert(allknots.end(), knots.begin(), knots.end());
  } 
  std::sort(allknots.begin(), allknots.end());
  
  // drop all multiple knots completely, even first/last
  margin_pred cmp(umergetol);
  Vector::iterator last;
  last = std::unique(allknots.begin(), allknots.end(), cmp);
  allknots.erase(last, allknots.end());
  
  static const Real zeros[] = {0.0, 0.0, 0.0};
  static const Real ones[] = {1.0, 1.0, 1.0};
  Vector uknots;
  if (allknots.size()+6 <= iMaxKnots) {
  
    // equilibrate knot positions to improve conditioning
    allknots.insert(allknots.begin(), zeros, zeros+3);
    allknots.insert(allknots.end(), ones, ones+3);
    uknots = allknots;
    const int jak(3), njak(2*jak+1);
    const int nak(uknots.size());
    for (int i=4; i<nak-4; ++i) {
      Real sum(0.0);
      for (int j=0; j<njak; ++j)
        sum += allknots[i+j-jak];
      uknots[i] = sum / njak;
    }
 
  } else {
  
    // simplify geometry if knot count is limited   
    uknots.resize(iMaxKnots - 6);
    const int nu(uknots.size());
    const int na(allknots.size());
    
    Vector t(na);
    for (int i=0; i<na; ++i)
      t[i] = Real(i) / (na - 1);
    
    // linear table-lookup
    Vector::iterator pos;
    uknots.front() = allknots.front();
    uknots.back() = allknots.back(); 
    for (int i=1; i<nu-1; ++i) {
      Real tu = Real(i) / (nu-1);
      pos = lower_bound(t.begin(), t.end(), tu);
      int k = std::distance(t.begin(), pos);
      Real st = (tu - t[k-1]) / (t[k] - t[k-1]);
      uknots[i] = (1-st)*allknots[k-1] + st*allknots[k];
    }
    
    uknots.insert(uknots.begin(), zeros, zeros+3);
    uknots.insert(uknots.end(), ones, ones+3);
  }
  
  ub = SplineBasis(3,uknots);
  
  // adapt curves to new knot vector
  for (uint i=0; i<cv.size(); ++i)
    cv[i]->adapt(uknots);
  
  return uknots.size();
}

void SkinSurf::globalIpol(CurvePtrArray & cv)
{
  assert(cv.size() > 3);

  // merge knot vectors and compute v-parametrization
  uint nuk = adaptCurves(cv);

  // v-direction basis
  Vector vp(cv.size());
  Curve::arclenParamet(cv, vp);
  
  // complain on undefined v-parameters 
  if (not isnormal(norm(vp)))
    throw Error("SkinSurf::init(): Undefined v-parametrization.\n"
                "Coincident sections?");
  
  vb.init(3, vp);

  // to obtain surface controlpoints, interpolate curves through
  // section controlpoints along the v-direction
  uint udeg(3);
  uint nu = nuk - udeg - 1;
  PointGrid<3> cpg(nu, cv.size());
  for (uint j=0; j<cv.size(); ++j) {
    const PointList<3> & ccp(cv[j]->controls());
    for (uint i=0; i<nu; ++i)
      cpg(i,j) = ccp[i];
  }

  // coefficient matrix
  Matrix cf(vp.size(),vp.size());
  for (uint i=0; i<vp.size(); ++i) {
    int span = vb.findSpan(vp[i]);
    for (int j=span-3; j<=span; ++j)
      cf(i,j) = vb.eval(j,vp[i]);
  }
  LuDecomp<Matrix> lu;
  int stat = lu.factor(cf);
  assert(stat == 0);

  // interpolate
  Matrix rhs(cv.size(), 3);
  cp.resize(nu,cv.size());
  for (uint i=0; i<nu; ++i) {
    for (uint j=0; j<cpg.ncols(); ++j)
      for (uint k=0; k<3; ++k)
        rhs(j,k) = cpg(i,j)[k];
    stat = lu.msolve(rhs);
    assert(stat == 0);
    for (uint j=0; j<cv.size(); ++j)
      for (uint k=0; k<3; ++k)
        cp(i,j)[k] = rhs(j,k);
  }
}

void SkinSurf::localIpol(CurvePtrArray & cv, bool akima)
{
  // get curve centers
  adaptCurves(cv);

  // collect curve control points
  PointGrid<3> cvp(cv[0]->controls().size(), cv.size());
  for (uint i=0; i<cv.size(); ++i) {
    const PointList<3> & lcp(cv[i]->controls());
    assert(lcp.size() == cvp.nrows());
    for (uint j=0; j<lcp.size(); ++j) {
      cvp(j,i) = lcp[j];
    }
  }

  // local cubic interpolation of surface controlpoints
  uint nct = 2*cv.size();
  uint nu = cv.front()->controls().size();
  Vector vsum(cv.size());
  cp.resize(nu,nct);
  for (uint i=0; i<nu; i++) 
    lcubCtlPoints(cvp, i, akima);
  
  Curve::arclenParamet(cv, vsum);
  
  // compute v-knots, setup v-basis
  uint vdeg(3);
  Vector vk(2*vsum.size()+4);
  for (uint j=1; j<vsum.size()-1; j++)
    vk[vdeg+2*j-1] = vk[vdeg+2*j] = vsum[j];
  for (uint j=vdeg+2*vsum.size()-3; j<vk.size(); j++)
    vk[j] = 1.;
  vb = SplineBasis(vdeg,vk);
}

void SkinSurf::tangentsBessel(const PointList<3> & pts, 
                              PointList<3> & tng) const
{
  // estimate tangent vectors using the Bessel scheme
  // [Piegl/Tiller, p.388, 9.32]
  Real du;
  Vector u(pts.size());
  for (uint i=1; i<pts.size(); i++) {
    du = norm(pts[i]-pts[i-1]);
    if (du == 0)
      throw Error("SkinSurf::tangents(): Coincident section points.");  
    u[i] = u[i-1] + du;
  }
  u /= u[u.size()-1];

  Real ak;
  tng.resize(pts.size());
  for (uint i=1; i<pts.size()-1; i++) {
    assert( fabs(u[i]-u[i-1]) > 0);
    assert( fabs(u[i]-u[i+1]) > 0);
    assert( fabs(u[i+1]-u[i-1]) > 0);
    ak = (u[i]-u[i-1])/(u[i+1] - u[i-1]);
    tng[i] = (1-ak)*(pts[i]-pts[i-1])/(u[i]-u[i-1])
           + ak*(pts[i+1]-pts[i])/(u[i+1]-u[i]);
  }

  uint n = tng.size()-1;
  tng[0] = 2.*(pts[1]-pts[0])/(u[1]-u[0]) - tng[1];
  tng[n] = 2.*(pts[n]-pts[n-1])/(u[n]-u[n-1]) - tng[n-1];
}

void SkinSurf::tangentsAkima(const PointList<3> & pts, 
                             PointList<3> & tng) const
{
  // estimate tangent vectors using the Akima scheme
  // [Piegl/Tiller, p.388, 9.33] --- need at least five points
  const int n(pts.size());
  PointList<3> q(n);
  for (int i=1; i<n; ++i)
    q[i] = pts[i] - pts[i-1];
  q[0] = 2.*q[1] - q[2];
  Vct3 qm1( 2.*q[0] - q[1] );
  Vct3 qp1( 2.*q[n-1] - q[n-2] );
  Vct3 qp2( 2.*qp1 - q[n-1] );
  
  // regular 5-point scheme 
  Real ak, t1, t2;
  tng.resize(n);
  for (int k=1; k<n-2; ++k) {
    t1 = norm( cross(q[k-1], q[k]) );
    t2 = norm( cross(q[k+1], q[k+2]) );
    if ( fabs(t1+t2) < gmepsilon )
      ak = 1.0;
    else
      ak = t1 / (t1 + t2);
    tng[k] = (1.0 - ak)*q[k] + ak*q[k+1];
    normalize(tng[k]);
  }

  // handle first point : k == 0 
  t1 = norm( cross(qm1, q[0]) );
  t2 = norm( cross(q[1], q[2]) );
  if ( fabs(t1+t2) < gmepsilon )
    ak = 1.0;
  else
    ak = t1 / (t1 + t2);
  tng[0] = (1.0 - ak)*q[0] + ak*q[1];
  normalize(tng[0]);
  
  // handle last points : k == n-2 
  t1 = norm( cross(q[n-3], q[n-2]) );
  t2 = norm( cross(q[n-1], qp1) );
  if ( fabs(t1+t2) < gmepsilon )
    ak = 1.0;
  else
    ak = t1 / (t1 + t2);
  tng[n-2] = (1.0 - ak)*q[n-2] + ak*q[n-1];
  normalize(tng[n-2]);
  
  // handle last points : k == n-1 
  t1 = norm( cross(q[n-2], q[n-1]) );
  t2 = norm( cross(qp1, qp2) );
  if ( fabs(t1+t2) < gmepsilon )
    ak = 1.0;
  else
    ak = t1 / (t1 + t2);
  tng[n-1] = (1.0 - ak)*q[n-1] + ak*qp1;
  normalize(tng[n-1]);
}

void SkinSurf::lcubCtlPoints(const PointGrid<3> & cvp, uint row, bool akima)
{
  // compute control points for local cubic interpolation
  assert(cp.nrows() == cvp.nrows());
  assert(cp.ncols() == 2*cvp.ncols());
  PointList<3> pts(cvp.ncols()), tng(cvp.ncols());
  for (uint j=0; j<cvp.ncols(); ++j)
    pts[j] = cvp(row,j);

  if (akima and pts.size() > 4)
    tangentsAkima(pts, tng);
  else
    tangentsBessel(pts, tng);
  double a,b,c,alfa,ltan;
  ltan = normalize(tng[0]);
  assert(ltan > 0);
  cp(row,0) = pts[0];
  for (uint i=0; i<pts.size()-1; i++) {
    ltan = normalize(tng[i+1]);
    assert(ltan > 0);
    a = 16 - sq(norm((tng[i]+tng[i+1])));
    b = 12*dot(pts[i+1]-pts[i], tng[i]+tng[i+1]);
    c = -36*sq(norm(pts[i+1]-pts[i]));

    // FIXME: handle the case sq(b)-4*a*c < 0 !!!
    assert(sq(b)-4*a*c >= 0);
    alfa = max((-b+sqrt(sq(b)-4*a*c))/(2*a),(-b-sqrt(sq(b)-4*a*c))/(2*a));
    assert(alfa > 0);
    cp(row, 2*i+1) = pts[i] + alfa/3. * tng[i];
    cp(row, 2*i+2) = pts[i+1] - alfa/3. * tng[i+1];
  }
  cp(row, cp.ncols()-1) = pts.back();
}

XmlElement SkinSurf::toXml(bool) const
{
  XmlElement xe("SkinSurf");
  xe["name"] = ids; 
  if (iploc)
    xe.attribute("interpolation") = "local";
  else
    xe.attribute("interpolation") = "global";
  if (ipakima)
    xe.attribute("akima") = "true";
  else
    xe.attribute("akima") = "false";
  
  for (uint i=0; i<ipc.size(); ++i)
    xe.append(ipc[i]->toXml());
  
  return xe;
}
    
void SkinSurf::fromXml(const XmlElement & xe)
{
  if (xe.name() != "SkinSurf")
    throw Error("SkinSurf: incompatible XML representation.");
 
  rename(xe.attribute("name"));
  string ipmode = xe.attribute("interpolation");
  if (ipmode == "local")
    iploc = true;
  else if (ipmode == "global")
    iploc = false;
  else
    throw Error("SkinSurf::fromXml() : Unknown interpolation mode.");  
     
  ipakima = false;
  if (xe.hasAttribute("akima") and xe.attribute("akima") == "true") {
    ipakima = true;
  }

  ipc.clear();
  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    CurvePtr cp;
    cp = Curve::createFromXml(*itr);
    if (cp)
      ipc.push_back(cp);  
  }
  
  if (ipc.size() < 4)
    throw Error("SkinSurf::fromXml() : Need at least four section curves.");
  
  init(ipc, iploc, ipakima);
}

void SkinSurf::initGridPattern(Vector & up, Vector & vp) const
{
  uint nu = std::min(32u, std::max(cp.nrows(), 8u));
  uint nv = std::min(32u, std::max(cp.ncols(), 8u));

  AbstractCurve::gridFromKnots(nu, ub.getKnots(), up);
  AbstractCurve::gridFromKnots(nv, vb.getKnots(), vp);

  // up = equi_pattern(15);
  // vp = cosine_pattern(25, 2*PI, 0.0, 0.7);
}

void SkinSurf::dimStats(Surface::DimStat &stat) const
{
  Surface::dimStats(stat);
  stat.nControlU = cp.nrows();
  stat.nControlV = cp.ncols();
}

void SkinSurf::isSymmetric(bool & usym, bool & vsym) const
{
  usym = false;
  vsym = false;
}

int SkinSurf::toIges(IgesFile & file, int tfi) const
{
  const Vector & ukts(ub.getKnots());
  const Vector & vkts(vb.getKnots());
  if (ukts.empty() or vkts.empty()) {
      cout << "ukts: " << ukts.size() << " vkts: " << vkts.size() << endl;
    return 0;
  }
  
  IgesSplineSurface igs;
  igs.setup(cp.nrows(), cp.ncols(), 3, 3, &ukts[0], &vkts[0], &cp[0][0]);
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
  
  igs.label("SKIN_SRF");
  igs.flagClosed(uclosed, vclosed);
  int ipar = igs.append( file );
  cout << "SkinSurf entry: " << ipar << endl;
  return ipar;
}  
