
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
 
#include "defines.h"
#include "xcept.h"
#include "splinebasis.h"

using namespace std;

SplineBasis::SplineBasis(uint deg, const Vector & knots) : p(deg), k(knots)
{
  // normalize knots
  Real kmin = k.front();
  Real kabs = k.back() - kmin;
  k -= kmin;
  k /= kabs;
}

const Vector & SplineBasis::init(uint deg, uint nuk,
                                 const Real knots[], const int mtp[])
{
  p = deg;

  k.clear();
  for (uint i=0; i<nuk; ++i) {
    const int m = mtp[i];
    for (int j=0; j<m; ++j)
      k.push_back( knots[i] );
  }

  // normalize knots
  Real kmin = k.front();
  Real kabs = k.back() - kmin;
  k -= kmin;
  k /= kabs;

  // ensure that the first values are exactly 0.0 and
  // the last are exactly 1.0 (may not happen after the above)
  const int nk = k.size();
  int m = mtp[0];
  for (int j=0; j<m; ++j)
    k[j] = 0.0;
  m = mtp[nuk-1];
  for (int j=0; j<m; ++j)
    k[nk-1-j] = 1.0;

  return k;
}

const Vector & SplineBasis::init(uint deg, const Vector & parm)
{
  // initialize knots from parameter values
  uint n, m;
  p = deg;
  n = parm.size() - 1;
  m = n + p + 1;  
  k.resize(m+1);
  k = 0.0;

  // knot placement by 'averaging' [Pie97] Eq. 9.8
  for (uint j=1; j<=n-p; ++j)
    for (uint i=j; i<=j+p-1; ++i)
      k[j+p] += parm[i]/p;

  for (uint i=n+1; i<=m; ++i)
    k[i] = 1.;

  return k;
}

Real SplineBasis::recurse(int i, int deg, Real u) const
{
  // recursive version of eval, private
  if (deg == 0) {
    if (k(i) <= u and u < k(i+1))
      return 1.0;
    else
      return 0.0;
  }

  // special case
  if ( fsmall(u-k[k.size()-1]) and uint(i) == k.size()-deg-2 )
    return 1.0;

  Real d1 = k(i+deg) - k(i);
  Real d2 = k(i+deg+1) - k(i+1);

  if ( fsmall(d1) and fsmall(d2) )
    return 0.0;
  else if ( fsmall(d2) )
    return (u-k(i))/d1*recurse(i,deg-1,u);
  else if ( fsmall(d1) )
    return (k(i+deg+1)-u)/d2*recurse(i+1,deg-1,u);
  else
    return (u-k(i))/d1*recurse(i,deg-1,u) +
            (k(i+deg+1)-u)/d2*recurse(i+1,deg-1,u);
}

Real SplineBasis::recurse_derive(int i, int degree, Real u, int d) const
{
  if (d > degree)
    return 0.0;

  if (d == 0)
    return recurse(i,degree,u);

  Real d1 = k(i+degree) - k(i);
  Real d2 = k(i+degree+1) - k(i+1);

  if ( fsmall(d1) and fsmall(d2) )
    return 0.0; 
  else if (fsmall(d2))
    return degree*recurse_derive(i,degree-1,u,d-1)/d1;
  else if (fsmall(d1))
    return -degree*recurse_derive(i+1,degree-1,u,d-1)/d2;
  else
    return degree*(recurse_derive(i,degree-1,u,d-1)/d1 -
                   recurse_derive(i+1,degree-1,u,d-1)/d2);
}

#ifndef MATLAB_MEX_FILE

XmlElement SplineBasis::toXml(bool share) const
{
  const uint nk(k.size());
  XmlElement xe("SplineBasis");
  xe["degree"] = str(p);
  xe["nknots"] = str(nk);

  xe.asBinary(nk, k.pointer(), share);
    
  return xe;
}
    
void SplineBasis::fromXml(const XmlElement & xe)
{
  if (xe.name() != "SplineBasis")
    throw Error("SplineBasis: Incompatible xml representation: "+xe.name());
  
  p = Int(xe.attribute("degree"));
  
  k.allocate( Int(xe.attribute("nknots")) );
  xe.fetch(k.size(), k.pointer());
}

#endif
