
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
 
#ifndef GENUA_DEFINES_H
#define GENUA_DEFINES_H

#include <vector>
#include <map>
#include <complex>
#include <limits>
#include <cassert>
#include <cmath>
#ifndef Q_MOC_RUN
#include <boost/config.hpp>
#endif

#if defined(__GLIBC__) || defined(__clang__)

#include <cstdint>

#else

#ifndef Q_MOC_RUN
#include <boost/cstdint.hpp>
#endif

using boost::int8_t;
using boost::int16_t;
using boost::int32_t;
using boost::int64_t;

using boost::uint8_t;
using boost::uint16_t;
using boost::uint32_t;
using boost::uint64_t;

#endif

// platform definitions
#if defined(__linux)
#define GENUA_LINUX
#define GENUA_POSIX
#elif defined(__sun)
#define GENUA_SOLARIS
#define GENUA_POSIX
#elif defined(_WIN32)
#define GENUA_WIN32
#elif defined(__APPLE__)
#define GENUA_MACOSX
#define GENUA_POSIX
#else
#define GENUA_GENERIC
#endif

#if defined(__GLIBC__)
#define GENUA_GLIBC __GLIBC__
#endif

// wordsize
#if defined(__LP64__) || defined(_LP64)  
#define GENUA_64BIT
#else
#define GENUA_32BIT
#endif

// compiler detection
#if defined(__clang__)
#define GENUA_CLANG
#elif defined(__INTEL_COMPILER)
#define GENUA_ICC
#elif defined(__GNUG__)
#define GENUA_GCC (__GNUC__ << 16) | (__GNUC_MINOR__ << 8) | (__GNUC_PATCHLEVEL__)
#elif defined(_MSC_VER) && !defined(__INTEL_COMPILER)
#define GENUA_MSVC
#elif defined  __SUNPRO_CC
#define GENUA_SUNCC
#endif

#if defined(GENUA_GCC) || defined(GENUA_CLANG) || (defined(GENUA_ICC) && !defined(GENUA_WIN32))
#define attr_always_inline  __attribute__ ((always_inline))
#define attr_flatten        __attribute__ ((flatten))
// #define attr_target(x)      __attribute__ ((__target__ ( #x )))
#define attr_target(x)
#define force_inline        inline
#elif defined(GENUA_WIN32) && !defined(GENUA_GCC)
#define attr_always_inline
#define attr_flatten
#define attr_target(x)
#define force_inline        __forceinline
#else
#define attr_always_inline
#define attr_flatten
#define attr_target(x)
#define force_inline        inline
#endif

#if defined(GENUA_ICC) && defined(GENUA_LINUX)

#undef isfinite
#undef isnan

namespace std {

inline bool isfinite(double x) { return __builtin_isfinite(x); }
inline bool isfinite(float x) { return __builtin_isfinite(x); }


inline bool isnan(double x) { return __builtin_isnan(x); }
inline bool isnan(float x) { return __builtin_isnan(x); }

}

#endif

// windows
#if defined(GENUA_WIN32)

// #include <windows.h>

// strtod() is *very* stupid on win32 :
// it calls strlen() every time. replace.
#include "strconv.h"
#define genua_strtod  sanos_strtod
#define genua_atof    sanos_atof

// strtol, on the other hand, seems to work
#define genua_strtol   strtol
#define genua_strtoul  strtoul
#define genua_atol     atol

#if defined(GENUA_GCC)
#include <stdint.h>
#define UINT64_LITERAL(x)   static_cast<unsigned long long>(x ## ull)
#define INT64_LITERAL(x)    static_cast<long long>(x ## ll)

// this generates conflicts in C++ 2011 mode because glibc has macros
// of the same name
// using std::isfinite;
// using std::isnormal;
// using std::isnan;

#else

// 4996 warns that the std library is unsafe. of course it is.
#pragma warning(disable : 4996 4244 4267)

// use standard keywords 'and', 'or' etc
#include <iso646.h>

// for 64bit literals
#define UINT64_LITERAL(x)   x ## ui64
#define INT64_LITERAL(x)    x ## i64

// undefine macros min and max (use std:: instead)
#undef min
#undef max

// replace standard functions missing from the MS stdc library
#include <boost/math/tr1.hpp>
#include <boost/math/special_functions/fpclassify.hpp>

// std functions defined from VS 2013 onwards (1800)
namespace std {

#if _MSC_VER < 1800
using boost::math::isfinite;
using boost::math::isnormal;
using boost::math::isnan;

using boost::math::tr1::round;
using boost::math::tr1::roundf;
using boost::math::tr1::acosh;
using boost::math::tr1::acoshf;
using boost::math::tr1::asinh;
using boost::math::tr1::asinhf;
using boost::math::tr1::atanh;
using boost::math::tr1::atanhf;
using boost::math::tr1::cbrt;
using boost::math::tr1::cbrtf;

inline double log2(double a) { return 1.44269504088896 * log(a); }
inline float log2f(float a) { return 1.44269504088896f * logf(a); }
#else
// _MSC_VER == 1800 is Visual Studio 2013, which finally implements
// the missing math functions:
// http://blogs.msdn.com/b/vcblog/archive/2013/07/19/
//       c99-library-support-in-visual-studio-2013.aspx
#endif

}


#ifdef  GENUA_MSVC
// MSVC doesn't know there's a standard for this
#define DEFPRAGMA(x)  __pragma(x)
// this should work according to MSDN, but it has no effect
// #pragma warning( disable : 4100 4244 4068 4267 )
#else
#define DEFPRAGMA(x)  _Pragma(#x)
#endif

#endif // end of win32 but not gcc

#else  // not win32

#define DEFPRAGMA(x)  _Pragma(#x)

#ifdef GENUA_GLIBC

  #ifdef isnan
  #undef isnan
  #undef isfinite
  /*
  #include <boost/math/special_functions/fpclassify.hpp>
  namespace std {
  using boost::math::isfinite;
  using boost::math::isnan;
  }
  */
  #endif

#endif

#include <stdint.h>
#define UINT64_LITERAL(x)   static_cast<unsigned long long>(x ## ull)
#define INT64_LITERAL(x)    static_cast<long long>(x ## ll)

// strtod works fine everywhere else
#define genua_strtod  strtod
#define genua_atof    atof
#define genua_strtol  strtol
#define genua_strtoul  strtoul
#define genua_atol    atol

#endif

#ifndef PI
#ifndef M_PI
#define M_PI 3.14159265358979323846
#define PI   3.14159265358979323846
#else
#define PI   3.14159265358979323846
#endif
#endif

typedef double Real;
typedef std::complex<double> Complex;
static const double gmepsilon(1e-12);

typedef unsigned int   uint;
typedef unsigned char  uchar;
typedef unsigned long  ulong;

typedef std::vector<uint> Indices;
typedef std::vector<std::string> StringArray;
typedef std::map<uint, uint> IndexMap;
typedef std::map<std::string, std::string> StringMap;

const Real huge = std::numeric_limits<Real>::max();
const Real tiny = std::numeric_limits<Real>::min();
const uint NotFound = std::numeric_limits<uint>::max();
const float NotFloat = std::numeric_limits<float>::max();
const double NotDouble = std::numeric_limits<double>::max();

template <class NumType>
inline NumType sq(NumType a) {return a*a;}

template <class NumType>
inline NumType cb(NumType a) {return a*a*a;}

inline bool fnear(Real a, Real b) {return std::fabs(a-b) < gmepsilon;}
inline bool fsmall(Real a) {return std::fabs(a) < gmepsilon;}

template <class NumType>
inline NumType sign(NumType a) {return ((a < 0) ? -1 : 1); }

template <typename Type>
inline Type fabs(std::complex<Type> x) 
{
  return sqrt( sq(real(x)) + sq(imag(x)) );
}

// needed for boost::shared_ptr
struct null_deleter
{
  void operator()(void const *) const {}
};

#ifdef BOOST_NO_CXX11_NULLPTR
#ifndef nullptr
#define nullptr 0
#endif
#endif

// enable compiler-specific pragmas where available

#ifdef GENUA_CLANG

#define CPHINT_FP_CONTRACT    _Pragma("STDC FP_CONTRACT ON")
#define CPHINT_UNROLL_LOOP    _Pragma("clang loop unroll(enable)")
#define CPHINT_SIMD_LOOP      _Pragma("clang loop vectorize(enable)")
#define CPHINT_NOSIMD_LOOP    _Pragma("clang loop vectorize(disable)")
#define CPHINT_HOTSPOT_BEGIN
#define CPHINT_HOTSPOT_END

#elif defined(GENUA_ICC)

#define CPHINT_FP_CONTRACT    _Pragma("STDC FP_CONTRACT ON")
#define CPHINT_UNROLL_LOOP    _Pragma("unroll")
#define CPHINT_SIMD_LOOP      _Pragma("vector")
#define CPHINT_NOSIMD_LOOP    _Pragma("novector")
#define CPHINT_HOTSPOT_BEGIN  _Pragma("intel optimization_level 3")
#define CPHINT_HOTSPOT_END

#elif defined(GENUA_GCC)

#define CPHINT_FP_CONTRACT    _Pragma("STDC FP_CONTRACT ON")
#define CPHINT_UNROLL_LOOP
#define CPHINT_SIMD_LOOP
#define CPHINT_NOSIMD_LOOP
#define CPHINT_HOTSPOT_BEGIN  _Pragma("GCC optimization_level 3")
#define CPHINT_HOTSPOT_END    _Pragma("GCC optimization_level reset")

#elif defined(GENUA_MSVC)

#define CPHINT_FP_CONTRACT    __pragma(fp_contract (on))
#define CPHINT_UNROLL_LOOP
#define CPHINT_SIMD_LOOP
#define CPHINT_NOSIMD_LOOP
#define CPHINT_HOTSPOT_BEGIN  __pragma(optimize("2", on))
#define CPHINT_HOTSPOT_END

#else

#define CPHINT_FP_CONTRACT
#define CPHINT_UNROLL_LOOP
#define CPHINT_SIMD_LOOP
#define CPHINT_NOSIMD_LOOP
#define CPHINT_HOTSPOT_BEGIN
#define CPHINT_HOTSPOT_END

#endif

#endif

