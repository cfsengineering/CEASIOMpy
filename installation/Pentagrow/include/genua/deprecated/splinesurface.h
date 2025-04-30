
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       splinesurface.h
 * begin:      Sun Feb 25 2001
 * copyright:  (c) 2001 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * spline surface
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#ifndef _GENUA_SPLINESURFACE_H
#define _GENUA_SPLINESURFACE_H

#include <set>
#include <vector>

#include "pattern.h"
#include "xmlelement.h"
#include "point.h"
#include "spline.h"

/** B-Spline Surface.

  A parametric piecewise polynomial surface of arbitrary degree, the
  two-parametric equivalent of nurb curves.

  */
template <uint N>
class SplineSurf
{
  public:

    /// empty construction
    SplineSurf() {};

    // construction
    SplineSurf(const PointGrid<N> & cp, int udeg, int vdeg,
               const Vector & uk, const Vector & vk) : ctlpoints(cp),
                ubas(udeg,uk), vbas(vdeg,vk)
      {
        if (cp.nrows() != uk.size()-udeg-1)
          throw InvalidArg("Control net and knot vector incompatible (u).");

        if (cp.ncols() != vk.size()-vdeg-1)
          throw InvalidArg("Control net and knot vector incompatible (v).");
      }

    /// return controlpoints
    const PointGrid<N> & getCp() const
      {return ctlpoints;}

    /// return degree (u)
    uint udegree() const
      {return ubas.degree();}

    /// return degree (v)
    uint vdegree() const
      {return vbas.degree();}

    /// return u knot vector
    const Vector & uKnots() const
      {return ubas.getKnots();}
      
    /// return v knot vector
    const Vector & vKnots() const
      {return vbas.getKnots();}

    /// evaluation
    SVector<N> eval(Real u, Real v) const
      {
        // return the point at (u,v)
        SVector<N> pt;

        uint i,j, uspan, vspan;
        uspan = ubas.findSpan(u);
        vspan = vbas.findSpan(v);

        for (i = uspan-udegree(); i <= uspan; i++)
          for (j = vspan-vdegree(); j <= vspan; j++)
            pt += ubas.eval(i,u) * ctlpoints(i,j) * vbas.eval(j,v);

        return pt;
      }

    /// derivation (ku times in u, kv times in v direction)
    SVector<N> derive(Real u, Real v, int ku, int kv) const
      {
        // derivation 'on the edge' doesn't work
        if (u < gmepsilon) u = gmepsilon;
        if (u > 1-gmepsilon) u = 1-gmepsilon;
        if (v < gmepsilon) v = gmepsilon;
        if (v > 1-gmepsilon) v = 1-gmepsilon;
        SVector<N> pt;
        uint uspan, vspan;
        uspan = ubas.findSpan(u);
        vspan = vbas.findSpan(v);

        for (uint i = uspan-udegree(); i <= uspan; i++)
          for (uint j = vspan-vdegree(); j <= vspan; j++)
            pt += ubas.derive(i,u,ku) * ctlpoints(i,j) * vbas.derive(j,v,kv);

        return pt;
      }

    /// interpolate over set of splines with knot vector vk
    void interpolate(const std::vector<Spline<N> > & sec, const Vector & vk,
       uint vdeg=3);

    /// interpolate grid of points
    void interpolate(const PointGrid<N> & pts, uint udeg=3, uint vdeg=3);

    /// return a section curve running in u-direction
    Spline<N> ucut(Real v) const;

    /// return a section curve running in v-direction
    Spline<N> vcut(Real u) const;

    /// return xml representation
    XmlElement toXml() const {
      const Vector & uk(ubas.getKnots());
      const Vector & vk(vbas.getKnots());
      XmlElement xe("SplineSurf");
      xe["uknots"] = str(uk.size());
      xe["vknots"] = str(vk.size());
      xe["udegree"] = str(ubas.degree());
      xe["vdegree"] = str(vbas.degree());

      std::stringstream ss;
      XmlElement xuk("UKnots");
      for (uint i=0; i<uk.size(); ++i)
        ss << uk[i] << std::endl;
      xuk.text() = ss.str();
      ss.clear();

      XmlElement xvk("VKnots");
      for (uint i=0; i<vk.size(); ++i)
        ss << vk[i] << std::endl;
      xvk.text() = ss.str();
      ss.clear();

      xe.append(xuk);
      xe.append(xvk);
      xe.append(ctlpoints.toXml());
      return xe;
    }

    void fromXml(const XmlElement & xe) {
      assert(xe.name() == "SplineSurf");
      uint nuk, nvk, udg, vdg;
      nuk = Int( xe.attribute("uknots") );
      nvk = Int( xe.attribute("vknots") );
      udeg = Int( xe.attribute("udegree") );
      vdeg = Int( xe.attribute("vdegree") );

      Vector uk(nuk), vk(nvk);
      XmlElement::const_iterator itr;
      itr = xe.findChild("UKnots");
      assert(itr != xe.end());
      std::stringstream ss;
      ss << itr->text();
      for (uint i=0; i<nuk; ++i)
        ss >> uk[i];
      ubas = SplineBasis(udeg, uk);
      ss.clear();

      itr = xe.findChild("VKnots");
      assert(itr != xe.end());
      ss << itr->text();
      for (uint i=0; i<nvk; ++i)
        ss >> vk[i];
      vbas = SplineBasis(vdeg, vk);
      ss.clear();

      itr = xe.findChild("ControlPoints");
      assert(itr != xe.end());
      ctlpoints.fromXml(*itr);
    }

    /// obtain approximate v-parameter vector (along columns)
    Vector vparametrize(const PointGrid<N> & pts) const;

    /// obtain approximate u-parameter vector (along rows)
    Vector uparametrize(const PointGrid<N> & pts) const;

  private:

    /// control net
    PointGrid<N> ctlpoints;

    /// two knot vectors for two parameters
    SplineBasis ubas,vbas;

};

/* ----------- Implementation -------------------------------------------------------- */

// 'fuzzy' comparison object -- helper struct

namespace {

struct num_less
{
  num_less(Real e=gmepsilon) : eps(e) {};

  bool operator() (Real a, Real b)
    {
      if ( (b-a) > eps)
        return true;
      else
        return false;
    }

  Real eps;
};

} // local namespace

template <uint N>
void SplineSurf<N>::interpolate(const std::vector<Spline<N> > & sec,
                                const Vector & vk, uint vdeg)
{
  // interpolate set of splines
  if (vdeg >= sec.size())
    throw InvalidArg("v-degree >= number of sections.");

  std::vector<Spline<N> > skel(sec);

  // merge knot vectors
  typename std::vector<Spline<N> >::iterator itr;
  std::multiset<Real> uk, tmp, common;
  Vector ukvec;
  uint udeg(1);

  // find highest degree
  udeg = 1;
  for (itr = skel.begin(); itr != skel.end(); itr++)
    udeg = max(udeg, itr->degree() );

  for (itr = skel.begin(); itr != skel.end(); itr++)
    {
      // elevate degree
      if (itr->degree() < udeg)
        itr->elevateDegree(udeg);

      // copy knot vector into multiset
      ukvec = itr->getKnots();
      uk.clear();
      std::copy(ukvec.begin(), ukvec.end(), inserter(uk, uk.begin()));

      // build union of tmp and uk -- tmp is necessary because input and output
      // of set_union must not overlap
      common.clear();
      std::set_union(uk.begin(), uk.end(), tmp.begin(), tmp.end(),
                    inserter(common, common.begin()), num_less(1e-6) );

      tmp.clear();
      // copy common to tmp
      std::copy(common.begin(), common.end(), inserter(tmp, tmp.begin()) );
    }

  // common now contains the unified knot vector
  Vector uknots;
  uknots.resize(common.size());
  std::copy(common.begin(), common.end(), uknots.begin());
  ubas = SplineBasis(udeg,uknots);

  for (itr = skel.begin(); itr != skel.end(); itr++)
    itr->adaptKnots(uknots);

  // v-direction basis
  vbas = SplineBasis(vdeg,vk);

//  // control points
//  ctlpoints.resize(uknots.size()-udeg-1, skel.size());
//  PointGrid<N> secpts;
//  uint i,j;
//  for (j=0; j<ctlpoints.ncols(); j++)
//    {
//      secpts = skel[j].getCp();
//      for (i=0; i<ctlpoints.nrows(); i++)
//        ctlpoints(i,j) = secpts[i];
//    }

  // to obtain surface controlpoints, interpolate curves through
  // section controlpoints in v-direction

  uint nu = uknots.size()-udeg-1;
  PointGrid<N> cpg(nu, skel.size());
  for (uint j=0; j<skel.size(); j++)
    for (uint i=0; i<nu; i++)
      cpg(i,j) = skel[j].getCp()[j];
  
  Vector vp = vparametrize(cpg);
  Matrix cf(vp.size(),vp.size()), rhs(vp.size(),N);
  for (uint i=0; i<vp.size(); i++) {
    int span = vbas.findSpan(vp(i));
    for (int j=span-vdeg; j<=span; j++)
      cf(i,j) = vbas.eval(j,vp(i));
  }
  DVector<int> ip = lu_factor(cf);

  
  PointGrid<N> vl(skel.size()), qg(skel.size());
  ctlpoints.resize(nu, skel.size());
  for (uint i=0; i<nu; i++) {
    for (uint j=0; j<skel.size(); j++)
      vl[j] = skel[j].getCp()[i];
    rhs = vl.toMatrix();
    lu_solve(cf, ip, rhs);
    qg.fromMatrix(rhs);
    for (uint j=0; j<skel.size(); j++)
      ctlpoints(i,j) = qg[j];
  }
}

template <uint N>
void SplineSurf<N>::interpolate(const PointGrid<N> & pts, uint udeg, uint vdeg)
{
  // interpolate using averaged parametrization UNTESTED!
  uint m,n;
  m = pts.nrows();
  n = pts.ncols();

  if (m < udeg+1)
    throw InvalidArg("Not enough points in u-direction.");
  if (n < vdeg+1)
    throw InvalidArg("Not enough points in v-direction.");

  // compute average parameters
  Vector up(m), vp(n);
  up = uparametrize(pts);
  vp = vparametrize(pts);

  // produce knots using averaging
  Vector uk(m+udeg+1), vk(n+vdeg+1);
  for (uint j=1; j<=m-udeg-1; j++)
    for (uint i=j; i<=j+udeg-1; i++)
      uk(j+udeg) += 1./udeg * up(i);

  for (uint i=0; i<udeg+1; i++)
    uk(m+udeg-i) = 1.0;

  for (uint j=1; j<=n-vdeg-1; j++)
    for (uint i=j; i<=j+vdeg-1; i++)
      vk(j+vdeg) += 1./vdeg * vp(i);

  for (uint i=0; i<vdeg+1; i++)
    vk(n+vdeg-i) = 1.0;

  ubas = SplineBasis(udeg, uk);
  vbas = SplineBasis(vdeg, vk);

  // solve for control points  
  Matrix a(m,m);
  for (uint i=0; i<up.size(); i++) {
    int span = ubas.findSpan(up(i));
    for (int j=span-udeg; j<=span; j++)
      a(i,j) = ubas.eval(j,up(i));
  }
  
  DVector<int> ip = lu_factor(a);

  // interpolate along u
  PointGrid<N> ccp(m,n);
  for (uint j=0; j<n; j++) {
    Matrix rhs(m,N);
    for (uint i=0; i<m; i++)
      for (uint k=0; k<N; k++)
        rhs(i,k) = pts(i,j)[k];
    lu_solve(a,ip,rhs);
    for (uint i=0; i<m; i++)
      for (uint k=0; k<N; k++)
        ccp(i,j)[k] = rhs(i,k);
  }

  a.clear();
  a.resize(n,n);  
  for (uint i=0; i<vp.size(); i++) {
    int span = vbas.findSpan(vp(i));
    for (int j=span-vdeg; j<=span; j++)
      a(i,j) = vbas.eval(j,vp(i));
  }
  ip = lu_factor(a);

  // interpolate along v
  ctlpoints.resize(m,n);
  for (uint i=0; i<m; i++) {
    Matrix rhs(n,N);
    for (uint j=0; j<n; j++)
      for (uint k=0; k<N; k++)
        rhs(j,k) = ccp(i,j)[k];
    lu_solve(a,ip,rhs);
    for (uint j=0; j<n; j++)
      for (uint k=0; k<N; k++)
        ctlpoints(i,j)[k] = rhs(j,k);            
  }
}

template <uint N>
Spline<N> SplineSurf<N>::ucut(Real v) const
{
  // cut the surface at constant v, return the section curve
  PointGrid<N> secCp(ctlpoints.nrows());

  uint vspan = vbas.findSpan(v);
  for (uint i = vspan-vdegree(); i <= vspan; i++)
    for (uint j = 0; j < ctlpoints.nrows(); j++)
      secCp[j] += ctlpoints(j,i) * vbas.eval(i,v);

  Spline<N> sect(ubas.getKnots(), secCp, udegree());
  return sect;
}

template <uint N>
Spline<N> SplineSurf<N>::vcut(Real u) const
{
  // cut the surface at constant u, return the section curve
  PointGrid<N> secCp(ctlpoints.ncols());

  uint uspan = ubas.findSpan(u);
  for (uint i = uspan-udegree(); i <= uspan; i++)
    for (uint j = 0; j < ctlpoints.ncols(); j++)
      secCp[j] += ctlpoints(i,j) * ubas.eval(i,u);

  Spline<N> sect(vbas.getKnots(), secCp, vdegree());
  return sect;
}

template <uint N>
Vector SplineSurf<N>::vparametrize(const PointGrid<N> & pts) const
{
  // compute v-parametrization (along columns)
  PointList<N> q;
  for (uint j=0; j<pts.ncols(); j++) {
    Real sl, len(0);
    SVector<N> ctr;
    for (uint i=1; i<pts.nrows(); i++) {
      sl = norm(pts(i,j)-pts(i-1,j));
      len += sl;
      ctr += 0.5*sl*(pts(i,j)+pts(i-1,j));
    }
    if (len > 0)
      q.push_back(ctr/len);
    else
      q.push_back(pts(0,j));    
  }
  Vector u(q.size());
  for (uint i=1; i<q.size(); i++)
    u[i] = u[i-1] + norm(q[i]-q[i-1]);
  u /= u[u.size()-1];
  return u;
}

template <uint N>
Vector SplineSurf<N>::uparametrize(const PointGrid<N> & pts) const
{
  // compute u-parametrization (along rows)
  PointList<N> q;
  for (uint i=0; i<pts.nrows(); i++) {
    Real sl, len(0);
    SVector<N> ctr;
    for (uint j=1; j<pts.ncols(); j++) {
      sl = norm(pts(i,j)-pts(i,j-1));
      len += sl;
      ctr += 0.5*sl*(pts(i,j)+pts(i,j-1));
    }
    if (len > 0)
      q.push_back(ctr/len);
    else
      q.push_back(pts(i,0));
  }
  Vector u(q.size());
  for (uint i=1; i<q.size(); i++)
    u[i] = u[i-1] + norm(q[i]-q[i-1]);
  u /= u[u.size()-1];
  return u;
}

/* ----------- Functions ------------------------------------------------------------- */

/// output operator for SplineSurf (xml)
template <uint N>
ostream & operator<<(ostream & os, const SplineSurf<N> & spl)
  { return spl.writeXML(os); }

/// input operator for SplineSurf (xml)
template <uint N>
istream & operator>>(istream & is, SplineSurf<N> & spl)
  { return spl.readXML(os); }

#endif

