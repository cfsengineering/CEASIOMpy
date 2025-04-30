
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
 
#ifndef GENUA_SSE_H
#define GENUA_SSE_H

#include "bitfiddle.h"

#if defined(__INTEL_COMPILER)

#if defined(__AVX2__) && !defined(ARCH_AVX2)
#define ARCH_AVX2
#elif defined(__AVX__) && !defined(ARCH_AVX)
#define ARCH_AVX
#elif defined(__SSE4_2__) && !defined(ARCH_SSE42)
#define ARCH_SSE42
#elif defined(__SSE4_1__) && !defined(ARCH_SSE41)
#define ARCH_SSE41
#elif defined(__SSE3__) && !defined(ARCH_SSE3)
#define ARCH_SSE3
#elif defined(__SSE2__) && !defined(ARCH_SSE2)
#define ARCH_SSE2
#endif

// contains all intrinsics, including SVML definitions
#include <immintrin.h>
#define GENUA_USE_SVML

#elif defined(__GNUC__)  // works for clang as well

#if defined(__AVX2__) && !defined(ARCH_AVX2)
#define ARCH_AVX2
#elif defined(__AVX__) && !defined(ARCH_AVX)
#define ARCH_AVX
#elif defined(__SSE4_2__) && !defined(ARCH_SSE42)
#define ARCH_SSE42
#elif defined(__SSE4_1__) && !defined(ARCH_SSE41)
#define ARCH_SSE41
#elif defined(__SSE3__) && !defined(ARCH_SSE3)
#define ARCH_SSE3
#elif defined(__SSE2__) && !defined(ARCH_SSE2)
#define ARCH_SSE2
#endif

#endif  // compiler-specific

#if defined(ARCH_AVX2)

// #pragma message("AVX2")

// introduced with Haswell

#ifndef ARCH_AVX
#define ARCH_AVX
#endif

#ifndef ARCH_SSE42
#define ARCH_SSE42
#endif

#ifndef ARCH_SSE41
#define ARCH_SSE41
#endif

#ifndef ARCH_SSE3
#define ARCH_SSE3
#endif

#ifndef ARCH_SSE2
#define ARCH_SSE2
#endif

#ifndef ARCH_SSE
#define ARCH_SSE
#endif

#ifndef ARCH_FN
#define ARCH_FN(x)  x ## _avx2
#endif

#include <immintrin.h>

#elif defined(ARCH_AVX)

// introduced with Sandy Bridge, Core i3/5/7-2xxx

// #pragma message("AVX")

#ifndef ARCH_SSE42
#define ARCH_SSE42
#endif

#ifndef ARCH_SSE41
#define ARCH_SSE41
#endif

#ifndef ARCH_SSE3
#define ARCH_SSE3
#endif

#ifndef ARCH_SSE2
#define ARCH_SSE2
#endif

#ifndef ARCH_SSE
#define ARCH_SSE
#endif

#ifndef ARCH_FN
#define ARCH_FN(x)  x ## _avx
#endif

#include <immintrin.h>

#elif defined(ARCH_SSE42)

// introduced with Nehalem, Core i3/5/7-xxx

// #pragma message("SSE 4.2")

#ifndef ARCH_SSE41
#define ARCH_SSE41
#endif

#ifndef ARCH_SSE3
#define ARCH_SSE3
#endif

#ifndef ARCH_SSE2
#define ARCH_SSE2
#endif

#ifndef ARCH_SSE
#define ARCH_SSE
#endif

#ifndef ARCH_FN
#define ARCH_FN(x)  x ## _sse42
#endif

#include <nmmintrin.h>

#elif defined(ARCH_SSE41)

// introduced with Penryn, Core 2 Duo E7xxx/E8xxx/P7xxx-P9xxx/T7xxx-T9xxx

// #pragma message("SSE 4.1")

#ifndef ARCH_SSE3
#define ARCH_SSE3
#endif

#ifndef ARCH_SSE2
#define ARCH_SSE2
#endif

#ifndef ARCH_SSE
#define ARCH_SSE
#endif

#ifndef ARCH_FN
#define ARCH_FN(x)  x ## _sse41
#endif

#include <smmintrin.h>

#elif defined(ARCH_SSE3)

// #pragma message("SSE3")

#ifndef ARCH_SSE2
#define ARCH_SSE2
#endif

#ifndef ARCH_SSE
#define ARCH_SSE
#endif

#ifndef ARCH_FN
#define ARCH_FN(x)  x ## _sse3
#endif

#include <pmmintrin.h>

#elif defined(ARCH_SSE2)

// #pragma message("SSE2")

#ifndef ARCH_SSE
#define ARCH_SSE
#endif

#ifndef ARCH_FN
#define ARCH_FN(x)  x ## _sse2
#endif

#include <emmintrin.h>

#elif defined(ARCH_SSE)

#ifndef ARCH_FN
#define ARCH_FN(x)  x ## _sse
#endif

#include <xmmintrin.h>

#else // no SIMD ISA support

#ifndef ARCH_FN
#define ARCH_FN(x)  x ## _generic
#endif

#endif  // ARCH_ selector

#ifdef _MSC_VER /* visual c++  or icc/win */
# define ALIGNAS(bytes)  __declspec(align(bytes))  
# define ALIGNED_SSE __declspec(align(16))
# define ALIGNED_AVX __declspec(align(32))
#else /* gcc or icc/mac or icc/linux */
#if defined(GENUA_CLANG)
# define ALIGNAS(bytes)  alignas(bytes)
#elif defined(GENUA_GCC)
#if ((GENUA_GCC) >= ((4 << 16)|(8 << 8)))
# define ALIGNAS(bytes)  alignas(bytes)
#else
# define ALIGNAS(bytes) __attribute__((__aligned__(bytes)))
#endif // gcc version
#endif // unix
# define ALIGNED_SSE __attribute__((__aligned__(16)))
# define ALIGNED_AVX __attribute__((__aligned__(32)))
#endif

#define SSE_PS_CONST1(Name, Val) ALIGNED_SSE const float Name[4] = { Val, Val, Val, Val }
#define SSE_PS_CONST4(Name, Val0, Val1, Val2, Val3) ALIGNED_SSE const float Name[4] = { Val0, Val1, Val2, Val3 }

inline bool sse_aligned(const void *p) {return pointer_aligned<16>(p);}
inline bool avx_aligned(const void *p) {return pointer_aligned<32>(p);}

#undef QUAD_SHUFFLE
#define QUAD_SHUFFLE(a,b,c,d)  ( (a) | (b) << 2 | (c) << 4 | (d) << 6 )


#endif // SSE_H
