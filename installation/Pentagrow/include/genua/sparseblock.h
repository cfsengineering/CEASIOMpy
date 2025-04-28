
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

#ifndef GENUA_SPARSEBLOCK_H
#define GENUA_SPARSEBLOCK_H

#include "smatrix.h"
#include "smallqr.h"
#include "simdsupport.h"

// TODO
// - Cleanup, repack into helper class
// - introduce fused multiply-add

namespace detail {

template <typename FloatType, int M>
struct block_op
{

  // diagonally scale a = diag(rs) * a * diag(fabs(cs))
  static void scale( const FloatType rs[],  const FloatType cs[],
                     SMatrix<M,M,FloatType> &a )
  {
    for (int j=0; j<M; ++j) {
      FloatType fs = std::fabs(cs[j]);
      for (int i=0; i<M; ++i)
        a(i,j) *= rs[i]*fs;
    }
  }

  // b += a*x
  static void mvadd( const SMatrix<M,M,FloatType> &a,
                     const FloatType x[], FloatType b[] )
  {
    for (int j=0; j<M; ++j)
      for (int i=0; i<M; ++i)
        b[i] += a(i,j)*x[j];
  }

  // b -= a*x
  static void mvsub( const SMatrix<M,M,FloatType> &a,
                     const FloatType x[], FloatType b[] )
  {
    for (int j=0; j<M; ++j)
      for (int i=0; i<M; ++i)
        b[i] -= a(i,j)*x[j];
  }

  // c += a*b
  static void mmadd(const SMatrix<M,M,FloatType> &a,
                    const SMatrix<M,M,FloatType> &b,
                    SMatrix<M,M,FloatType> &c)
  {
    for (int j=0; j<M; ++j)
      for (int i=0; i<M; ++i)
        for (int k=0; k<M; ++k)
          c(i,j) += a(i,k) * b(k,j);
  }

  // c -= a*b
  static void mmsub(const SMatrix<M,M,FloatType> &a,
                    const SMatrix<M,M,FloatType> &b,
                    SMatrix<M,M,FloatType> &c)
  {
    for (int j=0; j<M; ++j)
      for (int i=0; i<M; ++i)
        for (int k=0; k<M; ++k)
          c(i,j) -= a(i,k) * b(k,j);
  }
};

template <>
struct block_op<double,2>
{
  // scale a
  static void scale( const double rs[], const double cs[],
                     SMatrix<2,2,double> &a )
  {
    double2 vrs(rs), ac;
    for (int j=0; j<2; ++j) {
      ac.load(a.colpointer(j));
      ac *= vrs * fabs(double2(cs[j]));
      ac.store(a.colpointer(j));
    }
  }

  // b += a*x
  static void mvadd( const SMatrix<2,2,double> &a,
                     const double x[], double b[] )
  {
    double2 bv(b);
    // bv = fmuladd(double2( a.colpointer(0) ), double2(x[0]), bv);
    // bv = fmuladd(double2(a.colpointer(1)), double2(x[1]), bv);
    bv += double2( a.colpointer(0) ) * x[0];
    bv += double2( a.colpointer(1) ) * x[1];
    bv.store(b);
  }

  // b -= a*x
  static void mvsub( const SMatrix<2,2,double> &a,
                     const double x[], double b[] )
  {
    // x need not be aligned in general, loaded as scalar
    double2 bv(b);
    bv -= double2( a.colpointer(0) ) * x[0];
    bv -= double2( a.colpointer(1) ) * x[1];
    bv.store(b);
  }

  // c += a*b
  static void mmadd(const SMatrix<2,2,double> &a,
                    const SMatrix<2,2,double> &b,
                    SMatrix<2,2,double> &c)
  {
    double2 ac0(a.colpointer(0));
    double2 ac1(a.colpointer(1));

    double2 cc0(c.colpointer(0));
    cc0 += ac0*b(0,0) + ac1*b(1,0);
    cc0.store(c.colpointer(0));

    double2 cc1(c.colpointer(1));
    cc1 += ac0*b(0,1) + ac1*b(1,1);
    cc1.store(c.colpointer(1));
  }

  // c -= a*b
  static void mmsub(const SMatrix<2,2,double> &a,
                    const SMatrix<2,2,double> &b,
                    SMatrix<2,2,double> &c)
  {
    double2 ac0(a.colpointer(0));
    double2 ac1(a.colpointer(1));

    double2 cc0(c.colpointer(0));
    cc0 -= ac0*b(0,0) + ac1*b(1,0);
    cc0.store(c.colpointer(0));

    double2 cc1(c.colpointer(1));
    cc1 -= ac0*b(0,1) + ac1*b(1,1);
    cc1.store(c.colpointer(1));
  }
};

template <>
struct block_op<float,4>
{
  // scale
  static void scale( const float rs[], const float cs[],
                     SMatrix<4,4,float> &a )
  {
    float4 vrs(rs), ac;
    for (int j=0; j<4; ++j) {
      ac.load(a.colpointer(j));
      ac *= vrs * fabs(float4(cs[j]));
      ac.store(a.colpointer(j));
    }
  }

  // b += a*x
  static void mvadd( const SMatrix<4,4,float> &a,
                     const float x[], float b[] )
  {
    float4 bv(b);
    bv += float4( a.colpointer(0) ) * x[0];
    bv += float4( a.colpointer(1) ) * x[1];
    bv += float4( a.colpointer(2) ) * x[2];
    bv += float4( a.colpointer(3) ) * x[3];
    bv.store(b);
  }

  // b -= a*x
  static void mvsub( const SMatrix<4,4,float> &a,
                     const float x[], float b[] )
  {
    float4 bv(b);
    bv -= float4( a.colpointer(0) ) * x[0];
    bv -= float4( a.colpointer(1) ) * x[1];
    bv -= float4( a.colpointer(2) ) * x[2];
    bv -= float4( a.colpointer(3) ) * x[3];
    bv.store(b);
  }

  // c += a*b
  static void mmadd(const SMatrix<4,4,float> &a,
                    const SMatrix<4,4,float> &b,
                    SMatrix<4,4,float> &c)
  {
    float4 ac0(a.colpointer(0));
    float4 ac1(a.colpointer(1));
    float4 ac2(a.colpointer(2));
    float4 ac3(a.colpointer(3));

    float4 cc0(c.colpointer(0));
    cc0 += ac0*b(0,0) + ac1*b(1,0) + ac2*b(2,0) + ac3*b(3,0);
    cc0.store(c.colpointer(0));

    float4 cc1(c.colpointer(1));
    cc1 += ac0*b(0,1) + ac1*b(1,1) + ac2*b(2,1) + ac3*b(3,1);
    cc1.store(c.colpointer(1));

    float4 cc2(c.colpointer(2));
    cc2 += ac0*b(0,2) + ac1*b(1,2) + ac2*b(2,2) + ac3*b(3,2);
    cc2.store(c.colpointer(2));

    float4 cc3(c.colpointer(3));
    cc3 += ac0*b(0,3) + ac1*b(1,3) + ac2*b(2,3) + ac3*b(3,3);
    cc3.store(c.colpointer(3));
  }

  // c -= a*b
  static void mmsub(const SMatrix<4,4,float> &a,
                    const SMatrix<4,4,float> &b,
                    SMatrix<4,4,float> &c)
  {
    float4 ac0(a.colpointer(0));
    float4 ac1(a.colpointer(1));
    float4 ac2(a.colpointer(2));
    float4 ac3(a.colpointer(3));

    float4 cc0(c.colpointer(0));
    cc0 -= ac0*b(0,0) + ac1*b(1,0) + ac2*b(2,0) + ac3*b(3,0);
    cc0.store(c.colpointer(0));

    float4 cc1(c.colpointer(1));
    cc1 -= ac0*b(0,1) + ac1*b(1,1) + ac2*b(2,1) + ac3*b(3,1);
    cc1.store(c.colpointer(1));

    float4 cc2(c.colpointer(2));
    cc2 -= ac0*b(0,2) + ac1*b(1,2) + ac2*b(2,2) + ac3*b(3,2);
    cc2.store(c.colpointer(2));

    float4 cc3(c.colpointer(3));
    cc3 -= ac0*b(0,3) + ac1*b(1,3) + ac2*b(2,3) + ac3*b(3,3);
    cc3.store(c.colpointer(3));
  }
};

template <>
struct block_op<double,4>
{
  // scale a
  static void scale( const double rs[], const double cs[],
                     SMatrix<4,4,double> &a )
  {
    double4 vrs(rs), ac;
    for (int j=0; j<4; ++j) {
      ac.load(a.colpointer(j));
      ac *= vrs * fabs(double4(cs[j]));
      ac.store(a.colpointer(j));
    }
  }

  // b += a*x
  static void mvadd( const SMatrix<4,4,double> &a,
                     const double x[], double b[] )
  {
    double4 bv(b);
    bv += double4( a.colpointer(0) ) * x[0];
    bv += double4( a.colpointer(1) ) * x[1];
    bv += double4( a.colpointer(2) ) * x[2];
    bv += double4( a.colpointer(3) ) * x[3];
    bv.store(b);
  }

  // b -= a*x
  static void mvsub( const SMatrix<4,4,double> &a,
                     const double x[], double b[] )
  {
    // x need not be aligned in general, loaded as scalar
    double4 bv(b);
    bv -= double4( a.colpointer(0) ) * x[0];
    bv -= double4( a.colpointer(1) ) * x[1];
    bv -= double4( a.colpointer(2) ) * x[2];
    bv -= double4( a.colpointer(3) ) * x[3];
    bv.store(b);
  }

  // c += a*b
  static void mmadd(const SMatrix<4,4,double> &a,
                    const SMatrix<4,4,double> &b,
                    SMatrix<4,4,double> &c)
  {
    double4 ac0(a.colpointer(0));
    double4 ac1(a.colpointer(1));
    double4 ac2(a.colpointer(2));
    double4 ac3(a.colpointer(3));

    double4 cc0(c.colpointer(0));
    cc0 += ac0*b(0,0) + ac1*b(1,0) + ac2*b(2,0) + ac3*b(3,0);
    cc0.store(c.colpointer(0));

    double4 cc1(c.colpointer(1));
    cc1 += ac0*b(0,1) + ac1*b(1,1) + ac2*b(2,1) + ac3*b(3,1);
    cc1.store(c.colpointer(1));

    double4 cc2(c.colpointer(2));
    cc2 += ac0*b(0,2) + ac1*b(1,2) + ac2*b(2,2) + ac3*b(3,2);
    cc2.store(c.colpointer(2));

    double4 cc3(c.colpointer(3));
    cc3 += ac0*b(0,3) + ac1*b(1,3) + ac2*b(2,3) + ac3*b(3,3);
    cc3.store(c.colpointer(3));
  }

  // c -= a*b
  static void mmsub(const SMatrix<4,4,double> &a,
                    const SMatrix<4,4,double> &b,
                    SMatrix<4,4,double> &c)
  {
    double4 ac0(a.colpointer(0));
    double4 ac1(a.colpointer(1));
    double4 ac2(a.colpointer(2));
    double4 ac3(a.colpointer(3));

    double4 cc0(c.colpointer(0));
    cc0 -= ac0*b(0,0) + ac1*b(1,0) + ac2*b(2,0) + ac3*b(3,0);
    cc0.store(c.colpointer(0));

    double4 cc1(c.colpointer(1));
    cc1 -= ac0*b(0,1) + ac1*b(1,1) + ac2*b(2,1) + ac3*b(3,1);
    cc1.store(c.colpointer(1));

    double4 cc2(c.colpointer(2));
    cc2 -= ac0*b(0,2) + ac1*b(1,2) + ac2*b(2,2) + ac3*b(3,2);
    cc2.store(c.colpointer(2));

    double4 cc3(c.colpointer(3));
    cc3 -= ac0*b(0,3) + ac1*b(1,3) + ac2*b(2,3) + ac3*b(3,3);
    cc3.store(c.colpointer(3));
  }
};

template <>
struct block_op<float,8>
{
  // scale
  static void scale( const float rs[], const float cs[],
                     SMatrix<8,8,float> &a )
  {
    float8 vrs(rs), ac;
    for (int j=0; j<8; ++j) {
      ac.load(a.colpointer(j));
      ac *= vrs * fabs(float8(cs[j]));
      ac.store(a.colpointer(j));
    }
  }

  // b += a*x
  static void mvadd( const SMatrix<8,8,float> &a,
                     const float x[], float b[] )
  {
    float8 bv(b);
    bv += float8( a.colpointer(0) ) * x[0];
    bv += float8( a.colpointer(1) ) * x[1];
    bv += float8( a.colpointer(2) ) * x[2];
    bv += float8( a.colpointer(3) ) * x[3];
    bv += float8( a.colpointer(4) ) * x[4];
    bv += float8( a.colpointer(5) ) * x[5];
    bv += float8( a.colpointer(6) ) * x[6];
    bv += float8( a.colpointer(7) ) * x[7];
    bv.store(b);
  }

  // b -= a*x
  static void mvsub( const SMatrix<8,8,float> &a,
                     const float x[], float b[] )
  {
    float8 bv(b);
    bv -= float8( a.colpointer(0) ) * x[0];
    bv -= float8( a.colpointer(1) ) * x[1];
    bv -= float8( a.colpointer(2) ) * x[2];
    bv -= float8( a.colpointer(3) ) * x[3];
    bv -= float8( a.colpointer(4) ) * x[4];
    bv -= float8( a.colpointer(5) ) * x[5];
    bv -= float8( a.colpointer(6) ) * x[6];
    bv -= float8( a.colpointer(7) ) * x[7];
    bv.store(b);
  }

  // c += a*b
  static void mmadd(const SMatrix<8,8,float> &a,
                    const SMatrix<8,8,float> &b,
                    SMatrix<8,8,float> &c)
  {
    float8 ac0(a.colpointer(0));
    float8 ac1(a.colpointer(1));
    float8 ac2(a.colpointer(2));
    float8 ac3(a.colpointer(3));
    float8 ac4(a.colpointer(4));
    float8 ac5(a.colpointer(5));
    float8 ac6(a.colpointer(6));
    float8 ac7(a.colpointer(7));

    // let compiler decide on unrolling
    float8 cc;
    CPHINT_UNROLL_LOOP
    for (int i=0; i<8; ++i) {
      cc.load(c.colpointer(i));
      cc += ac0*b(0,i) + ac1*b(1,i) + ac2*b(2,i) + ac3*b(3,i) +
            ac4*b(4,i) + ac5*b(5,i) + ac6*b(6,i) + ac7*b(7,i);
      cc.store(c.colpointer(i));
    }
  }

  // c -= a*b
  static void mmsub(const SMatrix<8,8,float> &a,
                    const SMatrix<8,8,float> &b,
                    SMatrix<8,8,float> &c)
  {
    float8 ac0(a.colpointer(0));
    float8 ac1(a.colpointer(1));
    float8 ac2(a.colpointer(2));
    float8 ac3(a.colpointer(3));
    float8 ac4(a.colpointer(4));
    float8 ac5(a.colpointer(5));
    float8 ac6(a.colpointer(6));
    float8 ac7(a.colpointer(7));

    // let compiler decide on unrolling
    float8 cc;
    CPHINT_UNROLL_LOOP
    for (int i=0; i<8; ++i) {
      cc.load(c.colpointer(i));
      cc -= ac0*b(0,i) + ac1*b(1,i) + ac2*b(2,i) + ac3*b(3,i) +
            ac4*b(4,i) + ac5*b(5,i) + ac6*b(6,i) + ac7*b(7,i);
      cc.store(c.colpointer(i));
    }
  }
};

template <>
struct block_op<double,8>
{
  // scale
  static void scale( const double rs[], const double cs[],
                     SMatrix<8,8,double> &a )
  {
    double8 vrs(rs), ac;
    for (int j=0; j<8; ++j) {
      ac.load(a.colpointer(j));
      ac *= vrs * fabs(double8(cs[j]));
      ac.store(a.colpointer(j));
    }
  }

  // b += a*x
  static void mvadd( const SMatrix<8,8,double> &a,
                     const double x[], double b[] )
  {
    double8 bv(b);
    bv += double8( a.colpointer(0) ) * x[0];
    bv += double8( a.colpointer(1) ) * x[1];
    bv += double8( a.colpointer(2) ) * x[2];
    bv += double8( a.colpointer(3) ) * x[3];
    bv += double8( a.colpointer(4) ) * x[4];
    bv += double8( a.colpointer(5) ) * x[5];
    bv += double8( a.colpointer(6) ) * x[6];
    bv += double8( a.colpointer(7) ) * x[7];
    bv.store(b);
  }

  // b -= a*x
  static void mvsub( const SMatrix<8,8,double> &a,
                     const double x[], double b[] )
  {
    double8 bv(b);
    bv -= double8( a.colpointer(0) ) * x[0];
    bv -= double8( a.colpointer(1) ) * x[1];
    bv -= double8( a.colpointer(2) ) * x[2];
    bv -= double8( a.colpointer(3) ) * x[3];
    bv -= double8( a.colpointer(4) ) * x[4];
    bv -= double8( a.colpointer(5) ) * x[5];
    bv -= double8( a.colpointer(6) ) * x[6];
    bv -= double8( a.colpointer(7) ) * x[7];
    bv.store(b);
  }

  // c += a*b
  static void mmadd(const SMatrix<8,8,double> &a,
                    const SMatrix<8,8,double> &b,
                    SMatrix<8,8,double> &c)
  {
    double8 ac0(a.colpointer(0));
    double8 ac1(a.colpointer(1));
    double8 ac2(a.colpointer(2));
    double8 ac3(a.colpointer(3));
    double8 ac4(a.colpointer(4));
    double8 ac5(a.colpointer(5));
    double8 ac6(a.colpointer(6));
    double8 ac7(a.colpointer(7));

    // let compiler decide on unrolling
    double8 cc;
    CPHINT_UNROLL_LOOP
    for (int i=0; i<8; ++i) {
      cc.load(c.colpointer(i));
      cc += ac0*b(0,i) + ac1*b(1,i) + ac2*b(2,i) + ac3*b(3,i) +
            ac4*b(4,i) + ac5*b(5,i) + ac6*b(6,i) + ac7*b(7,i);
      cc.store(c.colpointer(i));
    }
  }

  // c -= a*b
  static void mmsub(const SMatrix<8,8,double> &a,
                    const SMatrix<8,8,double> &b,
                    SMatrix<8,8,double> &c)
  {
    double8 ac0(a.colpointer(0));
    double8 ac1(a.colpointer(1));
    double8 ac2(a.colpointer(2));
    double8 ac3(a.colpointer(3));
    double8 ac4(a.colpointer(4));
    double8 ac5(a.colpointer(5));
    double8 ac6(a.colpointer(6));
    double8 ac7(a.colpointer(7));

    // let compiler decide on unrolling
    double8 cc;
    CPHINT_UNROLL_LOOP
    for (int i=0; i<8; ++i) {
      cc.load(c.colpointer(i));
      cc -= ac0*b(0,i) + ac1*b(1,i) + ac2*b(2,i) + ac3*b(3,i) +
            ac4*b(4,i) + ac5*b(5,i) + ac6*b(6,i) + ac7*b(7,i);
      cc.store(c.colpointer(i));
    }
  }
};

// ------------------- legacy ------------------------------------------------

// transpose in-place
template <typename FloatType, int M>
inline void block_transpose(SMatrix<M,M,FloatType> &a)
{
  for (int i=0; i<M; ++i)
    for (int j=i+1; j<M; ++j)
      std::swap(a(i,j), a(j,i));
}

// primitive generic form of b += a*x
template <typename AType, typename XType, typename BType, int M>
inline void block_muladdv(const SMatrix<M,M,AType> &a,
                          const XType x[], BType b[])
{
#pragma omp simd reduction(+:b) collapse(2)
  for (int j=0; j<M; ++j)
    for (int i=0; i<M; ++i)
      b[i] += a(i,j)*x[j];
}

// primitive generic form of b -= a*x
template <typename AType, typename XType, typename BType, int M>
inline void block_mulsubv(const SMatrix<M,M,AType> &a,
                          const XType x[], BType b[])
{
#pragma omp simd reduction(-:b) collapse(2)
  for (int j=0; j<M; ++j)
    for (int i=0; i<M; ++i)
      b[i] -= a(i,j)*x[j];
}

// primitive generic form of b += a^T * x = x^T * a
template <typename AType, typename XType, typename BType, int M>
inline void block_tmuladdv(const SMatrix<M,M,AType> &a,
                           const XType x[], BType b[])
{
#pragma omp simd reduction(+:b) collapse(2)
  for (int j=0; j<M; ++j)
    for (int i=0; i<M; ++i)
      b[j] += x[i]*a(i,j);
}

// primitive general block update c += a*b
template <typename FloatType, int M>
inline void block_mmadd(const SMatrix<M,M,FloatType> &a,
                        const SMatrix<M,M,FloatType> &b,
                        SMatrix<M,M,FloatType> &c)
{
#pragma omp simd reduction(+:c) collapse(3)
  for (int j=0; j<M; ++j)
    for (int i=0; i<M; ++i)
      for (int k=0; k<M; ++k)
        c(i,j) += a(i,k) * b(k,j);
}

// primitive general block update c -= a*b
template <typename FloatType, int M>
inline void block_mmsub(const SMatrix<M,M,FloatType> &a,
                        const SMatrix<M,M,FloatType> &b,
                        SMatrix<M,M,FloatType> &c)
{
#pragma omp simd reduction(-:c) collapse(3)
  for (int j=0; j<M; ++j)
    for (int i=0; i<M; ++i)
      for (int k=0; k<M; ++k)
        c(i,j) -= a(i,k) * b(k,j);
}

template <typename FloatType, int M>
inline bool block_inverse(const SMatrix<M,M,FloatType> &p,
                          SMatrix<M,M,FloatType> &invp)
{
  if (M == 1) {
    invp[0] = FloatType(1) / p[0];
    return (p[0] != FloatType(0));
  }

  FloatType qrf[M*M], tau[M];
  memcpy(qrf, p.pointer(), M*M*sizeof(FloatType));
  int qrok = qr<M,M>( qrf, tau );
  invp = SMatrix<M,M,FloatType>::identity();
  for (int i=0; i<M; ++i)
    qrsolve<M,M>(qrf, tau, invp.colpointer(i));

  return qrok;
}

template <typename FloatType, int M>
inline FloatType block_maxabs(const SMatrix<M,M,FloatType> &a)
{
  FloatType r(0);
  for (int i=0; i<M*M; ++i)
    r = std::max(r, std::abs(a[i]));
  return r;
}

template <>
inline float block_maxabs<float,4>(const SMatrix<4,4,float> &a)
{
  float4 r;
  r = fabs( float4(a.colpointer(0)) );
  r = max( r, fabs( float4(a.colpointer(1)) ) );
  r = max( r, fabs( float4(a.colpointer(2)) ) );
  r = max( r, fabs( float4(a.colpointer(3)) ) );

  float t[4];
  r.store(t);
  t[0] = std::max(t[0], t[1]);
  t[2] = std::max(t[2], t[3]);
  return std::max(t[0], t[2]);
}

// manually vectorized form of b += a*x
template <>
inline void block_muladdv<float,float,float,4>(const Mtx44f &a,
                                               const float x[], float b[])
{
  // x need not be aligned in general, loaded as scalar
  assert( sse_aligned(a.pointer()) );
  assert( sse_aligned(b) );
  float4 bv(b);
  bv += float4( a.colpointer(0) ) * x[0];
  bv += float4( a.colpointer(1) ) * x[1];
  bv += float4( a.colpointer(2) ) * x[2];
  bv += float4( a.colpointer(3) ) * x[3];
  bv.store(b);
}

// manually vectorized form of b += x^t * a
template <>
inline void block_tmuladdv<float,float,float,4>(const Mtx44f &a,
                                                const float x[], float b[])
{
  // b need not be aligned in general, accessed as scalar
  assert( sse_aligned(a.pointer()) );
  assert( sse_aligned(x) );
  float4 xv(x);
  b[0] += dot( float4(a.colpointer(0)), xv );
  b[1] += dot( float4(a.colpointer(1)), xv );
  b[2] += dot( float4(a.colpointer(2)), xv );
  b[3] += dot( float4(a.colpointer(3)), xv );
}

// manually vectorized form of b += a*x
template <>
inline void block_muladdv<float,float,float,8>(const SMatrix<8,8,float> &a,
                                               const float x[], float b[])
{
  // x need not be aligned in general, loaded as scalar
  assert( sse_aligned(a.pointer()) );
  assert( sse_aligned(b) );
  float8 bv(b);
  bv += float8( a.colpointer(0) ) * x[0];
  bv += float8( a.colpointer(1) ) * x[1];
  bv += float8( a.colpointer(2) ) * x[2];
  bv += float8( a.colpointer(3) ) * x[3];
  bv += float8( a.colpointer(4) ) * x[4];
  bv += float8( a.colpointer(5) ) * x[5];
  bv += float8( a.colpointer(6) ) * x[6];
  bv += float8( a.colpointer(7) ) * x[7];
  bv.store(b);
}

// manually vectorized form of b += a*x
template <>
inline void block_muladdv<double,double,double,2>(const Mtx22 &a,
                                                  const double x[], double b[])
{
  // x need not be aligned in general, loaded as scalar
  assert( sse_aligned(a.pointer()) );
  assert( sse_aligned(b) );
  double2 bv(b);
  bv += double2( a.colpointer(0) ) * x[0];
  bv += double2( a.colpointer(1) ) * x[1];
  bv.store(b);
}

// manually vectorized form of b += a*x
template <>
inline void block_muladdv<double,double,double,4>(const Mtx44 &a,
                                                  const double x[], double b[])
{
  // x need not be aligned in general, loaded as scalar
  assert( sse_aligned(a.pointer()) );
  assert( sse_aligned(b) );
  double4 bv(b);
  bv += double4( a.colpointer(0) ) * x[0];
  bv += double4( a.colpointer(1) ) * x[1];
  bv += double4( a.colpointer(2) ) * x[2];
  bv += double4( a.colpointer(3) ) * x[3];
  bv.store(b);
}

// manually vectorized form of b += a*x
template <>
inline void block_muladdv<double,double,double,8>(const SMatrix<8,8,double> &a,
                                                  const double x[], double b[])
{
  // x need not be aligned in general, loaded as scalar
  assert( sse_aligned(a.pointer()) );
  assert( sse_aligned(b) );
  double8 bv(b);
  bv += double8( a.colpointer(0) ) * x[0];
  bv += double8( a.colpointer(1) ) * x[1];
  bv += double8( a.colpointer(2) ) * x[2];
  bv += double8( a.colpointer(3) ) * x[3];
  bv += double8( a.colpointer(4) ) * x[4];
  bv += double8( a.colpointer(5) ) * x[5];
  bv += double8( a.colpointer(6) ) * x[6];
  bv += double8( a.colpointer(7) ) * x[7];
  bv.store(b);
}

// TODO - difficult.
// manually vectorized form of b += a*x
//template <>
//inline void block_muladdv<float,float,float,4>(const Mtx44f &a,
//                                               const float x[], float b[])
//{}

// manually vectorized block update  c += a*b
template <>
inline void block_mmadd<float,4>(const Mtx44f &a, const Mtx44f &b, Mtx44f &c)
{
  float4 ac0(a.colpointer(0));
  float4 ac1(a.colpointer(1));
  float4 ac2(a.colpointer(2));
  float4 ac3(a.colpointer(3));

  float4 cc0(c.colpointer(0));
  cc0 += ac0*b(0,0) + ac1*b(1,0) + ac2*b(2,0) + ac3*b(3,0);
  cc0.store(c.colpointer(0));

  float4 cc1(c.colpointer(1));
  cc1 += ac0*b(0,1) + ac1*b(1,1) + ac2*b(2,1) + ac3*b(3,1);
  cc1.store(c.colpointer(1));

  float4 cc2(c.colpointer(2));
  cc2 += ac0*b(0,2) + ac1*b(1,2) + ac2*b(2,2) + ac3*b(3,2);
  cc2.store(c.colpointer(2));

  float4 cc3(c.colpointer(3));
  cc3 += ac0*b(0,3) + ac1*b(1,3) + ac2*b(2,3) + ac3*b(3,3);
  cc3.store(c.colpointer(3));
}

// manually vectorized block update  c += a*b
template <>
inline void block_mmadd<float,8>(const SMatrix<8,8,float> &a,
                                 const SMatrix<8,8,float> &b, SMatrix<8,8,float> &c)
{
  float8 ac0(a.colpointer(0));
  float8 ac1(a.colpointer(1));
  float8 ac2(a.colpointer(2));
  float8 ac3(a.colpointer(3));
  float8 ac4(a.colpointer(4));
  float8 ac5(a.colpointer(5));
  float8 ac6(a.colpointer(6));
  float8 ac7(a.colpointer(7));

  // let compiler decide on unrolling
  float8 cc;
  for (int i=0; i<8; ++i) {
    cc.load(c.colpointer(i));
    cc += ac0*b(0,i) + ac1*b(1,i) + ac2*b(2,i) + ac3*b(3,i) +
          ac4*b(4,i) + ac5*b(5,i) + ac6*b(6,i) + ac7*b(7,i);
    cc.store(c.colpointer(i));
  }
}

// manually vectorized block update  c += a*b
template <>
inline void block_mmadd<double,2>(const Mtx22 &a, const Mtx22 &b, Mtx22 &c)
{
  double2 ac0(a.colpointer(0));
  double2 ac1(a.colpointer(1));

  double2 cc0(c.colpointer(0));
  cc0 += ac0*b(0,0) + ac1*b(1,0);
  cc0.store(c.colpointer(0));

  double2 cc1(c.colpointer(1));
  cc1 += ac0*b(0,1) + ac1*b(1,1);
  cc1.store(c.colpointer(1));
}

// manually vectorized block update  c += a*b
template <>
inline void block_mmadd<double,4>(const Mtx44 &a, const Mtx44 &b, Mtx44 &c)
{
  double4 ac0(a.colpointer(0));
  double4 ac1(a.colpointer(1));
  double4 ac2(a.colpointer(2));
  double4 ac3(a.colpointer(3));

  double4 cc0(c.colpointer(0));
  cc0 += ac0*b(0,0) + ac1*b(1,0) + ac2*b(2,0) + ac3*b(3,0);
  cc0.store(c.colpointer(0));

  double4 cc1(c.colpointer(1));
  cc1 += ac0*b(0,1) + ac1*b(1,1) + ac2*b(2,1) + ac3*b(3,1);
  cc1.store(c.colpointer(1));

  double4 cc2(c.colpointer(2));
  cc2 += ac0*b(0,2) + ac1*b(1,2) + ac2*b(2,2) + ac3*b(3,2);
  cc2.store(c.colpointer(2));

  double4 cc3(c.colpointer(3));
  cc3 += ac0*b(0,3) + ac1*b(1,3) + ac2*b(2,3) + ac3*b(3,3);
  cc3.store(c.colpointer(3));
}

// manually vectorized block update  c += a*b
template <>
inline void block_mmsub<float,4>(const Mtx44f &a, const Mtx44f &b, Mtx44f &c)
{
  float4 ac0(a.colpointer(0));
  float4 ac1(a.colpointer(1));
  float4 ac2(a.colpointer(2));
  float4 ac3(a.colpointer(3));

  float4 cc0(c.colpointer(0));
  cc0 -= ac0*b(0,0) + ac1*b(1,0) + ac2*b(2,0) + ac3*b(3,0);
  cc0.store(c.colpointer(0));

  float4 cc1(c.colpointer(1));
  cc1 -= ac0*b(0,1) + ac1*b(1,1) + ac2*b(2,1) + ac3*b(3,1);
  cc1.store(c.colpointer(1));

  float4 cc2(c.colpointer(2));
  cc2 -= ac0*b(0,2) + ac1*b(1,2) + ac2*b(2,2) + ac3*b(3,2);
  cc2.store(c.colpointer(2));

  float4 cc3(c.colpointer(3));
  cc3 -= ac0*b(0,3) + ac1*b(1,3) + ac2*b(2,3) + ac3*b(3,3);
  cc3.store(c.colpointer(3));
}

// manually vectorized block update  c += a*b
template <>
inline void block_mmsub<float,8>(const SMatrix<8,8,float> &a,
                                 const SMatrix<8,8,float> &b, SMatrix<8,8,float> &c)
{
  float8 ac0(a.colpointer(0));
  float8 ac1(a.colpointer(1));
  float8 ac2(a.colpointer(2));
  float8 ac3(a.colpointer(3));
  float8 ac4(a.colpointer(4));
  float8 ac5(a.colpointer(5));
  float8 ac6(a.colpointer(6));
  float8 ac7(a.colpointer(7));

  // let compiler decide on unrolling
  float8 cc;
  for (int i=0; i<8; ++i) {
    cc.load(c.colpointer(i));
    cc -= ac0*b(0,i) + ac1*b(1,i) + ac2*b(2,i) + ac3*b(3,i) +
          ac4*b(4,i) + ac5*b(5,i) + ac6*b(6,i) + ac7*b(7,i);
    cc.store(c.colpointer(i));
  }
}

// manually vectorized block update  c += a*b
template <>
inline void block_mmsub<double,2>(const Mtx22 &a, const Mtx22 &b, Mtx22 &c)
{
  double2 ac0(a.colpointer(0));
  double2 ac1(a.colpointer(1));

  double2 cc0(c.colpointer(0));
  cc0 += ac0*b(0,0) + ac1*b(1,0);
  cc0.store(c.colpointer(0));

  double2 cc1(c.colpointer(1));
  cc1 -= ac0*b(0,1) + ac1*b(1,1);
  cc1.store(c.colpointer(1));
}

// manually vectorized block update  c += a*b
template <>
inline void block_mmsub<double,4>(const Mtx44 &a, const Mtx44 &b, Mtx44 &c)
{
  double4 ac0(a.colpointer(0));
  double4 ac1(a.colpointer(1));
  double4 ac2(a.colpointer(2));
  double4 ac3(a.colpointer(3));

  double4 cc0(c.colpointer(0));
  cc0 -= ac0*b(0,0) + ac1*b(1,0) + ac2*b(2,0) + ac3*b(3,0);
  cc0.store(c.colpointer(0));

  double4 cc1(c.colpointer(1));
  cc1 -= ac0*b(0,1) + ac1*b(1,1) + ac2*b(2,1) + ac3*b(3,1);
  cc1.store(c.colpointer(1));

  double4 cc2(c.colpointer(2));
  cc2 -= ac0*b(0,2) + ac1*b(1,2) + ac2*b(2,2) + ac3*b(3,2);
  cc2.store(c.colpointer(2));

  double4 cc3(c.colpointer(3));
  cc3 -= ac0*b(0,3) + ac1*b(1,3) + ac2*b(2,3) + ac3*b(3,3);
  cc3.store(c.colpointer(3));
}

// manually vectorized block update  c -= a*b
template <>
inline void block_mmsub<double,8>(const SMatrix<8,8,double> &a,
                                  const SMatrix<8,8,double> &b, SMatrix<8,8,double> &c)
{
  double8 ac0(a.colpointer(0));
  double8 ac1(a.colpointer(1));
  double8 ac2(a.colpointer(2));
  double8 ac3(a.colpointer(3));
  double8 ac4(a.colpointer(4));
  double8 ac5(a.colpointer(5));
  double8 ac6(a.colpointer(6));
  double8 ac7(a.colpointer(7));

  // let compiler decide on unrolling
  double8 cc;
  for (int i=0; i<8; ++i) {
    cc.load(c.colpointer(i));
    cc -= ac0*b(0,i) + ac1*b(1,i) + ac2*b(2,i) + ac3*b(3,i) +
          ac4*b(4,i) + ac5*b(5,i) + ac6*b(6,i) + ac7*b(7,i);
    cc.store(c.colpointer(i));
  }
}

} // namespace detail


#endif // SPARSEBLOCK_H
