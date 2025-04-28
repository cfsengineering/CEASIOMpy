
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
 
#include <math.h>
#include "algo.h"
#include "pattern.h"

using namespace std;

Vector expand_pattern(uint n, Real f)
{
  Vector a;
  expand_pattern(n, f, a);
  return a;
}

void expand_pattern(uint n, Real f, Vector & a)
{
  if (f == 1) {
    a = equi_pattern(n);
    return;
  }
  a.resize(n);
  Real dx = 1.0 / ( 1.0 + (pow(f, Real(n-1)) - 1.0)/(f - 1) );
  a[0] = 0.0;
  for (uint i=1; i<n; ++i) {
    a[i] = a[i-1] + dx;
    dx *= f;
  }
  a /= a.back();
}

void airfoil_pattern(uint nps, Real tle, Real xle, Real xte, Vector & tp)
{
  // enforce at least 8 points
  nps = max(nps, 8u);
  
  Vector vte, vle;
  const int nnose = max(4u, nps/8);
  const int ns = (nps - nnose + 3)/4 + 1;
  expand_pattern(ns, xte, vte);
  expand_pattern(ns, xle, vle);
  
  // min/max segment size
  Real te_max = vte[ns-1] - vte[ns-2];
  Real le_min = vle[1] - vle[0];
  Real le_max = vle[ns-1] - vle[ns-2];
  
  // extend of nose region
  Real le_size, le_start, le_end, tbup(0.3), tblo(0.7);
  for (int k=0; k<8; ++k) {
    Real len_upper = tle - tbup;
    Real len_lower = tblo - tle;
    le_size = (nnose-1)*le_min*sqrt(len_upper*len_lower);
    le_start = tle - 0.5*le_size;
    le_end = tle + 0.5*le_size;
    
    // break points for equal size panels at bp
    tbup = le_start * le_max / (te_max + le_max);
    tblo = (te_max + le_end*le_max) / (le_max + te_max);
  } 
  
  Vector t;
  t.reserve(nps+1);
  Vector tmp(ns);
  
  // first segment : trailing edge to upper break point
  tmp = tbup*vte;
  t.insert(t.end(), tmp.begin(), tmp.end()-1);
  
  // second segment : upper break to start of LE region
  tmp = (tbup-le_start)*vle + le_start;
  t.insert(t.end(), tmp.begin()+1, tmp.end());
  
  // third segment : LE region
  for (int i=0; i<nnose-1; ++i) {
    Real tn = Real(i) / (nnose-1);
    t.push_back( (1.-tn)*le_start + tn*le_end );
  }
  
  // fourth segment : end of LE region to lower break point
  tmp = (tblo - le_end)*vle + le_end;
  t.insert(t.end(), tmp.begin(), tmp.end()-1);
  
  // fifth segment : lower break point to trailing edge
  tmp = -(1.0 - tblo)*vte + 1.0;
  t.insert(t.end(), tmp.begin(), tmp.end());
  
  Vector::iterator last;
  sort(t.begin(), t.end());
  last = unique(t.begin(), t.end(), almost_equal<Real>(1e-9));
  t.erase(last, t.end());
  
  interpolate_pattern(t, nps, tp);
}

Vector polynomial_pattern(uint n, Real xp)
{
  Vector v(n);
  for (uint i=0; i<n; i++)
    v(i) = pow( Real(i)/(n-1), xp);
  return v;
}

Vector equi_pattern(uint n, Real from, Real to)
{
  // equidistant range
  Vector v(n);
  for (uint i=0; i<n; i++)
    v[i] = from + (to-from)*i/(n-1);
  return v;
}

Vector cosine_pattern(uint n, Real omega, Real phi, Real dmp)
{
  // generate a cosine-spaced pattern
  assert(n > 1);
  Vector v(n);
  Real u;
  for (uint i=0; i<n; i++)
    {
      u = Real(i)/(n-1);
      v(i) = u - dmp*sin(omega*u+phi)/omega;
    }

  v -= v[0];
  v /= v[n-1];

  return v;
}

Vector resize_pattern(const Vector & a, uint m)
{
  assert(a.size() > 1);
  assert(m > 1);

  // recurse if necessary
  if (m > 2*a.size()) {    
    Vector b = resize_pattern(a, 2*a.size());
    return resize_pattern(b, m);
  }

  Vector b(m);
  uint i,j,k,n;
  n = a.size();

  // expansion
  if ( m > n ) {
    k = m - n + 1;
    for (i=0; i<k-1; i++) {
      b[i] = (k-i) * a[0] / k;
      for (j=0; j<i; j++)
        b[i] += a[i] / k;
    }
    for (i=k-1; i<n; i++) {
      b[i] = 0.0;
      for (j=i-k+1; j<i+1; j++)
        b[i] += a[j] / k;
    }
    for (i=n; i<m; i++) {
      b[i] = (i-n+2)* a[n-1] / k;
      for (j=0; j<m-i-1; j++)
        b[i] += a[n-2-j] / k;
    }
  }
  
  // reduction
  else if ( m < n ) {
    k = n - m + 1;
    b[0] = a[0];
    for (i=1; i<m-1; i++) {
      for (j=0; j<k; j++)
        b[i] += a[i+j];
      b[i] /= Real(k);
    }
    b[m-1] = a[n-1];
  } else {
    return a;
  }

  return b;
}

Vector relax(const Vector & v, uint iter)
{
  Vector x(v);
  for (uint i=0; i<iter; i++)
    for (uint j=1; j<v.size()-1; j++)
      x[j] = 0.5*(x[j-1] + x[j+1]);

  return x;
}

void interpolate_pattern(const Vector & a, uint n, Vector & b)
{
  b.resize(n);
  b[0] = a.front();
  b[n-1] = a.back();
  const int np(n);
  const int na(a.size());
  for (int i=1; i<np-1; ++i) {
    Real t = Real(i)/(np-1);
    int ilo = int(t*(na-1));
    t = (t*(na-1) - Real(ilo));
    b[i] = (1-t)*a[ilo] + t*a[ilo+1];
  }
}

Vector interpolate_pattern(const Vector & a, uint n)
{
  Vector b(n);
  interpolate_pattern(a, n, b);
  return b;
}

Indices linspace(uint first, uint last, uint stride)
{
  Indices idx;
  for (uint i=first; i<last+stride; i+=stride)
    idx.push_back(i);
  return idx;
}


