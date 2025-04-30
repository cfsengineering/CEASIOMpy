
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
 
#include <iostream>
#include <deque>
#include <boost/regex.hpp>
#include <genua/pattern.h>
#include <genua/ioglue.h>
#include "spline.h"
#include "naca6generator.h"
#include "airfoil.h"

using std::string;
using namespace boost;

/* ---------- Airfoil ----------------------------------------------------- */

void Airfoil::read(const std::string & fname, int nap)
{
  ifstream in(asPath(fname).c_str(), std::ios::binary);
  Airfoil::read(in, nap);
}

void Airfoil::read(istream & is, int nap)
{
  napx = nap;
  if (!is)
    throw Error("Invalid stream in Airfoil::read().");

  // regular expression for pairs of floats
  string rxfloat("([+-]?([0-9]*\\.?[0-9]+|[0-9]+\\.?[0-9]*)([eE][+-]?[0-9]+)?)");
  regex ftline("[[:space:]]*"+rxfloat+"[[:space:]]+"+rxfloat+"[[:space:]]*");
  smatch what;

  // scan lines for pairs of floats
  string line;
  std::deque<Real> fx,fy;
  while (getline(is,line)) {
    if (regex_match(line, what, ftline)) {
      fx.push_back( Float(what[1].str()) );
      fy.push_back( Float(what[4].str()) );
    }
  }

  if (fx.size() < 4)
    throw Error("Not enough coordinates found in this stream.");

  // sometimes, the number of cordinates is given as a float (Fortran...?)
  // detect this case and throw out the first pair of coordinates
  if (fx[0] + fy[0] == fx.size() - 1) {
    fx.pop_front();
    fy.pop_front();
  }

  crd.resize(fx.size());
  for (uint i=0; i<fx.size(); i++) {
    crd[i][0] = fx[i];
    crd[i][1] = fy[i];
  }

  // call sorting routine
  sortCoords();

  // default interpolation: set y-coordinate to zero (wings)
  rebuild();
}

Real Airfoil::findLeadingEdge(Real tol) const
{
  Real t(0.5), lo(0.4), hi(0.6), x;
  while (hi - lo > tol) {
    t = 0.5*(hi+lo);
    x = derive(t,1)[0];
    if (x > 0)
      hi = t;
    else if (x < 0)
      lo = t;
    else
      return t;
  }
  return t;
}

void Airfoil::renormalize()
{
  Real xmin = std::numeric_limits<Real>::max();
  Real xmax = -xmin;
  const int np = crd.size();
  for (int i=0; i<np; ++i) {
    xmin = std::min( crd[i][0], xmin );
    xmax = std::max( crd[i][0], xmax );
  }
  Real scale = 1.0 / (xmax - xmin);
  for (int i=0; i<np; ++i) {
    crd[i][0] -= xmin;
    crd[i] *= scale;
  }
}

void Airfoil::naca(int code, bool closed)
{
  // build NACA - 4digit wing section
  if (code < 1 or code > 9999)
    throw Error("No such NACA 4-digit section");

  Real camber = (code/1000)* 0.01;
  Real cpos = ((code%1000)/100) * 0.1;
  Real thick = (code%100) * 0.01;

  naca4(camber, cpos, thick, closed);
}

void Airfoil::naca4(Real camber, Real cpos, Real thick, bool closed)
{
  Real theta, yc, yt, x;

  const uint n(60);
  PointList<2> pgu(n/2), pgl(n/2);
  Vector t = cosine_pattern(n/2, 2*PI, 0.0, 0.8);

  for (uint i=0; i<n/2; i++) {
    x = t(i);
    if (closed)
      yt =
          5*thick*(0.2969*sqrt(x)-0.126*x-0.3516*sq(x)+0.2843*cb(x)-0.1036*pow(x,4));

    else
      yt =
          5*thick*(0.2969*sqrt(x)-0.126*x-0.3516*sq(x)+0.2843*cb(x)-0.1015*pow(x,4));

    if (x < cpos) {
      yc = camber/sq(cpos)* (2*cpos*x-sq(x));
      theta = atan(camber/sq(cpos)* (2*cpos-2*x));
    } else {
      yc = camber/sq(1-cpos)* (1-2*cpos+2*cpos*x-sq(x));
      theta = atan(camber/sq(1-cpos)* (2*cpos-2*x));
    }

    pgu[i][0] = x - yt* sin(theta);
    pgu[i][1] = yc + yt*cos(theta);
    pgl[i][0] = x + yt* sin(theta);
    pgl[i][1] = yc - yt*cos(theta);
  }

  crd.resize(2*(n/2)-1);
  for (uint i=0; i<n/2; i++) {
    crd[i] = pgu[n/2-1-i];
    crd[i+n/2-1] = pgl[i];
  }
  sortCoords();
  rebuild();
}

void Airfoil::naca5(int iMeanLine, Real dcl, Real thick, bool closed)
{
  Real theta, yc, ycd, yt, x;

  const uint n(60);
  PointList<2> pgu(n/2), pgl(n/2);
  Vector t = cosine_pattern(n/2, 2*PI, 0.0, 0.8);

  // camberline parameters
  const Real vm[] = {0.058, 0.126, 0.2025, 0.29, 0.391};
  const Real vk[] = {361.4, 51.64, 15.957, 6.643, 3.23};
  
  int idx = (iMeanLine - 210)/10;
  if (idx < 0 or idx > 4)
    throw Error("Invalid NACA5 mean-line.");
  
  Real m = vm[idx];
  Real k1 = vk[idx] * dcl/0.3;
  for (uint i=0; i<n/2; i++) {
    x = t(i);
    
    // thickness distribution is the same as NACA-4
    if (closed)
      yt = 5*thick*(0.2969*sqrt(x)-0.126*x
                    -0.3516*sq(x)+0.2843*cb(x)-0.1036*pow(x,4));

    else
      yt = 5*thick*(0.2969*sqrt(x)-0.126*x
                    -0.3516*sq(x)+0.2843*cb(x)-0.1015*pow(x,4));

    // changed camberline
    if (x < m) {
      yc = k1/6. *(cb(x) - 3*m*sq(x) + sq(m)*(3-m)*x);
      ycd = k1/6. *(3*sq(x) - 6*m*x + sq(m)*(3-m));
    } else {
      yc = k1/6. *cb(m)*(1 - x);
      ycd = -k1/6.*cb(m);
    }
    theta = atan(ycd);

    pgu[i][0] = x - yt* sin(theta);
    pgu[i][1] = yc + yt*cos(theta);
    pgl[i][0] = x + yt* sin(theta);
    pgl[i][1] = yc - yt*cos(theta);
  }

  crd.resize(2*(n/2)-1);
  for (uint i=0; i<n/2; i++) {
    crd[i] = pgu[n/2-1-i];
    crd[i+n/2-1] = pgl[i];
  }
  sortCoords();
  rebuild();
}

void Airfoil::naca16(Real tc, Real xtcmax, Real cli, bool closed)
{
  const int nxp = 101;
  Vector up(nxp);
  airfoil_pattern(nxp, 0.5, 1.2, 1.05, up);

  crd.resize(nxp);
  for (int i=0; i<nxp; ++i) {
    Real x = std::fabs( 1.0 - 2*up[i] );
    Real yt;
    if (x < xtcmax)
      yt = tc*( 0.989665*sqrt(x) - 0.239250*x
                - 0.041*sq(x) - 0.5594*cb(x) );
    else
      yt = tc*( 0.01 + 2.325*(1-x) - 3.42*sq(1-x) + 1.46*cb(1-x) );
    Real yc = 0.0;
    if ((x > 0.0) and (x < 1))
      yc = -0.079577*cli*( x*log(x) + (1-x)*log(1-x) );
    if (up[i] < 0.5)
      crd[i] = Vct2( x, yc+yt );
    else
      crd[i] = Vct2( x, yc-yt );
  }

  if (closed)
    closeTrailingEdge();
  rebuild();
}

int Airfoil::naca(int ifamily, int icamber, Real toc, Real cli, Real a)
{
  int r;
  Naca6Generator ng;
  r = ng.generate( ifamily, icamber, toc, cli, a );
  if (r < 0)
    return r;
  else if (r < 8)
    return NACA6_LIBFAILED;
  
  Vector x(r), y(r);
  ng.copyCoordinates( x.pointer(), y.pointer() );
  
  crd.clear();
  crd.push_back( vct(x[0], y[0]) );
  for (uint i=1; i<uint(r); ++i) {
    const Vct2 & last(crd.back());
    if ( fabs(x[i]-last[0]) > gmepsilon )
      crd.push_back(vct(x[i], y[i]));
  }
  renormalize();
  rebuild();
  
  Vector tpar;
  xpattern(75, 1.15, 1.08, tpar);
  reparametrize(tpar);
  
  return NACA6_SUCCESS;
}

int Airfoil::naca(int ifamily, int icamber, Real toc, 
                  const Vector & vcli, const Vector & va)
{
  assert(vcli.size() == va.size());
  
  const uint nml(vcli.size());
  if (nml > 10)
    return NACA6_TOOMANYLINES;
  
  int r;
  Naca6Generator ng;
  for (uint i=0; i<nml; ++i)
    ng.addMeanLine( vcli[i], va[i] );
  r = ng.generate(ifamily, icamber, toc);
  if (r < 0)
    return r;
  else if (r < 8)
    return NACA6_LIBFAILED;
  
  Vector x(r), y(r);
  ng.copyCoordinates( x.pointer(), y.pointer() );
  
  crd.clear();
  crd.push_back( vct(x[0], y[0]) );
  for (uint i=1; i<uint(r); ++i) {
    const Vct2 & last(crd.back());
    if ( fabs(x[i]-last[0]) > gmepsilon )
      crd.push_back(vct(x[i], y[i]));
  }

  renormalize();
  rebuild();
  
  Vector tpar;
  xpattern(75, 1.15, 1.08, tpar);
  reparametrize(tpar);
  
  return NACA6_SUCCESS;
}

void Airfoil::flatPlate(Real thick, int nap)
{
  const Real xtail(0.2);
  const Real dxflat(1.0 - xtail - 0.5*thick);
  const int ntail(16);
  const int nflat(80);
  const int nnose(49);
  
  Vector uflat = cosine_pattern(nflat, 4*PI, 0.0, 0.8);
  Real x, y, cphi, sphi;
  crd.clear();
  for (int i=0; i<ntail; ++i) {
    Real t = Real(i) / (ntail-1);
    x = 1.0 - t*xtail;
    y = 0.5*thick * (1.0 - sq(1.0 - t));
    crd.push_back(vct(x,y));
  }
  for (int i=1; i<nflat; ++i) {
    Real t = uflat[i];
    x = (1.0 - xtail) - t*dxflat;
    y = 0.5*thick;
    crd.push_back(vct(x,y));
  }
  for (int i=1; i<nnose; ++i) {
    Real t = Real(i) / (nnose - 1);
    sincosine(t*PI, sphi, cphi);
    x = 0.5*thick*(1 - sphi);
    y = 0.5*thick*cphi;
    crd.push_back(vct(x,y));
  }
  for (int i=1; i<nflat; ++i) {
    Real t = uflat[i];
    x = 0.5*thick + dxflat*t;
    y = -0.5*thick;
    crd.push_back(vct(x,y));
  }
  for (int i=1; i<ntail; ++i) {
    Real t = Real(i) / (ntail-1);
    x = 0.5*thick + dxflat + xtail*t;
    y = -0.5*thick*(1.0 - sq(t));
    crd.push_back(vct(x,y));
  }
  
  napx = nap;
  sortCoords();
  rebuild();
}

void Airfoil::sortCoords()
{
  // sort coordinates read by Airfoil::read()

  // first: normalize everything by the largest x-coordinate
  double xmax(-1e18);
  for (uint i=0; i<crd.size(); i++)
    xmax = std::max(xmax, crd[i][0]);

  crd *= (1./xmax);

  // if the largest chordwise distance between two consecutive coordinates
  // is larger than 0.5, we assume to have seliger coordinate format,
  // otherwise lednicer's format
  uint brkidx = crd.size();
  for (uint i=1; i<crd.size(); i++) {
    if ( fabs(crd[i][0] - crd[i-1][0]) > 0.5) {
      brkidx = i;
      break;
    }
  }

  // reorder coordinates if necessary
  if (brkidx != crd.size()) {
    PointList<2> tmp = crd;

    // if the first coordinates are in correct direction, turn around the
    // second half (lower side)
    if (crd[0][0] > crd[1][0]) {
      for (uint i=brkidx; i<crd.size(); i++)
        crd[i] = tmp[tmp.size()-1+brkidx-i];
    } else {
      for (uint i=0; i<brkidx; i++)
        crd[i] = tmp[brkidx-1-i];
    }
  }

  // now, remove double coordinates
  std::vector<Vct2> tmp;
  tmp.push_back(crd[0]);
  for (uint i=1; i<crd.size(); i++) {
    if ( norm(crd[i]-tmp.back()) > gmepsilon)
      tmp.push_back(crd[i]);
  }
  crd.resize(tmp.size());
  std::copy(tmp.begin(), tmp.end(), crd.begin());

  // now, we'd like to make sure that the coordinates are ordered in the
  // right direction... how to do that?
}

void Airfoil::rebuild()
{
  // construct 3D points
  const uint np( crd.size() );
  PointList<3> ipts(np);
  for (uint i=0; i<np; ++i)
    ipts[i] = vct(crd[i][0], 0.0, crd[i][1]);
  
  if (napx > 0 and napx < 5)
    throw Error("Need more control points for approximation.");

  // start with full interpolation
  OpenFrame::init(ipts);
  if (napx <= 0 or uint(napx+2) >= np)
    return;
  
  // at this point, we have an airfoil interpolating all points in crd,
  // which we'll use to generate a sensible parametrization
  Vector up(napx);
  // adaptiveParam(napx, up);
  airfoil_pattern(napx, 0.5, 1.2, 1.1, up);

  // determine arc-length parametrization of crd
  Vector alp(np);
  for (uint i=1; i<np; ++i)
    alp[i] = alp[i-1] + norm(crd[i] - crd[i-1]);
  alp /= alp.back();

  // add points in the up parametrisation in order to fill in
  alp.insert(alp.end(), up.begin(), up.end());
  std::sort(alp.begin(), alp.end());
  alp.erase( std::unique(alp.begin(), alp.end(), almost_equal<Real>(1e-5)),
             alp.end());
  const uint nipp = alp.size();

  // spline basis for approximation
  Curve::bas.init(3, up);

  Spline<2> spl;
  spl.interpolate(crd, 1);
  
  // find control points by least-squares approximation
  Vct4 b;
  Matrix cf(nipp, napx);
  Matrix rhs(nipp,3);
  uint span;
  for (uint i=0; i<nipp; ++i) {
    span = Curve::bas.eval(alp[i], b);
    for (uint k=0; k<4; ++k)
      cf(i, span-3+k) = b[k];
    Vct2 pt = spl.eval(alp[i]);
    rhs(i, 0) = pt[0];
    rhs(i, 2) = pt[1];
  }
  svd_solve(cf, rhs, 1e-6);

  Curve::cp.resize(napx);
  for (uint i=0; i<uint(napx); ++i)
    for (uint k=0; k<3; ++k)
      Curve::cp[i][k] = rhs(i,k);
}

void Airfoil::closeTrailingEdge(Real gap)
{
  // set up a line through nose and TE-midpoint and rotate
  // both upper and lower coordinates around nose so much that TE is closed.
  uint pi(0);
  Vct2 pivot = point(1e18,1e18);
  for (uint i=0; i<crd.size(); i++) {
    if (crd[i][0] < pivot[0]) {
      pivot = crd[i];
      pi = i;
    }
  }

  Vct2 tetip = 0.5*(crd.front() + crd.back());
  Vct2 updiff( tetip - crd.front() + vct(0.0, 0.5*gap) );
  Vct2 lodiff( tetip - crd.back() - vct(0.0, 0.5*gap) );
  double t;

  // process upper side
  for (uint i=0; i<pi; i++) {
    t = (crd[i][0]-pivot[0]) / (tetip[0]-pivot[0]);
    crd[i] += t* updiff;
  }

  // process lower side
  for (uint i=pi+1; i<crd.size(); i++) {
    t = (crd[i][0]-pivot[0]) / (tetip[0]-pivot[0]);
    crd[i] += t* lodiff;
  }
  rebuild();
}

void Airfoil::extend(Real dxNose, Real dyNose, Real dxTail, Real dyTail)
{
  // find the point with highest z-value
  const uint np = crd.size();
  Real zmax = -std::numeric_limits<Real>::max();
  uint izmax = NotFound;
  for (uint i=0; i<np; ++i) {
    Real z = crd[i][1];
    if (z > zmax) {
      zmax = z;
      izmax = i;
    }
  }
  assert(izmax != NotFound);

  // points ahead of this one will be stretched
  // forward linearly and upward quadratically
  const Real xzmax = crd[izmax][0];
  for (uint i=0; i<np; ++i) {
    Vct2 &p(crd[i]);
    Real t = (xzmax - p[0])/xzmax;
    if (t > 0.0) {
      p[0] -= t*dxNose;
      p[1] += sq(t)*dyNose;
    }
    t = (p[0] - xzmax)/(1.0 - xzmax);
    if (t > 0.0) {
      p[0] += t*dxTail;
      p[1] += sq(t)*dyTail;
    }
  }

  rebuild();
}

void Airfoil::chop(Real xcut)
{
  Real xp, x, xn, t;
  PointList<2> tmp;
  for (uint i=0; i<crd.size(); ++i) {
    x = crd[i][0];
    if (x < xcut) {
      
      // find first point on reduced section
      if (i > 0 and crd[i-1][0] > xcut) {
        xp = crd[i-1][0];
        t = (xp - xcut) / (xp - x);
        tmp.push_back( (1-t)*crd[i-1] + t*crd[i] );
      }
      
      tmp.push_back(crd[i]);
      
      // find last point on reduced section
      if (i < crd.size()-1 and crd[i+1][0] > xcut) {
        xn = crd[i+1][0];
        t = (xcut - x) / (xn - x);
        tmp.push_back( (1-t)*crd[i] + t*crd[i+1]);
      }
      
    }
  }
  tmp.swap(crd);
  rebuild();
}

Real Airfoil::parameter(Real x, Real start) const
{
  // find parameter value for given x/c value

  Real t, lo, hi, miss;

  Spline<2> sp;
  sp.interpolate(crd,2);

  lo = std::max(0., 0.8*start);
  hi = std::min(1., 1.25*start);
  t = 0.5* (lo+hi);
  miss = sp.eval(t)[0] - x;

  if (start < 0.5) {
    while ( fabs(miss) > 1e-4 ) {
      if (miss > 0)
        lo = t;
      else
        hi = t;
      t = 0.5*(lo+hi);
      miss = sp.eval(t)[0] - x;
    }
  } else {
    while ( fabs(miss) > 1e-4 ) {
      if (miss > 0)
        hi = t;
      else
        lo = t;
      t = 0.5*(lo+hi);
      miss = sp.eval(t)[0] - x;
    }
  }

  return t;
}

void Airfoil::adaptiveParam(size_t na, Vector &ua) const
{
  // initialize ua by allocating na/2 points to equidistant spacing
  size_t nap = std::max(size_t(20), na/2);
  ua = equi_pattern(nap, 0.0, 1.0);

  // start by inserting nodes in segments where local kink angle is > 45deg
  Real climit = cos(rad(45.));

  // permitted distance between interpolated chord and midpoint
  Real maxchord = 0.001 * norm(eval(0.5) - eval(0.0));

  // number of smoothing iterations to run inside each refinement sweep
  const size_t nsm = 2;

  Vct3 pa, pb, tga, tgb;
  while (nap < na) {

    // insert points where angle between tangents is too large
    tgline(ua[0], pa, tga);
    for (size_t i=1; i<nap; ++i) {
      Real umid = 0.5*(ua[i-1] + ua[i]);
      tgline(ua[i], pb, tgb);
      Vct3 pmid = eval(umid);
      Vct3 lpm = 0.5*(pa + pb);
      if ( cosarg(tga, tgb) < climit or
           norm(pmid - lpm) > maxchord)
        ua.push_back( umid );
      tga = tgb;
      pa = pb;

      // limit insertions to prescribed maximum
      if (ua.size() == na)
        break;
    }

    // if no points were inserted, reduce the criterion and repeat'
    // limit = 45, 32.8, 23.5, 16.7, ...
    if (ua.size() == nap) {
      climit = std::sqrt(climit);
      maxchord *= 0.5;
      continue;
    }

    // inserted points are already sorted, just merge ranges
    std::inplace_merge(ua.begin(), ua.begin()+nap, ua.end());

    // if any points were inserted, smooth parameter distribution a little
    // in order to avoid too large differences between segment sizes
    nap = ua.size();
    for (size_t j=0; j<nsm; ++j) {
      for (size_t i=1; i<nap-1; ++i)
        ua[i] = 0.5*ua[i] + 0.25*(ua[i-1] + ua[i+1]);
      for (size_t i=(nap-2); i>=1; --i)
        ua[i] = 0.5*ua[i] + 0.25*(ua[i-1] + ua[i+1]);
    }
  }
}

void Airfoil::xpattern(uint nps, Real xle, Real xte, Vector & t) const
{
  airfoil_pattern(nps, findLeadingEdge(1e-6), xle, xte, t);
}

void Airfoil::reparametrize(const Vector & t)
{
  Spline<2> spl;
  spl.interpolate(crd);
  
  const int n = t.size();
  crd.resize(n);
  for (int i=0; i<n; ++i)
    crd[i] = spl.eval(t[i]);
  
  rebuild();
}

void Airfoil::approximate(int n)
{
  napx = n;
  rebuild();
}

void Airfoil::write(ostream & os, string hdr) const
{
  // write (with header)
  os.precision(14);
  os << std::scientific;
  if (hdr.size() > 1)
    os << hdr;
  for (uint i=0; i<crd.size(); i++) {
    os << "  " << crd[i][0] << "  " << crd[i][1] << endl;
  }
}

XmlElement Airfoil::toXml(bool) const
{
  XmlElement xe("Airfoil");
  xe.attribute("name") = ids;
  
  if (napx != -1)
    xe["napx"] = str(napx);
  
  XmlElement xc("Coordinates");
  xc.attribute("pcount") = str(crd.size());

  std::stringstream ss;
  ss.precision(16);
  for (uint i=0; i<crd.size(); ++i)
    ss << crd[i] << endl;
  xc.text() = ss.str();
  
  xe.append(std::move(xc));
  xe.append(Curve::trafoToXml());
  
  return xe;
}

void Airfoil::fromXml(const XmlElement & xe)
{
  if (xe.name() != "Airfoil")
    throw Error("Incompatible XML representation for Airfoil.");

  rename(xe.attribute("name"));
  napx = xe.attr2int("napx", -1);
  
  //   XmlElement::const_iterator itr;
  //   itr = xe.findChild("Coordinates");
  //   if (itr == xe.end()) {
  //     if (xe.hasAttribute("naca")) {
  //       int ncode = Int(xe.attribute("naca"));
  //       this->naca(ncode, true);
  //     } else if (xe.hasAttribute("file")) {
  //       this->read(xe.attribute("file"));
  //     } else
  //       throw Error("Airfoil xml representation must contain coordinates, filename or NACA 4-digit code.");
  //   } else {
  //
  //     // have coordinate list - read interpolation points
  //     Vct2 pt;
  //     crd.clear();
  //     stringstream ss(itr->text());
  //     while (ss >> pt)
  //       crd.push_back(pt);
  //
  //     rebuild();
  //     // closeTrailingEdge();
  //   }
  
  // try to construct airfoil from spec if present
  crd.clear();
  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    if (itr->name() == "NACA6") {
      int ifamily = itr->attr2int("family", 64);
      int icamber = itr->attr2int("camberline", 64);
      Real toc = itr->attr2float("thickness", 0.15);
      Real cli = itr->attr2float("design_cl", 0.4);
      Real a = itr->attr2float("a", 1.0);
      naca(ifamily, icamber, toc, cli, a);
      break;
    } else if (itr->name() == "NACA5") {
      int imeanline = itr->attr2int("meanline", 230);
      Real dcl = itr->attr2float("design_cl", 0.3);
      Real toc = itr->attr2float("thickness", 0.15);
      naca5(imeanline, dcl, toc);
      break;
    } else if (itr->name() == "NACA4") {
      Real camber = itr->attr2float("camber", 0.02);
      Real cpos = itr->attr2float("camber_pos", 0.3);
      Real toc = itr->attr2float("thickness", 0.15);
      naca4(camber, cpos, toc);
      break;
    } else if (itr->name() == "RoundedPlate") {
      Real toc = itr->attr2float("thickness", 0.02);
      flatPlate(toc, napx);
      break;
    } else if (itr->name() == "Coordinates") {
      // have coordinate list - read interpolation points
      Vct2 pt;
      std::stringstream ss(itr->text());
      while (ss >> pt)
        crd.push_back(pt);
      rebuild();
      break;
    }
  }
  
  // support old files
  if (crd.empty()) {
    if (xe.hasAttribute("naca")) {
      int ncode = Int(xe.attribute("naca"));
      this->naca(ncode, true);
    } else if (xe.hasAttribute("file")) {
      this->read(xe.attribute("file"));
    } else {
      throw Error("Airfoil tag does not contain a valid coordinate definition.");
    }
  }
  
  itr = xe.findChild("TrafoSequence");
  if (itr != xe.end())
    Curve::applyFromXml(*itr);
}

Airfoil *Airfoil::clone() const
{
  return new Airfoil(*this);
}

std::string Airfoil::naca6name(int ifamily, Real toc, Real cli)
{
  // assemble NACA 6 designation
  std::stringstream ss;
  ss << "NACA ";
  ss << std::fixed;
  ss.precision(2);

  if (ifamily < 100)
    ss << ifamily << "-";
  else
    ss << ifamily-100 <<  "A";
  
  int icli = int(std::round(cli*10.0));
  if ( Real(icli) == 10.0*cli )
    ss << icli;
  else
    ss << "(" << cli << ")";
  
  int itoc = int(100.0*toc);
  if ( fabs(Real(itoc) - 100.0*toc) < 0.001) {
    if (itoc > 9)
      ss << itoc;
    else
      ss << "0" << itoc;
  } else
    ss << "(" << 100.0*toc << ")";

  return ss.str();
}

std::string Airfoil::naca5name(int iMeanLine, Real dcl, Real thick)
{
  string id = "NACA ";
  int ic = int(std::round((iMeanLine/100) * (dcl/0.3)));
  int cp = iMeanLine - 200;
  id += str(100*ic + cp);
  id += str(int(std::round(100*thick)));
  return id;
}

std::string Airfoil::naca4name(Real camber, Real cpos, Real thick)
{
  string id = "NACA ";
  int ic = uint(std::round(100*camber));
  int cp = uint(std::round(10*cpos));
  
  if (camber == 0.0) {
    id += "00";
  } else {
    id += str(ic) + str(cp);
  }
  
  int ct = uint(std::round(100 * thick));
  if (ct == 0 and thick != 0)
    id += "-" + str( int(100*thick) );
  else
    id += str(ct);
  return id;
}

std::string Airfoil::searchCoordName(const std::string & fname)
{
  const string nmrc("-+01234567890eE., \t\r");
  const string akey("# airfoil: ");
  const string fkey("# filename: ");
  string line;
  string::size_type pos;
  ifstream in(asPath(fname).c_str(), std::ios::binary);
  while ( getline(in,line) ) {
    line = strip(line);
    if (not line.empty()) {
      if (line.substr(0, fkey.length()) == fkey) {
        continue;
      } else if (line.substr(0, akey.length()) == akey) {
        return strip(line.substr(akey.length(), line.length()));
      } else if (line[0] == '#' or line[0] == '%') {
        return strip(line.substr(1));
      } else {
        pos = line.find_first_not_of(nmrc);
        if (pos != string::npos)
          return line;
      }
    }
  }
  
  return string("");
}
