
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
 
#ifndef GENUA_DOUBLE2_H
#define GENUA_DOUBLE2_H
#include "sse.h"
#include "simdbase.h"

#ifdef ARCH_SSE2

#if defined(__INTEL_COMPILER)

#define GENUA_USE_SVML

#else

// pull in implementation for trig and log functions
#define USE_SSE2
#include "ssetrigo.h"

#endif

/** Double-precision SIMD vector.

  Just like float4, double2 is a short-vector SIMD object which behaves
  mostly as a scalar. This class is only available if ARCH_SSE2 is defined
  (at least).

  \b Note: Load/store functions require aligned memory arguments!

  \ingroup numerics
  \sa double4, double8, float4, float8, float16
*/
struct double2 : public SimdBase<double,2>
{
  typedef double Scalar;

  /// vector width
  static int width() {return 2;}

  /// undefined construction
  double2() {}

  /// set all values to a
  explicit double2(double a) {xmm = _mm_set1_pd(a);}

  /// copy vector type
  explicit double2(__m128d x) {xmm = x;}

  /// set from two doubles
  double2(double x, double y) {
    xmm = _mm_set_pd(x, y);
  }

  /// aligned load
  explicit double2(const double *v) {
    xmm = _mm_load_pd(v);
  }

  /// set all values to a
  double2 & operator= (double a) {
    xmm = _mm_set_pd(a, a);
    return *this;
  }

  /// computed assignment
  double2 & operator+= (const double2 &a) {
    xmm = _mm_add_pd(xmm, a.xmm);
    return *this;
  }

  /// computed assignment
  double2 & operator*= (const double2 &a) {
    xmm = _mm_mul_pd(xmm, a.xmm);
    return *this;
  }

  /// computed assignment
  double2 & operator-= (const double2 &a) {
    xmm = _mm_sub_pd(xmm, a.xmm);
    return *this;
  }

  /// computed assignment
  double2 & operator/= (const double2 &a) {
    xmm = _mm_div_pd(xmm, a.xmm);
    return *this;
  }

  /// computed assignment
  double2 & operator&= (const double2 &a) {
    xmm = _mm_and_pd(xmm, a.xmm);
    return *this;
  }

  /// computed assignment
  double2 & operator|= (const double2 &a) {
    xmm = _mm_or_pd(xmm, a.xmm);
    return *this;
  }

  /// computed assignment
  double2 & operator^= (const double2 &a) {
    xmm = _mm_xor_pd(xmm, a.xmm);
    return *this;
  }

  /// extract sign bits
  int signbits() const {return _mm_movemask_pd(xmm);}

  /// set first value
  void first(double a) {xmm = _mm_set_sd(a);}

  /// extract first value
  double first() const {return _mm_cvtsd_f64(xmm);}

  /// return horizontal sum
  double sum() const {
#if defined(ARCH_SSE3)
    __m128d t = _mm_hadd_pd(xmm, xmm);
    return _mm_cvtsd_f64(t);
#else
    alignas(16) double v[2];
    _mm_store_pd(v, xmm);
    return v[0]+v[1];
#endif
  }

  /// explicit load from aligned memory location
  void load(const double *v) {  xmm = _mm_load_pd(v); }

  /// explicit load from unaligned memory location
  void loadu(const double *v) {  xmm = _mm_loadu_pd(v); }

  /// store to aligned location
  void store(double *v) const {_mm_store_pd(v, xmm);}

  /// store to unaligned location
  void storeu(double *v) const {_mm_storeu_pd(v, xmm);}

  /// return sign mask
  static double2 signmask() {
    const union {uint64_t i[2]; __m128d x;} mask = {{0x8000000000000000L,
                                                     0x8000000000000000L}};
    return double2( mask.x );
  }

  __m128d xmm;
};

// ------------- declaration macros ----------------------------------------

#undef SIMD_DECLARE_ARITHM_OP
#define SIMD_DECLARE_ARITHM_OP(op, intrin) \
  inline double2 operator op (const double2 &a, const double2 &b) \
{ \
  return double2( _mm_ ## intrin(a.xmm, b.xmm) ); \
  } \
  inline double2 operator op (const double2 &a, double b) \
{ \
  return a op double2(b); \
  } \
  inline double2 operator op (double a, const double2 &b) \
{ \
  return double2(a) op b; \
  } \

#undef SIMD_DECLARE_BINARY_OP
#define SIMD_DECLARE_BINARY_OP(op, intrin) \
  inline double2 operator op (const double2 &a, const double2 &b) \
{ \
  return double2( _mm_ ## intrin(a.xmm, b.xmm) ); \
  } \

#undef SIMD_DECLARE_BINARY_FN
#define SIMD_DECLARE_BINARY_FN(fn, intrin) \
  inline double2 fn(const double2 &a, const double2 &b) \
{ \
  return double2( _mm_ ## intrin(a.xmm, b.xmm) ); \
  } \

#undef SIMD_DECLARE_UNARY_FN
#define SIMD_DECLARE_UNARY_FN(fn, intrin) \
  inline double2 fn(const double2 &a) \
{ \
  return double2( _mm_ ## intrin(a.xmm) ); \
  } \

// ------------ logical operators ----------------------------------------

SIMD_DECLARE_BINARY_OP(&, and_pd)
SIMD_DECLARE_BINARY_OP(|, or_pd)
SIMD_DECLARE_BINARY_OP(^, xor_pd)
SIMD_DECLARE_BINARY_FN(andnot, andnot_pd)
SIMD_DECLARE_BINARY_OP(==, cmpeq_pd)
SIMD_DECLARE_BINARY_OP(!=, cmpneq_pd)
SIMD_DECLARE_BINARY_OP(<, cmplt_pd)
SIMD_DECLARE_BINARY_OP(<=, cmple_pd)
SIMD_DECLARE_BINARY_OP(>, cmpgt_pd)
SIMD_DECLARE_BINARY_OP(>=, cmpge_pd)

SIMD_DECLARE_BINARY_FN(mask_eq, cmpeq_pd)
SIMD_DECLARE_BINARY_FN(mask_neq, cmpneq_pd)
SIMD_DECLARE_BINARY_FN(mask_lt, cmplt_pd)
SIMD_DECLARE_BINARY_FN(mask_le, cmple_pd)
SIMD_DECLARE_BINARY_FN(mask_nle, cmpnle_pd)
SIMD_DECLARE_BINARY_FN(mask_nlt, cmpnlt_pd)
SIMD_DECLARE_BINARY_FN(mask_gt, cmpgt_pd)
SIMD_DECLARE_BINARY_FN(mask_ge, cmpge_pd)
SIMD_DECLARE_BINARY_FN(mask_nge, cmpnge_pd)
SIMD_DECLARE_BINARY_FN(mask_ngt, cmpngt_pd)

inline double2 operator~ (const double2 &a)
{
  const union {uint64_t i[2]; __m128d x;} mask = {{0xffffffffffffffff,
                                                  0xffffffffffffffff}};
  return double2(_mm_xor_pd(mask.x, a.xmm));
}

// ------------ arithmetic operators ----------------------------------------

SIMD_DECLARE_ARITHM_OP(+, add_pd)
SIMD_DECLARE_ARITHM_OP(-, sub_pd)
SIMD_DECLARE_ARITHM_OP(*, mul_pd)
SIMD_DECLARE_ARITHM_OP(/, div_pd)

inline double2 operator- (const double2 &a)
{
  return (double2::signmask() ^ a);
}

inline double2 fabs(const double2 &a)
{
  return andnot( double2::signmask(), a );
}

// return x with the sign of y
inline double2 copysign(const double2 &x, const double2 &y)
{
  double2 m = double2::signmask();
  return ( (m & y) | andnot(m, x) );
}

#ifdef ARCH_SSE3

SIMD_DECLARE_BINARY_FN(hadd, hadd_pd)

force_inline double dot(const double2 &a, const double2 &b) attr_always_inline;
force_inline double dot(const double2 &a, const double2 &b)
{
  double2 r1 = a*b;
  double2 r2 = hadd(r1, r1);
  return r2.first();
}

#endif // SSE3

// return a*b + c
force_inline double2 fmuladd(const double2 &a, const double2 &b, const double2 &c) attr_always_inline;
force_inline double2 fmuladd(const double2 &a, const double2 &b, const double2 &c)
{
#ifdef ARCH_AVX2
  return double2( _mm_fmadd_pd(a.xmm, b.xmm, c.xmm) );
#else
  return a*b + c;
#endif
}

// return a*b - c
force_inline double2 fmulsub(const double2 &a, const double2 &b, const double2 &c) attr_always_inline;
force_inline double2 fmulsub(const double2 &a, const double2 &b, const double2 &c)
{
#ifdef ARCH_AVX2
  return double2( _mm_fmsub_pd(a.xmm, b.xmm, c.xmm) );
#else
  return a*b - c;
#endif
}

// ----------- mathematical functions --------------------------------------

SIMD_DECLARE_UNARY_FN(sqrt, sqrt_pd)
SIMD_DECLARE_BINARY_FN(max, max_pd)
SIMD_DECLARE_BINARY_FN(min, min_pd)

#ifdef GENUA_USE_SVML

SIMD_DECLARE_UNARY_FN(cbrt, cbrt_pd)
SIMD_DECLARE_BINARY_FN(pow, pow_pd)
SIMD_DECLARE_UNARY_FN(log, log_pd)
SIMD_DECLARE_UNARY_FN(log2, log2_pd)
SIMD_DECLARE_UNARY_FN(log10, log10_pd)
SIMD_DECLARE_UNARY_FN(exp, exp_pd)
SIMD_DECLARE_UNARY_FN(exp2, exp2_pd)
SIMD_DECLARE_UNARY_FN(sin, sin_pd)
SIMD_DECLARE_UNARY_FN(cos, cos_pd)
SIMD_DECLARE_UNARY_FN(asin, asin_pd)
SIMD_DECLARE_UNARY_FN(acos, acos_pd)
SIMD_DECLARE_UNARY_FN(atan, atan_pd)
SIMD_DECLARE_BINARY_FN(atan2, atan2_pd)

inline void sincos(const double2 &a, double2 & sa, double2 & sc)
{
  sa = double2( _mm_sincos_pd(&(sc.xmm), a.xmm) );
}

#endif

// ------------- permutations --------------------------

#ifdef ARCH_SSE41

template <int imm>
inline double2 blend(const double2 &a, const double2 &b)
{
  return double2( _mm_blend_pd(a.xmm, b.xmm, imm) );
}

inline double2 blendv(const double2 &a, const double2 &b, const double2 &mask)
{
  return double2( _mm_blendv_pd(a.xmm, b.xmm, mask.xmm) );
}

#endif

#undef SIMD_DECLARE_UNARY_FN
#undef SIMD_DECLARE_BINARY_FN
#undef SIMD_DECLARE_BINARY_OP
#undef SIMD_DECLARE_ARITHM_OP

#endif // ARCH_SSE2

#endif // DOUBLE2_H
