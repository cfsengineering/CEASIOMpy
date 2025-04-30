#ifndef GENUA_SIMDBASE_H
#define GENUA_SIMDBASE_H

#include "sse.h"
#include <boost/static_assert.hpp>

// forward declarations needed for template disambiguation

template <typename ScalarType, int W> struct SimdBase;

template <typename VectorType, typename XType, int W>
force_inline void simd_strided_gather(int stride, const XType x[],
                                      VectorType &xp) attr_always_inline;

template <typename VectorType, typename XType, int W>
force_inline void simd_strided_scatter(int stride,
                                       const VectorType &xp,
                                       XType x[]) attr_always_inline;

template <typename VectorType, typename XType, int W>
force_inline void simd_strided_pack(int stride, const XType x[],
                                    VectorType xp[]) attr_always_inline;

template <typename VectorType, typename XType, int W>
force_inline void simd_strided_unpack(int stride,
                                      const VectorType xp[],
                                      XType x[]) attr_always_inline;

/** Base class for vector types.
 *
 * This is a thin wrapper base class which serves to make the vector width
 * available to algorithms which avoid specifying the width as an additional
 * template argument. Strictly speaking, this would only be required for
 * compilers which don't understand C++11 constexpr.
 *
 * Furthermore, there are a few general gather/scatter operations implemented
 * here. These are often needed to transpose scalar arrays for SIMD processing.
 * Although these are implemented in a very basic manner, inspection of the
 * generated assembler shows that compilers turn this into appropriate sequences
 * of extract/insert instructions where available.
 *
 * \ingroup numerics
 * \sa float4, float8, double2, double4, EmulatedSimdType
 */
template <typename ScalarType, int W>
struct SimdBase
{
  typedef ScalarType      Scalar;

  /// the number of lanes, or vector width
  static const int lanes = W;

  /// strided gather (x need not be aligned)
  template <typename VectorType>
  static void gather(int m, const Scalar x[], VectorType &xp)
  {
    simd_strided_gather<VectorType,Scalar,W>(m, x, xp);
  }

  /// strided scatter (x need not be aligned)
  template <typename VectorType>
  static void scatter(int m, const VectorType &xp, Scalar x[])
  {
    simd_strided_scatter<VectorType,Scalar,W>(m, xp, x);
  }

  /// pack W*m values from x where they are stored with stride m
  template <typename VectorType>
  static void pack(int m, const Scalar x[], VectorType xp[])
  {
    simd_strided_pack<VectorType,Scalar,W>(m, x, xp);
  }

  /// store W*m values to x where they are stored with stride m
  template <typename VectorType>
  static void unpack(int m, const VectorType xp[], Scalar x[])
  {
    simd_strided_unpack<VectorType,Scalar,W>(m, x, xp);
  }
};

template <typename VectorType, typename XType, int W>
force_inline void simd_strided_gather(int stride, const XType x[],
                                      VectorType &xp)
{
  typedef typename VectorType::Scalar Scalar;
  BOOST_STATIC_ASSERT(W*sizeof(Scalar) <= 32);
  ALIGNAS(32) Scalar tmp[W];
#pragma clang loop unroll(enable)
  for (int j=0; j<W; ++j)
    tmp[j] = Scalar(x[stride*j]);
  xp.load(tmp);
}

template <typename VectorType, typename XType, int W>
force_inline void simd_strided_scatter(int stride,
                                       const VectorType &xp,
                                       XType x[])
{
  typedef typename VectorType::Scalar Scalar;
  BOOST_STATIC_ASSERT(W*sizeof(Scalar) <= 32);
  ALIGNAS(32) Scalar tmp[W];
  xp.store(tmp);
#pragma clang loop unroll(enable)
  for (int j=0; j<W; ++j)
    x[stride*j] = XType(tmp[j]);
}

template <typename VectorType, typename XType, int W>
force_inline void simd_strided_pack(int stride, const XType x[],
                                    VectorType xp[])
{
  typedef typename VectorType::Scalar Scalar;
  BOOST_STATIC_ASSERT(W*sizeof(Scalar) <= 32);
  ALIGNAS(32) Scalar tmp[W];
  for (int i=0; i<stride; ++i) {
#pragma clang loop unroll(enable)
    for (int j=0; j<W; ++j)
      tmp[j] = Scalar(x[stride*j+i]);
    xp[i].load(tmp);
  }
}

template <typename VectorType, typename XType, int W>
force_inline void simd_strided_unpack(int stride,
                                      const VectorType xp[],
                                      XType x[])
{
  typedef typename VectorType::Scalar Scalar;
  BOOST_STATIC_ASSERT(W*sizeof(Scalar) <= 32);
  ALIGNAS(32) Scalar tmp[W];
  for (int i=0; i<stride; ++i) {
    xp[i].store(tmp);
#pragma clang loop unroll(enable)
    for (int j=0; j<W; ++j)
      x[stride*j+i] = XType(tmp[j]);
  }
}

#endif // SIMDBASE_H

