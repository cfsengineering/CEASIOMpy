
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
 
#ifndef GENUA_DOUBLE4_H
#define GENUA_DOUBLE4_H

#include "sse.h"
#include "simdtype.h"

#ifdef ARCH_SSE2

#ifdef ARCH_AVX

#include <immintrin.h>

/** Double-precision SIMD vector.

  Just like float4, double4 is a short-vector SIMD object which behaves
  mostly as a scalar. This class is only available if ARCH_SSE2 is defined
  (at least). When AVX is available, most operations map to single instructions,
  otherwise, the same effect is emulated using pairs of SSE2 intrinsics.

  \b Note: Load/store functions require aligned memory arguments!

  \ingroup numerics
  \sa double2, double8, float4, float8, float16
*/
struct double4  : public SimdBase<double,4>
{
  typedef double Scalar;

  /// vector width
  static int width() {return 4;}

  /// undefined construction
  double4() {}

  /// set all values to a
  explicit double4(double a) {ymm = _mm256_set1_pd(a);}

  /// copy vector type
  explicit double4(__m256d x) {ymm = x;}

  /// set from two doubles
  double4(double x, double y, double z, double w) {
    ymm = _mm256_set_pd(x, y, z, w);
  }

  /// aligned load
  explicit double4(const double *v) {
    ymm = _mm256_load_pd(v);
  }

  /// set all values to a
  double4 & operator= (double a) {
    ymm = _mm256_set_pd(a, a, a, a);
    return *this;
  }

  /// computed assignment
  double4 & operator+= (const double4 &a) {
    ymm = _mm256_add_pd(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  double4 & operator*= (const double4 &a) {
    ymm = _mm256_mul_pd(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  double4 & operator-= (const double4 &a) {
    ymm = _mm256_sub_pd(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  double4 & operator/= (const double4 &a) {
    ymm = _mm256_div_pd(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  double4 & operator&= (const double4 &a) {
    ymm = _mm256_and_pd(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  double4 & operator|= (const double4 &a) {
    ymm = _mm256_or_pd(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  double4 & operator^= (const double4 &a) {
    ymm = _mm256_xor_pd(ymm, a.ymm);
    return *this;
  }

  /// extract sign bits
  int signbits() const {return _mm256_movemask_pd(ymm);}

  /// access first value
  double first() const {
    double r[4];
    _mm256_storeu_pd(r, ymm);
    return r[0];
  }

  /// return horizontal sum
  double sum() const {
    __m256d h = _mm256_add_pd(ymm, _mm256_permute2f128_pd(ymm, ymm, 0x1));
    __m128d x = _mm256_castpd256_pd128(h);
    return _mm_cvtsd_f64( _mm_hadd_pd(x,x) );
  }

  /// explicit load from aligned memory location
  void load(const double *v) {  ymm = _mm256_load_pd(v); }

  /// explicit load from unaligned memory location
  void loadu(const double *v) {  ymm = _mm256_loadu_pd(v); }

  /// store to aligned location
  void store(double *v) const {_mm256_store_pd(v, ymm);}

  /// store to unaligned location
  void storeu(double *v) const {_mm256_storeu_pd(v, ymm);}

  __m256d ymm;
};

// ------------- declaration macros ----------------------------------------

#undef SIMD_DECLARE_ARITHM_OP
#define SIMD_DECLARE_ARITHM_OP(op, intrin) \
inline double4 operator op (const double4 &a, const double4 &b) \
{ \
  return double4( _mm256_ ## intrin(a.ymm, b.ymm) ); \
} \
inline double4 operator op (const double4 &a, double b) \
{ \
  return a op double4(b); \
} \
inline double4 operator op (double a, const double4 &b) \
{ \
  return double4(a) op b; \
} \

#undef SIMD_DECLARE_BINARY_OP
#define SIMD_DECLARE_BINARY_OP(op, intrin) \
inline double4 operator op (const double4 &a, const double4 &b) \
{ \
  return double4( _mm256_ ## intrin(a.ymm, b.ymm) ); \
} \

#undef SIMD_DECLARE_BINARY_FN
#define SIMD_DECLARE_BINARY_FN(fn, intrin) \
inline double4 fn(const double4 &a, const double4 &b) \
{ \
  return double4( _mm256_ ## intrin(a.ymm, b.ymm) ); \
} \

#undef SIMD_DECLARE_UNARY_FN
#define SIMD_DECLARE_UNARY_FN(fn, intrin) \
inline double4 fn(const double4 &a) \
{ \
  return double4( _mm256_ ## intrin(a.ymm) ); \
} \

#undef SIMD_DECLARE_CMP_OP
#define SIMD_DECLARE_CMP_OP(op, flag) \
inline double4 operator op (const double4 &a, const double4 &b) \
{ \
  return double4( _mm256_cmp_pd(a.ymm, b.ymm, flag) ); \
} \

// ------------ arithmetic operators ----------------------------------------

SIMD_DECLARE_ARITHM_OP(+, add_pd)
SIMD_DECLARE_ARITHM_OP(-, sub_pd)
SIMD_DECLARE_ARITHM_OP(*, mul_pd)
SIMD_DECLARE_ARITHM_OP(/, div_pd)

inline double4 operator- (const double4 &a)
{
  const union {uint64_t i[4]; __m256d x;} mask = {{0x8000000000000000L,
                                                   0x8000000000000000L,
                                                   0x8000000000000000L,
                                                   0x8000000000000000L }};
  return double4( _mm256_xor_pd(mask.x, a.ymm) );
}

SIMD_DECLARE_BINARY_FN(hadd, hadd_pd)

//force_inline float dot(const double4 &a, const double4 &b) attr_always_inline;
//force_inline double dot(const double4 &a, const double4 &b)
//{
//  double4 p = a*b;
//  _m256d t1 = _mm256_permute2f128_pd(p.ymm, p.ymm, 0x20);
//  _m256d t2 = _mm256_permute2f128_pd(p.ymm, p.ymm, 0x31);
//  _m256d t3 = _mm256_hadd_pd(t1, t2);
//  t1 = _mm256_permute2f128_pd(t3, t3, 0x20);
//  t2 = _mm256_permute2f128_pd(t3, t3, 0x31);
//  t3 = _mm256_hadd_pd(t1, t2);

//  double r;
//  _mm256_store_sd(&r, t3);
//  return r;
//}

// return a*b + c
force_inline double4 fmuladd(const double4 &a, const double4 &b, const double4 &c) attr_always_inline;
force_inline double4 fmuladd(const double4 &a, const double4 &b, const double4 &c)
{
#ifdef ARCH_AVX2
  return double4( _mm256_fmadd_pd(a.ymm, b.ymm, c.ymm) );
#else
  return a*b + c;
#endif
}

// return a*b - c
force_inline double4 fmulsub(const double4 &a, const double4 &b, const double4 &c) attr_always_inline;
force_inline double4 fmulsub(const double4 &a, const double4 &b, const double4 &c)
{
#ifdef ARCH_AVX2
  return double4( _mm256_fmsub_pd(a.ymm, b.ymm, c.ymm) );
#else
  return a*b - c;
#endif
}

// ----------- mathematical functions --------------------------------------

SIMD_DECLARE_UNARY_FN(sqrt, sqrt_pd)
SIMD_DECLARE_BINARY_FN(max, max_pd)
SIMD_DECLARE_BINARY_FN(min, min_pd)

inline double4 fabs(const double4 &a)
{
  const union {int64_t i[4]; __m256d x;} mask = {{0x7fffffffffffffffL,
                                                    0x7fffffffffffffffL,
                                                    0x7fffffffffffffffL,
                                                    0x7fffffffffffffffL }};
  return double4( _mm256_and_pd(mask.x, a.ymm) );
}

// return x with the sign of y
inline double4 copysign(const double4 &x, const double4 &y)
{
  // a mask for the sign bit
  const union {uint64_t i[4]; __m256d x;} mask = {{0x8000000000000000L,
                                                    0x8000000000000000L,
                                                    0x8000000000000000L,
                                                    0x8000000000000000L }};
  __m256d sign_y = _mm256_and_pd(mask.x, y.ymm);
  __m256d abs_x = _mm256_andnot_pd(mask.x, x.ymm);
  return double4( _mm256_or_pd(sign_y, abs_x) );
}

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

inline void sincos(const double4 &a, double4 & sa, double4 & sc)
{
  sa = double4( _mm256_sincos_pd(&(sc.ymm), a.ymm) );
}

#endif

// ------------ logical operators ----------------------------------------

SIMD_DECLARE_BINARY_OP(&, and_pd)
SIMD_DECLARE_BINARY_OP(|, or_pd)
SIMD_DECLARE_BINARY_OP(^, xor_pd)
SIMD_DECLARE_BINARY_FN(andnot, andnot_pd)

inline double4 operator~ (const double4 &a)
{
  const union {uint64_t i[4]; __m256d x;} mask = {{ 0xffffffffffffffffL,
                                                   0xffffffffffffffffL,
                                                   0xffffffffffffffffL,
                                                   0xffffffffffffffffL }};
  return double4(_mm256_xor_pd(mask.x, a.ymm));
}

SIMD_DECLARE_CMP_OP(==, _CMP_EQ_UQ)
SIMD_DECLARE_CMP_OP(!=, _CMP_NEQ_UQ)
SIMD_DECLARE_CMP_OP(<, _CMP_LT_OQ)
SIMD_DECLARE_CMP_OP(<=, _CMP_LE_OQ)
SIMD_DECLARE_CMP_OP(>, _CMP_GT_OQ)
SIMD_DECLARE_CMP_OP(>=, _CMP_GE_OQ)

inline double4 mask_nlt(const double4 &a, const double4 &b)
{
  return double4( _mm256_cmp_pd(a.ymm, b.ymm, _CMP_NLT_UQ) );
}

inline double4 mask_nle(const double4 &a, const double4 &b)
{
  return double4( _mm256_cmp_pd(a.ymm, b.ymm, _CMP_NLE_UQ) );
}

inline double4 mask_ngt(const double4 &a, const double4 &b)
{
  return double4( _mm256_cmp_pd(a.ymm, b.ymm, _CMP_NGT_UQ) );
}

inline double4 mask_nge(const double4 &a, const double4 &b)
{
  return double4( _mm256_cmp_pd(a.ymm, b.ymm, _CMP_NGE_UQ) );
}

// ---------- permutations -----------------------------------

template <int imm>
inline double4 blend(const double4 &a, const double4 &b)
{
  return double4( _mm256_blend_pd(a.ymm, b.ymm, imm) );
}

inline double4 blendv(const double4 &a, const double4 &b, const double4 &mask)
{
  return double4( _mm256_blendv_pd(a.ymm, b.ymm, mask.ymm) );
}

#undef SIMD_DECLARE_CMP_OP
#undef SIMD_DECLARE_UNARY_FN
#undef SIMD_DECLARE_BINARY_FN
#undef SIMD_DECLARE_BINARY_OP
#undef SIMD_DECLARE_ARITHM_OP

#else

#include "double2.h"
typedef EmulatedSimdType<double2, 2> double4;

template <int imm>
inline double4 blend(const double4 &a, const double4 &b)
{
  double4 c;
  c.x[0] = blend<(imm & 3)>( a.x[0], b.x[0] );
  c.x[1] = blend<(imm >> 2)>( a.x[1], b.x[1] );
  return c;
}

#endif // ARCH_AVX
#endif // ARCH_SSE2

#endif

