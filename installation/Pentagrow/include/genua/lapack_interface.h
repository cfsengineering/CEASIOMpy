// 
// Modified for use in libgenua by David Eller <david.eller@gmx.net>
// originally from the matrix template library (MTL)
//
// Copyright 1997, 1998, 1999 University of Notre Dame.
// Authors: Andrew Lumsdaine, Jeremy G. Siek, Lie-Quan Lee
//
// This file is part of the Matrix Template Library
//
// You should have received a copy of the License Agreement for the
// Matrix Template Library along with the software;  see the
// file LICENSE.  If not, contact Office of Research, University of Notre
// Dame, Notre Dame, IN  46556.
//
// Permission to modify the code and to distribute modified code is
// granted, provided the text of this NOTICE is retained, a notice that
// the code was modified is included with the above COPYRIGHT NOTICE and
// with the COPYRIGHT NOTICE in the LICENSE file, and that the LICENSE
// file is distributed with the modified code.
//
// LICENSOR MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED.
// By way of example, but not limitation, Licensor MAKES NO
// REPRESENTATIONS OR WARRANTIES OF MERCHANTABILITY OR FITNESS FOR ANY
// PARTICULAR PURPOSE OR THAT THE USE OF THE LICENSED SOFTWARE COMPONENTS
// OR DOCUMENTATION WILL NOT INFRINGE ANY PATENTS, COPYRIGHTS, TRADEMARKS
// OR OTHER RIGHTS.
//

#ifndef LAPACK_INTERFACE_H
#define LAPACK_INTERFACE_H

#include "defines.h"

// default is to expect the F77 interface to BLAS
#if !defined(CBLAS) && !defined(F77BLAS)
#define F77BLAS 1
#endif

#if defined(CBLAS)
extern "C" {
#include <cblas.h>
}
#endif

/** C++ Declarations for Lapack routines.
  The following declarations where taken from the sources of the Matrix
  Template Library (MTL 2.1.2-15).
*/
namespace lapack
{

  typedef std::complex<double>  zcplx;
  typedef std::complex<float>   scplx;

#ifdef GENUA_LAPACK_ILP64
  typedef int64_t lpint;
#else
  typedef int lpint;
#endif

  extern "C"
  {

    void dgecon_ (const char & norm, const lpint & n, const double da[],
                  const lpint & lda, const double & danorm,
                  double & drcond, double dwork[],
                  lpint iwork2[], lpint & info);

    void sgecon_ (const char & norm, const lpint & n,
                  const float sa[], const lpint & lda,
                  const float & sanorm, float & srcond,
                  float swork[], lpint iwork2[],
                  lpint & info);

    void zgecon_ (const char & norm, const lpint & n,
                  const std::complex<double> za[], const lpint & lda,
                  const double & danorm, double & drcond,
                  std::complex<double> zwork[], double dwork2[],
                  lpint & info);

    void cgecon_ (const char& norm, const lpint& n,
                  const std::complex<float> sa[], const lpint& lda,
                  const float & danorm, float& srcond,
                  std::complex<float> cwork[],  float swork2[],
                  lpint& info);


    void dgeev_(const char& jobvl, const char& jobvr,
                const lpint& n, double da[],
                const lpint& lda, double dwr[],
                double dwi[], double dvl[],
                const lpint& ldvl, double dvr[],
                const lpint& ldvr, double dwork[],
                const lpint& ldwork, lpint& info);

    void sgeev_(const char& jobvl, const char& jobvr,
                const lpint&  n, float sa[],
                const lpint& lda, float swr[],
                float swi[], float svl[],
                const lpint& ldvl, float svr[],
                const lpint& ldvr, float swork[],
                const lpint& ldwork, lpint& info);

    void zgeev_(const char& jobvl, const char& jobvr,
                const lpint&  n, std::complex<double> za[],
                const lpint& lda, std::complex<double> zw[],
                std::complex<double> zvl[], const lpint& ldvl,
                std::complex<double> zvr[], const lpint& ldvr,
                std::complex<double> zwork[], const lpint& ldwork,
                double dwork2[], lpint& info);

    void cgeev_(const char& jobvl, const char& jobvr,
                const lpint&  n, std::complex<float> ca[],
                const lpint& lda, std::complex<float> cw[],
                std::complex<float> cvl[], const lpint& ldvl,
                std::complex<float> cvr[], const lpint& ldvr,
                std::complex<float> cwork[], const lpint& ldwork,
                float swork2[], lpint& info);

    void dgeqpf_(const lpint & m, const lpint & n,
                 double da[], const lpint & lda,
                 lpint jpivot[], double dtau[],
                 double dwork[], lpint & info);

    void sgeqpf_(const lpint & m, const lpint & n,
                 float sa[], const lpint & lda,
                 lpint jpivot[], float stau[],
                 float swork[], lpint & info);

    void zgeqpf_(const lpint & m,
                 const lpint & n,
                 std::complex<double> za[],
                 const lpint & lda,
                 lpint jpivot[],
                 std::complex<double> ztau[],
                 std::complex<double> zwork[],
                 double dwork2[],
                 lpint & info);

    void cgeqpf_(const lpint & m,
                 const lpint & n,
                 std::complex<float> ca[],
                 const lpint & lda,
                 lpint jpivot[],
                 std::complex<float> ctau[],
                 std::complex<float> cwork[],
                 float swork2[],
                 lpint& info);

    void dgeqrf_(const lpint & m,
                 const lpint & n,
                 double da[],
                 const lpint & lda,
                 double dtau[],
                 double dwork[],
                 const lpint& ldwork,
                 lpint& info);

    void sgeqrf_(const lpint & m,
                 const lpint & n,
                 float sa[],
                 const lpint & lda,
                 float stau[],
                 float swork[],
                 const lpint& ldwork,
                 lpint& info);

    void zgeqrf_(const lpint & m,
                 const lpint & n,
                 std::complex<double> za[],
                 const lpint & lda,
                 std::complex<double> ztau[],
                 std::complex<double> zwork[],
                 const lpint& ldwork,
                 lpint & info);

    void cgeqrf_(const lpint & m,
                 const lpint & n,
                 std::complex<float> ca[],
                 const lpint & lda,
                 std::complex<float> ctau[],
                 std::complex<float> cwork[],
                 const lpint& ldwork,
                 lpint & info);

    /** Solve linear system of equations.
      Double precision, simple interface.
      */
    void dgesv_(const lpint & n,
                const lpint & nrhs,
                double da[],
                const lpint & lda,
                lpint ipivot[],
                double db[],
                const lpint & ldb,
                lpint & info);

    void sgesv_(const lpint & n,
                const lpint & nrhs,
                float sa[],
                const lpint & lda,
                lpint ipivot[],
                float sb[],
                const lpint & ldb,
                lpint & info);

    void zgesv_(const lpint & n,
                const lpint & nrhs,
                std::complex<double> za[],
                const lpint & lda,
                lpint ipivot[],
                std::complex<double> zb[],
                const lpint & ldb,
                lpint & info);

    void cgesv_(const lpint & n,
                const lpint & nrhs,
                std::complex<float> ca[],
                const lpint & lda,
                lpint ipivot[],
                std::complex<float> cb[],
                const lpint & ldb,
                lpint & info);

    void dgetrf_ (const lpint& m,
                  const lpint& n,
                  double da[],
                  const lpint& lda,
                  lpint ipivot[],
                  lpint& info);

    void sgetrf_ (const lpint& m,
                  const lpint& n,
                  float sa[],
                  const lpint& lda,
                  lpint ipivot[],
                  lpint& info);

    void zgetrf_ (const lpint& m,
                  const lpint& n,
                  std::complex<double> za[],
                  const lpint& lda,
                  lpint ipivot[],
                  lpint& info);

    void cgetrf_ (const lpint& m,
                  const lpint& n,
                  std::complex<float> ca[],
                  const lpint& lda,
                  lpint ipivot[],
                  lpint& info);

    void dgetri_ (const lpint& n,
                  double a[],
                  const lpint& lda,
                  const lpint ipiv[],
                  double work[],
                  const lpint& lwork,
                  lpint& info);

    void sgetri_ (const lpint& n,
                  float a[],
                  const lpint& lda,
                  const lpint ipiv[],
                  float work[],
                  const lpint& lwork,
                  lpint& info);

    void zgetri_ (const lpint& n,
                  std::complex<double> a[],
                  const lpint& lda,
                  const lpint ipiv[],
                  std::complex<double> work[],
                  const lpint& lwork,
                  lpint& info);

    void cgetri_ (const lpint& n,
                  std::complex<float> a[],
                  const lpint& lda,
                  const lpint ipiv[],
                  std::complex<float> work[],
                  const lpint& lwork,
                  lpint& info);

    void dgetrs_ (const char& transa,
                  const lpint& n,
                  const lpint& nrhs,
                  const double da[],
                  const lpint& lda,
                  const lpint ipivot[],
                  double db[],
                  const lpint& ldb,
                  lpint& info);

    void sgetrs_ (const char& transa,
                  const lpint& n,
                  const lpint& nrhs,
                  const float  sa[],
                  const lpint& lda,
                  const lpint ipivot[],
                  float sb[],
                  const lpint& ldb,
                  lpint& info);

    void zgetrs_ (const char& transa,
                  const lpint& n,
                  const lpint& nrhs,
                  const std::complex<double> za[],
                  const lpint& lda,
                  const lpint ipivot[],
                  std::complex<double> zb[],
                  const lpint& ldb,
                  lpint& info);

    void cgetrs_ (const char& transa,
                  const lpint& n,
                  const lpint& nrhs,
                  const std::complex<float> ca[],
                  const lpint& lda,
                  const lpint ipivot[],
                  std::complex<float> cb[],
                  const lpint& ldb,
                  lpint& info);

    void dgeequ_ (const lpint& m, const lpint& n, const double da[], const lpint& lda,
                  double r[], double c[], double& rowcnd, double& colcnd,
                  double& amax, lpint& info);

    void sgeequ_ (const lpint& m, const lpint& n, const float da[], const lpint& lda,
                  float r[], float c[], float& rowcnd, float& colcnd,
                  float& amax, lpint& info);

    void cgeequ_ (const lpint& m, const lpint& n, const std::complex<float> da[],
                  const lpint& lda, std::complex<float> r[], std::complex<float> c[],
                  float& rowcnd, float& colcnd,
                  float& amax, lpint& info);

    void zgeequ_ (const lpint& m, const lpint& n, const std::complex<double> da[],
                  const lpint& lda, std::complex<double> r[], std::complex<double> c[],
                  double& rowcnd, double& colcnd,
                  double& amax, lpint& info);



    void dgelqf_ (const lpint& m, const lpint& n, double da[], const lpint& lda,
                  double dtau[], double work[], const lpint& ldwork, lpint& info);

    void sgelqf_ (const lpint& m, const lpint& n, float da[], const lpint& lda,
                  float dtau[], float work[], const lpint& ldwork, lpint& info);

    void cgelqf_ (const lpint& m, const lpint& n, std::complex<float> da[], const lpint& lda,
                  std::complex<float> dtau[], std::complex<float> work[],
                  const lpint& ldwork, lpint& info);

    void zgelqf_ (const lpint& m, const lpint& n, std::complex<double> da[], const lpint& lda,
                  std::complex<double> dtau[], std::complex<double> work[],
                  const lpint& ldwork, lpint& info);



    void dorglq_(const lpint& m, const lpint& n, const lpint& k,
                 double da[], lpint& lda, double dtau[],
                 double dwork[], const lpint& ldwork, lpint& info);

    void sorglq_(const lpint& m, const lpint& n, const lpint& k,
                 float da[], lpint& lda, float dtau[],
                 float dwork[], const lpint& ldwork, lpint& info);


    void dorgqr_(const lpint& m, const lpint& n, const lpint& k,
                 double da[], const lpint& lda, double dtau[],
                 double dwork[], const lpint& ldwork, lpint& info);

    void sorgqr_(const lpint& m, const lpint& n, const lpint& k,
                 float da[], const lpint& lda, float dtau[],
                 float dwork[], const lpint& ldwork, lpint& info);

    void dgeevx_ (const char & balanc,
                  const char & jobvl,
                  const char & jobvr,
                  const char & sense,
                  const lpint & n,
                  double da[],
                  const lpint & lda,
                  double dwr[],
                  double dwi[],
                  double dvl[],
                  const lpint & ldvl,
                  double dvr[],
                  const lpint & ldvr,
                  lpint & ilo,
                  lpint & ihi,
                  double dscale[],
                  double & dabnrm,
                  double drcone[],
                  double drconv[],
                  double dwork[],
                  const lpint & ldwork,
                  lpint iwork2[],
                  lpint & info);

    // linear least squares
    void dgels_(const char & trans, const lpint & m, const lpint & n,
                const lpint & nrhs, double A[], const lpint & lda, double b[], const lpint & ldb,
                double work[], const lpint & lwork, lpint & info);

    // linear least squares
    void sgels_(const char & trans, const lpint & m, const lpint & n,
                const lpint & nrhs, float A[], const lpint & lda, float b[], const lpint & ldb,
                float work[], const lpint & lwork, lpint & info);
    
    // linear least squares
    void zgels_(const char & trans, const lpint & m, const lpint & n,
                const lpint & nrhs, zcplx A[], const lpint & lda, zcplx b[], const lpint & ldb,
                zcplx work[], const lpint & lwork, lpint & info);

    // linear least squares
    void cgels_(const char & trans, const lpint & m, const lpint & n,
                const lpint & nrhs, scplx A[], const lpint & lda, scplx b[], const lpint & ldb,
                scplx work[], const lpint & lwork, lpint & info);
    
    // linear least squares using SVD
    void dgelsd_(const lpint & m, const lpint & n, const lpint & nrhs, double a[], const lpint & lda,
                 double b[], const lpint & ldb, double s[], const double & rcond, lpint & rank,
                 double work[], const lpint & lwork, lpint iwork[], lpint & info);
    
    // linear least squares using SVD
    void sgelsd_(const lpint & m, const lpint & n, const lpint & nrhs, float a[], const lpint & lda,
                 float b[], const lpint & ldb, float s[], const float & rcond, lpint & rank,
                 float work[], const lpint & lwork, lpint iwork[], lpint & info);
    
//     // linear least squares using SVD
//     void zgelsd_(const lpint & m, const lpint & n, const lpint & nrhs, zcplx a[], const lpint & lda,
//                  zcplx b[], const lpint & ldb, double s[], const double & rcond, lpint & rank,
//                  zcplx work[], const lpint & lwork, lpint iwork[], lpint & info);
//     
//     // linear least squares using SVD
//     void cgelsd_(const lpint & m, const lpint & n, const lpint & nrhs, scplx a[], const lpint & lda,
//                  scplx b[], const lpint & ldb, float s[], const float & rcond, lpint & rank,
//                  scplx work[], const lpint & lwork, lpint iwork[], lpint & info);
    
    // equality-constrained least squares
    void dgglse_(const lpint & m, const lpint & n, const lpint & p, double a[], const lpint & lda,
                 double b[], const lpint & ldb, double c[], double d[], double x[],
                 double work[], const lpint & lwork, lpint & info);
    
    // equality-constrained least squares
    void sgglse_(const lpint & m, const lpint & n, const lpint & p, float a[], const lpint & lda,
                 float b[], const lpint & ldb, float c[], float d[], float x[],
                 float work[], const lpint & lwork, lpint & info);

    // equality-constrained least squares
    void zgglse_(const lpint & m, const lpint & n, const lpint & p, zcplx a[], const lpint & lda,
                 zcplx b[], const lpint & ldb, zcplx c[], zcplx d[], zcplx x[],
                 zcplx work[], const lpint & lwork, lpint & info);
    
    // equality-constrained least squares
    void cgglse_(const lpint & m, const lpint & n, const lpint & p, scplx a[], const lpint & lda,
                 scplx b[], const lpint & ldb, scplx c[], scplx d[], scplx x[],
                 scplx work[], const lpint & lwork, lpint & info);
    
    // eigenvalues of symmetric matrix
    void dsyevd_(const char & jobz, const char & uplo, const lpint & n,
                 double A[], const lpint & lda, double W[], double work[], const lpint & lwork,
                 lpint iwork[], const lpint & liwork, lpint & info);

    // eigenvalues of symmetric matrix
    void ssyevd_(const char & jobz, const char & uplo, const lpint & n,
                 float A[], const lpint & lda, float W[], float work[], const lpint & lwork,
                 lpint iwork[], const lpint & liwork, lpint & info);

    // eigenvalues of symmetric matrix
    void zsyevd_(const char & jobz, const char & uplo, const lpint & n,
                 std::complex<double> A[], const lpint & lda,
                 std::complex<double> W[], std::complex<double> work[], const lpint & lwork,
                 lpint iwork[], const lpint & liwork, lpint & info);

    // eigenvalues of symmetric matrix
    void csyevd_(const char & jobz, const char & uplo, const lpint & n,
                 std::complex<float> A[], const lpint & lda,
                 std::complex<float> W[], std::complex<float> work[], const lpint & lwork,
                 lpint iwork[], const lpint & liwork, lpint & info);

    // eigenvalues of non-symmetric matrix
    void dgeevd_(const char & jobvl, const char & jobvr, const lpint & n,
                 double a[], const lpint & lda, double wr[], double wi[],
                 double vl[], const lpint & ldvl, double vr[], const lpint & ldvr,
                 double work[], const lpint & lwork, lpint & info);

    // eigenvalues of non-symmetric matrix
    void sgeevd_(const char & jobvl, const char & jobvr, const lpint & n,
                 float a[], const lpint & lda, float wr[], float wi[],
                 float vl[], const lpint & ldvl, float vr[], const lpint & ldvr,
                 float work[], const lpint & lwork, lpint & info);

    // eigenvalues of non-symmetric matrix
    void cgeevd_(const char & jobvl, const char & jobvr, const lpint & n,
                 std::complex<float> a[], const lpint & lda,
                 std::complex<float> wr[], std::complex<float> wi[],
                 std::complex<float> vl[], const lpint & ldvl,
                 std::complex<float> vr[], const lpint & ldvr,
                 std::complex<float> work[], const lpint & lwork, lpint & info);

    // eigenvalues of non-symmetric matrix
    void zgeevd_(const char & jobvl, const char & jobvr, const lpint & n,
                 std::complex<double> a[], const lpint & lda,
                 std::complex<double> wr[], std::complex<double> wi[],
                 std::complex<double> vl[], const lpint & ldvl,
                 std::complex<double> vr[], const lpint & ldvr,
                 std::complex<double> work[], const lpint & lwork, lpint & info);

    // SVD decomposition
    void dgesdd_(const char & jobz, const lpint & m, const lpint & n, double A[],
                 const lpint & lda, double S[], double U[], const lpint & ldu,
                 double VT[], const lpint & ldvt, double work[], const lpint & lwork,
                 lpint & info);

    void sgesdd_(const char & jobz, const lpint & m, const lpint & n, float A[],
                 const lpint & lda, float S[], float U[], const lpint & ldu,
                 float VT[], const lpint & ldvt, float work[], const lpint & lwork,
                 lpint & info);

    void cgesdd_(const char & jobz, const lpint & m, const lpint & n, std::complex<float> A[],
                 const lpint & lda, std::complex<float> S[], std::complex<float> U[],
                 const lpint & ldu, std::complex<float> VT[], const lpint & ldvt,
                 std::complex<float> work[], const lpint & lwork, lpint & info);

    void zgesdd_(const char & jobz, const lpint & m, const lpint & n, std::complex<double> A[],
                 const lpint & lda, std::complex<double> S[], std::complex<double> U[],
                 const lpint & ldu, std::complex<double> VT[], const lpint & ldvt,
                 std::complex<double> work[], const lpint & lwork, lpint & info);


    // compute matrix anorm
    double dlange_(const char & anorm, const lpint & m, const lpint & n,
                   const double A[], const lpint & lda, double work[]);

    float slange_(const char & anorm, const lpint & m, const lpint & n,
                  const float A[], const lpint & lda, float work[]);

    float clange_(const char & anorm, const lpint & m, const lpint & n,
                  const std::complex<float> A[], const lpint & lda,
                  float work[]);

    double zlange_(const char & anorm, const lpint & m, const lpint & n,
                   const std::complex<double> A[], const lpint & lda,
                   double work[]);

    // generalized eigenvalue problem
    void sggev_( const char & jobvl, const char & jobvr, const lpint & n,
                 std::complex<float> A[], const lpint & lda,
                 std::complex<float> B[], const lpint & ldb,
                 std::complex<float> alpha[], std::complex<float> beta[],
                 std::complex<float> vl[], const lpint & ldvl,
                 std::complex<float> vr[], const lpint & ldvr,
                 std::complex<float> work[], const lpint & lwork,
                 float rwork[], lpint & info );

    void zggev_( const char & jobvl, const char & jobvr, const lpint & n,
                 std::complex<double> A[], const lpint & lda,
                 std::complex<double> B[], const lpint & ldb,
                 std::complex<double> alpha[], std::complex<double> beta[],
                 std::complex<double> vl[], const lpint & ldvl,
                 std::complex<double> vr[], const lpint & ldvr,
                 std::complex<double> work[], const lpint & lwork,
                 double rwork[], lpint & info );

    // solve banded linear system 
    void sgbsv_(const lpint & n, const lpint & kl, const lpint & ku, const lpint & nrhs,
               float ab[], const lpint & ldab, lpint ipiv[], float b[],
               const lpint & ldb, lpint & info);
    
    void dgbsv_(const lpint & n, const lpint & kl, const lpint & ku, const lpint & nrhs,
               double ab[], const lpint & ldab, lpint ipiv[], double b[],
               const lpint & ldb, lpint & info);
    
    void cgbsv_(const lpint & n, const lpint & kl, const lpint & ku, const lpint & nrhs,
               std::complex<float> ab[], const lpint & ldab, lpint ipiv[],
               std::complex<float> b[], const lpint & ldb, lpint & info);
    
    void zgbsv_(const lpint & n, const lpint & kl, const lpint & ku, const lpint & nrhs,
               std::complex<double> ab[], const lpint & ldab, lpint ipiv[],
               std::complex<double> b[], const lpint & ldb, lpint & info);
    
    // solve symmetric positive definite linear system
    void sposv_(const char & uplo, const lpint & n, const lpint & nrhs,
                float a[], const lpint & lda, float b[], const lpint & ldb,
                lpint & info);

    void dposv_(const char & uplo, const lpint & n, const lpint & nrhs,
                double a[], const lpint & lda, double b[], const lpint & ldb,
                lpint & info);

    // schur decomposition

    void dhseqr_(const char &job, const char &compz, const lpint &n,
                 const lpint &ilo, const lpint &ihi, double h[], const lpint &ldh,
                 double wr[], double wi[], double z[], const lpint &ldz,
                 double work[], const lpint &lwork, lpint &info);

    void dgehd2_(const lpint &n, const lpint &ilo, const lpint &ihi, double a[],
                 const lpint &lda, double tau[], double work[], lpint &info);

    void dorghr_(const lpint &n, const lpint &ilo, const lpint &ihi, double a[],
                 const lpint &lda, double tau[], double work[],
                 const lpint &lwork, lpint &info);

    void dgebal_(const char &job, const lpint &n, double a[], const lpint &lda,
                 lpint &ilo, lpint &ihi, double scale[], lpint &info);

    void shseqr_(const char &job, const char &compz, const lpint &n,
                 const lpint &ilo, const lpint &ihi, float h[], const lpint &ldh,
                 float wr[], float wi[], float z[], const lpint &ldz,
                 float work[], const lpint &lwork, lpint &info);

    void sgehd2_(const lpint &n, const lpint &ilo, const lpint &ihi, float a[],
                 const lpint &lda, float tau[], float work[], lpint &info);

    void sorghr_(const lpint &n, const lpint &ilo, const lpint &ihi, float a[],
                 const lpint &lda, float tau[], float work[],
                 const lpint &lwork, lpint &info);

    void sgebal_(const char &job, const lpint &n, float a[], const lpint &lda,
                 lpint &ilo, lpint &ihi, float scale[], lpint &info);

    
    /* Fortran interface to BLAS routines. Since the C++ code is written 
     * against the F77 interface below, the cblas versions must be wrapped 
     * in case the F77BLAS is not available.
     */

#ifdef F77BLAS

    // vector scaling
    void dscal_(const lpint & n, const double & da, double dx[], const lpint & incx);

    // vector scaling
    void sscal_(const lpint & n, const float & da, float dx[], const lpint & incx);

    // vector scaling
    void cscal_(const lpint & n, const std::complex<float> & da,
                std::complex<float> dx[], const lpint & incx);

    // vector scaling
    void zscal_(const lpint & n, const std::complex<double> & da,
                std::complex<double> dx[], const lpint & incx);

    // y = a*x + y
    void daxpy_(const lpint & n, const double & alpha, const double x[],
                const lpint & incX, double y[], const lpint & incY);

    // y = a*x + y
    void saxpy_(const lpint & n, const float & alpha, const float x[],
                const lpint & incX, float y[], const lpint & incY);

    // y = a*x + y
    void caxpy_(const lpint & n, const std::complex<float> & alpha, const std::complex<float> x[],
                const lpint & incX, std::complex<float> y[], const lpint & incY);

    // y = a*x + y
    void zaxpy_(const lpint & n, const std::complex<double> & alpha, const std::complex<double> x[],
                const lpint & incX, std::complex<double> y[], const lpint & incY);

    // Matrix multiply, double precision.
    void dgemm_(const char & ta, const char & tb,
                const lpint & cols, const lpint & rows, const lpint & mids,
                const double & alfa, const double B[], const lpint & ldb,
                const double A[], const lpint & lda, const double & beta,
                double C[], const lpint & ldc);

    // Matrix multiply, double precision.
    void sgemm_(const char & ta, const char & tb,
                const lpint & cols, const lpint & rows, const lpint & mids,
                const float & alfa, const float B[], const lpint & ldb,
                const float A[], const lpint & lda, const float & beta,
                float C[], const lpint & ldc);

    // Matrix multiply, std::complex<float> precision.
    void cgemm_(const char & ta, const char & tb,
                const lpint & cols, const lpint & rows, const lpint & mids,
                const std::complex<float> & alfa, const std::complex<float> B[], const lpint & ldb,
                const std::complex<float> A[], const lpint & lda, const std::complex<float> & beta,
                std::complex<float> C[], const lpint & ldc);

    // Matrix multiply, double precision.
    void zgemm_(const char & ta, const char & tb,
                const lpint & cols, const lpint & rows, const lpint & mids,
                const std::complex<double> & alfa, const std::complex<double> B[], const lpint & ldb,
                const std::complex<double> A[], const lpint & lda, const std::complex<double> & beta,
                std::complex<double> C[], const lpint & ldc);

    // matrix-vector multiply
    void dgemv_(const char & trans, const lpint & m, const lpint & n,
                const double & alpha, const double A[], const lpint & lda,
                const double X[], const lpint & incx, const double & beta,
                double Y[], const lpint & incy);

    // matrix-vector multiply
    void sgemv_(const char & trans, const lpint & m, const lpint & n,
                const float & alpha, const float A[], const lpint & lda,
                const float X[], const lpint & incx, const float & beta,
                float Y[], const lpint & incy);

    // matrix-vector multiply
    void cgemv_(const char & trans, const lpint & m, const lpint & n,
                const std::complex<float> & alpha, const std::complex<float> A[],
                const lpint & lda, const std::complex<float> X[], const lpint & incx,
                const std::complex<float> & beta,
                std::complex<float> Y[], const lpint & incy);

    // matrix-vector multiply
    void zgemv_(const char & trans, const lpint & m, const lpint & n,
                const std::complex<double> & alpha, const std::complex<double> A[],
                const lpint & lda, const std::complex<double> X[], const lpint & incx,
                const std::complex<double> & beta,
                std::complex<double> Y[], const lpint & incy);

#else  // use CBLAS interfaces to ATLAS or vanilla cblas

#define CVT_TRANSPOSE(c) \
   (((c) == 'N' || (c) == 'n') ? CblasNoTrans : \
    ((c) == 'T' || (c) == 't') ? CblasTrans : \
    ((c) == 'C' || (c) == 'c') ? CblasConjTrans : \
    -1)

#define CVT_UPLO(c) \
   (((c) == 'U' || (c) == 'u') ? CblasUpper : \
    ((c) == 'L' || (c) == 'l') ? CblasLower : \
    -1)

#define CVT_DIAG(c) \
   (((c) == 'U' || (c) == 'u') ? CblasUnit : \
    ((c) == 'N' || (c) == 'n') ? CblasNonUnit : \
    -1)

#define CVT_SIDE(c) \
   (((c) == 'L' || (c) == 'l') ? CblasLeft : \
    ((c) == 'R' || (c) == 'r') ? CblasRight : \
    -1)

     // vector scaling
    inline void dscal_(const lpint & n, const double & da, double dx[], const lpint & incx) {
      cblas_dscal(n, da, dx, incx);
    }

    // vector scaling
    inline void sscal_(const lpint & n, const float & da, float dx[], const lpint & incx) {
      cblas_sscal(n, da, dx, incx);
    }

    // vector scaling
    inline void cscal_( const lpint & n, const std::complex<float> & da,
                        std::complex<float> dx[], const lpint & incx)
    {
      cblas_cscal(n, (void*) &da, (void *) dx, incx);
    }

    // vector scaling
    inline void zscal_(const lpint & n, const std::complex<double> & da,
                std::complex<double> dx[], const lpint & incx)
    {
      cblas_zscal(n, (void*) &da, (void *) dx, incx);
    }

     // y = a*x + y
    inline void daxpy_(const lpint & n, const double & alpha, const double x[],
                const lpint & incX, double y[], const lpint & incY)
    {
      cblas_daxpy(n, alpha, x, incX, y, incY);
    }

    // y = a*x + y
    inline void saxpy_(const lpint & n, const float & alpha, const float x[],
                const lpint & incX, float y[], const lpint & incY)
    {
      cblas_saxpy(n, alpha, x, incX, y, incY);
    }

    // y = a*x + y
    inline void caxpy_(const lpint & n, const std::complex<float> & alpha, const std::complex<float> x[],
                       const lpint & incX, std::complex<float> y[], const lpint & incY)
    {
      cblas_caxpy(n, (void *) &alpha, (void *) x, incX, (void *) y, incY);
    }

    // y = a*x + y
    inline void zaxpy_(const lpint & n, const std::complex<double> & alpha, const std::complex<double> x[],
                       const lpint & incX, std::complex<double> y[], const lpint & incY)
    {
      cblas_zaxpy(n, (void *) &alpha, (void *) x, incX, (void *) y, incY);
    }

    // Matrix multiply, double precision.
    inline void dgemm_(const char & ta, const char & tb,
                       const lpint & cols, const lpint & rows, const lpint & mids,
                       const double & alfa, const double B[], const lpint & ldb,
                       const double A[], const lpint & lda, const double & beta,
                       double C[], const lpint & ldc) {
      cblas_dgemm(CblasColMajor, CVT_TRANSPOSE(ta), CVT_TRANSPOSE(tb), cols, rows,
                  mids, alfa, B, ldb, A, lda, beta, C, ldc );
    }

    // Matrix multiply, double precision.
    inline void sgemm_(const char & ta, const char & tb,
                       const lpint & cols, const lpint & rows, const lpint & mids,
                       const float & alfa, const float B[], const lpint & ldb,
                       const float A[], const lpint & lda, const float & beta,
                       float C[], const lpint & ldc) {
      cblas_sgemm(CblasColMajor, CVT_TRANSPOSE(ta), CVT_TRANSPOSE(tb), cols, rows,
                  mids, alfa, B, ldb, A, lda, beta, C, ldc );
    }

    // Matrix multiply, std::complex<float> precision.
    inline void cgemm_(const char & ta, const char & tb,
                       const lpint & cols, const lpint & rows, const lpint & mids,
                       const std::complex<float> & alfa, const std::complex<float> B[], const lpint & ldb,
                       const std::complex<float> A[], const lpint & lda, const std::complex<float> & beta,
                       std::complex<float> C[], const lpint & ldc) {
      cblas_cgemm(CblasColMajor, CVT_TRANSPOSE(ta), CVT_TRANSPOSE(tb), cols, rows,
                  mids, (const void*) (&alfa), (const void*) B, ldb, (const void *) A, lda,
                  (const void *) beta, (void*) C, ldc );
    }

    // Matrix multiply, complex double precision.
    inline void zgemm_(const char & ta, const char & tb,
                       const lpint & cols, const lpint & rows, const lpint & mids,
                       const std::complex<double> & alfa, const std::complex<double> B[], const lpint & ldb,
                       const std::complex<double> A[], const lpint & lda, const std::complex<double> & beta,
                       std::complex<double> C[], const lpint & ldc) {
      cblas_zgemm(CblasColMajor, CVT_TRANSPOSE(ta), CVT_TRANSPOSE(tb), cols, rows,
                  mids, (const void*) (&alfa), (const void*) B, ldb, (const void *) A, lda,
                  (const void *) beta, (void*) C, ldc );
    }
    
    // matrix-vector multiply
    inline void dgemv_(const char & trans, const lpint & m, const lpint & n,
                const double & alpha, const double A[], const lpint & lda,
                const double X[], const lpint & incx, const double & beta,
                double Y[], const lpint & incy)
    {
      cblas_dgemv(CblasColMajor, CVT_TRANSPOSE(trans), m, n, alpha, A, lda, X, incx, beta, Y, incy);
    }

    // matrix-vector multiply
    inline void sgemv_(const char & trans, const lpint & m, const lpint & n,
                const float & alpha, const float A[], const lpint & lda,
                const float X[], const lpint & incx, const float & beta,
                float Y[], const lpint & incy)
    {
      cblas_sgemv(CblasColMajor, CVT_TRANSPOSE(trans), m, n, alpha, A, lda, X, incx, beta, Y, incy);
    }

    // matrix-vector multiply
    inline void cgemv_(const char & trans, const lpint & m, const lpint & n,
                const std::complex<float> & alpha, const std::complex<float> A[],
                const lpint & lda, const std::complex<float> X[], const lpint & incx,
                const std::complex<float> & beta,
                std::complex<float> Y[], const lpint & incy);
    {
      cblas_sgemv(CblasColMajor, CVT_TRANSPOSE(trans), m, n,
                  (const void *) &alpha, (const void*) A, lda,
                  (const void*) X, incx, (const void*) beta, (void*) Y, incy);
    }

    // matrix-vector multiply
    inline void zgemv_(const char & trans, const lpint & m, const lpint & n,
                const std::complex<double> & alpha, const std::complex<double> A[],
                const lpint & lda, const std::complex<double> X[], const lpint & incx,
                const std::complex<double> & beta,
                std::complex<double> Y[], const lpint & incy);
    {
      cblas_zgemv(CblasColMajor, CVT_TRANSPOSE(trans), m, n,
                  (const void *) &alpha, (const void*) A, lda,
                  (const void*) X, incx, (const void*) beta, (void*) Y, incy);
    }

#endif

  } // extern C

  // manually written overload functions for matrix norms
  inline double lange(const char & anorm, const lpint & m, const lpint & n,
                      const double A[], const lpint & lda)
  {
    if (anorm == 'M' or anorm == 'm') {
      double *work = new double[m];
      double nm = dlange_(anorm, m, n, A, lda, work);
      delete [] work;
      return nm;
    } else
      return lapack::dlange_(anorm, m, n, A, lda, 0);
  }

  inline float lange(const char & anorm, const lpint & m, const lpint & n,
                     const float A[], const lpint & lda)
  {
    if (anorm == 'M' or anorm == 'm') {
      float *work = new float[m];
      float nm = slange_(anorm, m, n, A, lda, work);
      delete [] work;
      return nm;
    } else
      return lapack::slange_(anorm, m, n, A, lda, 0);
  }

  inline float lange(const char & anorm, const lpint & m, const lpint & n,
                     const std::complex<float> A[], const lpint & lda)
  {
    if (anorm == 'M' or anorm == 'm') {
      float *work = new float[m];
      float nm = clange_(anorm, m, n, A, lda, work);
      delete [] work;
      return nm;
    } else
      return lapack::clange_(anorm, m, n, A, lda, 0);
  }


  inline double lange(const char & anorm, const lpint & m, const lpint & n,
                      const std::complex<double> A[], const lpint & lda)
  {
    if (anorm == 'M' or anorm == 'm') {
      double *work = new double[m];
      double nm = zlange_(anorm, m, n, A, lda, work);
      delete [] work;
      return nm;
    } else
      return lapack::zlange_(anorm, m, n, A, lda, 0);
  }

#include "lapack_overload.h"

} // end namespace lapack

#endif
