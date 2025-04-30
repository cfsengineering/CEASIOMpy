
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
 #ifndef GENUA_MORTON_H
#define GENUA_MORTON_H

#include "defines.h"
#include "bitfiddle.h"

/** N-dimensional Morton code.

  MortonLess is a comparison functor which can be used to sort N-dimensional
  integer-valued points along a Z-order curve.

   Chan, T. (2002), "Closest-point problems simplified on the RAM",
   ACM-SIAM Symposium on Discrete Algorithms.
  */
template <class UIntType, int ND>
class MortonLess
{
public:

  /// determine whether a[] < b[] in the z-order sense
  bool operator() (const UIntType a[], const UIntType b[]) const {
    UIntType j(0), x(0), y;
    for (int k=0; k<ND; ++k) {
      y = a[k] ^ b[k];
      if ( (x < y) and (x < (x ^ y)) ) {
        j = k;
        x = y;
      }
    }
    return a[j] < b[j];
  }

  /// overload for types which support &a[0]
  template <class Indexable>
  bool operator() (const Indexable & a, const Indexable & b) const {
    const MortonLess & self(*this);
    return self(&a[0], &b[0]);
  }
};

/** Morton order using quantized floating-point values.

  QuantMortonLess defines a z-order curve sorting order by first
  quantizing N-dimensional floating-point values with a given base value and
  scale and then applying an integer-based MortonLess comparator.

  Testing shows that it is more effiicent to first quantize the floating point
  data once and apply integer morton sorting then.

*/
template <class FloatType, class UIntType, int ND>
class QuantMortonLess
{
  /// construct quantizing z-order comparison
  QuantMortonLess(const FloatType minval[], const FloatType iscl[])
    : qmin(minval), qiscal(iscl) {}

  /// determine whether a[] < b[] in the z-order sense
  bool operator() (const FloatType a[], const FloatType b[]) const {
    UIntType ai[ND], bi[ND];
    for (int k=0; k<ND; ++k) {
      ai[k] = static_cast<UIntType>( (a[k] - qmin[k]) * qiscal[k] );
      bi[k] = static_cast<UIntType>( (b[k] - qmin[k]) * qiscal[k] );
    }
    MortonLess<UIntType,ND> iless;
    return iless(ai, bi);
  }

private:

  /// quantization base value
  const FloatType *qmin;

  /// quantization scale factor
  const FloatType *qiscal;
};

template <class UIntType, int ND, int NV>
class ElementMortonLess
{
public:

  /// construct element comparator
  ElementMortonLess(const UIntType v[], const UIntType e[])
    : qiv(v), eli(e) {}

  /// evaluate comparison of element a and b
  bool operator() (int a, int b) const {
    //    UIntType actr[ND], bctr[ND];
    //    for (int i=0; i<ND; ++i)
    //      actr[i] = bctr[i] = 0;

    //    const UIntType *avi = &eli[a*NV];
    //    const UIntType *bvi = &eli[b*NV];
    //    for (int i=0; i<NV; ++i) {
    //      const UIntType *pa = &qiv[ND*avi[i]];
    //      const UIntType *pb = &qiv[ND*bvi[i]];
    //      for (int k=0; k<ND; ++k) {
    //        actr[k] += pa[k];
    //        bctr[k] += pb[k];
    //      }
    //    }

    //    MortonLess<UIntType, ND> iless;
    //    return iless(actr, bctr);

    UIntType amin[ND], amax[ND], bmin[ND], bmax[ND];
    for (int j=0; j<ND; ++j) {
      amin[j] = bmin[j] = std::numeric_limits<UIntType>::max();
      amax[j] = bmax[j] = 0;
    }

    // determine bounding boxes for elements a and b
    const UIntType *avi = &eli[a*NV];
    const UIntType *bvi = &eli[b*NV];
    for (int i=0; i<NV; ++i) {
      const UIntType *pa = &qiv[ND*avi[i]];
      const UIntType *pb = &qiv[ND*bvi[i]];
      for (int j=0; j<ND; ++j) {
        amax[j] = std::max(amax[j], pa[j]);
        amin[j] = std::min(amin[j], pa[j]);
        bmax[j] = std::max(bmax[j], pb[j]);
        bmin[j] = std::min(bmin[j], pb[j]);
      }
    }

    // set amin, bmin to the bounding box center
    for (int j=0; j<ND; ++j) {
      amin[j] = (amin[j] + amax[j]) / 2;
      bmin[j] = (bmin[j] + bmax[j]) / 2;
    }

    MortonLess<UIntType, ND> iless;
    return iless(amin, bmin);
  }

private:

  /// quantized integer coordinates of the element vertices
  const UIntType *qiv;

  /// element vertex indices
  const UIntType *eli;
};

/** Morton code for floating-point values.

  This Morton z-code comparison functor uses the implementation described in
  the paper by Connor and Kumar referenced below. On a Nehalem CPU, this
  implementation was found to be slightly slower than an integer quantization
  pass follwowed by a integer-based Morton sort step. The advantage of the
  float-based Morton comparator is that there is no need to know the range
  of input values a priori, which is a requirement for dynamic-range preserving
  quantization.

  Michael Connor, Piyush Kumar: "Fast construction of k-Nearest Neighbor Graphs
  for Point Clouds", IEEE TRANSACTIONS ON VISUALIZATION AND COMPUTER GRAPHICS,
  SEPTEMBER 2009
*/
template <class FloatType, int ND>
class FloatMortonLess
{
public:

  /// compare Morton order of two float points
  bool operator() (const FloatType a[], const FloatType b[]) const
  {
    int x(0), dim(0);
    for (int j=0; j<ND; ++j) {
      int y = xormsb(a[j], b[j]);
      if (x < y) {
        x = y;
        dim = j;
      }
    }
    return a[dim] < b[dim];
  }

private:

  /// determine the most significant differing bit
  int xormsb(FloatType a, FloatType b) const
  {
    int x = ieee_exponent(a);
    int y = ieee_exponent(b);
    if (x == y) {
      int z = msdb(ieee_mantissa(a), ieee_mantissa(b));
      return x-z;
    }
    return (y < x) ? x : y;
  }

  /// return the most significant differing bit
  int msdb(uint32_t a, uint32_t b) const {
    return 32 - lzcount32(a ^ b);
  }

  /// return the most significant differing bit
  int msdb(uint64_t a, uint64_t b) const {
    return 64 - lzcount64(a ^ b);
  }

};

// -- global functions to compute morton code values

namespace detail
{

inline uint32_t Part1By1(uint32_t x)
{
  x &= 0x0000ffff;                  // x = ---- ---- ---- ---- fedc ba98 7654 3210
  x = (x ^ (x <<  8)) & 0x00ff00ff; // x = ---- ---- fedc ba98 ---- ---- 7654 3210
  x = (x ^ (x <<  4)) & 0x0f0f0f0f; // x = ---- fedc ---- ba98 ---- 7654 ---- 3210
  x = (x ^ (x <<  2)) & 0x33333333; // x = --fe --dc --ba --98 --76 --54 --32 --10
  x = (x ^ (x <<  1)) & 0x55555555; // x = -f-e -d-c -b-a -9-8 -7-6 -5-4 -3-2 -1-0
  return x;
}

inline uint64_t Part1By1_64b(uint64_t x)
{
  x &= 0x00000000ffffffffL;
  x = (x ^ (x << 16)) & 0x0000ffff0000ffffLL;
  x = (x ^ (x <<  8)) & 0x00ff00ff00ff00ffLL;
  x = (x ^ (x <<  4)) & 0x0f0f0f0f0f0f0f0fLL;
  x = (x ^ (x <<  2)) & 0x3333333333333333LL;
  x = (x ^ (x <<  1)) & 0x5555555555555555LL;
  return x;
}

template <typename IntType, int M>
inline IntType spread_bits(IntType x)
{
  IntType shift = M;
  IntType msk = ~IntType(0) ;
  msk ^= (msk << shift);
  x &= msk;
  while (shift > 1) {
    shift >>= 1;
    msk ^= (msk << shift);
    x = (x ^ (x << shift)) & msk;
  }
  return x;
}

inline uint32_t Part1By2(uint32_t x)
{
  x &= 0x000003ff;                  // x = ---- ---- ---- ---- ---- --98 7654 3210
  x = (x ^ (x << 16)) & 0xff0000ff; // x = ---- --98 ---- ---- ---- ---- 7654 3210
  x = (x ^ (x <<  8)) & 0x0300f00f; // x = ---- --98 ---- ---- 7654 ---- ---- 3210
  x = (x ^ (x <<  4)) & 0x030c30c3; // x = ---- --98 ---- 76-- --54 ---- 32-- --10
  x = (x ^ (x <<  2)) & 0x09249249; // x = ---- 9--8 --7- -6-- 5--4 --3- -2-- 1--0
  return x;
}

inline uint32_t Compact1By1(uint32_t x)
{
  x &= 0x55555555;                  // x = -f-e -d-c -b-a -9-8 -7-6 -5-4 -3-2 -1-0
  x = (x ^ (x >>  1)) & 0x33333333; // x = --fe --dc --ba --98 --76 --54 --32 --10
  x = (x ^ (x >>  2)) & 0x0f0f0f0f; // x = ---- fedc ---- ba98 ---- 7654 ---- 3210
  x = (x ^ (x >>  4)) & 0x00ff00ff; // x = ---- ---- fedc ba98 ---- ---- 7654 3210
  x = (x ^ (x >>  8)) & 0x0000ffff; // x = ---- ---- ---- ---- fedc ba98 7654 3210
  return x;
}

inline uint32_t Compact1By2(uint32_t x)
{
  x &= 0x09249249;                  // x = ---- 9--8 --7- -6-- 5--4 --3- -2-- 1--0
  x = (x ^ (x >>  2)) & 0x030c30c3; // x = ---- --98 ---- 76-- --54 ---- 32-- --10
  x = (x ^ (x >>  4)) & 0x0300f00f; // x = ---- --98 ---- ---- 7654 ---- ---- 3210
  x = (x ^ (x >>  8)) & 0xff0000ff; // x = ---- --98 ---- ---- ---- ---- 7654 3210
  x = (x ^ (x >> 16)) & 0x000003ff; // x = ---- ---- ---- ---- ---- --98 7654 3210
  return x;
}

}

inline uint32_t encodeMorton(uint32_t x, uint32_t y)
{
  assert(x < (1u << 15));
  assert(y < (1u << 15));
  return (detail::Part1By1(y) << 1) + detail::Part1By1(x);
}

inline uint64_t encodeMorton64(uint64_t x, uint64_t y)
{
  assert(x < (1u << 31));
  assert(y < (1u << 31));
  return (detail::Part1By1_64b(y) << 1) + detail::Part1By1_64b(x);
}

inline uint32_t encodeMorton(uint32_t x, uint32_t y, uint32_t z)
{
  assert(x < (1u << 10));
  assert(y < (1u << 10));
  assert(z < (1u << 10));
  return (detail::Part1By2(z) << 2) + (detail::Part1By2(y) << 1)
      + detail::Part1By2(x);
}

inline void decodeMorton(uint32_t code,
                         uint32_t & x, uint32_t & y)
{
  x = detail::Compact1By1(code >> 0);
  y = detail::Compact1By1(code >> 1);
}

inline void decodeMorton(uint32_t code,
                         uint32_t & x, uint32_t & y, uint32_t & z)
{
  x = detail::Compact1By2(code >> 0);
  y = detail::Compact1By2(code >> 1);
  z = detail::Compact1By2(code >> 2);
}

template <typename IntType, int M>
inline IntType interleave_bits(IntType a, IntType b)
{
  IntType as = detail::spread_bits<IntType,M>(a);
  IntType bs = detail::spread_bits<IntType,M>(b);
  return (as << 1) | bs;
}

template <typename IntType, int M>
inline IntType interleave_bits(IntType a, IntType b, IntType c)
{
  IntType as = detail::spread_bits<IntType,M>(a);
  IntType bs = detail::spread_bits<IntType,M>(b);
  IntType cs = detail::spread_bits<IntType,M>(c);
  return (as << 2) | (bs << 1) | cs;
}


#endif // MORTON_H
