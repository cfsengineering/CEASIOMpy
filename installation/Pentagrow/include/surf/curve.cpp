
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
 
#include <sstream>
#include <genua/lls.h>
#include <genua/lse.h>
#include <genua/pattern.h>
#include "iges.h"
#include "curve.h"
#include "openframe.h"
#include "symframe.h"
#include "airfoil.h"
#include "ellipframe.h"
#include "eggframe.h"
#include "beziersegment.h"

using namespace std;

Curve::Curve(const std::string & s) : AbstractCurve(s)
{
  tfs(0,0) = tfs(1,1) = tfs(2,2) = tfs(3,3) = 1.0;  
}

void Curve::initSpline(const Vector &knots, const PointList<3> &ctp)
{
  bas = SplineBasis(3, knots);
  cp = ctp;
}

void Curve::bezier(const Vct3 bp[])
{
  cp.resize(4);
  for (int i=0; i<4; ++i)
    cp[i] = bp[i];

  Vector knots(8);
  std::fill(knots.begin()+4, knots.end(), 1.0);
  bas = SplineBasis(3, knots);
}

void Curve::bezier(const Vct3 &p0, const Vct3 &t0,
                   const Vct3 &p1, const Vct3 &t1)
{
  BezierSegment bz(p0, t0, p1, t1);
  this->bezier( bz.controls() );
}

void Curve::interpolate(const PointList<3> & a)
{
  Vector dummy;
  this->interpolate(a, dummy);
}

void Curve::interpolate(const PointList<3> & a, Vector & u)
{
  assert(a.size() > 3);

  // always cubic
  const int p(3);
  const int n = a.size();

  // chord length parametrization
  u.resize(n);
  for (int i=1; i<n; ++i)
    u[i] = u[i-1] + norm(a[i] - a[i-1]);

  assert(u.back() != 0);
  u /= u.back();

  // construct basis
  bas.init(p, u);

  // set up linear system of equations
  Matrix cf(n,n), rs(n, 3);
  for (int i=0; i<n; ++i) {
    int span = bas.findSpan(u[i]);
    for (int j=span-p; j<=span; ++j)
      cf(i,j) = bas.eval(j,u[i]);
    for (int j=0; j<3; ++j)
      rs(i,j) = a[i][j];
  }

  try {
    lu_solve(cf,rs);
  } catch (Error & xcp) {
    stringstream ss;
    ss << "Curve::interpolate() - " << endl;
    ss << "Factorization failed with matrix for parameter vector:" << endl;
    ss << u << endl;
    throw Error(ss.str());
  }
  
  cp.resize(n);
  for (int i=0; i<n; ++i)
    for (int j=0; j<3; ++j)
      cp[i][j] = rs(i,j);
}

void Curve::interpolate(const PointList<3> & pts, const PointList<3> & tng,
                        Vector & u)
{
  const int np = pts.size();
  if (np < 2)
    throw Error("Curve::interpolate() - Not enough points for cubic curve.");

  assert(tng.size() == uint(np));

  // use arc-length parametrization if none provided
  if (u.size() != pts.size()) {
    u.allocate(np);
    u[0] = 0.0;
    for (int i=1; i<np; ++i)
      u[i] = u[i-1] + norm(pts[i] - pts[i-1]);
    u /= u.back();
    u.front() = 0.0;
    u.back() = 1.0;
  }

  // parameter vector to use for knot computation
  Vector ub;
  interpolate_pattern(u, 2*np, ub);

  // set up cubic spline basis
  const int p(3);
  bas.init(p, ub);

  // set up linear system of equations
  const int neq = 2*np;
  SMatrix<2,4> b;
  Matrix cf(neq,neq), rs(neq, 3);
  for (int i=0; i<np; ++i) {
    int span = bas.derive(u[i], b);
    for (int j=0; j<=p; ++j) {
      cf(2*i+0, span-3+j) = b(0,j);
      cf(2*i+1, span-3+j) = b(1,j);
    }

    for (int k=0; k<3; ++k) {
      rs(2*i+0, k) = pts[i][k];
      rs(2*i+1, k) = tng[i][k];
    }
  }

  try {
    lu_solve(cf, rs);
  } catch (Error & xcp) {
    stringstream ss;
    ss << "Curve::interpolate() - " << endl;
    ss << "Factorization failed with matrix for parameter vector:" << endl;
    ss << u << endl;
    throw Error(ss.str());
  }

  cp.resize(neq);
  for (int i=0; i<neq; ++i)
    for (int j=0; j<3; ++j)
      cp[i][j] = rs(i,j);
}

void Curve::approximate(const PointList<3> & pts, const Vector & uip)
{
  // spline basis for approximation
  const uint np = pts.size();
  const uint napx = uip.size();
  bas.init(3, uip); 
  
  // construct parameters for approximation
  Vector up(np);
  for (uint i=1; i<np; ++i)
    up[i] = up[i-1] + norm(pts[i] - pts[i-1]);
  up /= up.back();
  
  // find control points by least-squares approximation
  // we constrain the least-squares approximation to pass
  // exactly through the first and last points
  Vct4 b;
  Matrix cf(np, napx), bcn(2, napx);
  Matrix rhs(np,3), dcn(2, 3), x(napx, 3);
  uint span;
  for (uint i=0; i<np; ++i) {
    span = bas.eval(up[i], b);
    for (uint k=0; k<4; ++k)
      cf(i, span-3+k) = b[k];
    for (uint k=0; k<3; ++k)
      rhs(i,k) = pts[i][k];
  }
  
  // setup equality constraints
  bcn(0, 0) = 1.0;
  bcn(1, napx-1) = 1.0;
  for (uint k=0; k<3; ++k) {
    dcn(0,k) = pts.front()[k];
    dcn(1,k) = pts.back()[k];
  }  
  int stat = lse_msolve(cf, bcn, rhs, dcn, x); 
  if (stat != 0) {
    stringstream ss;
    ss << "LAPACK failed in constrained least-squares routine GGLSE." << endl;
    ss << "status flag: " << stat << endl;
    throw Error(ss.str());
  }
    
  cp.resize(napx);
  for (uint i=0; i<uint(napx); ++i)
    for (uint k=0; k<3; ++k)
      cp[i][k] = x(i,k);
}

void Curve::akima(const PointList<3> &pts)
{
  // H.Akima: A New Method of Interpolation and Smooth Curve
  // Fitting Based on Local Procedures

  // find local slopes using Akima's rule; wrap around at the ends
  const int np = pts.size();
  PointList<3> tg(np);
  Real l34, l12;
  for (int i=0; i<np; ++i) {
    Vct3 m1 = pts[(i-1)%np] - pts[(i-2)%np];
    Vct3 m2 = pts[(i)%np] - pts[(i-1)%np];
    Vct3 m3 = pts[(i+1)%np] - pts[(i)%np];
    Vct3 m4 = pts[(i+2)%np] - pts[(i+1)%np];
    l12 = norm(m2 - m1);
    l34 = norm(m4 - m3);
    if ((l12 > gmepsilon) or (l34 > gmepsilon))
      tg[i] = (l34*m2 + l12*m3) / (l34 + l12);
    else
      tg[i] = 0.5*(m2 + m3);
  }

  // solve as above
  Vector u;
  interpolate(pts, tg, u);
}

Vct3 Curve::eval(Real t) const
{
  assert(t >= 0);
  assert(t <= 1);
  Vct3 pt;
  Vct4 b;
  uint span = bas.eval(t, b);
  for (uint i=0; i<4; ++i)
    pt += b[i] * cp[span-3+i];
  return pt;
}

Vct3 Curve::derive(Real t, uint k) const
{
  assert(t >= 0);
  assert(t <= 1);
  
  Vct3 pt;
  if (k == 0) {
    return eval(t);
  } else {
    Matrix b(k+1,4);
    uint span = bas.derive(t, k, b);
    for (uint i=0; i<4; ++i)
      pt += b(k,i) * cp[span-3+i];
  }
  return pt;
}

void Curve::tgline(Real t, Vct3 & c, Vct3 & dc) const
{
  assert(t >= 0);
  assert(t <= 1);
  
  c = 0.0;
  dc = 0.0;
  SMatrix<2,4,Real> b;
  uint span = bas.derive(t, b);
  for (uint i=0; i<4; ++i) {
    const Vct3 & cpt( cp[span-3+i] );
    c  += cpt * b(0,i);
    dc += cpt * b(1,i);
  }
}

Real Curve::curvature(Real t) const
{
  assert(t >= 0);
  assert(t <= 1);
  
  // need first and second derivative
  Vct3 dc, ddc;
  SMatrix<3,4> b;
  uint span = bas.derive(t, b);
  for (uint i=0; i<4; ++i) {
    const Vct3 & cpt( cp[span-3+i] );    
    dc  += cpt * b(1,i);
    ddc += cpt * b(2,i);
  }
  
  Real  x1(dc[0]),  y1(dc[1]),  z1(dc[2]);
  Real x2(ddc[0]), y2(ddc[1]), z2(ddc[2]);
  Real t1 = sq(z2*y1 - y2*z1);
  Real t2 = sq(x2*z1 - z2*x1);
  Real t3 = sq(y2*x1 - x2*y1);
  Real t4 = cb( sqrt(sq(x1) + sq(y1) + sq(z1)) );
  return sqrt(t1 + t2 + t3) / t4;
}

void Curve::adapt(const Vector & nk)
{
  // adapt spline to new knot vector, do not change
  // parametrization symmetry

  const uint p(3);
  uint n;
  // number of new control points
  n  = nk.size() - p - 1;
  // parameters for system
  Vector u(n);

  // generate suitable parameter values to avoid singular
  // coefficient matrix (similar to 'averaging')
  // important condition: parameter vector must be symmetric if knot
  // vector is symmetric (Piegl's algorithm 5.4 cannot guarantee that!)
  Real ip = 1.0/p;
  for (uint i=0; i<n; i++) {
    for (uint j=i+1; j<=i+p; j++)
      u[i] += nk[j];
    u[i] *= ip;
  }
  
  // bandwidth 
  int ku(p), kl(p);
  
  // setup system of equations
  Vct4 b;
  Vct3 pu;
  SplineBasis nbas(p,nk);
  Matrix bcf(2*kl+ku+1,n), rm(n,3);
  for (uint i=0; i<n; i++) {
    pu = eval(u[i]);
    rm(i,0) = pu[0];
    rm(i,1) = pu[1];
    rm(i,2) = pu[2];
    int span = nbas.eval(u[i], b);
    for (int j=0; j<4; j++) { 
      int col = span-3+j;
      int row = kl+ku+i-col;
      bcf(row, col) = b[j];
    }
  }

  // solve for new control points
  int stat = banded_lu_solve(kl, ku, bcf, rm);
  if (stat != 0)
    throw Error("Lapack: LU solve failed in Curve::adapt().");
  
  cp.resize(n);
  for (uint i=0; i<n; ++i)
    for (uint j=0; j<3; ++j)
      cp[i][j] = rm(i,j);

  bas.setKnots(nk);
}

Vct3 Curve::center() const
{
  assert(!cp.empty());
  Vct3 ctr, lc;
  Real len, sum(0);
  for (uint i=1; i<cp.size(); ++i) {
    lc = 0.5*(cp[i] + cp[i-1]);
    len = norm(cp[i] - cp[i-1]);
    ctr += len*lc;
    sum += len;
  }
  ctr /= sum;
  return ctr;
}

void Curve::reverse()
{
  const Vector & kts( bas.getKnots() );
  const int n = kts.size();
  Vector ki(n);
  for (int i=0; i<n; ++i)
    ki[n-i-1] = 1.0 - kts[i];

  bas = SplineBasis(3, ki);
  std::reverse(cp.begin(), cp.end());
}

void Curve::apply()
{
  PointList<3>::iterator itr;
  for (itr = cp.begin(); itr != cp.end(); ++itr)
    *itr = RFrame::forward(*itr);
  
  tfs = RFrame::trafoMatrix() * tfs;
  RFrame::clear();
}

void Curve::initGrid(Vector &t) const
{
  const int ntv = 2 + (cp.size()-1)*2;
  AbstractCurve::gridFromKnots( ntv, bas.getKnots(), t );
}

XmlElement Curve::toXml(bool share) const
{
  XmlElement xe("Curve");
  xe.attribute("name") = ids;
  xe.append(bas.toXml(share));
  
  XmlElement xb("ControlPoints");
  xb.attribute("count") = str(cp.size());
  xb.asBinary( 3*cp.size(), cp.pointer(), share );
  xe.append(std::move(xb));

  return xe;
}

void Curve::fromXml(const XmlElement & xe)
{
  if (xe.name() != "Curve") 
    throw Error("Curve: incompatible XML representation.");
  ids = xe.attribute("name");
  
  XmlElement::const_iterator itr;
  itr = xe.findChild("SplineBasis");
  if (itr == xe.end())
    throw Error("Curve: Spline basis not found in XML representation.");
  bas.fromXml(*itr);
  
  itr = xe.findChild("ControlPoints");
  if (itr == xe.end())
    throw Error("Curve: No control points not found in XML representation.");

  cp.resize( Int(itr->attribute("count")) );
  itr->fetch( 3*cp.size(), cp.pointer() );
  
//  Vct3 tmp;
//  cp.clear();
//  cp.reserve(Int(itr->attribute("count")));
//  stringstream ss(itr->text());
//  while (ss >> tmp)
//    cp.push_back(tmp);
}

CurvePtr Curve::createFromXml(const XmlElement & xe)
{
  CurvePtr cp;
  AbstractCurvePtr acp = AbstractCurve::createFromXml(xe);
  cp = boost::dynamic_pointer_cast<Curve>( acp );
  return cp;
}

void Curve::applyFromXml(const XmlElement & xt)
{
  if (xt.name() != "TrafoSequence")
    throw Error("Incompatible XML representation for transformation sequence.");
  stringstream ss(xt.text());
  ss >> tfs;
  RFrame::setTrafoMatrix(tfs);
  apply();  
}
    
XmlElement Curve::trafoToXml() const
{
  XmlElement xt("TrafoSequence");
  stringstream ss;
  ss << tfs;
  xt.text() = ss.str();  
  return xt;
}

Curve *Curve::clone() const
{
  return new Curve(*this);
}

uint Curve::arclenParamet(const CurvePtrArray & cpa, Vector & vp)
{
  const int nc(cpa.size());
  if (nc == 0)
    return 0;
  
  // evaluate curves at nt points around the circumference  
  const int nt(8);
  Real dt = 1.0/nt;
  PointGrid<3> pts(nt,nc);
  for (int j=0; j<nc; ++j) {
    const Curve & cv(*cpa[j]);
    for (int i=0; i<nt; ++i) {
      Real t = 0.5*dt + i*dt;
      pts(i,j) = cv.eval(t);
    }
  }
  
  // compute a mean parametrization 
  uint nid(0);
  vp.resize(nc); 
  vp[0] = 0.0;
  for (int j=1; j<nc; ++j) {
    vp[j] = vp[j-1];
    for (int i=0; i<nt; ++i) {
      vp[j] += norm(pts(i,j) - pts(i,j-1));
    }
    if (vp[j] == vp[j-1])
      ++nid;
  }
  
  // normalize to 0..1
  vp -= vp.front();
  vp /= vp.back();
  
  // strange, sometimes vp.back() ends up as 0.99998
  vp.front() = 0.0;
  vp.back() = 1.0;

  return nid;
}

int Curve::toIges(IgesFile & file, int tfi) const
{
  const Vector & kts(knots());
  if (kts.empty())
    return 0;
  


  IgesSplineCurve igs;
  igs.setup(cp.size(), 3, &kts[0], &cp[0][0]);
  igs.trafoMatrix( tfi );
  
  // determine if curve is closed 
  if (norm(eval(0.0) - eval(1.0)) < file.modelTolerance())
    igs.flagClosed( true );
  else
    igs.flagClosed( false );
  igs.label("SPLN_CRV");

  if (not name().empty()) {
    IgesNameProperty nprop(name());
    int ip = nprop.append(file);
    igs.addPropRef(ip);
  }

  return igs.append( file );
}

bool Curve::fromIges(const IgesFile & file, const IgesDirEntry & dir)
{
  if (dir.etype != 126)
    return false;

  IgesEntityPtr eptr = file.createEntity(dir);
  IgesSplineCurve icv;
  if (not IgesEntity::as(eptr, icv))
    return false;

  if ((not icv.isPolynomial()) or icv.degree() != 3)
    return false;

  bas = SplineBasis(icv.degree(), icv.knotVector());
  cp = icv.ctrlPoints();
  unity(tfs);

  setIgesName(file, icv);
  setIgesTransform(file, dir);

  return true;
}
