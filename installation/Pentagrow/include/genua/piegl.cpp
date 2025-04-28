
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
 
#include "piegl.h"
 
void Piegl::dEvalBasis(Real u, int span, int deg,
                const Real knot[], Real N[])
{
  const int K = Piegl::MaxDegree+1;
  assert(deg <= Piegl::MaxDegree);
  
  SVector<K> tleft, tright;
  Real temp(0), saved(0);
  N[0] = 1.0;
  for (int j=1; j <= deg; j++) {
    tleft[j] = u - knot[span+1-j];
    tright[j] = knot[span+j] - u;
    saved = 0.0;
    for (int r=0; r<j; r++){
      temp = N[r] / (tright[r+1] + tleft[j-r]);
      N[r] = saved + tright[r+1] * temp;
      saved = tleft[j-r] * temp;
    }
    N[j] = saved;
  }
}

void Piegl::dDeriveBasis(Real u, int span, int deg, int n,
                  const Vector & knot, Matrix & ders)
{
  Piegl::dDeriveBasis(u, span, deg, n, knot, ders.nrows(), ders.pointer());
}

void Piegl::dDeriveBasis(Real u, int span, int deg, int n, const Vector & knot,
                  int lda, Real pders[])
{
  const int K = Piegl::MaxDegree+1;
  assert(deg <= Piegl::MaxDegree);

  SMatrix<K,K> ndu;
  SVector<K> tleft, tright;
  
  Real saved, temp;
  ndu(0, 0) = 1.0;
  for (int j=1; j <= deg; j++) {
    tleft[j] = u - knot[span+1-j];
    tright[j] = knot[span+j] - u;
    saved = 0.0;
    for (int r=0; r<j; r++) {
      ndu(j, r) = tright[r+1] + tleft[j-r];
      temp = ndu(r, j-1) / ndu(j, r);
      ndu(r, j) = saved + tright[r+1] * temp;
      saved = tleft[j-r] * temp;
    }
    ndu(j, j) = saved;
  }

#undef  ders
#define ders(i,j)  pders[((j)*lda + (i))]

  for (int j=0; j<=deg; j++)
    ders(0,j) = ndu(j, deg);

  SMatrix<K,K> a;
  for (int r=0; r<=deg; r++) {
    
    int s1(0), s2(1);
    a(0, 0) = 1.0;
    for (int k=1; k<=n; k++) {
      Real d(0.0);
      int rk, pk, j1, j2;
      rk = r-k;
      pk = deg-k;
      if ( r >= k ) {
        a(s2, 0) = a(s1, 0) / ndu(pk+1, rk);
        d = a(s2, 0) * ndu(rk, pk);
      }
      if ( rk >= -1 ) {
        j1 = 1;
      } else {
        j1 = -rk;
      }
      if ( r-1 <= pk ) {
        j2 = k-1;
      } else {
        j2 = deg-r;
      }
      for (int j=j1; j<=j2; j++) {
        a(s2, j) = (a(s1, j) - a(s1, j-1)) / ndu(pk+1, rk+j);
        d += a(s2, j) * ndu(rk+j, pk);
      }
      if ( r <= pk ) {
        a(s2, k) = -a(s1, k-1) / ndu(pk+1, r);
        d += a(s2, k) * ndu(r, pk);
      }
      ders(k,r) = d;
      std::swap(s1,s2);
    }
  }

  int r(deg);
  for (int k=1; k<=n; k++) {
    for (int j=0; j<=deg; j++)
      ders(k,j) *= r;
    r *= deg-k;
  }

#undef ders
}

