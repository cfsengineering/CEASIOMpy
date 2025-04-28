/* Copyright (C) 2015 David Eller <david@larosterna.com>
 *
 * This program is free software; you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free Software
 * Foundation; either version 2 of the License, or (at your option) any later
 * version. This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details. You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
 */

#ifndef BITFIDDLE_H
#define BITFIDDLE_H

#include "defines.h"

#ifdef GENUA_MSVC
#include <intrin.h>
#endif

typedef union { float f; int32_t i; uint32_t u;} union32_t;
typedef union { double f; int64_t i; uint64_t u;} union64_t;

#define FLOAT_SIGNMASK  (1 << 31);
#define DOUBLE_SIGNMASK INT64_LITERAL(0x8000000000000000)

/* Implementation of copysign() for MSVC, which does not have it */

#ifdef _MSC_VER
inline float copysignf(float x, float y)
#else
inline float genua_copysignf(float x, float y)
#endif
{
  // better done with SSE, need to check for movemask intrisics
  // and argument alignment
  union32_t ux, uy;
  ux.f = x;
  uy.f = y;
  ux.i &= ~FLOAT_SIGNMASK;     // zero out the sign bit of x
  uy.i &=  FLOAT_SIGNMASK;     // keep just the sign of y
  ux.i = ux.i | uy.i;
  return ux.f;
}

#ifdef _MSC_VER
inline double copysign(double x, double y)
#else
inline double genua_copysign(double x, double y)
#endif
{
  union64_t ux, uy;
  ux.f = x;
  uy.f = y;
  ux.i &= ~DOUBLE_SIGNMASK;     // zero out the sign bit of x
  uy.i &=  DOUBLE_SIGNMASK;     // keep just the sign of y
  ux.i = ux.i | uy.i;
  return ux.f;
}

//template <class Type, int N>
//inline const Type *align_pointer(const Type *p)
//{
//  union { const Type *ptr; size_t s; } up;
//  up.ptr = p;
//  up.s += (N - 1);
//  up.s &= ~(N - 1);
//  return up.ptr;
//}

template <int N>
inline bool pointer_aligned(const void *p)
{
  union { const void *ptr; size_t s; } up;
  up.ptr = p;
  const size_t mask = (N - 1);
  return (up.s & mask) == 0;
}

template <class Type>
inline Type nextpow2(Type k)
{
  // assuming signed type or k > 0
  k--;
  for (int i=1; i<int(sizeof(Type)*8); i<<=1)
    k = k | k >> i;
  return k+1;
}

template <class Type>
int floorlog2(Type n)
{
  // obvious version
  if (n <= 0)
    return -1;

  int lg2 = 0;
  while (n >>= 1)
    ++lg2;
  return lg2;

  //  assert(sizeof(uint) == 4);
  //  if (n == 0)
  //    return -1;

  //  int pos = 0;
  //  if (n >= 1 << 16) {
  //    n >>= 16;
  //    pos += 16;
  //  }
  //  if (n >= 1 << 8) {
  //    n >>=  8;
  //    pos +=  8;
  //  }
  //  if (n >= 1 << 4) {
  //    n >>=  4;
  //    pos +=  4;
  //  }
  //  if (n >= 1 << 2) {
  //    n >>=  2;
  //    pos +=  2;
  //  }
  //  if (n >= 1 << 1) {
  //    pos +=  1;
  //  }
  //  return pos;
}

template <class Type>
int ceillog2(Type n)
{
  // obvious version
  if (n <= 0)
    return -1;

  return floorlog2(n - 1) + 1;
}

inline int lzcount32(uint32_t x)
{
#if defined(GENUA_ICC)
  return x == 0 ? 32 : (31 - _bit_scan_reverse(x));
#elif defined(GENUA_GCC) || defined(GENUA_CLANG)
  return x == 0 ? 32 : __builtin_clz(x);
#elif defined(_MSC_VER)
  unsigned long index;
  unsigned char flag = _BitScanReverse(&index, x);
  return (flag != 0) ? (31 - index) : 32;
#else
  int r = 0;
  while (x >>= 1)
    r++;
  return r;
#endif
}

inline int lzcount64(uint64_t x)
{
#if defined(GENUA_GCC) || defined(GENUA_CLANG)
  if (sizeof(uint64_t) == sizeof(long))
    return x == 0 ? 64 : __builtin_clzl(x);
  else
    return x == 0 ? 64 : __builtin_clzll(x);
#elif defined(_MSC_VER) && defined(_M_X64)
  unsigned long index;
  unsigned char flag = _BitScanReverse64(&index, x);
  return (flag != 0) ? (63 - index) : 64;
#else
  int r = 0;
  while (x >>= 1)
    r++;
  return r;
#endif
}

// single precision float

inline uint32_t ieee_exponent(float f)
{
  union32_t u;
  u.f = f;
  return (u.i & 0x7f800000) >> 23;
}

inline uint32_t ieee_mantissa(float f)
{
  union32_t u;
  u.f = f;
  return (u.i & 0x007FFFFF);
}

// double precision float

inline uint64_t ieee_exponent(double f)
{
  union64_t u;
  u.f = f;
  return (u.i & INT64_LITERAL(0x7ff0000000000000)) >> 52;
}

inline uint64_t ieee_mantissa(double f)
{
  union64_t u;
  u.f = f;
  return (u.i & INT64_LITERAL(0x000fffffffffffff));
}

inline uint32_t reverse_bits(uint32_t v)
{
  v = ((v >> 1) & 0x55555555) | ((v & 0x55555555) << 1);
  v = ((v >> 2) & 0x33333333) | ((v & 0x33333333) << 2);
  v = ((v >> 4) & 0x0F0F0F0F) | ((v & 0x0F0F0F0F) << 4);
  v = ((v >> 8) & 0x00FF00FF) | ((v & 0x00FF00FF) << 8);
  v = ( v >> 16             ) | ( v               << 16);
  return v;
}

inline uint64_t reverse_bits(uint64_t v)
{
  v = ((v >> 1)  & UINT64_LITERAL(0x5555555555555555)) |
      ((v & UINT64_LITERAL(0x5555555555555555)) << 1);
  v = ((v >> 2)  & UINT64_LITERAL(0x3333333333333333)) |
      ((v & UINT64_LITERAL(0x3333333333333333)) << 2);
  v = ((v >> 4)  & UINT64_LITERAL(0x0F0F0F0F0F0F0F0F)) |
      ((v & UINT64_LITERAL(0x0F0F0F0F0F0F0F0F)) << 4);
  v = ((v >> 8)  & UINT64_LITERAL(0x00FF00FF00FF00FF)) |
      ((v & UINT64_LITERAL(0x00FF00FF00FF00FF)) << 8);
  v = ((v >> 16) & UINT64_LITERAL(0x0000FFFF0000FFFF)) |
      ((v & UINT64_LITERAL(0x0000FFFF0000FFFF)) << 16);
  v = ( v >> 32             ) | ( v               << 32);
  return v;
}

inline bool bit_is_set(uint bitset, uint bits)
{
  return (bitset & bits) == bits;
}

inline bool allbits_set(uint bitset, uint bits)
{
  return (bitset & bits) == bits;
}

inline bool anybit_set(uint bitset, uint bits)
{
  return (bitset & bits) != 0;
}

inline bool allbits_unset(uint bitset, uint bits)
{
  return (bitset & bits) == 0;
}

inline bool anybit_unset(uint bitset, uint bits)
{
  return (bitset & bits) != bits;
}

#endif // BITFIDDLE_H
