
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
 #ifndef GENUA_FLOAT8_H
#define GENUA_FLOAT8_H

#include "sse.h"
#include "simdtype.h"

#ifdef ARCH_AVX

#ifndef __AVX__
#define __AVX__
#endif

#include <immintrin.h>

/** Single-precision SIMD vector.

  float4 tries to emulate the OpenCL short vector syntax in order to
  simplify vectorization. It is, however, not a good match for
  geometric (3D, 4D) vectors. Instead, the most efficient way to use this
  class and variants (float8, double4) is to replace scalar function arguments
  with SIMD vectors. When, for instance, a function computes the intersection of
  two triangles, the vectorized version could process 8 triangle pairs at once
  by replacing 'double' with 'double8' arguments.

  \b Note: Load instructions require aligned memory arguments!

  \ingroup numerics
  \sa double2, double4, double8, float4, float16
*/
struct float8 : public SimdBase<float,8>
{
  typedef float Scalar;
  typedef SimdBase<float,8>   Base;

  /// undefined construction
  float8() {}

  /// set all values to a
  explicit force_inline float8(float a) attr_always_inline {ymm = _mm256_set1_ps(a);}

  /// copy vector type
  explicit force_inline float8(__m256 x) attr_always_inline {ymm = x;}

  /// set from four floats
  float8(float x7, float x6, float x5, float x4,
         float x3, float x2, float x1, float x0) {
    ymm = _mm256_set_ps(x7,x6,x5,x4,x3,x2,x1,x0);
  }

  /// aligned load
  explicit force_inline float8(const float *v) attr_always_inline {
    ymm = _mm256_load_ps(v);
  }

  /// type width
  static int width() attr_always_inline {return 8;}

  /// set all four values to a
  force_inline float8 & operator= (float a) {
    ymm = _mm256_set_ps(a, a, a, a, a, a, a, a);
    return *this;
  }

  /// computed assignment
  force_inline float8 & operator+= (const float8 &a) attr_always_inline {
    ymm = _mm256_add_ps(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  force_inline float8 & operator*= (const float8 &a) attr_always_inline {
    ymm = _mm256_mul_ps(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  force_inline float8 & operator-= (const float8 &a) attr_always_inline {
    ymm = _mm256_sub_ps(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  force_inline float8 & operator/= (const float8 &a) attr_always_inline {
    ymm = _mm256_div_ps(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  force_inline float8 & operator&= (const float8 &a) attr_always_inline {
    ymm = _mm256_and_ps(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  force_inline float8 & operator|= (const float8 &a) attr_always_inline {
    ymm = _mm256_or_ps(ymm, a.ymm);
    return *this;
  }

  /// computed assignment
  force_inline float8 & operator^= (const float8 &a) attr_always_inline {
    ymm = _mm256_xor_ps(ymm, a.ymm);
    return *this;
  }

  /// extract sign bits
  force_inline int signbits() const attr_always_inline {return _mm256_movemask_ps(ymm);}

  // clang does not have the corresponding intrinsics
#if defined(GENUA_ICC)

  /// set first value
  force_inline void first(float a) {
    ymm = _mm256_set_ss(a);
  }

  /// extract first value
  force_inline float first() const {return _mm256_cvtss_f32(ymm);}

#endif

  /// horizontal sum
  float sum() const {
    // hiQuad = ( x7, x6, x5, x4 )
    const __m128 hiQuad = _mm256_extractf128_ps(ymm, 1);
    // loQuad = ( x3, x2, x1, x0 )
    const __m128 loQuad = _mm256_castps256_ps128(ymm);
    // sumQuad = ( x3 + x7, x2 + x6, x1 + x5, x0 + x4 )
    const __m128 sumQuad = _mm_add_ps(loQuad, hiQuad);
    // loDual = ( -, -, x1 + x5, x0 + x4 )
    const __m128 loDual = sumQuad;
    // hiDual = ( -, -, x3 + x7, x2 + x6 )
    const __m128 hiDual = _mm_movehl_ps(sumQuad, sumQuad);
    // sumDual = ( -, -, x1 + x3 + x5 + x7, x0 + x2 + x4 + x6 )
    const __m128 sumDual = _mm_add_ps(loDual, hiDual);
    // lo = ( -, -, -, x0 + x2 + x4 + x6 )
    const __m128 lo = sumDual;
    // hi = ( -, -, -, x1 + x3 + x5 + x7 )
    const __m128 hi = _mm_shuffle_ps(sumDual, sumDual, 0x1);
    // sum = ( -, -, -, x0 + x1 + x2 + x3 + x4 + x5 + x6 + x7 )
    const __m128 sum = _mm_add_ss(lo, hi);
    return _mm_cvtss_f32(sum);
  }

  /// explicit load from aligned memory location
  force_inline void load(const float *v) attr_always_inline {  ymm = _mm256_load_ps(v); }

  /// explicit load from unaligned memory location
  force_inline void loadu(const float *v) attr_always_inline {  ymm = _mm256_loadu_ps(v); }

  /// store to aligned location
  force_inline void store(float *v) const attr_always_inline {_mm256_store_ps(v, ymm);}

  /// store to unaligned location
  force_inline void storeu(float *v) const attr_always_inline {_mm256_storeu_ps(v, ymm);}

  /// return sign mask
  static force_inline float8 signmask() attr_always_inline {
    const union {uint32_t i[8]; __m256 x;} mask = {{0x80000000, 0x80000000,
                                                    0x80000000, 0x80000000,
                                                    0x80000000, 0x80000000,
                                                    0x80000000, 0x80000000}};
    return float8( mask.x );
  }

  /// return mask with all bits zero
  static force_inline float8 zeromask() attr_always_inline {
    return float8(_mm256_setzero_ps());
  }

  /// return mask with all bits one
  static force_inline float8 onemask() attr_always_inline {
    const union {uint32_t i[8]; __m256 x;} mask = {{0xffffffff, 0xffffffff,
                                                    0xffffffff, 0xffffffff,
                                                    0xffffffff, 0xffffffff,
                                                    0xffffffff, 0xffffffff}};
    return float8(mask.x);
  }

  __m256 ymm;
};

// ------------- declaration macros ----------------------------------------

#undef SIMD_DECLARE_ARITHM_OP
#define SIMD_DECLARE_ARITHM_OP(op, intrin) \
  force_inline float8 operator op (const float8 &a, const float8 &b) attr_always_inline; \
  force_inline float8 operator op (const float8 &a, const float8 &b)  \
{ \
  return float8( _mm256_ ## intrin(a.ymm, b.ymm) ); \
  } \
  force_inline float8 operator op (const float8 &a, float b) attr_always_inline; \
  force_inline float8 operator op (const float8 &a, float b) \
{ \
  return a op float8(b); \
  } \
  force_inline float8 operator op (float a, const float8 &b) attr_always_inline; \
  force_inline float8 operator op (float a, const float8 &b)  \
{ \
  return float8(a) op b; \
  } \

#undef SIMD_DECLARE_BINARY_OP
#define SIMD_DECLARE_BINARY_OP(op, intrin) \
  force_inline float8 operator op (const float8 &a, const float8 &b) attr_always_inline; \
  force_inline float8 operator op (const float8 &a, const float8 &b)  \
{ \
  return float8( _mm256_ ## intrin(a.ymm, b.ymm) ); \
  } \

#undef SIMD_DECLARE_BINARY_FN
#define SIMD_DECLARE_BINARY_FN(fn, intrin) \
  force_inline float8 fn(const float8 &a, const float8 &b) attr_always_inline; \
  force_inline float8 fn(const float8 &a, const float8 &b) \
{ \
  return float8( _mm256_ ## intrin(a.ymm, b.ymm) ); \
  } \

#undef SIMD_DECLARE_UNARY_FN
#define SIMD_DECLARE_UNARY_FN(fn, intrin) \
  force_inline float8 fn(const float8 &a) attr_always_inline; \
  force_inline float8 fn(const float8 &a)  \
{ \
  return float8( _mm256_ ## intrin(a.ymm) ); \
  } \

#undef SIMD_DECLARE_CMP_OP
#define SIMD_DECLARE_CMP_OP(op, flag) \
  force_inline float8 operator op (const float8 &a, const float8 &b) attr_always_inline; \
  force_inline float8 operator op (const float8 &a, const float8 &b)  \
{ \
  return float8( _mm256_cmp_ps(a.ymm, b.ymm, flag) ); \
  }

// --------------- logical operators --------------------------------

SIMD_DECLARE_BINARY_OP(&, and_ps)
SIMD_DECLARE_BINARY_OP(|, or_ps)
SIMD_DECLARE_BINARY_OP(^, xor_ps)
SIMD_DECLARE_BINARY_FN(andnot, andnot_ps)
SIMD_DECLARE_CMP_OP(==, _CMP_EQ_UQ)
SIMD_DECLARE_CMP_OP(!=, _CMP_NEQ_UQ)
SIMD_DECLARE_CMP_OP(<, _CMP_LT_OQ)
SIMD_DECLARE_CMP_OP(<=, _CMP_LE_OQ)
SIMD_DECLARE_CMP_OP(>, _CMP_GT_OQ)
SIMD_DECLARE_CMP_OP(>=, _CMP_GE_OQ)

force_inline float8 mask_neq(const float8 &a, const float8 &b) attr_always_inline;
force_inline float8 mask_neq(const float8 &a, const float8 &b)
{
  return float8( _mm256_cmp_ps(a.ymm, b.ymm, _CMP_NEQ_UQ) );
}

force_inline float8 mask_nlt(const float8 &a, const float8 &b) attr_always_inline;
force_inline float8 mask_nlt(const float8 &a, const float8 &b)
{
  return float8( _mm256_cmp_ps(a.ymm, b.ymm, _CMP_NLT_UQ) );
}

force_inline float8 mask_nle(const float8 &a, const float8 &b) attr_always_inline;
force_inline float8 mask_nle(const float8 &a, const float8 &b)
{
  return float8( _mm256_cmp_ps(a.ymm, b.ymm, _CMP_NLE_UQ) );
}

force_inline float8 mask_ngt(const float8 &a, const float8 &b) attr_always_inline;
force_inline float8 mask_ngt(const float8 &a, const float8 &b)
{
  return float8( _mm256_cmp_ps(a.ymm, b.ymm, _CMP_NGT_UQ) );
}

force_inline float8 mask_nge(const float8 &a, const float8 &b) attr_always_inline;
force_inline float8 mask_nge(const float8 &a, const float8 &b)
{
  return float8( _mm256_cmp_ps(a.ymm, b.ymm, _CMP_NGE_UQ) );
}

force_inline float8 operator~ (const float8 &a) attr_always_inline;
force_inline float8 operator~ (const float8 &a)
{
  const union {uint32_t i[8]; __m256 x;} mask = {{0xffffffff, 0xffffffff,
                                                  0xffffffff, 0xffffffff,
                                                  0xffffffff, 0xffffffff,
                                                  0xffffffff, 0xffffffff}};
  return float8(_mm256_xor_ps(mask.x, a.ymm));
}

// --------------- arithmetic operators ------------------

SIMD_DECLARE_ARITHM_OP(+, add_ps)
SIMD_DECLARE_ARITHM_OP(-, sub_ps)
SIMD_DECLARE_ARITHM_OP(*, mul_ps)
SIMD_DECLARE_ARITHM_OP(/, div_ps)

force_inline float8 operator- (const float8 &a) attr_always_inline;
force_inline float8 operator- (const float8 &a)
{
  return (float8::signmask() ^ a);
}

force_inline float8 fabs(const float8 &a) attr_always_inline;
force_inline float8 fabs(const float8 &a)
{
  return andnot( float8::signmask(), a );
}

// return x with the sign of y
force_inline float8 copysign(const float8 &x, const float8 &y) attr_always_inline;
force_inline float8 copysign(const float8 &x, const float8 &y)
{
  float8 m = float8::signmask();
  return ( (m & y) | andnot(m, x) );
}

// return a*b + c
force_inline float8 fmuladd(const float8 &a, const float8 &b, const float8 &c) attr_always_inline;
force_inline float8 fmuladd(const float8 &a, const float8 &b, const float8 &c)
{
#ifdef ARCH_AVX2
  return float8( _mm256_fmadd_ps(a.ymm, b.ymm, c.ymm) );
#else
  return a*b + c;
#endif
}

// return a*b - c
force_inline float8 fmulsub(const float8 &a, const float8 &b, const float8 &c) attr_always_inline;
force_inline float8 fmulsub(const float8 &a, const float8 &b, const float8 &c)
{
#ifdef ARCH_AVX2
  return float8( _mm256_fmsub_ps(a.ymm, b.ymm, c.ymm) );
#else
  return a*b - c;
#endif
}

// --------------- permutations ----------------------------

template <int imm>
force_inline float8 blend(const float8 &a, const float8 &b) attr_always_inline;

template <int imm>
force_inline float8 blend(const float8 &a, const float8 &b)
{
  return float8( _mm256_blend_ps(a.ymm, b.ymm, imm) );
}

force_inline float8 blendv(const float8 &a, const float8 &b, const float8 &mask) attr_always_inline;
force_inline float8 blendv(const float8 &a, const float8 &b, const float8 &mask)
{
  return float8( _mm256_blendv_ps(a.ymm, b.ymm, mask.ymm) );
}

// --------------- mathemetical functions ------------------

//// multiply-add, if available, else emulated, return a*b + c
//force_inline float8 fmadd(const float8 &a, const float8 &b, const float8 &c)
//{
//#ifdef ARCH_AVX2
//  return float8( _mm256_fmadd_ps(a.ymm, b.ymm, c.ymm) );
//#else
//  return a*b + c;
//#endif
//}

//// multiply-substract, if available, else emulated, return a*b - c
//force_inline float8 fmsub(const float8 &a, const float8 &b, const float8 &c)
//{
//#ifdef ARCH_AVX2
//  return float8( _mm256_fmsub_ps(a.ymm, b.ymm, c.ymm) );
//#else
//  return a*b - c;
//#endif
//}

force_inline float8 sqrt(const float8 &a) attr_always_inline;
force_inline float8 sqrt(const float8 &a)
{
  return float8( _mm256_sqrt_ps(a.ymm) );
}

force_inline float8 rsqrt(const float8 &a) attr_always_inline;
force_inline float8 rsqrt(const float8 &a)
{
  return float8( _mm256_rsqrt_ps(a.ymm) );
}

force_inline float8 recip(const float8 &a) attr_always_inline;
force_inline float8 recip(const float8 &a)
{
  return float8( _mm256_rcp_ps(a.ymm) );
}

force_inline bool any_negative(const float8 &a) attr_always_inline;
force_inline bool any_negative(const float8 &a)
{
  return _mm256_movemask_ps(a.ymm) != 0;
}

force_inline float8 max(const float8 &a, const float8 &b) attr_always_inline;
force_inline float8 max(const float8 &a, const float8 &b)
{
  return float8( _mm256_max_ps(a.ymm, b.ymm) );
}

force_inline float8 min(const float8 &a, const float8 &b) attr_always_inline;
force_inline float8 min(const float8 &a, const float8 &b)
{
  return float8( _mm256_min_ps(a.ymm, b.ymm) );
}

#ifdef GENUA_USE_SVML

force_inline float8 cbrt(const float8 &a)
{
  return float8( _mm256_cbrt_ps(a.ymm) );
}

force_inline float8 log(const float8 &a)
{
  return float8( _mm256_log_ps(a.ymm) );
}

force_inline float8 log2(const float8 &a)
{
  return float8( _mm256_log2_ps(a.ymm) );
}

force_inline float8 log10(const float8 &a)
{
  return float8( _mm256_log10_ps(a.ymm) );
}

force_inline float8 exp(const float8 &a)
{
  return float8( _mm256_exp_ps(a.ymm) );
}

force_inline float8 exp2(const float8 &a)
{
  return float8( _mm256_exp2_ps(a.ymm) );
}

force_inline float8 pow(const float8 &a, const float8 &b)
{
  return float8( _mm256_pow_ps(a.ymm, b.ymm) );
}

force_inline float8 sin(const float8 &a)
{
  return float8( _mm256_sin_ps(a.ymm) );
}

force_inline float8 cos(const float8 &a)
{
  return float8( _mm256_cos_ps(a.ymm) );
}

force_inline void sincos(const float8 &a, float8 & sa, float8 & sc)
{
  sa = float8( _mm256_sincos_ps(&(sc.ymm), a.ymm) );
}

force_inline float8 asin(const float8 &a)
{
  return float8( _mm256_asin_ps(a.ymm) );
}

force_inline float8 acos(const float8 &a)
{
  return float8( _mm256_acos_ps(a.ymm) );
}

force_inline float8 atan(const float8 &a)
{
  return float8( _mm256_atan_ps(a.ymm) );
}

force_inline float8 atan2(const float8 &a, const float8 &b)
{
  return float8( _mm256_atan2_ps(a.ymm, b.ymm) );
}

#else // don't have math library for AVX,

#include "avxtrigo.h"

force_inline float8 log(const float8 &a)
{
  return float8( _mm256_log_ps(a.ymm) );
}

force_inline float8 exp(const float8 &a)
{
  return float8( _mm256_exp_ps(a.ymm) );
}

force_inline float8 sin(const float8 &a)
{
  return float8( _mm256_sin_ps(a.ymm) );
}

force_inline float8 cos(const float8 &a)
{
  return float8( _mm256_cos_ps(a.ymm) );
}

force_inline void sincos(const float8 &a, float8 & sa, float8 & sc)
{
  sincos256_ps( a.ymm, &(sa.ymm), &(sc.ymm) );
}

#endif // short-vector math library

#undef SIMD_DECLARE_CMP_OP
#undef SIMD_DECLARE_UNARY_FN
#undef SIMD_DECLARE_BINARY_FN
#undef SIMD_DECLARE_BINARY_OP
#undef SIMD_DECLARE_ARITHM_OP

#else // no AVX available

#include "float4.h"
typedef EmulatedSimdType<float4,2> float8;

template <int imm>
force_inline float8 blend(const float8 &a, const float8 &b) attr_always_inline;

template <int imm>
force_inline float8 blend(const float8 &a, const float8 &b)
{
  float8 c;
  c.x[0] = blend<(imm & 15)>( a.x[0], b.x[0] );
  c.x[1] = blend<(imm >> 4)>( a.x[1], b.x[1] );
  return c;
}

#endif // no AVX

#endif // FLOAT8_H
