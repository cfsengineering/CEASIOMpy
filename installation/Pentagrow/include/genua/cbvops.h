
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

#ifndef GENUA_CBVOPS_H
#define GENUA_CBVOPS_H

#include "forward.h"
#include "defines.h"
#include "simdsupport.h"

namespace internal {

template <typename FloatType>
struct CbvOps
{
  // single-array functions

  static FloatType* fill(size_t n, const FloatType &a, FloatType v[]) {
OMP_SIMD("aligned(v:8)")
    for (size_t i=0; i<n; ++i)
      v[i] = a;
    return v;
  }

  static FloatType sqsum(size_t n, const FloatType v[]) {
    FloatType sum(0);
OMP_SIMD("reduction(+:sum) aligned(v:8)")
    for (size_t i=0; i<n; ++i)
      sum += v[i]*v[i];
    return sum;
  }

  static FloatType maxabs(size_t n, const FloatType v[]) {
    FloatType val(0);
OMP_SIMD("reduction(max:val) aligned(v:8)")
    for (size_t i=0; i<n; ++i) {
      FloatType va = std::fabs(v[i]);
      val = (va > val) ? va : val;
    }
    return val;
  }

  static FloatType minabs(size_t n, const FloatType v[]) {
    FloatType val = std::numeric_limits<FloatType>::max();
OMP_SIMD("reduction(min:val) aligned(v:8)")
    for (size_t i=0; i<n; ++i){
      FloatType va = std::fabs(v[i]);
      val = (va < val) ? va : val;
    }
    return val;
  }

  static FloatType* scale(size_t n, const FloatType &a, FloatType v[]) {
OMP_SIMD("aligned(v:8)")
    for (size_t i=0; i<n; ++i)
      v[i] *= a;
    return v;
  }

  // two-array functions

  static FloatType dot(size_t n, const FloatType x[], const FloatType y[]) {
    FloatType sum(0);
OMP_SIMD("reduction(+:sum) aligned(x,y:8)")
    for (size_t i=0; i<n; ++i)
      sum += x[i]*y[i];
    return sum;
  }

  static FloatType* axpy(size_t n,
                         const FloatType &a, const FloatType x[],
                         const FloatType &b, FloatType y[])
  {
OMP_SIMD("aligned(x,y:8)")
    for (size_t i=0; i<n; ++i)
      y[i] = a*x[i] + b*y[i];
    return y;
  }

  /// Hadamard (element-wise) product
  static FloatType* hprod(size_t n,
                          const FloatType xa[], const FloatType xb[],
                          FloatType y[])
  {
OMP_SIMD("aligned(xa,xb,y:8)")
    for (size_t i=0; i<n; ++i)
      y[i] = xa[i] * xb[i];
    return y;
  }

  // three-array functions

  static FloatType* axpy(size_t n,
                   const FloatType &a, const FloatType x[],
                   const FloatType &b, const FloatType y[],
                   const FloatType &c, FloatType z[])
  {
OMP_SIMD("aligned(x,y,z:8)")
    for (size_t i=0; i<n; ++i)
      z[i] = a*x[i] + b*y[i] + c*z[i];
    return z;
  }

};

template <>
struct CbvOps<std::complex<float> >
{
  // single-array functions

  static std::complex<float>* fill(size_t n,
                   const std::complex<float> &a, std::complex<float> v[]) {
OMP_SIMD("aligned(v:8)")
    for (size_t i=0; i<n; ++i)
      v[i] = a;
    return v;
  }

  static std::complex<float> sqsum(size_t n, const std::complex<float> v[]) {
    float sum(0);
OMP_SIMD("reduction(+:sum) aligned(v:8)")
    for (size_t i=0; i<n; ++i)
      sum += std::real( std::conj(v[i]) * v[i] );
    return sum;
  }

  static std::complex<float> maxabs(size_t n, const std::complex<float> v[]) {
    float val(0), va;
OMP_SIMD("reduction(max:val) aligned(v:8)")
    for (size_t i=0; i<n; ++i) {
      va = std::abs(v[i]);
      val = (va > val) ? va : val;
    }
    return val;
  }

  static std::complex<float> minabs(size_t n, const std::complex<float> v[]) {
    float va, val = std::numeric_limits<float>::max();
OMP_SIMD("reduction(min:val) aligned(v:8)")
    for (size_t i=0; i<n; ++i){
      va = std::abs(v[i]);
      val = (va < val) ? va : val;
    }
    return val;
  }

  static std::complex<float>* scale(size_t n,
                    const std::complex<float> &a, std::complex<float> v[]) {
OMP_SIMD("aligned(v:8)")
    for (size_t i=0; i<n; ++i)
      v[i] *= a;
    return v;
  }

  // two-array functions

  static std::complex<float> dot(size_t n, const std::complex<float> x[],
                                 const std::complex<float> y[])
  {
    float rsum(0.0f), isum(0.0f);
    std::complex<float> t;
OMP_SIMD("reduction(+:rsum,isum) aligned(x,y:8)")
    for (size_t i=0; i<n; ++i) {
      t = std::conj(x[i]) * y[i];
      rsum += t.real();
      isum += t.imag();
    }
    return std::complex<float>(rsum, isum);
  }


  static std::complex<float>* axpy(size_t n,
                   const std::complex<float> &a, const std::complex<float> x[],
                   const std::complex<float> &b, std::complex<float> y[])
  {
OMP_SIMD("aligned(x,y:8)")
    for (size_t i=0; i<n; ++i)
      y[i] = a*x[i] + b*y[i];
    return y;
  }

  /// Hadamard (element-wise) product
  static std::complex<float>* hprod(size_t n,
                          const std::complex<float> xa[], const std::complex<float> xb[],
                          std::complex<float> y[])
  {
OMP_SIMD("aligned(xa,xb,y:8)")
    for (size_t i=0; i<n; ++i)
      y[i] = xa[i] * xb[i];
    return y;
  }

  // three-array functions

  static std::complex<float>* axpy(size_t n,
                   const std::complex<float> &a, const std::complex<float> x[],
                   const std::complex<float> &b, const std::complex<float> y[],
                   const std::complex<float> &c, std::complex<float> z[])
  {
OMP_SIMD("aligned(x,y,z:8)")
    for (size_t i=0; i<n; ++i)
      z[i] = a*x[i] + b*y[i] + c*z[i];
    return z;
  }

};

template <>
struct CbvOps<std::complex<double> >
{
  // single-array functions

  static std::complex<double>* fill(size_t n,
                   const std::complex<double> &a, std::complex<double> v[]) {
OMP_SIMD("aligned(v:8)")
    for (size_t i=0; i<n; ++i)
      v[i] = a;
    return v;
  }

  static std::complex<double> sqsum(size_t n, const std::complex<double> v[]) {
    double sum(0);
OMP_SIMD("reduction(+:sum) aligned(v:8)")
    for (size_t i=0; i<n; ++i) {
      sum += std::real( std::conj(v[i]) * v[i] );
    }
    return std::complex<double>(sum, 0.0);
  }

  static std::complex<double> maxabs(size_t n, const std::complex<double> v[]) {
    double val(0), va;
OMP_SIMD("reduction(max:val) aligned(v:8)")
    for (size_t i=0; i<n; ++i) {
      va = std::abs(v[i]);
      val = (va > val) ? va : val;
    }
    return val;
  }

  static std::complex<double> minabs(size_t n, const std::complex<double> v[]) {
    double va, val = std::numeric_limits<double>::max();
OMP_SIMD("reduction(min:val) aligned(v:8)")
    for (size_t i=0; i<n; ++i){
      va = std::abs(v[i]);
      val = (va < val) ? va : val;
    }
    return val;
  }

  static std::complex<double>* scale(size_t n,
                    const std::complex<double> &a, std::complex<double> v[]) {
OMP_SIMD("aligned(v:8)")
    for (size_t i=0; i<n; ++i)
      v[i] *= a;
    return v;
  }

  // two-array functions

  static std::complex<double> dot(size_t n, const std::complex<double> x[],
                                 const std::complex<double> y[])
  {
    double rsum(0.0), isum(0.0);
    std::complex<double> t;
OMP_SIMD("reduction(+:rsum,isum) aligned(x,y:8)")
    for (size_t i=0; i<n; ++i) {
      t = std::conj(x[i]) * y[i];
      rsum += t.real();
      isum += t.imag();
    }
    return std::complex<double>(rsum, isum);
  }


  static std::complex<double>* axpy(size_t n,
                   const std::complex<double> &a, const std::complex<double> x[],
                   const std::complex<double> &b, std::complex<double> y[])
  {
OMP_SIMD("aligned(x,y:8)")
    for (size_t i=0; i<n; ++i)
      y[i] = a*x[i] + b*y[i];
    return y;
  }

  /// Hadamard (element-wise) product
  static std::complex<double>* hprod(size_t n,
                          const std::complex<double> xa[], const std::complex<double> xb[],
                          std::complex<double> y[])
  {
OMP_SIMD("aligned(xa,xb,y:8)")
    for (size_t i=0; i<n; ++i)
      y[i] = xa[i] * xb[i];
    return y;
  }

  // three-array functions

  static std::complex<double>* axpy(size_t n,
                   const std::complex<double> &a, const std::complex<double> x[],
                   const std::complex<double> &b, const std::complex<double> y[],
                   const std::complex<double> &c, std::complex<double> z[])
  {
OMP_SIMD("aligned(x,y,z:8)")
    for (size_t i=0; i<n; ++i)
      z[i] = a*x[i] + b*y[i] + c*z[i];
    return z;
  }

};

// partial specializations for compilers without OpenMP 4

#if !defined(_OPENMP) || (_OPENMP < 201307)

template <>
struct CbvOps<float>
{

  // single-array functions

  static float* fill(size_t n, const float &a, float v[]) {
    float16 va(a);
    const size_t ncl = n/16 + ((n&15) != 0);
    for (size_t i=0; i<ncl; ++i)
      va.store(&v[16*i]);
    return v;
  }

  static float sqsum(size_t n, const float v[]) {
    float16 vi, vsum(0.0f);
    const size_t ncl = n/16 + ((n&15) != 0);
    for (size_t i=0; i<ncl; ++i) {
      vi.load(&v[16*i]);
      vsum = fmuladd(vi, vi, vsum);
    }

    ALIGNAS(32) float tmp[16];
    vsum.store(tmp);
    float sum(0.0f);
    for (int j=0; j<16; ++j)
      sum += tmp[j];
    return sum;
  }

  static float maxabs(size_t n, const float v[]) {
    float16 vi, vmax(0.0f);
    const size_t ncl = n/16 + ((n&15) != 0);
    for (size_t i=0; i<ncl; ++i) {
      vi.load(&v[16*i]);
      vmax = max(vmax, fabs(vi));
    }

    ALIGNAS(32) float tmp[16];
    vmax.store(tmp);
    float smax(0.0f);
    for (int j=0; j<16; ++j)
      smax = std::max(smax, tmp[j]);
    return smax;
  }

  static float minabs(size_t n, const float v[]) {
    float16 vi, vmin( std::numeric_limits<float>::max() );
    const size_t ncl = n/16 + ((n&15) != 0);
    for (size_t i=0; i<ncl; ++i) {
      vi.load(&v[16*i]);
      vmin = min(vmin, fabs(vi));
    }

    ALIGNAS(32) float tmp[16];
    vmin.store(tmp);
    float smin = std::numeric_limits<float>::max();
    for (int j=0; j<16; ++j)
      smin = std::min(smin, tmp[j]);
    return smin;
  }

  static float* scale(size_t n, const float &a, float v[]) {
    float16 vi, va(a);
    const size_t ncl = n/16 + ((n&15) != 0);
    for (size_t i=0; i<ncl; ++i) {
      vi.load(&v[16*i]);
      vi *= va;
      vi.store(&v[16*i]);
    }
    return v;
  }

  // two-array functions

  static float dot(size_t n, const float x[], const float y[]) {
    float16 vsum(0.0f);
    const size_t ncl = n/16 + ((n&15) != 0);
    for (size_t i=0; i<ncl; ++i)
      vsum = fmuladd(float16(&x[16*i]), float16(&y[16*i]), vsum);

    ALIGNAS(32) float tmp[16];
    vsum.store(tmp);
    float sum(0.0f);
    for (int j=0; j<16; ++j)
      sum += tmp[j];
    return sum;
  }

  static float* axpy(size_t n,
                   const float &a, const float x[],
                   const float &b, float y[])
  {
    const float16 va(a), vb(b);
    const size_t ncl = n/16 + ((n&15) != 0);
    for (size_t i=0; i<ncl; ++i)
      fmuladd(va, float16(&x[16*i]), vb*float16(&y[16*i])).store(&y[16*i]);
    return y;
  }

  /// Hadamard (element-wise) product, y = xa * xb
  static float* hprod(size_t n,
                      const float xa[], const float xb[],
                      float y[])
  {
    const size_t ncl = n/16 + ((n&15) != 0);
    for (size_t i=0; i<ncl; ++i) {
      float16 yi = float16(&xa[16*i]) * float16(&xb[16*i]);
      yi.store(&y[16*i]);
    }
    return y;
  }

  // three-array functions

  static float* axpy(size_t n,
                   const float &a, const float x[],
                   const float &b, const float y[],
                   const float &c, float z[])
  {
    const float16 va(a), vb(b), vc(c);
    float16 t1, t2;
    const size_t ncl = n/16 + ((n&15) != 0);
    for (size_t i=0; i<ncl; ++i) {
      t1 = fmuladd(vb, float16(&y[16*i]), vc*float16(&z[16*i]));
      t2 = fmuladd(va, float16(&x[16*i]), t1);
      t2.store(&z[16*i]);
    }
    return z;
  }

};

template <>
struct CbvOps<double>
{

  // single-array functions

  static double* fill(size_t n, const double &a, double v[]) {
    double8 va(a);
    const size_t ncl = n/8 + ((n&7) != 0);
    for (size_t i=0; i<ncl; ++i)
      va.store(&v[8*i]);
    return v;
  }

  static double sqsum(size_t n, const double v[]) {
    double8 vi, vsum(0.0f);
    const size_t ncl = n/8 + ((n&7) != 0);
    for (size_t i=0; i<ncl; ++i) {
      vi.load(&v[8*i]);
      vsum = fmuladd(vi, vi, vsum);
    }

    ALIGNAS(32) double tmp[8];
    vsum.store(tmp);
    double sum(0.0f);
    for (int j=0; j<8; ++j)
      sum += tmp[j];
    return sum;
  }

  static double maxabs(size_t n, const double v[]) {
    double8 vi, vmax(0.0);
    const size_t ncl = n/8 + ((n&7) != 0);
    for (size_t i=0; i<ncl; ++i) {
      vi.load(&v[8*i]);
      vmax = max(vmax, fabs(vi));
    }

    ALIGNAS(32) double tmp[8];
    vmax.store(tmp);
    double smax(0.0);
    for (int j=0; j<8; ++j)
      smax = std::max(smax, tmp[j]);
    return smax;
  }

  static double minabs(size_t n, const double v[]) {
    double8 vi, vmin( std::numeric_limits<double>::max() );
    const size_t ncl = n/8 + ((n&7) != 0);
    for (size_t i=0; i<ncl; ++i) {
      vi.load(&v[8*i]);
      vmin = min(vmin, fabs(vi));
    }

    ALIGNAS(32) double tmp[8];
    vmin.store(tmp);
    double smin = std::numeric_limits<double>::max();
    for (int j=0; j<8; ++j)
      smin = std::min(smin, tmp[j]);
    return smin;
  }

  static double* scale(size_t n, const double &a, double v[]) {
    double8 vi, va(a);
    const size_t ncl = n/8 + ((n&7) != 0);
    for (size_t i=0; i<ncl; ++i) {
      vi.load(&v[8*i]);
      vi *= va;
      vi.store(&v[8*i]);
    }
    return v;
  }

  // two-array functions

  static double dot(size_t n, const double x[], const double y[]) {
    double8 vsum(0.0f);
    const size_t ncl = n/8 + ((n&7) != 0);
    for (size_t i=0; i<ncl; ++i)
      vsum = fmuladd(double8(&x[8*i]), double8(&y[8*i]), vsum);

    ALIGNAS(32) double tmp[8];
    vsum.store(tmp);
    double sum(0.0f);
    for (int j=0; j<8; ++j)
      sum += tmp[j];
    return sum;
  }

  static double* axpy(size_t n,
                   const double &a, const double x[],
                   const double &b, double y[])
  {
    const double8 va(a), vb(b);
    const size_t ncl = n/8 + ((n&7) != 0);
    for (size_t i=0; i<ncl; ++i)
      fmuladd(va, double8(&x[8*i]), vb*double8(&y[8*i])).store(&y[8*i]);
    return y;
  }

  /// Hadamard (element-wise) product, y = xa * xb
  static double* hprod(size_t n,
                      const double xa[], const double xb[],
                      double y[])
  {
    const size_t ncl = n/8 + ((n&7) != 0);
    for (size_t i=0; i<ncl; ++i) {
      double8 yi = double8(&xa[8*i]) * double8(&xb[8*i]);
      yi.store(&y[8*i]);
    }
    return y;
  }

  // three-array functions

  static double* axpy(size_t n,
                   const double &a, const double x[],
                   const double &b, const double y[],
                   const double &c, double z[])
  {
    const double8 va(a), vb(b), vc(c);
    double8 t1, t2;
    const size_t ncl = n/8 + ((n&7) != 0);
    for (size_t i=0; i<ncl; ++i) {
      t1 = fmuladd(vb, double8(&y[8*i]), vc*double8(&z[8*i]));
      t2 = fmuladd(va, double8(&x[8*i]), t1);
      t2.store(&z[8*i]);
    }
    return z;
  }

};

#endif // partial specializations for OpenMP < 4.0

template <typename FloatType>
inline FloatType sqsum(const size_t n, const FloatType v[])
{
  return CbvOps<FloatType>::sqsum(n, v);
}

template <typename FloatType>
inline FloatType norm2(const size_t n, const FloatType v[])
{
  return std::sqrt( CbvOps<FloatType>::sqsum(n, v) );
}

template <typename FloatType>
inline FloatType maxabs(const size_t n, const FloatType v[])
{
  return CbvOps<FloatType>::maxabs(n, v);
}

template <typename FloatType>
inline FloatType minabs(const size_t n, const FloatType v[])
{
  return CbvOps<FloatType>::minabs(n, v);
}

template <typename FloatType>
inline FloatType* scale(size_t n, FloatType a, FloatType v[])
{
  return CbvOps<FloatType>::scale(n, a, v);
}

template <typename FloatType>
inline FloatType dotprod(size_t n, const FloatType x[], const FloatType y[])
{
  return CbvOps<FloatType>::dot(n, x, y);
}

template <typename FloatType>
inline FloatType* hprod(size_t n, const FloatType xa[],
                        const FloatType xb[], FloatType y[])
{
  return CbvOps<FloatType>::hprod(n, xa, xb, y);
}

template <typename FloatType>
inline FloatType* axpy(size_t n, FloatType a, const FloatType x[],
                 FloatType b, FloatType y[])
{
  return CbvOps<FloatType>::axpy(n, a, x, b, y);
}

template <typename FloatType>
inline FloatType* axpy(size_t n, FloatType a, const FloatType x[],
                 FloatType b, const FloatType y[],
                 FloatType c, FloatType z[])
{
  return CbvOps<FloatType>::axpy(n, a, x, b, y, c, z);
}

} // namespace internal

#endif // CBVOPS_H
