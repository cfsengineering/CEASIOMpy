
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
 
#ifndef GENUA_B64ARRAYOPS_H
#define GENUA_B64ARRAYOPS_H

#include <cstring>

#ifdef ARCH_SSE2
#include <emmintrin.h>  // SSE2 intrinsics
#endif

namespace detail
{

template <typename value_type>
struct block64
{
  static void blockcopy(value_type *dst, const value_type *src, size_t nel)
  {
#pragma vector aligned
    for (size_t i=0; i<nel; ++i)
      dst[i] = src[i];
  }

  static void blockfill(value_type *dst, value_type t, size_t nel)
  {
#pragma vector aligned
    for (size_t i=0; i<nel; ++i)
      dst[i] = t;
  }

  static void bytecopy(value_type *dst, const value_type *src, size_t nbytes)
  {
    memcpy(dst, src, nbytes);
  }

  static void bytemove(value_type *dst, const value_type *src, size_t nbytes)
  {
    memmove(dst, src, nbytes);
  }

  static value_type kahan_sum(const value_type *a, size_t n)
  {
    value_type sum(0), c(0), y, t;
#pragma vector aligned
    for (size_t i=0; i<n; ++i) {
      y = a[i] - c;
      t = sum + y;         // sum is big : precision lost
      c = (t - sum) - y;   // recover lost precision
      sum = t;
    }
    return sum;
  }

};

// partial specializations

#ifdef ARCH_SSE2

// blockcopy

template<>
inline void block64<float>::blockcopy(float *dst, const float *src, size_t nel)
{
  assert(pointer_aligned<64>(dst));
  assert(pointer_aligned<64>(src));

  const size_t nb = nel/16;
  for (size_t i=0; i<nb; ++i) {
    _mm_store_ps( dst+0, _mm_load_ps( src+0 ) );
    _mm_store_ps( dst+4, _mm_load_ps( src+4 ) );
    _mm_store_ps( dst+8, _mm_load_ps( src+8 ) );
    _mm_store_ps( dst+12, _mm_load_ps( src+12 ) );
  }
}

template<>
inline void block64<double>::blockcopy(double *dst, const double *src, size_t nel)
{
  assert(pointer_aligned<64>(dst));
  assert(pointer_aligned<64>(src));

  const size_t nb = nel/8;
  for (size_t i=0; i<nb; ++i) {
    _mm_store_pd( dst+0, _mm_load_pd( src+0 ) );
    _mm_store_pd( dst+2, _mm_load_pd( src+2 ) );
    _mm_store_pd( dst+4, _mm_load_pd( src+4 ) );
    _mm_store_pd( dst+6, _mm_load_pd( src+8 ) );
  }
}

// blockfill

template<>
inline void block64<float>::blockfill(float *dst, float t, size_t nel)
{
  assert(pointer_aligned<64>(dst));

  const size_t nb = nel/16;
  __mm128 x = _mm_set_ps(t, t, t, t);
  for (size_t i=0; i<nb; ++i) {
    _mm_store_ps( dst+0, x );
    _mm_store_ps( dst+4, x );
    _mm_store_ps( dst+8, x );
    _mm_store_ps( dst+12, x );
  }
}

template<>
inline void block64<double>::blockfill(double *dst, double t, size_t nel)
{
  assert(pointer_aligned<64>(dst));

  const size_t nb = nel/8;
  __mm128d x = _mm_set_pd(t, t);
  for (size_t i=0; i<nb; ++i) {
    _mm_store_pd( dst+0, x );
    _mm_store_pd( dst+4, x );
    _mm_store_pd( dst+8, x );
    _mm_store_pd( dst+12, x );
  }
}

// kahan sum

template<>
inline value_type block64<float>::kahan_sum(const float *a, size_t n)
{
  __mm128 sum[4], c[4], y[4], t[4];

  for (int i=0; i<4; ++i) {
    sum[i] = _mm_zero_ps();
    c[i] = _mm_zero_ps();
  }

  const size_t nb = nel/16;
  for (size_t i=0; i<nb; ++i) {
    y[0] = _mm_sub_ps( _mm_load_ps(a+0), c[0]);
    t[0] = _mm_add_ps( sum[0], y[0] );
    c[0] = _mm_sub_ps( _mm_sub_ps(t[0], sum[0]), y[0] );
    sum[0] = t[0];

    y[1] = _mm_sub_ps( _mm_load_ps(a+4), c[1]);
    t[1] = _mm_add_ps( sum[1], y[1] );
    c[1] = _mm_sub_ps( _mm_sub_ps(t[1], sum[1]), y[1] );
    sum[1] = t[1];

    y[2] = _mm_sub_ps( _mm_load_ps(a+8), c[2]);
    t[2] = _mm_add_ps( sum[2], y[2] );
    c[2] = _mm_sub_ps( _mm_sub_ps(t[2], sum[2]), y[2] );
    sum[2] = t[2];

    y[3] = _mm_sub_ps( _mm_load_ps(a+12), c[3]);
    t[3] = _mm_add_ps( sum[3], y[3] );
    c[3] = _mm_sub_ps( _mm_sub_ps(t[3], sum[3]), y[3] );
    sum[3] = t[3];
  }

  sum[0] = _mm_add_ps(sum[0], sum[1]);
  sum[2] = _mm_add_ps(sum[2], sum[3]);
  sum[0] = _mm_add_ps(sum[0], sum[2]);

  float res[4];
  _mm_store_ps(sum[0], res);

  return res[0]+res[1]+res[2]+res[3];
}

#endif // ARCH_SSE2

} // namespace detail;

#endif // B64ARRAYOPS_H
