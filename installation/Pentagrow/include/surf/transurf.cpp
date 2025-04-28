
/* ------------------------------------------------------------------------
 * project:    Surf
 * file:       transurf.cpp
 * begin:      May 2008
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Transition surface
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#include "transurf.h"
#include "igesfile.h"
#include "iges128.h"
#include <sstream>

using namespace std;

void TranSurf::init(const SurfacePtr & s0, const CurvePtr & c0,
                    const SurfacePtr & s1, const CurvePtr & c1, Real lenf)
{
  Vector upar;
  int nu = initOuterCols(c0, c1, upar);
  
  // compute middle control point rows 
  Vct3 Sv;
  for (int i=0; i<nu; ++i) {
    Real vl = norm( cp(i,3) - cp(i,0) );
    Sv = s0->derive(upar[i], 1.0, 0, 1);
    cp(i,1) = cp(i,0) + Sv*lenf*vl/norm(Sv);
    Sv = s1->derive(upar[i], 0.0, 0, 1);
    cp(i,2) = cp(i,3) - Sv*lenf*vl/norm(Sv);
  }
}

void TranSurf::init(const Vct3 & slope0, const CurvePtr & c0,
                    const SurfacePtr & s1, const CurvePtr & c1, Real lenf)
{
  Vector upar;
  int nu = initOuterCols(c0, c1, upar);
  
  // compute middle control point rows 
  Vct3 Sv;
  Real isl = 1.0 / norm(slope0);
  for (int i=0; i<nu; ++i) {
    Real vl = norm( cp(i,3) - cp(i,0) );
    cp(i,1) = cp(i,0) + slope0*lenf*vl * isl;
    Sv = s1->derive(upar[i], 0.0, 0, 1);
    cp(i,2) = cp(i,3) - Sv*lenf*vl/norm(Sv);
  }
}

void TranSurf::init(const SurfacePtr & s0, const CurvePtr & c0,
                    const Vct3 & slope1, const CurvePtr & c1, Real lenf)
{
  Vector upar;
  int nu = initOuterCols(c0, c1, upar);
  
  // compute middle control point rows 
  Vct3 Sv;
  Real isl = 1.0 / norm(slope1);
  for (int i=0; i<nu; ++i) {
    Real vl = norm( cp(i,3) - cp(i,0) );
    Sv = s0->derive(upar[i], 1.0, 0, 1);
    cp(i,1) = cp(i,0) + Sv*lenf*vl/norm(Sv);
    cp(i,2) = cp(i,3) - slope1*lenf*vl * isl;
  }
}

uint TranSurf::initOuterCols(const CurvePtr & c0, const CurvePtr & c1, Vector & upar)
{
  // merge knot vectors 
  Vector uknots, ukm(c0->knots());
  ukm.insert(ukm.end(), c1->knots().begin(), c1->knots().end());
  std::sort(ukm.begin(), ukm.end());
  
  almost_equal<Real> mpr(1e-6);
  Vector::iterator ulast = std::unique(ukm.begin(), ukm.end(), mpr);
  ukm.erase(ulast, ukm.end());
  
  // ukm now contains the unified knot vector
  uint udeg(3);
  uknots.resize(ukm.size()+6);
  std::copy(ukm.begin(), ukm.end(), uknots.begin()+3);
  
  for (uint i=0; i<4; ++i) 
    uknots[uknots.size()-1-i] = 1.0;
  ub = SplineBasis(udeg,uknots);
  
  // construct fixed v-basis for single segment 
  Vector vknots(8);
  for (int i=0; i<4; ++i) {
    vknots[i] = 0.0;
    vknots[4+i] = 1.0;
  }
  vb = SplineBasis(3, vknots);
  
  // adapt curves to new knot vector
  Curve cv0(*c0), cv1(*c1);
  cv0.adapt(uknots);
  cv1.adapt(uknots);
  
  // set first and last column of control point grid 
  const PointList<3> & cp0( cv0.controls() );
  const PointList<3> & cp1( cv1.controls() );
  const int nu = cv0.controls().size();
  cp.resize(nu, 4);
  for (int i=0; i<nu; ++i) {
    cp(i,0) = cp0[i];
    cp(i,3) = cp1[i];
  }
  
  // determine suitable u-parametrization 
  upar.allocate(nu);
  for (int i=0; i<nu; ++i) 
    upar[i] = ( uknots[i+1] + uknots[i+2] + uknots[i+3] ) / 3.;
  
  return nu;
}

Vct3 TranSurf::eval(Real u, Real v) const
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

Vct3 TranSurf::derive(Real u, Real v, uint ku, uint kv) const
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

void TranSurf::plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const
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

void TranSurf::apply()
{
  PointGrid<3>::iterator itr;
  for (itr = cp.begin(); itr != cp.end(); ++itr)
    *itr = RFrame::forward(*itr);
  RFrame::clear();
}

XmlElement TranSurf::toXml(bool share) const
{
  XmlElement xe("TranSurf");
  xe.attribute("name") = name();
  
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

void TranSurf::fromXml(const XmlElement & xe)
{
  if (xe.name() != "TranSurf")
    throw Error("Incompatible XML representation for TranSurf: "+xe.name());
  
  rename( xe.attribute("name") );
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
      itr->fetch(3*nr*nc, cp.pointer());
    }
  }
}

int TranSurf::toIges(IgesFile & file, int tfi) const
{
  const Vector & ukts(ub.getKnots());
  const Vector & vkts(vb.getKnots());
  if (ukts.empty() or vkts.empty())
    return 0;
  
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
  
  igs.label("TRAN_SRF");
  igs.flagClosed(uclosed, vclosed);
  return igs.append( file ); 
}


