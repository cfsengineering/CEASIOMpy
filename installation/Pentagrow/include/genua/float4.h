
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
 
#ifndef GENUA_FLOAT4_H
#define GENUA_FLOAT4_H

/** \file float4.h
 *  \brief SSE vectorization support.
 *
 *  \b Note: If this file is causing compilation failures, make sure that
 *  the proper architecture flag is defined for your machine. ARCH_SSE2 is
 *  the absolute minimum to use this header; SSE 4.1 (blend instructions) is
 *  highly recommended. When using qmake, you can set CONFIG+=sse41
 *  (and similar) to switch on vectorization support in compilation.
 *
 */

#include "simdbase.h"
#include "sse.h"

#ifdef ARCH_SSE2

#if !defined(GENUA_USE_SVML)

// pull in implementation for trig and log functions
#define USE_SSE2
#include "ssetrigo.h"

#endif

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
  \sa double2, double4, double8, float8, float16
*/
struct float4 : public SimdBase<float,4>
{
  typedef float Scalar;

  /// undefined construction
  float4() {}
  
  /// set all values to a
  explicit force_inline float4(float a) attr_always_inline {xmm = _mm_set1_ps(a);}
  
  /// copy vector type
  explicit force_inline float4(__m128 x) attr_always_inline {xmm = x;}
  
  /// set from four floats
   force_inline float4(float x, float y, float z, float w) attr_always_inline {
    xmm = _mm_set_ps(x, y, z, w);
  }
  
  /// aligned load
  force_inline explicit float4(const float *v) attr_always_inline {
    xmm = _mm_load_ps(v);
  }

  /// vector width
  static int width() attr_always_inline {return 4;}

  /// set all four values to a
  force_inline float4 & operator= (float a) attr_always_inline {
    xmm = _mm_set_ps(a, a, a, a);
    return *this;
  }
  
  /// computed assignment
  force_inline float4 & operator+= (const float4 &a) attr_always_inline {
    xmm = _mm_add_ps(xmm, a.xmm);
    return *this;
  }
  
  /// computed assignment
  force_inline float4 & operator*= (const float4 &a) attr_always_inline {
    xmm = _mm_mul_ps(xmm, a.xmm);
    return *this;
  }
  
  /// computed assignment
  force_inline float4 & operator-= (const float4 &a) attr_always_inline {
    xmm = _mm_sub_ps(xmm, a.xmm);
    return *this;
  }
  
  /// computed assignment
  force_inline float4 & operator/= (const float4 &a) attr_always_inline {
    xmm = _mm_div_ps(xmm, a.xmm);
    return *this;
  }

  /// computed assignment
  force_inline float4 & operator&= (const float4 &a) attr_always_inline {
    xmm = _mm_and_ps(xmm, a.xmm);
    return *this;
  }

  /// computed assignment
  force_inline float4 & operator|= (const float4 &a) attr_always_inline {
    xmm = _mm_or_ps(xmm, a.xmm);
    return *this;
  }

  /// computed assignment
  force_inline float4 & operator^= (const float4 &a) attr_always_inline {
    xmm = _mm_xor_ps(xmm, a.xmm);
    return *this;
  }
  
  /// extract sign bits
  force_inline int signbits() const attr_always_inline {return _mm_movemask_ps(xmm);}

  /// set first value
  force_inline void first(float a) attr_always_inline {xmm = _mm_set_ss(a);}
  
  /// extract first value
  force_inline float first() const attr_always_inline {return _mm_cvtss_f32(xmm);}

  /// horizontal sum (slow)
  force_inline float sum() const attr_always_inline {
#if defined(ARCH_SSE3)
    __m128 t = _mm_castsi128_ps(_mm_shuffle_epi32(_mm_castps_si128(xmm), 0x4d));
    __m128 h = _mm_hadd_ps(xmm, t);
    return _mm_cvtss_f32(h);
#else
    alignas(16) float v[4];
    _mm_store_ps(v, xmm);
    return v[0]+v[1]+v[2]+v[3];
#endif
  }

  /// explicit load from aligned memory location
  force_inline void load(const float *v) attr_always_inline {  xmm = _mm_load_ps(v); }

  /// explicit load from unaligned memory location
  force_inline void loadu(const float *v) attr_always_inline {  xmm = _mm_loadu_ps(v); }
  
  /// store to aligned location
  force_inline void store(float *v) const attr_always_inline {_mm_store_ps(v, xmm);}
  
  /// store to unaligned location
  force_inline void storeu(float *v) const attr_always_inline {_mm_storeu_ps(v, xmm);}
  
  /// return sign mask
  force_inline static float4 signmask() attr_always_inline {
    const union {uint32_t i[4]; __m128 x;} mask = {{0x80000000, 0x80000000,
                                                    0x80000000, 0x80000000}};
    return float4( mask.x );
  }

  /// return mask with all bits zero
  force_inline static float4 zeromask() attr_always_inline {
    return float4(_mm_setzero_ps());
  }

  /// return mask with all bits one
  force_inline static float4 onemask() attr_always_inline {
    const union {uint32_t i[4]; __m128 x;} mask = {{0xffffffff, 0xffffffff,
                                                    0xffffffff, 0xffffffff}};
    return float4(mask.x);
  }

  __m128 xmm; 
};

// ------------- declaration macros ----------------------------------------

#undef SIMD_DECLARE_ARITHM_OP
#define SIMD_DECLARE_ARITHM_OP(op, intrin) \
force_inline float4 operator op (const float4 &a, const float4 &b) attr_always_inline; \
force_inline float4 operator op (const float4 &a, const float4 &b) \
{ \
  return float4( _mm_ ## intrin(a.xmm, b.xmm) ); \
} \
force_inline float4 operator op (const float4 &a, float b) attr_always_inline; \
force_inline float4 operator op (const float4 &a, float b) \
{ \
  return a op float4(b); \
} \
force_inline float4 operator op (float a, const float4 &b) attr_always_inline; \
force_inline float4 operator op (float a, const float4 &b) \
{ \
  return float4(a) op b; \
} \

#undef SIMD_DECLARE_BINARY_OP
#define SIMD_DECLARE_BINARY_OP(op, intrin) \
force_inline float4 operator op (const float4 &a, const float4 &b) attr_always_inline; \
force_inline float4 operator op (const float4 &a, const float4 &b) \
{ \
  return float4( _mm_ ## intrin(a.xmm, b.xmm) ); \
} \

#undef SIMD_DECLARE_BINARY_FN
#define SIMD_DECLARE_BINARY_FN(fn, intrin) \
force_inline float4 fn(const float4 &a, const float4 &b) attr_always_inline; \
force_inline float4 fn(const float4 &a, const float4 &b) \
{ \
  return float4( _mm_ ## intrin(a.xmm, b.xmm) ); \
} \

#undef SIMD_DECLARE_UNARY_FN
#define SIMD_DECLARE_UNARY_FN(fn, intrin) \
force_inline float4 fn(const float4 &a) attr_always_inline; \
force_inline float4 fn(const float4 &a) \
{ \
  return float4( _mm_ ## intrin(a.xmm) ); \
} \

// --------------- logical operators --------------------------------

SIMD_DECLARE_BINARY_OP(&, and_ps)
SIMD_DECLARE_BINARY_OP(|, or_ps)
SIMD_DECLARE_BINARY_OP(^, xor_ps)
SIMD_DECLARE_BINARY_FN(andnot, andnot_ps)
SIMD_DECLARE_BINARY_OP(==, cmpeq_ps)
SIMD_DECLARE_BINARY_OP(!=, cmpneq_ps)
SIMD_DECLARE_BINARY_OP(<, cmplt_ps)
SIMD_DECLARE_BINARY_OP(<=, cmple_ps)
SIMD_DECLARE_BINARY_OP(>, cmpgt_ps)
SIMD_DECLARE_BINARY_OP(>=, cmpge_ps)
SIMD_DECLARE_BINARY_FN(mask_eq, cmpeq_ps)
SIMD_DECLARE_BINARY_FN(mask_neq, cmpneq_ps)
SIMD_DECLARE_BINARY_FN(mask_lt, cmplt_ps)
SIMD_DECLARE_BINARY_FN(mask_le, cmple_ps)
SIMD_DECLARE_BINARY_FN(mask_nle, cmpnle_ps)
SIMD_DECLARE_BINARY_FN(mask_nlt, cmpnlt_ps)
SIMD_DECLARE_BINARY_FN(mask_gt, cmpgt_ps)
SIMD_DECLARE_BINARY_FN(mask_ge, cmpge_ps)
SIMD_DECLARE_BINARY_FN(mask_nge, cmpnge_ps)
SIMD_DECLARE_BINARY_FN(mask_ngt, cmpngt_ps)

force_inline float4 operator~ (const float4 &a) attr_always_inline;
force_inline float4 operator~ (const float4 &a)
{
  const union {uint32_t i[4]; __m128 x;} mask = {{0xffffffff, 0xffffffff,
                                                  0xffffffff, 0xffffffff}};
  return float4(_mm_xor_ps(mask.x, a.xmm));
}

// --------------- arithmetic operators ------------------

SIMD_DECLARE_ARITHM_OP(+, add_ps)
SIMD_DECLARE_ARITHM_OP(-, sub_ps)
SIMD_DECLARE_ARITHM_OP(*, mul_ps)
SIMD_DECLARE_ARITHM_OP(/, div_ps)

force_inline float4 operator- (const float4 &a) attr_always_inline;
force_inline float4 operator- (const float4 &a)
{
  return (float4::signmask() ^ a);
}

force_inline float4 fabs(const float4 &a) attr_always_inline;
force_inline float4 fabs(const float4 &a)
{
  return andnot( float4::signmask(), a );
}

// return x with the sign of y
force_inline float4 copysign(const float4 &x, const float4 &y) attr_always_inline;
force_inline float4 copysign(const float4 &x, const float4 &y)
{
  float4 m = float4::signmask();
  return ( (m & y) | andnot(m, x) );
}

// return a*b + c
force_inline float4 fmuladd(const float4 &a, const float4 &b, const float4 &c) attr_always_inline;
force_inline float4 fmuladd(const float4 &a, const float4 &b, const float4 &c)
{
#ifdef ARCH_AVX2
  return float4( _mm_fmadd_ps(a.xmm, b.xmm, c.xmm) );
#else
  return a*b + c;
#endif
}

// return a*b - c
force_inline float4 fmulsub(const float4 &a, const float4 &b, const float4 &c) attr_always_inline;
force_inline float4 fmulsub(const float4 &a, const float4 &b, const float4 &c)
{
#ifdef ARCH_AVX2
  return float4( _mm_fmsub_ps(a.xmm, b.xmm, c.xmm) );
#else
  return a*b - c;
#endif
}

// --------------- mathematical functions ------------------

SIMD_DECLARE_UNARY_FN(sqrt, sqrt_ps)
SIMD_DECLARE_UNARY_FN(rsqrt, rsqrt_ps)
SIMD_DECLARE_UNARY_FN(recip, rcp_ps)
SIMD_DECLARE_BINARY_FN(max, max_ps)
SIMD_DECLARE_BINARY_FN(min, min_ps)

#ifdef GENUA_USE_SVML

SIMD_DECLARE_UNARY_FN(cbrt, cbrt_ps)
SIMD_DECLARE_BINARY_FN(pow, pow_ps)
SIMD_DECLARE_UNARY_FN(log, log_ps)
SIMD_DECLARE_UNARY_FN(log2, log2_ps)
SIMD_DECLARE_UNARY_FN(log10, log10_ps)
SIMD_DECLARE_UNARY_FN(exp, exp_ps)
SIMD_DECLARE_UNARY_FN(exp2, exp2_ps)
SIMD_DECLARE_UNARY_FN(sin, sin_ps)
SIMD_DECLARE_UNARY_FN(cos, cos_ps)
SIMD_DECLARE_UNARY_FN(asin, asin_ps)
SIMD_DECLARE_UNARY_FN(acos, acos_ps)
SIMD_DECLARE_UNARY_FN(atan, atan_ps)
SIMD_DECLARE_BINARY_FN(atan2, atan2_ps)

force_inline void sincos(const float4 &a, float4 & sa, float4 & sc) attr_always_inline;
force_inline void sincos(const float4 &a, float4 & sa, float4 & sc)
{
  sa = float4( _mm_sincos_ps(&(sc.xmm), a.xmm) );
}

#else

// use internal implementation in ssetrigo.h

force_inline float4 log(const float4 &a) { return float4( log_ps(a.xmm) ); }
force_inline float4 exp(const float4 &a) { return float4( exp_ps(a.xmm) ); }
force_inline float4 sin(const float4 &a) { return float4( sin_ps(a.xmm) ); }
force_inline float4 cos(const float4 &a) { return float4( cos_ps(a.xmm) ); }
force_inline void sincos(const float4 &a, float4 & sa, float4 & sc)
{
  sincos_ps(a.xmm, &(sa.xmm), &(sc.xmm));
}

#endif

//// multiply-add, if available, else emulated, return a*b + c
//force_inline float4 fmadd(const float4 &a, const float4 &b, const float4 &c)
//{
//#ifdef ARCH_AVX2
//  return float4( _mm_fmadd_ps(a.xmm, b.xmm, c.xmm) );
//#else
//  return a*b + c;
//#endif
//}

//// multiply-substract, if available, else emulated, return a*b - c
//force_inline float4 fmsub(const float4 &a, const float4 &b, const float4 &c)
//{
//#ifdef ARCH_AVX2
//  return float4( _mm_fmsub_ps(a.xmm, b.xmm, c.xmm) );
//#else
//  return a*b - c;
//#endif
//}

force_inline bool any_negative(const float4 &a)
{
  return _mm_movemask_ps(a.xmm) != 0;
}

// --------------- permutations ------------------

force_inline void swap(float4 & x, float4 & y)
{
  x = x ^ y;
  y = y ^ x;
  x = x ^ y;
}

#if !defined(_MSC_VER) && !defined(__clang__)

// Microsoft compiler is too stupid to see that the arguments to these
// force_inline functions always are literal constants. Can't use it with MSVC.

force_inline float4 shuffle(const float4 &a, const float4 &b,
                      int fp3, int fp2, int fp1, int fp0)
{
  return float4( _mm_shuffle_ps(a.xmm, b.xmm,
                                (fp3 << 6)|(fp2 << 4)|(fp1 << 2)|fp0) );
}

// return [ai ai ai ai]
force_inline float4 splat(const float4 &a, int i)
{
  return float4( _mm_shuffle_ps(a.xmm, a.xmm, (i << 6)|(i << 4)|(i << 2)|i) );
}

#else // Microsoft compiler or clang

#define shuffle(a, b, fp3, fp2, fp1, fp0) \
  float4( _mm_shuffle_ps((a).xmm, (b).xmm, ((fp3) << 6)|((fp2) << 4)|((fp1) << 2)|(fp0))

#define splat(a, i) \
  float4( _mm_shuffle_ps((a).xmm, (a).xmm, ((i) << 6)|((i) << 4)|((i) << 2)|(i) )

#endif

// return [a0 a2 b0 b2]
force_inline float4 interleave_even(const float4 &a, const float4 &b)
{
  return float4( _mm_shuffle_ps(a.xmm, b.xmm, (2 << 6)|(2 << 2)) );
}

// return [a1 a3 b1 b3]
force_inline float4 interleave_odd(const float4 &a, const float4 &b)
{
  return float4( _mm_shuffle_ps(a.xmm, b.xmm, (3 << 6)|(1 << 4)|(3 << 2)|1) );
}

#ifdef ARCH_SSE41

template <int imm>
force_inline float4 blend(const float4 &a, const float4 &b) attr_always_inline;

template <int imm>
force_inline float4 blend(const float4 &a, const float4 &b)
{
  return float4( _mm_blend_ps(a.xmm, b.xmm, imm) );
}

force_inline float4 blendv(const float4 &a, const float4 &b, const float4 &mask) attr_always_inline;
force_inline float4 blendv(const float4 &a, const float4 &b, const float4 &mask)
{
  return float4( _mm_blendv_ps(a.xmm, b.xmm, mask.xmm) );
}

#else

template <int imm>
inline float4 blend(const float4 &, const float4 &)
{
  float4 z(0.0f);
  assert(!"blend() requires at least SSE4.1");
  return z;
}

#endif

#ifdef ARCH_SSE3

/** Horizontal addition.

  c = hadd(a,b) is equivalent to 
  c[0] = a[0] + a[1]
  c[1] = a[2] + a[3]
  c[2] = b[0] + b[1]
  c[3] = b[2] + b[3]
 */
SIMD_DECLARE_BINARY_FN(hadd, hadd_ps)

#else // have SSE2, but no SSE3, must emulate _mm_hadd_ps

force_inline float4 hadd(const float4 &a, const float4 &b) attr_always_inline;
force_inline float4 hadd(const float4 &a, const float4 &b)
{
  return interleave_even(a,b) + interleave_odd(a,b);
}

#endif // hadd()

force_inline float hadd(const float4 &a) attr_always_inline;
force_inline float hadd(const float4 &a)
{
  float4 t = hadd(a,a);
  t = hadd(t,t);
  return t.first();
}

force_inline float dot(const float4 &a, const float4 &b) attr_always_inline;
force_inline float dot(const float4 &a, const float4 &b)
{
  float4 r1 = a*b;
  float4 r2 = hadd(r1, r1);
  float4 r3 = hadd(r2, r2);
  return r3.first();
}

#undef SIMD_DECLARE_UNARY_FN
#undef SIMD_DECLARE_BINARY_FN
#undef SIMD_DECLARE_BINARY_OP
#undef SIMD_DECLARE_ARITHM_OP

#endif // ARCH_SSE2

#endif
