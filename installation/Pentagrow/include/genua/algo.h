
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

#ifndef GENUA_ALGO_H
#define GENUA_ALGO_H

#include "defines.h"
#include <algorithm>
#include <numeric>
#include <cstdlib>

force_inline bool hint_likely(bool expr)
{
#if (GCC_VERSION >= 302) || (__INTEL_COMPILER >= 800) || defined(__clang__)
  return __builtin_expect(expr != 0, 1);
#else
  return expr;
#endif
}

force_inline bool hint_unlikely(bool expr)
{
#if (GCC_VERSION >= 302) || (__INTEL_COMPILER >= 800) || defined(__clang__)
  return __builtin_expect(expr != 0, 0);
#else
  return expr;
#endif
}

/// sort v and make unique (no allocation)
template <typename Container>
inline uint sort_unique(Container & v)
{
  std::sort(v.begin(), v.end());
  typename Container::iterator pos;
  pos = std::unique(v.begin(), v.end());
  v.erase(pos, v.end());
  return v.size();
}

/// sort tail, make unique and merge
template <typename Container>
size_t unique_merge_tail(size_t itail, Container &v)
{
  std::sort( v.begin()+itail, v.end() );
  v.erase( std::unique( v.begin()+itail, v.end() ), v.end() );
  std::inplace_merge(v.begin(), v.begin()+itail, v.end());
  v.erase( std::unique( v.begin(), v.end() ), v.end() );
  return v.size();
}

/// return index set which puts range into sorted order
template <class Iterator, class Comparison>
Indices isort(Iterator first, Iterator last, Comparison c)
{
  const size_t n = std::distance(first, last);
  Indices idx(n);
  std::iota(idx.begin(), idx.end(), 0);
  std::sort(idx.begin(), idx.end(), [&](uint a, uint b) {
    return c( *(first+a), *(first+b) );
  });
  return idx;
}

template <class Iterator>
Indices isort(Iterator first, Iterator last)
{
  typedef typename std::iterator_traits<Iterator>::value_type value_type;
  auto c = std::less<value_type>();
  return isort(first, last, c);
}

/// return iterator pointing to largest absolute value
template <class Iterator>
Iterator maxabs_element(Iterator first, Iterator last)
{
  typedef typename std::iterator_traits<Iterator>::value_type value_type;
  value_type maxval(0);
  Iterator pos, mpos = first;
  for (pos = first; pos != last; ++pos) {
    value_type xabs = std::abs(*pos);
    if (xabs > maxval) {
      maxval = xabs;
      mpos = pos;
    }
  }
  return mpos;
}

/// insert x into c so that x remains sorted
template <typename Container, typename Value>
inline void insert_sorted(Container & c, const Value & x)
{
  typename Container::iterator pos;
  pos = std::lower_bound(c.begin(), c.end(), x);
  c.insert(pos, x);
}

/// if x is not already in c, insert and return true, else false
template <typename Container, typename Value>
inline bool insert_once(Container & c, const Value & x)
{
  typename Container::iterator pos;
  pos = std::lower_bound(c.begin(), c.end(), x);
  if (pos == c.end() or *pos != x) {
    c.insert(pos, x);
    return true;
  } else {
    return false;
  }
}

template <class Container, class Value>
inline uint sorted_index(const Container & c,
                         const Value & x)
{
  typename Container::const_iterator pos;
  pos = std::lower_bound(c.begin(), c.end(), x);
  if (pos != c.end() and *pos == x)
    return std::distance(c.begin(), pos);
  else
    return NotFound;
}

template <class Container, class Value, class Comparison>
inline uint sorted_index(const Container & c,
                         const Value & x, Comparison cmp)
{
  typename Container::const_iterator pos;
  pos = std::lower_bound(c.begin(), c.end(), x, cmp);
  if ( pos != c.end() and (not cmp(*pos,x)) and (not cmp(x,*pos)) )
    return std::distance(c.begin(), pos);
  else
    return NotFound;
}

/// change the order of values in a in a random manner
template <typename Container>
inline void random_shuffle(Container & a)
{
  const uint n(a.size());
  for (uint i=0; i<n; ++i) {
    uint k = rand() % n;
    std::swap(a[i],a[k]);
  }
}

template<typename ValueType, class Compare>
inline const ValueType& median_of_three(const ValueType& a, const ValueType& b,
                                        const ValueType& c, Compare cmp)
{
  if (cmp(a, b))
    if (cmp(b, c))
      return b;
    else if (cmp(a, c))
      return c;
    else
      return a;
  else if (cmp(a, c))
    return a;
  else if (cmp(b, c))
    return c;
  else
    return b;
}

template<typename ValueType>
inline const ValueType& median_of_three(const ValueType& a, const ValueType& b,
                                        const ValueType& c)
{
  auto cmp = std::less<ValueType>();
  return median_of_three(a, b, c, cmp);
}

template <typename Iterator, class Compare>
inline typename std::iterator_traits<Iterator>::value_type
median_of_nine(Iterator begin, Iterator end, Compare cmp)
{
  typedef typename std::iterator_traits<Iterator>::value_type ValueType;
  typedef typename std::iterator_traits<Iterator>::difference_type SizeType;
  assert(std::distance(begin, end) > 8);
  SizeType step = std::distance(begin, end) / 8;
  Iterator pos(begin);
  const ValueType & a = median_of_three( *pos, *(pos + step),
                                 *(pos + 2*step), cmp );
  const ValueType & b = median_of_three( *(pos + 3*step), *(pos + 4*step),
                                 *(pos + 5*step), cmp );
  const ValueType & c = median_of_three( *(pos + 6*step), *(pos + 7*step),
                                 *(end - 1), cmp );
  return median_of_three(a, b, c, cmp);
}

template <typename Iterator>
inline typename std::iterator_traits<Iterator>::value_type
median_of_nine(Iterator begin, Iterator end)
{
  typedef typename std::iterator_traits<Iterator>::value_type ValueType;
  auto cmp = std::less<ValueType>();
  return median_of_nine(begin, end, cmp);
}

template <typename FloatType>
std::pair<FloatType,FloatType> solve_quadratic(const FloatType &a,
                                               const FloatType &b,
                                               const FloatType &c)
{
  FloatType t1 = std::sqrt(sq(b) - FloatType(4)*a*c);
  FloatType it2 = FloatType(0.5) / a;
  return std::make_pair( (t1-b)*it2, (-t1-b)*it2 );
}

template <class Functor, typename Scalar>
Scalar golden_ratio_minimum(Functor f, Scalar a, Scalar b, Scalar tol)
{
  assert(b > a);
  const Scalar iphi = 0.618033988749895;
  Scalar fa; //  = f(a);
  Scalar fb; //  = f(b);
  Scalar c = iphi*a + (1-iphi)*b;
  Scalar d = iphi*b + (1-iphi)*a;
  Scalar fc = f(c);
  Scalar fd = f(d);
  while (b-a > tol) {
    if (fc < fd) {
      b = d;
      fb = fd;
      d = c;
      fd = fc;
      c = iphi*a + (1-iphi)*b;
      fc = f(c);
    } else {
      a = c;
      fa = fc;
      c = d;
      fc = fd;
      d = iphi*b + (1-iphi)*a;
      fd = f(d);
    }
  }
  return 0.5*(a+b);
}

template <class Functor, typename Scalar>
Scalar golden_ratio_maximum(Functor f, Scalar a, Scalar b, Scalar tol)
{
  assert(b > a);
  const Scalar iphi = 0.618033988749895;
  Scalar fa; //  = f(a);
  Scalar fb; //  = f(b);
  Scalar c = iphi*a + (1-iphi)*b;
  Scalar d = iphi*b + (1-iphi)*a;
  Scalar fc = f(c);
  Scalar fd = f(d);
  while (b-a > tol) {
    if (fc > fd) {
      b = d;
      fb = fd;
      d = c;
      fd = fc;
      c = iphi*a + (1-iphi)*b;
      fc = f(c);
    } else {
      a = c;
      fa = fc;
      c = d;
      fc = fd;
      d = iphi*b + (1-iphi)*a;
      fd = f(d);
    }
  }
  return 0.5*(a+b);
}

/** Anderson and Björck's version of regula falsi.
 *
 * G. Dahlquist and Å. Björck: Numerical Methods in Scientific Computing,
 * Volume 1, SIAM, 2008.
 *
 */
template <class Functor, typename Scalar>
Scalar anderson_root(Functor f, Scalar a, Scalar b, Scalar xtol, Scalar ftol)
{
  Scalar fa = f(a);
  Scalar fb = f(b);
  int side = 0;
  while ( std::fabs(b-a) > xtol ) {
    Scalar c = a - fa * (b-a) / (fb - fa);
    Scalar fc = f(c);
    if ( std::fabs(fc) < ftol ) {
      return c;
    } else if (sign(fc) == sign(fa)) {
      if (side == -1) {
        Scalar m = 1 - fc/fa;
        fb *= (m > 0) ? m : 0.5;
      }
      a = c;
      fa = fc;
      side = -1;
    } else {
      if (side == 1) {
        Scalar m = 1 - fc/fb;
        fa *= (m > 0) ? m : 0.5;
      }
      b = c;
      fb = fc;
      side = 1;
    }
  }

  // fallthrough: initial |b - a| < xtol
  return 0.5*(a + b);
}

/** Single step of a Kahan summation.
  \param [in]  val The ith value to add to sum
  \param [out] sum The current sum so far
  \param [out] c Error accumulator, initialized to zero
*/
template <class Type>
inline void kahan_sum_step(const Type & val, Type & sum, Type & c)
{
  Type y = val - c;
  Type t = sum + y;   // sum is big : precision lost
  c = (t - sum) - y;  // recover lost precision
  sum = t;
}

// integer powers as recursive template

namespace detail {

template <int N, class FloatType>
struct IntPowHelper {
  FloatType eval(FloatType x) const {
    const int M = N/2;
    IntPowHelper<M,FloatType> half;
    FloatType t = half.eval(x);
    return (N & 1) ? t*t*x : t*t;
  }
};

template <class FloatType>
struct IntPowHelper<0,FloatType> {
  FloatType eval(FloatType) const {
    return FloatType(1);
  }
};

template <class FloatType>
struct IntPowHelper<1,FloatType> {
  FloatType eval(FloatType x) const {
    return x;
  }
};

template <class FloatType>
struct IntPowHelper<2,FloatType> {
  FloatType eval(FloatType x) const {
    return x*x;
  }
};

template <class FloatType>
struct IntPowHelper<3,FloatType> {
  FloatType eval(FloatType x) const {
    return x*x*x;
  }
};

}

template <int N, class FloatType>
force_inline FloatType intpow(FloatType x)
{
  const int M = (N >= 0) ? N : -N;
  detail::IntPowHelper<M,FloatType> helper;
  FloatType y = helper.eval(x);
  return (N >= 0) ? y : (FloatType(1) / y);
}

inline void random_fill(uint n, Real v[])
{
  const Real f(1.0 / RAND_MAX);
  for (uint i=0; i<n; ++i)
    v[i] = f*rand();
}

template <typename Type>
inline Type clamp(Type a, Type amin, Type amax)
{
  return std::min(amax, std::max(a, amin));
}

template <typename Type>
inline bool bclamp(Type a, Type amin, Type amax, Type &xcl)
{
  xcl = std::min(amax, std::max(a, amin));
  return (a < amin) or (a > amax);
}

template <typename Type>
inline Type smooth_step(Type a, Type left, Type right)
{
  Type x = clamp( (a - left) / (right - left), Type(0), Type(1) );
  return x*x*(Type(3) - Type(2)*x);
}

template <typename Type>
inline Type smooth_step(Type a)
{
  const Type f(1.0/6.0);
  Type x = clamp(f*a + Type(0.5) , Type(0), Type(1) );
  return Type(2)*x*x*(Type(3) - Type(2)*x) - 1;
}

template <typename Type>
inline Type perlin_step(Type a, Type left, Type right)
{
  Type x = clamp( (a - left) / (right - left), Type(0), Type(1) );
  return x*x*x*(x*(x*Type(6) - Type(15)) + Type(10));
}

template <typename Type>
inline Type perlin_step(Type a)
{
  const Type f(1.0/6.0);
  Type x = clamp(f*a + Type(0.5) , Type(0), Type(1) );
  return Type(2)*x*x*x*(x*(x*Type(6) - Type(15)) + Type(10)) - Type(1);
}

template <typename Type>
inline const Type & select(const Type & a, const Type & b, int c)
{
  return c ? b : a;
}

inline float signval(float a)
{
  return (a < 0.0f) ? -1.0f : 1.0f;
}

inline double signval(double a)
{
  return (a < 0.0) ? -1.0 : 1.0;
}

template <class Type>
class almost_equal
{
public:
  almost_equal(Type m) : margin(m) {}
  bool operator() (Type a, Type b) const {
    return fabs(a-b) < margin;
  }
private:
  Type margin;
};

template <class TypeArray>
class IndirectLess
{
public:

  typedef bool result_type;

  IndirectLess(const TypeArray & ta) : ary(ta) {}

  template <class Index>
  bool operator() (Index a, Index b) const {
    return ary[a] < ary[b];
  }

private:
  const TypeArray & ary;
};

template <class TypeArray, class Ordering>
class IndirectOrdering
{
public:

  IndirectOrdering(const TypeArray & ta, const Ordering & p)
    : ary(ta), op(p) {}

  template <class Index>
  bool operator() (Index a, Index b) const {
    return op(ary[a], ary[b]);
  }

private:
  const TypeArray & ary;
  const Ordering & op;
};

#if defined(GENUA_GCC)
#define HAVE_BSWAP_BUILTIN
#define intrin_bswap32  __builtin_bswap32
#define intrin_bswap64  __builtin_bswap64
#elif defined(GENUA_ICC)
#define HAVE_BSWAP_BUILTIN
#define intrin_bswap32  _bswap
#define intrin_bswap64  _bswap64
#endif

template <int width>
inline void swap_bytes(size_t nbytes, char *buf)
{
  assert(nbytes%width == 0);
  size_t nblock = nbytes/width;
#ifdef HAVE_BSWAP_BUILTIN
  if (width == 4) {
    union { char *c; uint32_t *i; } u;
    u.c = buf;
    uint32_t *p = u.i;
    for (size_t i=0; i<nblock; ++i)
      p[i] = intrin_bswap32(p[i]);
  } else if (width == 8) {
    union { char *c; uint64_t *i; } u;
    u.c = buf;
    uint64_t *p = u.i;
    for (size_t i=0; i<nblock; ++i)
      p[i] = intrin_bswap64(p[i]);
  } else {
    char tmp[width];
    for (size_t i=0; i<nblock; ++i) {
      for (int k=0; k<width; ++k)
        tmp[k] = buf[i*width+k];
      for (int k=0; k<width; ++k)
        buf[i*width+k] = tmp[width-1-k];
    }
  }
#else
  char tmp[width];
  for (size_t i=0; i<nblock; ++i) {
    for (int k=0; k<width; ++k)
      tmp[k] = buf[i*width+k];
    for (int k=0; k<width; ++k)
      buf[i*width+k] = tmp[width-1-k];
  }
#endif
}

inline void swap_bytes(int width, size_t nbytes, char *buf)
{
  assert(nbytes%width == 0);
  size_t nblock = nbytes/width;
  std::vector<char> tmp(width);
  for (size_t i=0; i<nblock; ++i) {
    for (int k=0; k<width; ++k)
      tmp[k] = buf[i*width+k];
    for (int k=0; k<width; ++k)
      buf[i*width+k] = tmp[width-1-k];
  }
}

inline bool is_bigendian()
{
  const int i = 1;
  return ( (*(char*)&i) == 0 );
}

template <int width>
inline void host2network(size_t nbytes, char *buf)
{
  if (not is_bigendian()) {
    swap_bytes<width>(nbytes, buf);
  }
}

#if defined(GENUA_POSIX)

#include <netinet/in.h>

inline int32_t host2network(int32_t a)
{
  union { int32_t i; uint32_t u; } s;
  s.i = a;
  s.u = htonl(s.u);
  return s.i;
}

inline uint32_t host2network(uint32_t a)
{
  return htonl(a);
}

inline float host2network(float a)
{
  union { float f; uint32_t u; } s;
  s.f = a;
  s.u = htonl(s.u);
  return s.f;
}

#else

inline uint32_t host2network(uint32_t a)
{
  if (not is_bigendian()) {
    uint32_t b(a);
    swap_bytes<4>(4, (char *) &b);
    return b;
  } else {
    return a;
  }
}

inline int32_t host2network(int32_t a)
{
  if (not is_bigendian()) {
    int32_t b(a);
    swap_bytes<4>(4, (char *) &b);
    return b;
  } else {
    return a;
  }
}

inline float host2network(float a)
{
  if (not is_bigendian()) {
    float b(a);
    swap_bytes<4>(4, (char *) &b);
    return b;
  } else {
    return a;
  }
}

#endif

inline double host2network(double a)
{
  if (not is_bigendian()) {
    double b(a);
    swap_bytes<8>(8, (char *) &b);
    return b;
  } else {
    return a;
  }
}

#define network2host host2network

inline uint32_t popcount(uint32_t x)
{
  // University of Kentucky : http://aggregate.org
  
  x -= ((x >> 1) & 0x55555555);
  x = (((x >> 2) & 0x33333333) + (x & 0x33333333));
  x = (((x >> 4) + x) & 0x0f0f0f0f);
  x += (x >> 8);
  x += (x >> 16);
  return (x & 0x0000003f);
}

inline uint32_t floor_ilog2(uint32_t x)
{
  // University of Kentucky : http://aggregate.org
  x |= (x >> 1);
  x |= (x >> 2);
  x |= (x >> 4);
  x |= (x >> 8);
  x |= (x >> 16);
  return (popcount(x) - 1);
}

namespace detail {

template <typename AType>
struct complex_version {
  typedef std::complex<AType> complex_type;
};

template <>
struct complex_version<std::complex<double> > {
  typedef std::complex<double> complex_type;
};

template <>
struct complex_version<std::complex<float> > {
  typedef std::complex<float> complex_type;
};

template <typename AType>
struct real_version {
  typedef AType real_type;
};

template <>
struct real_version<std::complex<float> > {
  typedef float real_type;
};

template <>
struct real_version<std::complex<double> > {
  typedef double real_type;
};

} // detail

// uint32_t ceil_log2(uint32_t x)
// {
//   int y = (x & (x - 1));
// 
//   y |= -y;
//   y >>= (sizeof(uint32_t) - 1);
//   x |= (x >> 1);
//   x |= (x >> 2);
//   x |= (x >> 4);
//   x |= (x >> 8);
//   x |= (x >> 16);
//   
//   return (popcount(x) - 1 - y);
// }

// void base64encode(size_t n, const char *raw, std::string & b64)
// {
//   const char a[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
//   
//   union {
//     uint32_t i;
//     char s[4];
//   } idx;
//   idx.i = 0;
//   
//   for (size_t k=0; k<n/3; ++k) {
//     idx.s[0] = raw[3*k];
//     idx.s[1] = raw[3*k+1];
//     idx.s[2] = raw[3*k+2];
//     b64.push_back( a[ idx.i & 0x3f ] );
//     b64.push_back( a[ idx.i & 0xfc0 ] );
//     b64.push_back( a[ idx.i & 0x3f000 ] );
//     b64.push_back( a[ idx.i & 0xfc0000 ] );
//   }
//   
//   size_t top = 3*(n/3);
//   if (top == n-2) {
//     idx.s = 0;
//     idx.s[0] = raw[3*k];
//     idx.s[1] = raw[3*k+1];
//     b64.push_back( a[ idx.i & 0x3f ] );
//     b64.push_back( a[ idx.i & 0xfc0 ] );
//     b64.push_back( a[ idx.i & 0x3f000 ] );
//     b64.push_back( a[ idx.i & 0xfc0000 ] );
//   } else if (top == n-1) {
//     idx.s = 0;
//     idx.s[0] = raw[3*k];
//     b64.push_back( a[ idx.i & 0x3f ] );
//     b64.push_back( a[ idx.i & 0xfc0 ] );
//     b64.push_back( a[ idx.i & 0x3f000 ] );
//     b64.push_back( a[ idx.i & 0xfc0000 ] );
//   }
// 
// }




#endif

