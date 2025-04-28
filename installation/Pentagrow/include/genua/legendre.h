
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
 
#ifndef GENUA_LEGENDRE_H
#define GENUA_LEGENDRE_H

#include "defines.h"
    
/** Efficiently compute Legendre polynomial.
 *
 * This template evaluates the Nth order Legendre polynomial by means of
 * compile-time recursion. When the degree N is onljy known at runtime,
 * use the implementation in boost/math/special_functions
 *
 * \ingroup numerics
 *
 */
template <uint N>
Real legendre(Real x)
{
  // compute legendre polynomial of degree N at x
  // high order recursion closed by specialized templates below
  return ((2*N+1)*x*legendre<N-1>(x) - N*legendre<N-2>(x))/(N+1);
}

template<>
Real legendre<0>(Real x)
  {return 1.0;}

template<>
Real legendre<1>(Real x)
  {return x;}

template<>
Real legendre<2>(Real x)
  {return 0.5*(3*sq(x)-1);}

template<>
Real legendre<3>(Real x)
  {return 0.5*(5*cb(x)-3*x);}

/// Compute binomial coefficient (n,k)
inline ulong binomial(ulong n, ulong k)
{
  if (k == 0 or k == n)
    return 1;
  else if (k == 1)
    return n;

  if (n-k < k)
    return binomial(n,n-k);

  ulong nm(n), dn(k);
  for (ulong i=1; i<k; i++) {
    nm *= n-i;
    dn *= k-i;
  }
  
  return nm/dn;
}

#endif

