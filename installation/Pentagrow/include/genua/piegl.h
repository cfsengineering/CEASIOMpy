
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

#ifndef GENUA_PIEGL_H
#define GENUA_PIEGL_H

/** \file piegl.h
 *  \brief  Evaluate spline basis functions.
 */

#include "defines.h"
#include "smatrix.h"
#include "dmatrix.h"

struct Piegl
{
  static const int MaxDegree = 15;

  // dynamic versions
  static void dEvalBasis(Real u, int span, int degr, const Real knot[], Real N[]);
  static void dDeriveBasis(Real u, int span, int degr, int n, const Vector & knot,
                    Matrix & ders);
  static void dDeriveBasis(Real u, int span, int degr, int n, const Vector & knot,
                    int lda, Real pders[]);

  /** Compute nonzero spline basis functions for compile-time degree */
  template <class FloatType, int degr>
  static void sEvalBasis(FloatType u, int span,
                         const DVector<FloatType> & knot,
                         SVector<degr+1,FloatType> & N)
  {
    SVector<degr+1,FloatType> tleft, tright;
    FloatType temp(0), saved(0);
    N[0] = 1.0;
    for (int j=1; j <= degr; ++j) {
      tleft[j] = u - knot[span+1-j];
      tright[j] = knot[span+j] - u;
      saved = 0.0;
      for (int r=0; r<j; ++r){
        temp = N[r] / (tright[r+1] + tleft[j-r]);
        N[r] = saved + tright[r+1] * temp;
        saved = tleft[j-r] * temp;
      }
      N[j] = saved;
    }
  }

  /** nth-derivation of spline basis functions. */
  template <class FloatType, int degr, int n>
  static void sDeriveBasis(FloatType u, int span,
                           const DVector<FloatType> & knot,
                           SMatrix<n+1,degr+1,FloatType> & ders)
  {
    SMatrix<degr+1, degr+1, FloatType> ndu;
    SVector<degr+1, FloatType> tleft, tright;
    FloatType saved(0), temp(0);
    ndu(0,0) = 1.0;
    for (int j=1; j <= degr; ++j) {
      tleft[j] = u - knot[span+1-j];
      tright[j] = knot[span+j] - u;
      saved = 0.0;
      for (int r=0; r<j; ++r) {
        ndu(j,r) = tright[r+1] + tleft[j-r];
        temp = ndu(r,j-1) / ndu(j,r);
        ndu(r,j) = saved + tright[r+1] * temp;
        saved = tleft[j-r] * temp;
      }
      ndu(j,j) = saved;
    }

    for (int j=0; j<=degr; ++j)
      ders(0,j) = ndu(j,degr);

    SMatrix<degr+1, degr+1, FloatType> a;
    for (int r=0; r<=degr; ++r) {

      int s1(0), s2(1);
      a(0,0) = 1.0;
      for (int k=1; k<=n; k++) {
        FloatType d(0.0);
        int rk, pk, j1, j2;
        rk = r-k;
        pk = degr-k;
        if ( r >= k ) {
          a(s2,0) = a(s1,0) / ndu(pk+1,rk);
          d = a(s2,0) * ndu(rk,pk);
        }

        j1 = (rk >= -1) ? 1 : -rk;
        j2 = (r-1 <= pk) ? (k-1) : (degr-r);

        for (int j=j1; j<=j2; j++) {
          a(s2,j) = (a(s1,j) - a(s1,j-1)) / ndu(pk+1,rk+j);
          d += a(s2,j) * ndu(rk+j,pk);
        }
        if ( r <= pk ) {
          a(s2,k) = -a(s1,k-1) / ndu(pk+1,r);
          d += a(s2,k) * ndu(r,pk);
        }
        ders(k,r) = d;
        std::swap(s1,s2);
      }
    }

    int r(degr);
    for (int k=1; k<=n; k++) {
      for (int j=0; j<=degr; j++)
        ders(k,j) *= r;
      r *= degr-k;
    }
  }

  /** Compute Bernstein basis functions for Bezier segments.
  Algorithm A1.3 from Piegl/Tiller, p 21 */
  template <int degr>
  static void bernstein(Real u, SVector<degr+1> & b)
  {
    b[0] = 1.0;
    Real t, u1 = 1.0 - u;
    for (int j=1; j<=degr; ++j) {
      Real s(0.0);
      for (int k=0; k<j; ++k) {
        t = b[k];
        b[k] = s + u1*t;
        s = u*t;
      }
      b[j] = s;
    }
  }

};

#endif
