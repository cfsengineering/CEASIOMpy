
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
 
#ifndef GENUA_SIMDTYPE_H
#define GENUA_SIMDTYPE_H

#include "defines.h"
#include "simdbase.h"

/** Auxilliary class used for type assembly.

  This is a helper class which is only used to synthesize wide vector types
  on systems which have support for a narrower SIMD vector type. In this way,
  it is possibel to write algorithms in terms of float8 and make them work
  even when only SSE -- but not AVX -- is present.

  \internal
  \sa float4, float8
  */
template <class Simd, int N>
class EmulatedSimdType : public SimdBase< typename Simd::Scalar, N*Simd::lanes >
{
public:

  typedef typename Simd::Scalar Scalar;

  /// empty constructor
  EmulatedSimdType<Simd,N>() {}

  /// broadcast single scalar to the entire vector
  explicit force_inline EmulatedSimdType<Simd,N>(Scalar a) attr_always_inline
  {
    for (int i=0; i<N; ++i)
      x[i] = Simd(a);
  }

  /// load from aligned memory location
  explicit force_inline EmulatedSimdType<Simd,N>(const Scalar *a) attr_always_inline
  {
    load(a);
  }

  /// vector width
  static int width() attr_always_inline {return N*Simd::width();}

  /// number of multiples of the base type
  static int multiple() attr_always_inline {return N;}

  /// computed assignment
  force_inline EmulatedSimdType<Simd,N> & operator+= (const EmulatedSimdType<Simd,N> & a) attr_always_inline
  {
    for (int i=0; i<N; ++i)
      x[i] += a.x[i];
    return *this;
  }

  /// computed assignment
  force_inline EmulatedSimdType<Simd,N> & operator-= (const EmulatedSimdType<Simd,N> & a) attr_always_inline
  {
    for (int i=0; i<N; ++i)
      x[i] -= a.x[i];
    return *this;
  }

  /// computed assignment
  force_inline EmulatedSimdType<Simd,N> & operator*= (const EmulatedSimdType<Simd,N> & a) attr_always_inline
  {
    for (int i=0; i<N; ++i)
      x[i] *= a.x[i];
    return *this;
  }

  /// computed assignment
  force_inline EmulatedSimdType<Simd,N> & operator/= (const EmulatedSimdType<Simd,N> & a) attr_always_inline
  {
    for (int i=0; i<N; ++i)
      x[i] /= a.x[i];
    return *this;
  }

  /// computed assignment
  force_inline EmulatedSimdType<Simd,N> & operator&= (const EmulatedSimdType<Simd,N> & a) attr_always_inline
  {
    for (int i=0; i<N; ++i)
      x[i] &= a.x[i];
    return *this;
  }

  /// computed assignment
  force_inline EmulatedSimdType<Simd,N> & operator|= (const EmulatedSimdType<Simd,N> & a) attr_always_inline
  {
    for (int i=0; i<N; ++i)
      x[i] |= a.x[i];
    return *this;
  }

  /// computed assignment
  force_inline EmulatedSimdType<Simd,N> & operator^= (const EmulatedSimdType<Simd,N> & a) attr_always_inline
  {
    for (int i=0; i<N; ++i)
      x[i] ^= a.x[i];
    return *this;
  }

  /// load from properly aligned memory location
  force_inline void load(const Scalar *a) attr_always_inline {
    for (int i=0; i<N; ++i) {
      x[i].load( a );
      a += Simd::width();
    }
  }

  /// load from unaligned memory location
  force_inline void loadu(const Scalar *a) attr_always_inline {
    for (int i=0; i<N; ++i) {
      x[i].loadu( a );
      a += Simd::width();
    }
  }

  /// store to properly aligned memory location
  force_inline void store(Scalar *a) const attr_always_inline {
    for (int i=0; i<N; ++i) {
      x[i].store( a );
      a += Simd::width();
    }
  }

  /// store to unaligned memory location
  force_inline void storeu(Scalar *a) const attr_always_inline {
    for (int i=0; i<N; ++i) {
      x[i].storeu( a );
      a += Simd::width();
    }
  }

  /// extract sign bits
  force_inline int signbits() const attr_always_inline {
    int sb = 0;
    for (int i=0; i<N; ++i) {
      sb |= ( x[i].signbits() << (i*Simd::width()) );
    }
    return sb;
  }

  /// emulate horizontal sum
  force_inline Scalar sum() const attr_always_inline {
    Simd tmp( Scalar(0) );
    for (int i=0; i<N; ++i)
      tmp += x[i];
    return tmp.sum();
  }

  /// return mask with all bits zero
  static force_inline EmulatedSimdType<Simd,N> zeromask() attr_always_inline {
    EmulatedSimdType<Simd,N> a;
    for (int i=0; i<N; ++i)
      a.x[i] = Simd::zeromask();
    return a;
  }

  /// return mask with all bits one
  static force_inline EmulatedSimdType<Simd,N> onemask() attr_always_inline {
    EmulatedSimdType<Simd,N> a;
    for (int i=0; i<N; ++i)
      a.x[i] = Simd::onemask();
    return a;
  }

  /// N instances of the basic type
  Simd x[N];
};

// declaration macros

#undef SIMD_DECLARE_UNARY_FN
#define SIMD_DECLARE_UNARY_FN(fn) \
  template <class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> fn(const EmulatedSimdType<Simd,N> & a) attr_always_inline; \
  \
  template <class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> fn(const EmulatedSimdType<Simd,N> & a) \
{ \
  EmulatedSimdType<Simd,N> c; \
  for (int i=0; i<N; ++i) \
  c.x[i] = fn( a.x[i] ); \
  return c; \
  } \

#undef SIMD_DECLARE_BINARY_FN
#define SIMD_DECLARE_BINARY_FN(fn) \
  template <class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> fn(const EmulatedSimdType<Simd,N> & a, \
  const EmulatedSimdType<Simd,N> & b) attr_always_inline; \
  \
  template <class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> fn(const EmulatedSimdType<Simd,N> & a, \
  const EmulatedSimdType<Simd,N> & b) \
{ \
  EmulatedSimdType<Simd,N> c; \
  for (int i=0; i<N; ++i) \
  c.x[i] = fn( a.x[i], b.x[i] ); \
  return c; \
  } \

#undef SIMD_DECLARE_ARITHM_OP
#define SIMD_DECLARE_ARITHM_OP(op) \
  template <class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> operator op(const EmulatedSimdType<Simd,N> & a, \
  const EmulatedSimdType<Simd,N> & b) attr_always_inline; \
  \
  template <class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> operator op(const EmulatedSimdType<Simd,N> & a, \
  const EmulatedSimdType<Simd,N> & b) \
{ \
  EmulatedSimdType<Simd,N> c; \
  for (int i=0; i<N; ++i) \
  c.x[i] = a.x[i] op b.x[i]; \
  return c; \
  } \
  \
  template <class ScalarType, class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> operator op(ScalarType sa, \
  const EmulatedSimdType<Simd,N> & b) attr_always_inline; \
  \
  template <class ScalarType, class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> operator op(ScalarType sa, \
  const EmulatedSimdType<Simd,N> & b) \
{ \
  return EmulatedSimdType<Simd,N>(sa) op b; \
  } \
  \
  template <class ScalarType, class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> operator op(const EmulatedSimdType<Simd,N> & a, \
  ScalarType sb) attr_always_inline; \
  \
  template <class ScalarType, class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> operator op(const EmulatedSimdType<Simd,N> & a, \
  ScalarType sb) \
{ \
  return a op EmulatedSimdType<Simd,N>(sb); \
  } \


#undef SIMD_DECLARE_BINARY_OP
#define SIMD_DECLARE_BINARY_OP(op) \
  template <class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> operator op(const EmulatedSimdType<Simd,N> & a, \
  const EmulatedSimdType<Simd,N> & b) attr_always_inline; \
    \
  template <class Simd, int N> \
  force_inline EmulatedSimdType<Simd,N> operator op(const EmulatedSimdType<Simd,N> & a, \
  const EmulatedSimdType<Simd,N> & b) \
{ \
  EmulatedSimdType<Simd,N> c; \
  for (int i=0; i<N; ++i) \
  c.x[i] = a.x[i] op b.x[i]; \
  return c; \
  } \

// ------------------ permutations -----------------------------------------

//template <class Simd, int N>
//force_inline void swap(EmulatedSimdType<Simd,N> & a, EmulatedSimdType<Simd,N> & b)
//{
//  std::swap(a, b);
//}

// SIMD_DECLARE_BINARY_FN(interleave_even)
// SIMD_DECLARE_BINARY_FN(interleave_odd)

// --------------- arithmetic operators ------------------

SIMD_DECLARE_ARITHM_OP(+)
SIMD_DECLARE_ARITHM_OP(-)
SIMD_DECLARE_ARITHM_OP(*)
SIMD_DECLARE_ARITHM_OP(/)

template <class Simd, int N>
force_inline EmulatedSimdType<Simd,N> operator- (const EmulatedSimdType<Simd,N> & a) attr_always_inline;

template <class Simd, int N>
force_inline EmulatedSimdType<Simd,N> operator- (const EmulatedSimdType<Simd,N> & a)
{
  EmulatedSimdType<Simd,N> c;
  for (int i=0; i<N; ++i)
    c.x[i] = -a.x[i];
  return c;
}

template <class Simd, int N>
force_inline EmulatedSimdType<Simd,N> fmuladd(const EmulatedSimdType<Simd,N> &a,
                                              const EmulatedSimdType<Simd,N> &b,
                                              const EmulatedSimdType<Simd,N> &c) attr_always_inline;

// return a*b + c
template <class Simd, int N>
force_inline EmulatedSimdType<Simd,N> fmuladd(const EmulatedSimdType<Simd,N> &a,
                                              const EmulatedSimdType<Simd,N> &b,
                                              const EmulatedSimdType<Simd,N> &c)
{
  EmulatedSimdType<Simd,N> r;
  for (int i=0; i<N; ++i)
    r.x[i] = fmuladd(a.x[i], b.x[i], c.x[i]);
  return r;
}

template <class Simd, int N>
force_inline EmulatedSimdType<Simd,N> fmulsub(const EmulatedSimdType<Simd,N> &a,
                                              const EmulatedSimdType<Simd,N> &b,
                                              const EmulatedSimdType<Simd,N> &c) attr_always_inline;

// return a*b - c
template <class Simd, int N>
force_inline EmulatedSimdType<Simd,N> fmulsub(const EmulatedSimdType<Simd,N> &a,
                                              const EmulatedSimdType<Simd,N> &b,
                                              const EmulatedSimdType<Simd,N> &c)
{
  EmulatedSimdType<Simd,N> r;
  for (int i=0; i<N; ++i)
    r.x[i] = fmulsub(a.x[i], b.x[i], c.x[i]);
  return r;
}

// ----------------- mathematical functions ------------------------

// SIMD_DECLARE_UNARY_FN(hadd)

SIMD_DECLARE_BINARY_FN(max)
SIMD_DECLARE_BINARY_FN(min)
SIMD_DECLARE_UNARY_FN(sqrt)
SIMD_DECLARE_UNARY_FN(fabs)
SIMD_DECLARE_UNARY_FN(recip)
SIMD_DECLARE_UNARY_FN(rsqrt)
SIMD_DECLARE_BINARY_FN(copysign)

#ifdef GENUA_USE_SVML

SIMD_DECLARE_UNARY_FN(cbrt)
SIMD_DECLARE_UNARY_FN(log)
SIMD_DECLARE_UNARY_FN(log2)
SIMD_DECLARE_UNARY_FN(log10)
SIMD_DECLARE_UNARY_FN(exp)
SIMD_DECLARE_UNARY_FN(exp2)
SIMD_DECLARE_BINARY_FN(pow)
SIMD_DECLARE_UNARY_FN(sin)
SIMD_DECLARE_UNARY_FN(cos)
SIMD_DECLARE_UNARY_FN(asin)
SIMD_DECLARE_UNARY_FN(acos)
SIMD_DECLARE_UNARY_FN(atan)
SIMD_DECLARE_BINARY_FN(atan2)

template <class Simd, int N>
force_inline void sincos(const EmulatedSimdType<Simd,N> & a,
                   EmulatedSimdType<Simd,N> & sa,
                   EmulatedSimdType<Simd,N> & ca ) attr_always_inline;

template <class Simd, int N>
force_inline void sincos(const EmulatedSimdType<Simd,N> & a,
                   EmulatedSimdType<Simd,N> & sa,
                   EmulatedSimdType<Simd,N> & ca )
{
  for (int i=0; i<N; ++i)
    sincos(a.x[i], sa.x[i], ca.x[i] );
}

#endif // SVML

// ----------------- logical operators -------------------------------

SIMD_DECLARE_BINARY_OP(&)
SIMD_DECLARE_BINARY_OP(|)
SIMD_DECLARE_BINARY_OP(^)
SIMD_DECLARE_BINARY_FN(andnot)
SIMD_DECLARE_BINARY_OP(==)
SIMD_DECLARE_BINARY_OP(!=)
SIMD_DECLARE_BINARY_OP(<)
SIMD_DECLARE_BINARY_OP(<=)
SIMD_DECLARE_BINARY_OP(>)
SIMD_DECLARE_BINARY_OP(>=)

template <class Simd, int N>
force_inline EmulatedSimdType<Simd,N> operator~ (const EmulatedSimdType<Simd,N> & a) attr_always_inline;

template <class Simd, int N>
force_inline EmulatedSimdType<Simd,N> operator~ (const EmulatedSimdType<Simd,N> & a)
{
  EmulatedSimdType<Simd,N> c;
  for (int i=0; i<N; ++i)
    c.x[i] = ~(a.x[i]);
  return c;
}

// -------------------- cleanup ---------------------------------------------

#undef SIMD_DECLARE_UNARY_FN
#undef SIMD_DECLARE_BINARY_FN
#undef SIMD_DECLARE_ARITHM_OP
#undef SIMD_DECLARE_BINARY_OP

#endif // SIMDTYPE_H
