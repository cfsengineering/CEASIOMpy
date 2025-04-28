
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
 
#ifndef GENUA_SIMDSUPPORT_H
#define GENUA_SIMDSUPPORT_H

#include "sse.h"
#include "simdtype.h"
#include "float4.h"
#include "float8.h"
#include "double2.h"
#include "double4.h"

// MSVC does not ignore "pragma omp simd" as required by the standard, so
// it needs to be disabled by macro instead
//
#if defined(_OPENMP) && (_OPENMP >= 201307)
#define PRAGMA_(x) _Pragma(#x)
#define OMP(directive) PRAGMA_(omp directive)
#define OMP_SIMD(clause) PRAGMA_("omp simd" clause)
#else
#define OMP_SIMD(x)
#endif

#ifdef ARCH_AVX

// the following types are always emulated until AVX-512 shows up

typedef EmulatedSimdType<float8, 2> float16;
typedef EmulatedSimdType<double4, 2> double8;
typedef EmulatedSimdType<double4, 4> double16;

template <int imm>
inline float16 blend(const float16 &a, const float16 &b)
{
  float16 c;
  c.x[0] = blend<(imm & 255)>( a.x[0], b.x[0] );
  c.x[1] = blend<(imm >> 8)>( a.x[1], b.x[1] );
  return c;
}

template <int imm>
inline double8 blend(const double8 &a, const double8 &b)
{
  double8 c;
  c.x[0] = blend<(imm & 15)>( a.x[0], b.x[0] );
  c.x[1] = blend<(imm >> 4)>( a.x[1], b.x[1] );
  return c;
}

template <int imm>
inline double16 blend(const double16 &a, const double16 &b)
{
  double16 c;
  c.x[0] = blend<(imm & 15)>( a.x[0], b.x[0] );
  c.x[1] = blend<((imm >> 4) & 15)>( a.x[1], b.x[1] );
  c.x[2] = blend<((imm >> 8) & 15)>( a.x[2], b.x[2] );
  c.x[3] = blend<((imm >> 12) & 15)>( a.x[3], b.x[3] );
  return c;
}

#else

typedef EmulatedSimdType<float4, 4> float16;
typedef EmulatedSimdType<double2, 4> double8;
typedef EmulatedSimdType<double2, 8> double16;

template <int imm>
inline float16 blend(const float16 &a, const float16 &b)
{
  float16 c;
  c.x[0] = blend<(imm & 15)>( a.x[0], b.x[0] );
  c.x[1] = blend<((imm >> 4) & 15)>( a.x[1], b.x[1] );
  c.x[2] = blend<((imm >> 8) & 15)>( a.x[2], b.x[2] );
  c.x[3] = blend<((imm >> 12) & 15)>( a.x[3], b.x[3] );
  return c;
}

template <int imm>
inline double8 blend(const double8 &a, const double8 &b)
{
  double8 c;
  c.x[0] = blend<(imm & 3)>( a.x[0], b.x[0] );
  c.x[1] = blend<((imm >> 2) & 3)>( a.x[1], b.x[1] );
  c.x[2] = blend<((imm >> 4) & 3)>( a.x[2], b.x[2] );
  c.x[3] = blend<((imm >> 6) & 3)>( a.x[3], b.x[3] );
  return c;
}

template <int imm>
inline double16 blend(const double16 &a, const double16 &b)
{
  double16 c;
  c.x[0] = blend<(imm & 3)>( a.x[0], b.x[0] );
  c.x[1] = blend<((imm >> 2) & 3)>( a.x[1], b.x[1] );
  c.x[2] = blend<((imm >> 4) & 3)>( a.x[2], b.x[2] );
  c.x[3] = blend<((imm >> 6) & 3)>( a.x[3], b.x[3] );
  c.x[4] = blend<((imm >> 8) & 3)>( a.x[4], b.x[4] );
  c.x[5] = blend<((imm >> 10) & 3)>( a.x[5], b.x[5] );
  c.x[6] = blend<((imm >> 12) & 3)>( a.x[6], b.x[6] );
  c.x[7] = blend<((imm >> 14) & 3)>( a.x[7], b.x[7] );
  return c;
}

#endif

// ----------------- global functions for all vector types ------------------

// mask ? b : a
inline float4 select(const float4 &a, const float4 &b, const float4 &mask)
{
  return (mask & b) | andnot(mask, a);
}

inline float8 select(const float8 &a, const float8 &b, const float8 &mask)
{
  return (mask & b) | andnot(mask, a);
}

inline float16 select(const float16 &a, const float16 &b, const float16 &mask)
{
  return (mask & b) | andnot(mask, a);
}

inline double2 select(const double2 &a, const double2 &b, const double2 &mask)
{
  return (mask & b) | andnot(mask, a);
}

inline double4 select(const double4 &a, const double4 &b, const double4 &mask)
{
  return (mask & b) | andnot(mask, a);
}

inline double8 select(const double8 &a, const double8 &b, const double8 &mask)
{
  return (mask & b) | andnot(mask, a);
}

inline double16 select(const double16 &a, const double16 &b, const double16 &mask)
{
  return (mask & b) | andnot(mask, a);
}

inline float select(float a, float b, bool mask)
{
  return mask ? b : a;
}

inline double select(double a, double b, bool mask)
{
  return mask ? b : a;
}

#endif // SIMDSUPPORT_H
