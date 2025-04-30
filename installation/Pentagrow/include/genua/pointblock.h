/* Copyright (C) 2018 David Eller <david@larosterna.com>
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

#ifndef GENUA_POINTBLOCK_H
#define GENUA_POINTBLOCK_H

#include "forward.h"
#include "simdsupport.h"
#include "bitfiddle.h"
#include "svector.h"
#include "point.h"

/** Block of 16 points.
 *
 *  Used for the vectorization of geometric algorithms.
 *
 * \ingroup numerics
 * \sa double2, double4, double8, float8, float16
 **/
struct PointBlock16f
{

  /// undefined block
  PointBlock16f() = default;

  /// copy construct
  PointBlock16f(const PointBlock16f &a) = default;

  /// broadcast single value to all values
  explicit PointBlock16f(float a) : xc(a), yc(a), zc(a) {}

  /// initialize from SIMD values
  PointBlock16f(const float16 &x, const float16 &y, const float16 &z)
    : xc(x), yc(y), zc(z) {}

  /// copy assignment
  PointBlock16f &operator= (const PointBlock16f &a) = default;

  /// load aligned array containing [x,y,z] in sequence
  void load(const float *x) {
    xc.load(x);
    yc.load(x+16);
    zc.load(x+32);
  }

  /// load aligned arrays
  void load(const float *x, const float *y, const float *z) {
    xc.load(x);
    yc.load(y);
    zc.load(z);
  }

  /// store to aligned arrays containing [x,y,z] in sequence
  void store(float *x) const {
    xc.store(x);
    yc.store(x+16);
    zc.store(x+32);
  }

  /// store to aligned arrays
  void store(float *x, float *y, float *z) const {
    xc.store(x);
    yc.store(y);
    zc.store(z);
  }

  /// shuffle in from (x,y,z,x,y,z...) storage
  force_inline void shuffleIn(const float *p) attr_always_inline {
    float ax[16], ay[16], az[16];
    for (int i=0; i<16; ++i) {
      ax[i] = p[3*i+0];
      ay[i] = p[3*i+1];
      az[i] = p[3*i+2];
    }
    xc = float16(ax);
    yc = float16(ay);
    zc = float16(az);
  }

  /// shuffle out to (x,y,z,x,y,z...) storage
  force_inline void shuffleOut(float *p) attr_always_inline {
    ALIGNED_AVX float ax[16], ay[16], az[16];
    xc.store(ax);
    yc.store(ay);
    zc.store(az);
    for (int i=0; i<16; ++i) {
      p[3*i+0] = ax[i];
      p[3*i+1] = ay[i];
      p[3*i+2] = az[i];
    }
  }

  /// add-assign
  PointBlock16f &operator+= (const PointBlock16f &a) {
    xc += a.xc;
    yc += a.yc;
    zc += a.zc;
    return *this;
  }

  /// substract-assign
  PointBlock16f &operator-= (const PointBlock16f &a) {
    xc -= a.xc;
    yc -= a.yc;
    zc -= a.zc;
    return *this;
  }

  /// scale by scalar
  PointBlock16f &operator*= (float a) {
    float16 f(a);
    xc *= f;
    yc *= f;
    zc *= f;
    return *this;
  }

  /// scale by vector
  PointBlock16f &operator*= (const float16 &f) {
    xc *= f;
    yc *= f;
    zc *= f;
    return *this;
  }

  /// normalize all points, return lengths
  float16 normalize() {
    float16 sql = fmuladd(xc, xc, fmuladd(yc, yc, zc*zc) );
    float16 len = sqrt(sql);
    float16 inl = float16(1.0f) / len;
    xc *= inl;
    yc *= inl;
    zc *= inl;
    return len;
  }

  /// make lengths equal to a
  PointBlock16f &rescale(const float16 &a) {
    float16 sql = fmuladd(xc, xc, fmuladd(yc, yc, zc*zc) );
    float16 inl = a / sqrt(sql);
    xc *= inl;
    yc *= inl;
    zc *= inl;
    return *this;
  }

  /// normalize all points
  PointBlock16f normalized() const {
    PointBlock16f b(*this);
    b.normalize();
    return b;
  }

  /// compute center of a pointlist using blocked SIMD operations
  static Vct3f center(const PointList3f &pts) {
    Vct3f ctr;
    const size_t np = pts.size();
    if ( hint_unlikely(np == 0) )
      return ctr;

    PointBlock16f a, sum(0.0f);
    const size_t nb = np/16;
    const float *fp = pts.front().pointer();
    if (nb > 0) {
      assert( pointer_aligned<64>(fp) );
      for (size_t i=0; i<nb; ++i) {
        a.load(fp);
        sum += a;
        fp += 48;
      }

      ALIGNED_AVX float tmp[48];
      sum.store(tmp);
      for (int k=0; k<16; ++k) {
        ctr[0] += tmp[3*k+0];
        ctr[1] += tmp[3*k+1];
        ctr[2] += tmp[3*k+2];
      }
    }

    for (size_t i=(16*nb); i<np; ++i)
      ctr += pts[i];

    return ctr;
  }

  /// compute distance from c for all points in pts
  static void distances(const PointList3f &pts, const Vct3f &c,
                        DVector<float> &dst)
  {
    const size_t np = pts.size();
    const size_t nb = np/16;
    dst.allocate(np);

    float16 cx(c[0]);
    float16 cy(c[1]);
    float16 cz(c[2]);
    PointBlock16f a, bc(cx, cy, cz);
    for (size_t i=0; i<nb; ++i) {
      a.shuffleIn(pts[16*i].pointer());
      a -= bc;
      float16 dsq = fmuladd(a.zc, a.zc, fmuladd(a.yc, a.yc, a.xc*a.xc));
      float16 ri = sqrt(dsq);
      ri.store(&dst[16*i]);
    }

    for (size_t i=(16*nb); i<np; ++i)
      dst[i] = norm(pts[i] - c);
  }

  /// 48 coordinate values
  float16 xc, yc, zc;
};

/// add blocks
inline PointBlock16f operator+(const PointBlock16f &a, const PointBlock16f &b)
{
  PointBlock16f c(a);
  c += b;
  return c;
}

/// substract blocks
inline PointBlock16f operator-(const PointBlock16f &a, const PointBlock16f &b)
{
  PointBlock16f c(a);
  c -= b;
  return c;
}

/// dot products between blocks
inline float16 dot(const PointBlock16f &a, const PointBlock16f &b)
{
  return fmuladd( a.xc, b.xc, fmuladd(a.yc, b.yc, a.zc*b.zc) );
  // return a.xc*b.xc + a.yc*b.yc + a.zc*b.zc;
}

/// cross product between blocks of points
inline PointBlock16f cross(const PointBlock16f &a, const PointBlock16f &b)
{
  float16 x = fmulsub(a.yc, b.zc, b.yc*a.zc);
  float16 y = fmulsub(a.zc, b.xc, b.zc*a.xc);
  float16 z = fmulsub(a.xc, b.yc, b.xc*a.yc);
  // float16 x = a.yc*b.zc - b.yc*a.zc;
  // float16 y = a.zc*b.xc - b.zc*a.xc;
  // float16 z = a.xc*b.yc - b.xc*a.yc;
  return PointBlock16f(x, y, z);
}

#endif // POINTBLOCK_H
