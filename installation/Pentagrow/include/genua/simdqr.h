#ifndef GENUA_SIMDQR_H
#define GENUA_SIMDQR_H

#include "simdsupport.h"
#include <boost/static_assert.hpp>

template <int M, int N>
force_inline int simd_qrf(float8 a[], float8 tau[]) attr_always_inline;

template <int M, int N>
force_inline void simd_qrsolve(const float8 a[],
                               const float8 tau[], float8 x[]) attr_always_inline;

namespace qrdetail
{

force_inline float8 qr_alpha(const float8 &xsq, const float8 &x) attr_always_inline;

force_inline float8 qr_alpha(const float8 &xsq, const float8 &x)
{
  return copysign(sqrt(xsq), x);
}

template <int M, int N>
force_inline float8 generate_reflector(int k, const float8 a[],
                                        float8 v[], float8 & tau) attr_always_inline;

template <int M, int N>
force_inline float8 generate_reflector(int k, const float8 a[],
                                        float8 v[], float8 & tau)
{
#undef  x
#define x(i)  a[(i) + k*M]

  // xsq is dot(x,x)
  float8 xsq(0.0f);
  for (int i=k; i<M; ++i)
    xsq = fmuladd(x(i), x(i), xsq);
    // xsq += x(i)*x(i);

  // alpha is |x| with the opposite sign of x[0]
  float8 alpha = qr_alpha(xsq, -x(k));

  // keep xsq equal to the squared norm of x by
  // updating the contribution of the first component
  xsq += xsq - 2.0f*x(k)*alpha;

  // first value of the reflector is
  // x(k) - alpha
  // normalize v such that v[k] == 1.0
  const float8 one(1.0f);
  float8 y = x(k) - alpha;
  tau = 2.0f*y*y / xsq;
  y = one / y;
  v[k] = one;
CPHINT_UNROLL_LOOP
  for (int i=k+1; i<M; ++i)
    v[i] = x(i) * y;

  // return the diagonal value of R
  return alpha;

#undef x
}

template <int M, int N>
force_inline void apply_reflector(int k, float8 tau,
                                  const float8 v[], float8 a[], float8 t[]) attr_always_inline;

template <int M, int N>
force_inline void apply_reflector(int k, float8 tau,
                                  const float8 v[], float8 a[], float8 t[])
{
#undef A
#define A(i,j)  a[i + j*M]

  // t = tau * v^T * A
  for (int j=k+1; j<N; ++j) {
    t[j] = float8(0.0f);
CPHINT_UNROLL_LOOP
    for (int i=k; i<M; ++i)
      t[j] = fmuladd(tau*A(i,j), v[i], t[j]);
      // t[j] += tau * A(i,j) * v[i];
  }

  // A = A - v * t;
  for (int j=k+1; j<N; ++j) {
CPHINT_UNROLL_LOOP
    for (int i=k; i<M; ++i)
      A(i,j) = fmuladd(-v[i], t[j], A(i,j));
      //A(i,j) -= v[i] * t[j];
  }
#undef A
}

} // namespace qrdetail

template <int M, int N>
force_inline int simd_qrf(float8 a[], float8 tau[])
{
#undef A
#define A(i,j)  a[i + j*M]

  float8 t[N], v[M];
  int sngl = 0;
CPHINT_UNROLL_LOOP
  for (int j=0; j<N; ++j) {
    float8 alpha = qrdetail::generate_reflector<M,N>(j, a, v, tau[j]);
    sngl |= (alpha == float8(0.0f)).signbits();
    qrdetail::apply_reflector<M,N>(j, tau[j], v, a, t);

    // store diagonal value of R and reflector in a
    A(j,j) = alpha;
CPHINT_UNROLL_LOOP
    for (int i=j+1; i<M; ++i)
      A(i,j) = v[i];
  }

#undef A

  return sngl ^ ((1 << 8) - 1);
}

template <int M, int N>
force_inline void simd_qrsolve(const float8 a[], const float8 tau[], float8 x[])
{
  BOOST_STATIC_ASSERT(M >= N);

#undef A
#define A(i,j)  a[i + j*M]

  // apply householder transformation to x
  // x <- Q^T x
  float8 vtx;
  for (int j=0; j<N; ++j) {
    vtx = x[j];
CPHINT_UNROLL_LOOP
    for (int i=j+1; i<M; ++i)
      vtx = fmuladd(x[i], A(i,j), vtx);  //  vtx += x[i] * A(i,j);
    x[j] = fmuladd(-tau[j], vtx, x[j]);  //  x[j] -= tau[j] * vtx;

CPHINT_UNROLL_LOOP
    for (int i=j+1; i<M; ++i)
      x[i] = fmuladd(-tau[j]*vtx, A(i,j), x[i]);  // x[i] -= tau[j] * vtx * A(i,j);
  }

  // solve by backsubstitution with R
  for (int i=N-1; i>=0; --i) {
CPHINT_UNROLL_LOOP
    for (int j=i+1; j<N; ++j)
      x[i] = fmuladd(-A(i,j), x[j], x[i]);  // x[i] -= A(i,j)*x[j];
    x[i] /= A(i,i);
  }

#undef A
}



#endif // SIMDQR_H

