
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       spline.h
 * begin:      Thu Feb 17 2000
 * copyright:  (c) 2000 by <david.eller@studserv.uni-stuttgart.de>
 * ------------------------------------------------------------------------
 * Spline classes
 *   templatized nov 2000
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#ifndef SURF_SPLINE_H
#define SURF_SPLINE_H

#include <iostream>

#include <genua/defines.h>
#include <genua/lapack.h>
#include <genua/point.h>
#include <genua/splinebasis.h>
#include <genua/xmlelement.h>

// curve characterisctic
//enum CurveClosure {undefined, open, closed, contin, smooth};

/** Non-uniform rational B-Spline.

  */
template <uint N>
class Spline
{
  public:

    /// default constructor
    Spline() {};

    /// build from knot vector and control point matrix
    Spline(const Vector & knots, const PointGrid<N> & cp, int deg=3)
            : bas(deg,knots), ctlpoints(cp) {
        // controlpoints P_0...P_n
        uint n = ctlpoints.size() - 1;
        closed = false;

        if (n != knots.size() - deg - 2)
          throw Error("Knot vector and control points incompatible.");
      }

    /// return knot vector
    const Vector & getKnots() const
      {return bas.getKnots();}

    /// return control polygon
    const PointGrid<N> & getCp() const
      {return ctlpoints;}

    /// return degree
    uint degree() const
      {return bas.degree();}

    /// evaluate curve at parameter value t
    SVector<N> eval(Real t) const {
        // compute curve value/vector for parameter t
        SVector<N> pt;
        int i, span;
        span = bas.findSpan(t);
        for (i=span-degree(); i<=span; i++)
          pt += bas.eval(i,t) * ctlpoints[i];
        return pt;
      }

    /// derive spline dv times at t
    SVector<N, Real> derive(Real t, int dv=1) const {
        // derive spline k times at t
        if (t < gmepsilon)
          t = gmepsilon;
        if (t > 1-gmepsilon)
          t = 1-gmepsilon;
        SVector<N> pt;
        int i, span;
        span = bas.findSpan(t);
        for (i=span-degree(); i<=span; i++)
          pt += bas.derive(i,t,dv) * ctlpoints[i];
        return pt;
      }

    /// adapt to new knot vector
    void adaptKnots(const Vector & nKnots);

    /// degree elevation
    void elevateDegree(uint newdeg);

    /// project point on curve, return parameter
    Real project(const SVector<N> & pt, Real tolerance = 1e-3) const;

    /// interpolate set of points without further constraints
    Vector interpolate(const PointGrid<N> & a, uint deg=3);

    /// interpolate set of points without further constraints
    Vector interpolate(const PointList<N> & a, uint deg=3);

    /// interpolate set of points with prescribed parameter vector
    Vector interpolate(const PointList<N> & a, const Vector & up, uint deg=3);
    
    /// approximate set of points with prescribed parameter vector
    void approximate(const PointList<N> & a, const Vector & up, uint deg=3);

    /// create a straight segment between a and b
    void line(const SVector<N> & a, const SVector<N> & b) {
        PointGrid<N> pg(2);
        pg[0] = a; pg[1] = b;
        interpolate(pg,1);
      }

    /// reverse direction
    void reverse()
      {
        // reverse direction
        Real first, last;
        Vector knots = bas.getKnots();

        first = knots[0];
        last = knots[knots.size()-1];
        Vector::iterator itr;

        for (itr = knots.begin(); itr != knots.end(); itr++)
          *itr = first + last - *itr;

        std::reverse(knots.begin(), knots.end());
        std::reverse(ctlpoints.begin(), ctlpoints.end());
        bas.setKnots(knots);
      }

    /// return xml representation
    XmlElement toXml() const {
      const Vector & k(bas.getKnots());
      XmlElement xe("Spline");
      xe["knots"] = str(k.size());
      xe["degree"] = str(bas.degree());

      std::stringstream ss;
      XmlElement xv("Knots");
      for (uint i=0; i<k.size(); ++i)
        ss << k[i] << std::endl;
      xv.text() = ss.str();

      std::stringstream st;
      XmlElement xc("ControlPoints");
      for (uint i=0; i<ctlpoints.size(); ++i)
        st << ctlpoints[i] << std::endl;
      xc.text() = st.str();

      xe.append(xv);
      xe.append(xc);
      xe.append(ctlpoints.toXml());
      return xe;
    }

    void fromXml(const XmlElement & xe) {
      assert(xe.name() == "Spline");
      uint nk = Int( xe.attribute("knots") );
      uint dg = Int( xe.attribute("degree") );
      Vector k(nk);
      XmlElement::const_iterator itr;
      itr = xe.findChild("Knots");
      assert(itr != xe.end());
      std::stringstream ss;
      ss << itr->text();
      for (uint i=0; i<nk; ++i)
        ss >> k[i];
      bas = SplineBasis(dg, k);
      itr = xe.findChild("ControlPoints");
      assert(itr != xe.end());
      ctlpoints.fromXml(*itr);
    }

  protected:

    /// knots
    SplineBasis bas;

    /// control points
    PointGrid<N> ctlpoints;

    /// closed or not?
    bool closed;
};

template <uint N>
void Spline<N>::adaptKnots(const Vector & nKnots)
{
  // adapt spline to new knot vector, do not change
  // parametrization symmetry

  int i, j, n, span;
  int p = degree();
  // size of SLE, number of new control points
  n  = nKnots.size() - p - 1;
  // parameters for system
  Vector u(n);

  // generate suitable parameter values to avoid singular
  // coefficient matrix (similar to 'averaging')
  // important condition: parameter vector must be symmetric if knot
  // vector is symmetric (Piegl's algorithm 5.4 cannot guarantee that!)
  for (i=0; i<n; i++)
    {
      for (j=i+1; j<=i+p; j++)
        u[i] += nKnots[j];
      u[i] /= p;
    }

  // setup system of equations
  SplineBasis nbas(p,nKnots);
  PointGrid<N> ncp(n), rhs(n);
  Matrix cf(n,n);
  for (i=0; i<n; i++)
    {
      rhs[i] = eval(u(i));
      span = nbas.findSpan(u(i));
      for (j=span-p; j<=span; j++)
        cf(i,j) = nbas.eval(j,u(i));
    }

  // solve
  Matrix sol(n,N);
  sol = lu_solve_copy(cf, rhs.toMatrix());
  ncp.fromMatrix(sol);

  // copy results
  ctlpoints = ncp;
  bas.setKnots(nKnots);
}

template <uint N>
void Spline<N>::elevateDegree(uint newdeg)
{
  // naive implementation, inefficient but simple
  // this replaces alg 5.9 from [Pie97] which has been implemented
  // but failed to work properly. This version may be less efficient, but
  // is 70% shorter.

  if (newdeg <= degree())
    return;

  int t = newdeg - degree();

  // compute new knot vector
  uint i(0), j, multi;
  std::vector<Real> nk;

  // build new knot vector
  nk.clear();
  Vector k = bas.getKnots();
  while (i < k.size())
    {
      // count knot multiplicity
      multi = std::count(k.begin(), k.end(), k[i]);
      // insert t new knots
      for (j = 0; j < multi+t; j++)
        nk.push_back(k[i]);
      i += multi;
    }

  Vector nknots(nk.size());
  std::copy(nk.begin(), nk.end(), nknots.begin());

  // compute new control points by means of
  // [Pie97] pg. 200
  // condition for ncp is that
  // new_basis(u) * ncp == old_basis(u) * ctlpoints
  // for all u, yielding a system of nh+1 equations
  uint nh, span;
  Real u;
  nh = nknots.size() - newdeg - 2;
  PointGrid<N> ncp(nh+1), rhs(nh+1);
  Matrix cf(nh+1, nh+1);

  // new basis
  SplineBasis nbas(newdeg,nknots);

  // build coefficient matrix
  for (i=0; i<=nh; i++)
    {
      // compute parameter by averaging knots
      u = nknots[i+1];
      for (j=i+2; j<=i+newdeg; j++)
        u += nknots[j];
      u /= newdeg;

      // changed !??
      rhs[i] = eval(u);
      span = nbas.findSpan(u);
      for (j=span-newdeg; j<=span; j++)
        cf(i,j) = nbas.eval(j,u);
    }

  // solve the system of equations
  ncp.fromMatrix( lu_solve_copy(cf, rhs.toMatrix()) );

  // copy results
  ctlpoints = ncp;
  bas = SplineBasis(newdeg,nknots);
}

/* probably needs a lift */

template <uint N>
Real Spline<N>::project(const SVector<N> & pt, Real tolerance) const
{
  // iterate to find projection of pt onto curve

  // find good starting value
  int i, n = ctlpoints.size();
  Real d, u, u0(0), dist(huge);
  Vector k = bas.getKnots();
  for (i=0; i<n; i++)
    {
      u = Real(i+1)/(n+1);
      d = norm(pt-eval(u));
      if (d < dist)
        {
          dist = d;
          u0 = u;
        }
    }

  bool converged = false;
  Real f0, f1, cosine;
  SVector<N,Real> p0,dev;
  dev = derive(u0,1);
  p0 = eval(u0);

  do
    {
      // compute new parameter (Newton)
      f0 = dot( dev, (p0-pt) );
      f1 = dot( derive(u0,2), (p0-pt) ) + fabs(dot(dev,dev));
      u = u0 - f0/f1;

      // wrap u around if curve is closed
      Real last = k[k.size()-1];
      if (u < k[0])
        {
          if (closed)
            u = last - k[0] + u0;
          else
            u = k[0];
        }
      else if (u > last)
        {
          if (closed)
            u = k[0] + u0 - last;
          else
            u = last;
        }

      // check for convergence
      dev = derive(u,1);
      p0 = eval(u);
      cosine = fabs( dot(dev, (p0-pt)) ) / norm(dev)/ norm(p0-pt);
      if ( norm(p0-pt) < tolerance )
        converged = true;
      else if ( norm((u-u0)*dev) < tolerance )
        converged = true;
      else if (cosine < tolerance)
        converged = true;
      u0 = u;
    }
  while (!converged);

  return u;
}

template <uint N>
Vector Spline<N>::interpolate(const PointGrid<N> & a, uint deg)
{
  // fit spline through points in a

  if (a.size() <= uint(deg))
    throw Error("Not enough points to interpolate to this degree.");

  uint p = deg;
  closed = false;
  Matrix cf(a.size(), a.size());
  int m, n, span;

  // number of control points -1
  n = a.size() - 1;
  // number of knots -1
  m = n + p +1;

  // chord length parametrization
  Vector u(a.size());
  SVector<N> dist;

  for (uint i=1; i<u.size(); i++)
    {
      dist = a[i] - a[i-1];
      u[i] = u[i-1] + norm(dist);
    }

  // normalize parametrization to range [0,1]
  u /= u[u.size()-1];

  // fill knot vector, insert (degree+1) multiple start and end knot
  Vector k(m+1);

  // knot placement by 'averaging' [Pie97] Eq. 9.8
  for (uint j=1; j<=n-p; j++)
    for (uint i=j; i<=j+p-1; i++)
      k[j+p] += 1./p * u[i];

  for (int i=n+1; i<=m; i++)
    k[i] = 1.;
  
  // construct basis
  bas = SplineBasis(deg,k);

  // set up linear system of equations
  for (uint i=0; i<a.size(); i++)
    {
      span = bas.findSpan(u(i));
      for (int j=span-p; j<=span; j++)
        cf(i,j) = bas.eval(j,u(i));
    }

  // solve for control points
  Matrix rs = a.toMatrix();
  ctlpoints.fromMatrix(lu_solve_copy(cf,rs));

  return u;
}

template <uint N>
Vector Spline<N>::interpolate(const PointList<N> & a, uint deg)
{
  // fit spline through points in a
  if (a.size() <= uint(deg))
    throw Error("Not enough points to interpolate to this degree.");

  uint p = deg;
  closed = false;
  Matrix cf(a.size(), a.size());
  int m, n, span;

  // number of control points -1
  n = a.size() - 1;
  // number of knots -1
  m = n + p +1;

  // chord length parametrization
  Vector u(a.size());
  for (uint i=1; i<u.size(); i++)
    u[i] = u[i-1] + norm(a[i] - a[i-1]);

  // normalize parametrization to range [0,1]
  u /= u[u.size()-1];

  // fill knot vector, insert (degree+1) multiple start and end knot
  Vector k(m+1);

  // knot placement by 'averaging' [Pie97] Eq. 9.8
  for (uint j=1; j<=n-p; j++)
    for (uint i=j; i<=j+p-1; i++)
      k[j+p] += 1./p * u[i];

  for (int i=n+1; i<=m; i++)
    k[i] = 1.;

  // construct basis
  bas = SplineBasis(deg,k);

  // set up linear system of equations
  for (uint i=0; i<a.size(); i++)
    {
      span = bas.findSpan(u(i));
      for (int j=span-p; j<=span; j++)
        cf(i,j) = bas.eval(j,u(i));
    }

  // solve for control points
  Matrix rs(a.size(), N);
  for (uint i=0; i<a.size(); i++)
    for (uint j=0; j<N; j++)
      rs(i,j) = a[i][j];

  rs = lu_solve_copy(cf,rs);
  ctlpoints.resize(a.size(), 1);
  for (uint i=0; i<a.size(); i++)
    for (uint j=0; j<N; j++)
      ctlpoints[i][j] = rs(i,j);

  return u;
}

template <uint N>
Vector Spline<N>::interpolate(const PointList<N> & a, const Vector & up, uint deg)
{
  // fit spline through points in a

  if (a.size() <= uint(deg))
    throw Error("Not enough points to interpolate to this degree.");
  if (up.size() != a.size())
    throw Error("Prescribed parameter vector incompatible.");

  uint p = deg;
  closed = false;
  Matrix cf(a.size(), a.size());
  int m, n, span;

  // number of control points -1
  n = a.size() - 1;
  // number of knots -1
  m = n + p +1;

  // normalize parametrization to range [0,1]
  Vector u;
  u = up / up[up.size()-1];

  // fill knot vector, insert (degree+1) multiple start and end knot
  Vector k(m+1);

  // knot placement by 'averaging' [Pie97] Eq. 9.8
  for (uint j=1; j<=n-p; j++)
    for (uint i=j; i<=j+p-1; i++)
      k[j+p] += 1./p * u[i];

  for (int i=n+1; i<=m; i++)
    k[i] = 1.;

  // construct basis
  bas = SplineBasis(deg,k);

  // set up linear system of equations
  for (uint i=0; i<a.size(); i++)
    {
      span = bas.findSpan(u(i));
      for (int j=span-p; j<=span; j++)
        cf(i,j) = bas.eval(j,u(i));
    }

  // solve for control points
  Matrix rs(a.size(), N);
  for (uint i=0; i<a.size(); i++)
    for (uint j=0; j<N; j++)
      rs(i,j) = a[i][j];

  rs = lu_solve_copy(cf,rs);
  ctlpoints.resize(a.size(), 1);
  for (uint i=0; i<a.size(); i++)
    for (uint j=0; j<N; j++)
      ctlpoints[i][j] = rs(i,j);

  return u;
}

template <uint N>
void Spline<N>::approximate(const PointList<N> & a, 
                            const Vector & up, uint deg)
{
  // least-squares fit spline through points in a
  if (a.size() <= uint(deg))
    throw Error("Not enough points to interpolate to this degree.");
  if (a.size() < up.size())
    throw Error("Cannot approximate to *more* controlpoints.");

  uint p = deg;
  closed = false;
  Matrix cf(a.size(), up.size());
  int m, n, span;

  // number of control points -1
  n = up.size() - 1;
  // number of knots -1
  m = n + p + 1;

  // normalize parametrization to range [0,1]
  Vector u(up);
  u /= up.back();

  // fill knot vector, insert (degree+1) multiple start and end knot
  Vector k(m+1);

  // knot placement by 'averaging' [Pie97] Eq. 9.8
  for (uint j=1; j<=n-p; j++)
    for (uint i=j; i<=j+p-1; i++)
      k[j+p] += 1./p * u[i];

  for (int i=n+1; i<=m; i++)
    k[i] = 1.;

  // construct basis
  bas = SplineBasis(deg,k);

  // compute arc-length parametrization for a
  Vector ap(a.size());
  for (uint i=1; i<a.size(); ++i) 
    ap[i] = ap[i-1] + norm(a[i] - a[i-1]);
  ap /= ap.back();
  
  // set up linear system of equations
  for (uint i=0; i<a.size(); i++) {
    span = bas.findSpan(ap[i]);
    for (int j=span-p; j<=span; j++)
      cf(i,j) = bas.eval(j, ap[i]);
  }

  // setup RHS
  Matrix rs(a.size(), N);
  for (uint i=0; i<a.size(); i++)
    for (uint j=0; j<N; j++)
      rs(i,j) = a[i][j];

  lls_solve(cf, rs);
  assert(rs.nrows() == up.size());
  ctlpoints.resize(rs.nrows(), 1);
  for (uint i=0; i<rs.nrows(); i++)
    for (uint j=0; j<N; j++)
      ctlpoints[i][j] = rs(i,j);
}

#endif

