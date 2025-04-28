
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
 
#ifndef GENUA_KDOP_H
#define GENUA_KDOP_H

#include "svector.h"
#include "float4.h"

/** Discrete oriented polytopes.

  Base class for discrete oriented polytopes (k-DOPs) which provides
  a general interface common to all specialized implementations. Note that the
  template parameter N is the number of plane directions (slabs), there are two
  planes (and hence distance coefficients) per direction.

  This base class is independent of the number of space dimensions. Specialized
  implementations which fix the number of space dimensions should derive from
  this base class.

  \ingroup geometry
  \sa NDPointTree, Dop2d2, Dop3d3, Dop4d4, Dop4d16
*/
template <class Type, int N>
class DopBase
{
public:

  typedef Type FloatType;

  /// initialize DOP
  DopBase() { this->reset(); }

  /// initialize DOP
  explicit DopBase(const Type pmin[], const Type pmax[]) {
    for (int i=0; i<N; ++i) {
      coef[i] = std::min( pmin[i], pmax[i] );
      coef[N+i] = std::max( pmin[i], pmax[i] );
    }
  }

  /// number of axes
  static int naxes() {return N;}

  /// pointer to first coefficient (stored serially)
  force_inline const FloatType *pointer() const {return coef;}

  /// pointer to first coefficient (stored serially)
  force_inline FloatType *pointer() {return coef;}

  /** Helper method to be used/specialized by child classes.
  This version of adapt() has been profiled to be the fastest implementation
  with current compilers. Use local variables fmin, fmax and iterate over the
  items to be enclosed by this DOP updating the local variables, then call
  setCoef() with the local fmin,fmax.
   */
  force_inline static void fit(const Type c[], Type fmin[], Type fmax[]) {
    for (int k=0; k<N; ++k) {
      fmin[k] = std::min(fmin[k], c[k]);
      fmax[k] = std::max(fmax[k], c[k]);
    }
  }

  /// minimum coefficient for plane k
  force_inline Type minCoef(int k) const {
    assert(k < N);
    return coef[k];
  }

  /// maximum coefficient for plane k
  force_inline Type maxCoef(int k) const {
    assert(k < N);
    return coef[N+k];
  }

  /// set coefficients explicitely
  void setCoef(const Type fmin[], const Type fmax[]) {
    for (int i=0; i<N; ++i) {
      coef[i] = fmin[i];
      coef[N+i] = fmax[i];
    }
  }

  /// test whether point p is inside or on box boundary
  force_inline bool inside(const Type p[]) const {
    bool isin = true;
    for (int i=0; i<N; ++i) {
      Type pi = p[i];
      isin &= ((pi >= minCoef(i)) and (pi <= maxCoef(i)));
    }
    return isin;
  }

  /// (under-) estimate the distance of c(p) from bounding volume
  force_inline Type minCoefDistance(const Type c[]) {
    Type dmin = std::numeric_limits<Type>::max();
    for (int i=0; i<N; ++i) {
      Type d1 = minCoef(i) - c[i];
      Type d2 = c[i] - maxCoef(i);
      if (d1 >= 0)
        dmin = std::min(dmin, d1);
      else if (d2 >= 0) // can't be both
        dmin = std::min(dmin, d2);
    }
    return dmin;
  }

  /// determine euclidean distance of point from box, return squared norm
  force_inline Type eclDistance(const Type p[], Type ds[]) const {
    Type sqd(0);
    for (int i=0; i<N; ++i) {
      Type d1 = minCoef(i) - p[i];
      Type d2 = p[i] - maxCoef(i);
      ds[i] = (d1 > 0) ? d1 : ( (d2 > 0) ? d2 : 0 );
      sqd += sq(ds[i]);
    }
    return sqd;
  }

  /// determine euclidean distance of point from box, return squared norm
  force_inline Type eclDistance(const Type c[]) const {
    // obviously, this only works for orthonormal axes (axis-aligned boxes)
    Type sqd(0);
    for (int i=0; i<N; ++i) {
      Type d1 = minCoef(i) - c[i];
      Type d2 = c[i] - maxCoef(i);
      Type di = (d1 > 0) ? d1 : ( (d2 > 0) ? d2 : 0 );
      sqd += sq(di);
    }
    assert(std::isfinite(sqd));
    return sqd;
  }

  /// adapt min and max of axis k to enclose c
  force_inline void adapt(uint k, Type c) {
    coef[k] = std::min(coef[k], c);
    coef[N+k] = std::max(coef[N+k], c);
  }

  /// adapt min and max for all axes
  force_inline void adapt(const Type c[]) {
    for (int i=0; i<N; ++i)
      adapt(i, c[i]);
  }

  /// determine index of longest axis
  int longestAxis() const {
    int ilong(0);
    Type lmax = maxCoef(0) - minCoef(0);
    for (int i=1; i<N; ++i) {
      Type dx = maxCoef(i) -  minCoef(i);
      if (dx > lmax) {
        ilong = i;
        lmax = dx;
      }
    }
    return ilong;
  }

  /// make box undefined
  force_inline void reset() {
    for (int i=0; i<N; ++i) {
      coef[i] = std::numeric_limits<Type>::max();
      coef[N+i] = -coef[i];
    }
  }

  /// expand box by a fixed amount in each direction
  force_inline void expand(Type dx) {
    for (int i=0; i<N; ++i) {
      coef[i] -= dx;
      coef[N+i] += dx;
    }
  }

  /// center coordinates
  force_inline void center(Type ctr[]) const {
    const Type half(0.5f);
    for (int i=0; i<N; ++i)
      ctr[i] = half*( coef[i] + coef[N+i] );
  }

  /// compute a box size (sum of squares of plane distances)
  force_inline Type sqsize() const {
    Type vol(0.0f);
    for (int i=0; i<N; ++i)
      vol += sq(maxCoef(i) - minCoef(i));
    return vol;
  }

  /// set all coefficients to huge value
  force_inline void invalidate() {
    for (int i=0; i<N; ++i)
      coef[i] = coef[N+i] = std::numeric_limits<Type>::max();
  }

  /// test for intersection with another DOP
  force_inline bool intersects(const DopBase<Type,N> & b) const {
    for (int i=0; i<N; ++i) {
      if (minCoef(i) > b.maxCoef(i))
        return false;
      else if (b.minCoef(i) > maxCoef(i))
        return false;
    }
    return true;
  }

  /// enclose another DOP
  force_inline void enclose(const DopBase<Type,N> & b) {
    const Type *bc = b.coef;
    adapt(&bc[0]);
    adapt(&bc[N]);
  }

  /// equality
  bool operator== (const DopBase<Type,N> & b) {
    for (int i=0; i<2*N; ++i)
      if (coef[i] != b.coef[i])
        return false;
    return true;
  }

protected:

  /// min/max coefficients for each plane
  Type coef[2*N];
};

// two space dimensions

/** 2D axis-aligned 2D bounding box expressed as a k-DOP.
 *
 * Replaces BndRect.
 *
 * \ingroup geometry
 * \sa DopBase
 */
template <class Type>
class Dop2d2 : public DopBase<Type,2>
{
  public:

  /// axis-aligned, hence coordinates are coefficients
  Type pointDistance(const Type p[]) const
  {
    return eclDistance(p);
  }

  static void fitPoint(const float q[], float fmin[], float fmax[])
  {
    DopBase<Type,2>::fit(q, fmin, fmax);
  }
};

// three space dimensions

/** Axis-aligned 3D bounding box expressed as a k-DOP.
 *
 * Replaces BndBox.
 *
 * \ingroup geometry
 * \sa DopBase
 */
template <class Type>
class Dop3d3 : public DopBase<Type,3>
{
public:

  /// empty
  Dop3d3() : DopBase<Type,3>() {}

  /// initialize using extreme points
  Dop3d3(const Type pmin[], const Type pmax[]) : DopBase<Type,3>(pmin, pmax) {}

  /// axis-aligned, hence coordinates are coefficients
  Type pointDistance(const Type p[]) const
  {
    return DopBase<Type,3>::eclDistance(p);
  }

  /// minmum distance from another box
  Type minDistance(const Dop3d3<Type> &a) const
  {
    Type sqd(0);
    for (int i=0; i<3; ++i) {
      Type d1 = a.minCoef(i) - this->maxCoef(i);
      Type d2 = this->minCoef(i) - a.maxCoef(i);
      if (d1 > 0)
        sqd += sq(d1);
      else if (d2 > 0)
        sqd += sq(d2);
    }
    return sqd;
  }

  static void fitPoint(const float q[], float fmin[], float fmax[])
  {
    DopBase<Type,3>::fit(q, fmin, fmax);
  }
};

/** Octahedral bounding volume in 3D.
 *
 * This oriented polytope uses four separating planes instead of the
 * tree cartesian planes, which results in slightly smaller volumes for
 * objects which are not naturally aligned with coordinate axes. Since there
 * are four axes, the fitting operation is vectorized when SSE2 instructions
 * are available.
 *
 * Because of the spatial orientation of the separating axes, this type of
 * DOP tends to be less useful for the common case of objects with some
 * kind of alignment along cartesian axes.
 *
 * \ingroup geometry
 * \sa DopBase
 */
template <class Type>
class Dop3d4 : public DopBase<Type,4>
{
public:

  static void fitPoint(const float q[], float fmin[], float fmax[])
  {
    const Type isq3( 0.577350269189626 );
    Type qx = q[0];
    Type qy = q[1];
    Type qz = q[2];

    Type c = isq3*(qx+qy+qz);
    fmin[0] = std::min(fmin[0], c);
    fmax[0] = std::max(fmax[0], c);
    c = isq3*(qx+qy-qz);
    fmin[1] = std::min(fmin[1], c);
    fmax[1] = std::max(fmax[1], c);
    c = isq3*(qx-qy+qz);
    fmin[2] = std::min(fmin[2], c);
    fmax[2] = std::max(fmax[2], c);
    c = isq3*(-qx+qy+qz);
    fmin[3] = std::min(fmin[3], c);
    fmax[3] = std::max(fmax[3], c);
  }
};

#if defined(ARCH_SSE2)

template <>
inline void Dop3d4<float>::fitPoint(const float q[], float fmin[], float fmax[])
{
  // q need not be aligned
  assert(sse_aligned(fmin));
  assert(sse_aligned(fmax));

  // axis directions
  const float isq3 = 0.577350269189626f;
  SSE_PS_CONST4(Ax, isq3, isq3, isq3, -isq3);
  SSE_PS_CONST4(Ay, isq3, isq3, -isq3, isq3);
  SSE_PS_CONST4(Az, isq3, -isq3, isq3, isq3);

  // compute coefficients
  float4 qx(q[0]), qy(q[1]), qz(q[2]);
  float4 c = float4(Ax)*qx + float4(Ay)*qy + float4(Az)*qz;
  min(c, float4(fmin)).store(fmin);
  max(c, float4(fmax)).store(fmax);
}

#endif // ARCH_SSE2

// four dimensions, space-time

/** Axis-aligned 4D bounding box expressed as a k-DOP.
 *
 * This is the 'cartesian' AABB for space-time coordinates. Is is extremely
 * efficient because the fitting operation translates directly to SIMD
 * instructions for (x,y,z,t) points.
 *
 *
 * \ingroup geometry
 * \sa DopBase
 */
template <class Type>
class Dop4d4 : public DopBase<Type,4>
{
  /// axis-aligned, hence coordinates are coefficients
  Type pointDistance(const Type p[]) const
  {
    return eclDistance(p);
  }

  /// specialized where SSE is available
  bool intersects(const Dop4d4<Type> & b) const {
    for (int i=0; i<4; ++i) {
      if (this->minCoef(i) > b.maxCoef(i))
        return false;
      else if (b.minCoef(i) > this->maxCoef(i))
        return false;
    }
    return true;
  }

  /// specialized where SSE is available
  static void fitPoint(const float q[], float fmin[], float fmax[])
  {
    DopBase<Type,4>::fit(q, fmin, fmax);
  }
};

#if defined(ARCH_SSE2)

template <>
inline void Dop4d4<float>::fitPoint(const float q[], float fmin[], float fmax[])
{
  // requires guaranteed alignment of all arguments
  // speedup factor 1.6 (gcc, profiled on Intel Lynnfield)
  assert(sse_aligned(q));
  assert(sse_aligned(fmin));
  assert(sse_aligned(fmax));
  float4 qx(q);
  min(qx, float4(fmin)).store(fmin);
  max(qx, float4(fmax)).store(fmax);
}

template <>
inline bool Dop4d4<float>::intersects(const Dop4d4<float> & b) const
{
  // cannot intersect if a_min > b_max *or* b_min > a_max

  // d1 = a_max - b_min, negative if no intersection possible
  float4 d1 = float4( &coef[4] ) - float4( &(b.coef[0]) );

  // d2 = b_max - a_min, negative if no intersection possible
  float4 d2 = float4( &(b.coef[4]) ) - float4( &coef[0] );

  // result is != 0 if any of the two is negative, intersection is only
  // possible if both are exactly zero, since then d1 > 0 and d2 > 0
  int flag = _mm_movemask_ps(d1.xmm) | _mm_movemask_ps(d2.xmm);
  return (flag == 0);
}

#endif // ARCH_SSE2

/** 9-plane discrete polytope in 3D.

  This is commonly referred to as an 18-DOP, as it uses a total
  of 18 planes (9 axes). Normal vectors are chosen such that pairs of
  planes are parallel.

 * \ingroup geometry
 * \sa DopBase
 */
template <class Type>
class Dop3d9 : public DopBase<Type, 9>
{
public:

  /// reset on construction
  Dop3d9() : DopBase<Type,9>() {}

  /// enclose 3D vertex p
  void enclose(const Type p[]) {
    Type c[9];
    pcoef(p, c);
    encloseCoef(c);
  }

  /// enclose another DOP
  void enclose(const Dop3d9<Type> & b) {
    DopBase<Type,9>::enclose(b);
  }

  /// add variance measure of 3D point p to var
  void addVariance(const Type ctr[], const Type p[], Type var[]) const {
    Type c[9];
    pcoef(p, c);
    for (int i=0; i<9; ++i)
      var[i] += sq( c[i] - ctr[i] );
  }

  /// scalar default implementation
  static void fitPoint(const float q[], float fmin[], float fmax[])
  {
    const Type rs2( 0.707106781186547 );
    Type c = q[0];
    fmin[0] = std::min(fmin[0], c);
    fmax[0] = std::max(fmax[0], c);
    c = q[1];
    fmin[1] = std::min(fmin[1], c);
    fmax[1] = std::max(fmax[1], c);
    c = q[2];
    fmin[2] = std::min(fmin[2], c);
    fmax[2] = std::max(fmax[2], c);
    c = rs2*(q[0] + q[1]);
    fmin[3] = std::min(fmin[3], c);
    fmax[3] = std::max(fmax[3], c);
    c = rs2*(q[0] + q[2]);
    fmin[4] = std::min(fmin[4], c);
    fmax[4] = std::max(fmax[4], c);
    c = rs2*(q[1] + q[2]);
    fmin[5] = std::min(fmin[5], c);
    fmax[5] = std::max(fmax[5], c);
    c = rs2*(q[0] - q[1]);
    fmin[6] = std::min(fmin[6], c);
    fmax[6] = std::max(fmax[6], c);
    c = rs2*(q[7] - q[2]);
    fmin[7] = std::min(fmin[7], c);
    fmax[7] = std::max(fmax[7], c);
    c = rs2*(q[1] - q[2]);
    fmin[8] = std::min(fmin[8], c);
    fmax[8] = std::max(fmax[8], c);
  }

protected:

  /// compute 9 coefficients for a point
  void pcoef(const Type p[], Type c[]) const {
    const float rs2 = 0.707106781186547f;
    c[0] = p[0];
    c[1] = p[1];
    c[2] = p[2];
    c[3] = rs2*(p[0] + p[1]);
    c[4] = rs2*(p[0] + p[2]);
    c[5] = rs2*(p[1] + p[2]);
    c[6] = rs2*(p[0] - p[1]);
    c[7] = rs2*(p[0] - p[2]);
    c[8] = rs2*(p[1] - p[2]);
  }

};

#ifdef ARCH_SSE2

template <>
inline void Dop3d9<float>::fitPoint(const float q[], float fmin[], float fmax[])
{
  assert(sse_aligned(fmin));
  assert(sse_aligned(fmax));

  // compute coefficients
  float4 qx(q[0]), qy(q[1]), qz(q[2]);

  // this could just as well use float8 (-> AVX, OpenCL...)

  // process the first 4 axes using SSE
  const float isq2 = 0.707106781186547f;
  SSE_PS_CONST4(Ax, 1.0f, 0.0f, 0.0f, isq2);
  SSE_PS_CONST4(Ay, 0.0f, 1.0f, 0.0f, isq2);
  SSE_PS_CONST4(Az, 0.0f, 0.0f, 1.0f, 0.0f);

  float4 c = float4(Ax)*qx + float4(Ay)*qy + float4(Az)*qz;
  min(c, float4(&fmin[0])).store(&fmin[0]);
  max(c, float4(&fmax[0])).store(&fmax[0]);

  // process the next 4 axes using SSE
  SSE_PS_CONST4(Bx, isq2, 0.0f, isq2, isq2);
  SSE_PS_CONST4(By, 0.0f, isq2, -isq2, 0.0f);
  SSE_PS_CONST4(Bz, isq2, isq2, 0.0f, -isq2);

  c = float4(Bx)*qx + float4(By)*qy + float4(Bz)*qz;
  min(c, float4(&fmin[4])).store(&fmin[4]);
  max(c, float4(&fmax[4])).store(&fmax[4]);

  // process last axis using scalar op
  float cs = isq2*(q[1] - q[2]);
  fmin[8] = std::min(fmin[8], cs);
  fmax[8] = std::max(fmax[8], cs);
}

#endif

/** 16-plane discrete polytope in 4D.

  A four-dimensional 32-DOP.

  \todo
  Implementation note: pcoef() is not optimized away, which means that
  c[16] (stack) is actually filled and read again once, resulting in a
  lot of uneccessary mov instructions. Need to find an alternative
  implementation which guarantees inlining.

*/
template <class Type>
class Dop4d16 : public DopBase<Type, 16>
{
public:

  /// reset on construction
  Dop4d16() : DopBase<Type,16>() {}

  //  /// enclose 4D vertex p
  //  void enclose(const Type p[]) {
  //    Type c[16];
  //    pcoef(p, c);
  //    encloseCoef(c);
  //  }

  void enclose(const Type p[]) {
    // 24 flops, 32 min/max, clocked to use 111 cpu cycles (Conroe)
    // that is 0.37 microseconds per call at 3GHz
    const float rs2 = 0.707106781186547f;
    adapt(0, p[0]);
    adapt(1, p[1]);
    adapt(2, p[2]);
    adapt(3, p[3]);
    adapt(4, rs2*(p[0] + p[1]));
    adapt(5, rs2*(p[0] + p[2]));
    adapt(6, rs2*(p[0] + p[3]));
    adapt(7, rs2*(p[1] + p[2]));

    adapt(8, rs2*(p[1] + p[3]));
    adapt(9, rs2*(p[2] + p[3]));
    adapt(10, rs2*(p[0] - p[1]));
    adapt(11, rs2*(p[0] - p[2]));

    adapt(12, rs2*(p[0] - p[3]));
    adapt(13, rs2*(p[1] - p[2]));
    adapt(14, rs2*(p[1] - p[3]));
    adapt(15, rs2*(p[2] - p[3]));
  }

  /// enclose another DOP
  void enclose(const Dop4d16<Type> & b) {
    DopBase<Type,16>::enclose(b);
  }

  /// add variance measure of 4D point p to var
  void addVariance(const Type ctr[], const Type p[], Type var[]) const {
    Type c[16];
    pcoef(p, c);
    for (int i=0; i<16; ++i)
      var[i] += sq( c[i] - ctr[i] );
  }

protected:

  /// compute 16 coefficients for a point
  void pcoef(const Type p[], Type c[]) const {
    const float rs2 = 0.707106781186547f;

    c[0] = p[0];
    c[1] = p[1];
    c[2] = p[2];
    c[3] = p[3];

    c[4] = rs2*(p[0] + p[1]);
    c[5] = rs2*(p[0] + p[2]);
    c[6] = rs2*(p[0] + p[3]);
    c[7] = rs2*(p[1] + p[2]);
    c[8] = rs2*(p[1] + p[3]);
    c[9] = rs2*(p[2] + p[3]);

    c[10] = rs2*(p[0] - p[1]);
    c[11] = rs2*(p[0] - p[2]);
    c[12] = rs2*(p[0] - p[3]);
    c[13] = rs2*(p[1] - p[2]);
    c[14] = rs2*(p[1] - p[3]);
    c[15] = rs2*(p[2] - p[3]);
  }

};

// specialization using SSE, need alignment guarantees
// profiled to be slower than scalar code (shufps latency?)

//#if defined(ARCH_SSE2)
//
//#include "float4.h"
//
//template <>
//inline void Dop4d16<float>::enclose(const float p[])
//{
//  assert(sse_aligned(coef));
//  assert(sse_aligned(p));
//
//  // constants
//  SSE_PS_CONST1(r1, 0.7071068f);
//  SSE_PS_CONST4(r2, 0.7071068f, 0.7071068f, -0.7071068f, -0.7071068f);
//
//  float4 clo(&coef[0]), chi(&coef[16]), xp(p);
//
//  // first block
//  //  adapt(0, p[0]);
//  //  adapt(1, p[1]);
//  //  adapt(2, p[2]);
//  //  adapt(3, p[3]);
//  min( float4(&coef[0]), xp).store( &coef[0] );
//  max( float4(&coef[16]), xp).store( &coef[16] );
//
//  // second block
//  //  adapt(4, rs2*(p[0] + p[1]));
//  //  adapt(5, rs2*(p[0] + p[2]));
//  //  adapt(6, rs2*(p[0] + p[3]));
//  //  adapt(7, rs2*(p[1] + p[2]));
//  float4 pa = shuffle(xp, xp, 0, 0, 0, 1);
//  float4 pb = shuffle(xp, xp, 1, 2, 3, 2);
//  float4 t = float4(r1)*(pa + pb);
//  min( float4(&coef[4]), t).store( &coef[4] );
//  max( float4(&coef[20]), t).store( &coef[20] );
//
//  // third block
//  //  adapt(8, rs2*(p[1] + p[3]));
//  //  adapt(9, rs2*(p[2] + p[3]));
//  //  adapt(10, rs2*(p[0] - p[1]));
//  //  adapt(11, rs2*(p[0] - p[2]));
//  pa = shuffle(xp, xp, 1,2,0,0);
//  pb = shuffle(xp, xp, 3,3,1,2);
//  t = float4(r1)*pa + float4(r2)*pb;
//  min( float4(&coef[8]), t).store( &coef[8] );
//  max( float4(&coef[24]), t).store( &coef[24] );
//
//  // fourth block
//  //  adapt(12, rs2*(p[0] - p[3]));
//  //  adapt(13, rs2*(p[1] - p[2]));
//  //  adapt(14, rs2*(p[1] - p[3]));
//  //  adapt(15, rs2*(p[2] - p[3]));
//  pa = shuffle(xp, xp, 0,1,1,2);
//  pb = shuffle(xp, xp, 3,2,3,3);
//  t = float4(r1)*(pa - pb);
//  min( float4(&coef[12]), t).store( &coef[12] );
//  max( float4(&coef[28]), t).store( &coef[28] );
//}
//
//#endif

#endif // KDOP_H
