
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
 
#ifndef GENUA_SMALLQR_H
#define GENUA_SMALLQR_H

#include "defines.h"
#include "sse.h"
#include "float4.h"

#ifdef _MSC_VER
#include "bitfiddle.h"  // for copysign()
#endif

namespace qrdetail {

  inline float qr_alpha(float y, float x) {
    return copysignf(sqrtf(y), x);
  }

  inline double qr_alpha(double xsq, double x) {
    return copysign(sqrt(xsq), x);
  }

#ifdef ARCH_SSE2
  inline float4 qr_alpha(const float4 & xsq, const float4 & x) {
    return copysign(sqrt(xsq), x);
  }
#endif

  template <int M, int N, typename Float>
  inline Float generate_reflector(int k, const Float a[],
                                  Float v[], Float & tau)
  {
#undef x
#define x(i)  a[i + k*M]

    // xsq is dot(x,x)
    Float xsq(0);
    CPHINT_SIMD_LOOP
    for (int i=k; i<M; ++i)
      xsq += x(i)*x(i);

    // alpha is |x| with the opposite sign of x[0]
    Float alpha = qr_alpha(xsq, -x(k));

    // keep xsq equal to the squared norm of x by
    // updating the contribution of the first component
    xsq += xsq - 2.0f*x(k)*alpha;

    // first value of the reflector is
    // x(k) - alpha
    // normalize v such that v[k] == 1.0
    Float y = x(k) - alpha;

    // ubsan reports undefined behavior when xsq == 0, but that is OK because
    // alpha == 0 is caught in qr() and leads to decomposition failure
    tau = 2.0f*y*y / xsq;
    y = 1.0f / y;
    v[k] = Float(1.0f);

    CPHINT_SIMD_LOOP
    for (int i=k+1; i<M; ++i)
      v[i] = x(i) * y;

    // return the diagonal value of R
    return alpha;

#undef x
  }

template <int M, int N, typename Float>
inline void apply_reflector(int k, Float tau,
                            const Float v[], Float a[], Float t[])
{
#undef A
#define A(i,j)  a[i + j*M]

    // t = tau * v^T * A
    for (int j=k+1; j<N; ++j) {
      t[j] = Float(0.0f);

      CPHINT_SIMD_LOOP
      for (int i=k; i<M; ++i)
        t[j] += tau * A(i,j) * v[i];
    }

    // A = A - v * t;
    for (int j=k+1; j<N; ++j) {
      CPHINT_SIMD_LOOP
      for (int i=k; i<M; ++i)
        A(i,j) -= v[i] * t[j];
    }
#undef A
  }

} // namespace qrdetail

/** Compute fixed-size QR factorization.
*/
template <int M, int N, typename Float>
inline int qr(Float a[], Float tau[])
{
#undef A
#define A(i,j)  a[i + j*M]

  // TODO : eliminate v by writing into a directly
  Float t[N], v[M];
  int sngl = false;
  for (int j=0; j<N; ++j) {
    Float alpha = qrdetail::generate_reflector<M,N,Float>(j, a, v, tau[j]);
    sngl |= (alpha == Float(0));
    qrdetail::apply_reflector<M,N,Float>(j, tau[j], v, a, t);

    // store diagonal value of R and reflector in a
    A(j,j) = alpha;
    CPHINT_UNROLL_LOOP
    for (int i=j+1; i<M; ++i)
      A(i,j) = v[i];
  }

#undef A

  // return true if all alpha != 0
  return !sngl;
}

#ifdef ARCH_SSE2

/** Partial specialization */
template <int M, int N>
inline int qr(float4 a[], float4 tau[])
{
#undef A
#define A(i,j)  a[i + j*M]

  // TODO : eliminate v by writing into a directly
  float4 t[N], v[M];
  int sngl = 0;
  for (int j=0; j<N; ++j) {
    float4 alpha = qrdetail::generate_reflector<M,N,float4>(j, a, v, tau[j]);
    sngl |= mask_eq(alpha, float4(0.0f)).signbits();
    qrdetail::apply_reflector<M,N,float4>(j, tau[j], v, a, t);

    // store diagonal value of R and reflector in a
    A(j,j) = alpha;
    CPHINT_UNROLL_LOOP
    for (int i=j+1; i<M; ++i)
      A(i,j) = v[i];
  }

#undef A

  return sngl ^ 0xf;
}

#endif

/** Solve a least-squares problem from existing QR factorization.

*/
template <int M, int N, typename Float>
inline void qrsolve(const Float a[], const Float tau[], Float x[])
{
  assert(M >= N);

#undef A
#define A(i,j)  a[i + j*M]

  // apply householder transformation to x
  // x <- Q^T x
  Float vtx;
  for (int j=0; j<N; ++j) {
    vtx = x[j];
    CPHINT_UNROLL_LOOP
    for (int i=j+1; i<M; ++i)
      vtx += x[i] * A(i,j);
    x[j] -= tau[j] * vtx;
    CPHINT_UNROLL_LOOP
    for (int i=j+1; i<M; ++i)
      x[i] -= tau[j] * vtx * A(i,j);
  }

  // solve by backsubstitution with R
  for (int i=N-1; i>=0; --i) {
    CPHINT_UNROLL_LOOP
    for (int j=i+1; j<N; ++j)
      x[i] -= A(i,j)*x[j];
    x[i] /= A(i,i);
  }

#undef A
}

/** Solve a small fixed-size least-squares problem.
  */
template <int M, int N, typename Float>
inline bool qrlls(Float a[], Float x[])
{
  assert(M >= N);

#undef A
#define A(i,j)  a[i + j*M]

  // factorize a
  Float tau[N];
  int qrok = qr<M,N,Float>(a, tau);

  // apply householder transformation to x
  // x <- Q^T x
  Float vtx;
  for (int j=0; j<N; ++j) {
    Float ajj = A(j,j);
    A(j,j) = 1.0f;
    vtx = 0.0f;
    CPHINT_UNROLL_LOOP
    for (int i=j; i<M; ++i)
      vtx += x[i] * A(i,j);
    CPHINT_UNROLL_LOOP
    for (int i=j; i<M; ++i)
      x[i] -= tau[j] * vtx * A(i,j);
    A(j,j) = ajj;
  }

  // solve by backsubstitution with R
  for (int i=N-1; i>=0; --i) {
    CPHINT_UNROLL_LOOP
    for (int j=i+1; j<N; ++j)
      x[i] -= A(i,j)*x[j];
    x[i] /= A(i,i);
  }

  return qrok != 0;

#undef A
}

/** Invert small matrix by means of QR */
template <int M, typename Float>
inline bool qrinv(const Float a[], Float ai[])
{
  Float qra[M*M], tau[M];
  memcpy(qra, a, M*M*sizeof(Float));
  bool qrOK = qr<M,M>(qra, tau);
  if (not qrOK)
    return false;

  memset(ai, 0, M*M*sizeof(Float));
  for (int i=0; i<M; ++i)
    ai[i*M+i] = 1;
  for (int i=0; i<M; ++i)
    qrsolve<M,M>(qra, tau, &ai[M*i]);
  return true;
}

#endif // SMALLQR_H
