
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
 
// automatically generated overloaded functions for the lapack interface
// do not edit: use the script genua/tools/lapacktrans.py to regenerate
// (c) 2004 by David Eller david.eller@gmx.net 

inline void gecon(const char & norm, const lpint & n, const double da[], const lpint & lda, const double & danorm, double & drcond, double dwork[], lpint iwork2[], lpint & info)
  {dgecon_(norm, n, da, lda, danorm, drcond, dwork, iwork2, info);}

inline void gecon(const char & norm, const lpint & n, const float sa[], const lpint & lda, const float & sanorm, float & srcond, float swork[], lpint iwork2[], lpint & info)
  {sgecon_(norm, n, sa, lda, sanorm, srcond, swork, iwork2, info);}

inline void gecon(const char & norm, const lpint & n, const std::complex<double> za[], const lpint & lda, const double & danorm, double & drcond, std::complex<double> zwork[], double dwork2[], lpint & info)
  {zgecon_(norm, n, za, lda, danorm, drcond, zwork, dwork2, info);}

inline void gecon(const char& norm, const lpint& n, const std::complex<float> sa[], const lpint& lda, const float & danorm, float& srcond, std::complex<float> cwork[], float swork2[], lpint& info)
  {cgecon_(norm, n, sa, lda, danorm, srcond, cwork, swork2, info);}

inline void geev(const char& jobvl, const char& jobvr, const lpint& n, double da[], const lpint& lda, double dwr[], double dwi[], double dvl[], const lpint& ldvl, double dvr[], const lpint& ldvr, double dwork[], const lpint& ldwork, lpint& info)
  {dgeev_(jobvl, jobvr, n, da, lda, dwr, dwi, dvl, ldvl, dvr, ldvr, dwork, ldwork, info);}

inline void geev(const char& jobvl, const char& jobvr, const lpint&  n, float sa[], const lpint& lda, float swr[], float swi[], float svl[], const lpint& ldvl, float svr[], const lpint& ldvr, float swork[], const lpint& ldwork, lpint& info)
  {sgeev_(jobvl, jobvr, n, sa, lda, swr, swi, svl, ldvl, svr, ldvr, swork, ldwork, info);}

inline void geev(const char& jobvl, const char& jobvr, const lpint&  n, std::complex<double> za[], const lpint& lda, std::complex<double> zw[], std::complex<double> zvl[], const lpint& ldvl, std::complex<double> zvr[], const lpint& ldvr, std::complex<double> zwork[], const lpint& ldwork, double dwork2[], lpint& info)
  {zgeev_(jobvl, jobvr, n, za, lda, zw, zvl, ldvl, zvr, ldvr, zwork, ldwork, dwork2, info);}

inline void geev(const char& jobvl, const char& jobvr, const lpint&  n, std::complex<float> ca[], const lpint& lda, std::complex<float> cw[], std::complex<float> cvl[], const lpint& ldvl, std::complex<float> cvr[], const lpint& ldvr, std::complex<float> cwork[], const lpint& ldwork, float swork2[], lpint& info)
  {cgeev_(jobvl, jobvr, n, ca, lda, cw, cvl, ldvl, cvr, ldvr, cwork, ldwork, swork2, info);}

inline void geqpf(const lpint & m, const lpint & n, double da[], const lpint & lda, lpint jpivot[], double dtau[], double dwork[], lpint & info)
  {dgeqpf_(m, n, da, lda, jpivot, dtau, dwork, info);}

inline void geqpf(const lpint & m, const lpint & n, float sa[], const lpint & lda, lpint jpivot[], float stau[], float swork[], lpint & info)
  {sgeqpf_(m, n, sa, lda, jpivot, stau, swork, info);}

inline void geqpf(const lpint & m, const lpint & n, std::complex<double> za[], const lpint & lda, lpint jpivot[], std::complex<double> ztau[], std::complex<double> zwork[], double dwork2[], lpint & info)
  {zgeqpf_(m, n, za, lda, jpivot, ztau, zwork, dwork2, info);}

inline void geqpf(const lpint & m, const lpint & n, std::complex<float> ca[], const lpint & lda, lpint jpivot[], std::complex<float> ctau[], std::complex<float> cwork[], float swork2[], lpint& info)
  {cgeqpf_(m, n, ca, lda, jpivot, ctau, cwork, swork2, info);}

inline void geqrf(const lpint & m, const lpint & n, double da[], const lpint & lda, double dtau[], double dwork[], const lpint& ldwork, lpint& info)
  {dgeqrf_(m, n, da, lda, dtau, dwork, ldwork, info);}

inline void geqrf(const lpint & m, const lpint & n, float sa[], const lpint & lda, float stau[], float swork[], const lpint& ldwork, lpint& info)
  {sgeqrf_(m, n, sa, lda, stau, swork, ldwork, info);}

inline void geqrf(const lpint & m, const lpint & n, std::complex<double> za[], const lpint & lda, std::complex<double> ztau[], std::complex<double> zwork[], const lpint& ldwork, lpint & info)
  {zgeqrf_(m, n, za, lda, ztau, zwork, ldwork, info);}

inline void geqrf(const lpint & m, const lpint & n, std::complex<float> ca[], const lpint & lda, std::complex<float> ctau[], std::complex<float> cwork[], const lpint& ldwork, lpint & info)
  {cgeqrf_(m, n, ca, lda, ctau, cwork, ldwork, info);}

inline void gesv(const lpint & n, const lpint & nrhs, double da[], const lpint & lda, lpint ipivot[], double db[], const lpint & ldb, lpint & info)
  {dgesv_(n, nrhs, da, lda, ipivot, db, ldb, info);}

inline void gesv(const lpint & n, const lpint & nrhs, float sa[], const lpint & lda, lpint ipivot[], float sb[], const lpint & ldb, lpint & info)
  {sgesv_(n, nrhs, sa, lda, ipivot, sb, ldb, info);}

inline void gesv(const lpint & n, const lpint & nrhs, std::complex<double> za[], const lpint & lda, lpint ipivot[], std::complex<double> zb[], const lpint & ldb, lpint & info)
  {zgesv_(n, nrhs, za, lda, ipivot, zb, ldb, info);}

inline void gesv(const lpint & n, const lpint & nrhs, std::complex<float> ca[], const lpint & lda, lpint ipivot[], std::complex<float> cb[], const lpint & ldb, lpint & info)
  {cgesv_(n, nrhs, ca, lda, ipivot, cb, ldb, info);}

inline void getrf(const lpint& m, const lpint& n, double da[], const lpint& lda, lpint ipivot[], lpint& info)
  {dgetrf_(m, n, da, lda, ipivot, info);}

inline void getrf(const lpint& m, const lpint& n, float sa[], const lpint& lda, lpint ipivot[], lpint& info)
  {sgetrf_(m, n, sa, lda, ipivot, info);}

inline void getrf(const lpint& m, const lpint& n, std::complex<double> za[], const lpint& lda, lpint ipivot[], lpint& info)
  {zgetrf_(m, n, za, lda, ipivot, info);}

inline void getrf(const lpint& m, const lpint& n, std::complex<float> ca[], const lpint& lda, lpint ipivot[], lpint& info)
  {cgetrf_(m, n, ca, lda, ipivot, info);}

inline void getri(const lpint& n, double a[], const lpint& lda, const lpint ipiv[], double work[], const lpint& lwork, lpint& info)
  {dgetri_(n, a, lda, ipiv, work, lwork, info);}

inline void getri(const lpint& n, float a[], const lpint& lda, const lpint ipiv[], float work[], const lpint& lwork, lpint& info)
  {sgetri_(n, a, lda, ipiv, work, lwork, info);}

inline void getri(const lpint& n, std::complex<double> a[], const lpint& lda, const lpint ipiv[], std::complex<double> work[], const lpint& lwork, lpint& info)
  {zgetri_(n, a, lda, ipiv, work, lwork, info);}

inline void getri(const lpint& n, std::complex<float> a[], const lpint& lda, const lpint ipiv[], std::complex<float> work[], const lpint& lwork, lpint& info)
  {cgetri_(n, a, lda, ipiv, work, lwork, info);}

inline void getrs(const char& transa, const lpint& n, const lpint& nrhs, const double da[], const lpint& lda, const lpint ipivot[], double db[], const lpint& ldb, lpint& info)
  {dgetrs_(transa, n, nrhs, da, lda, ipivot, db, ldb, info);}

inline void getrs(const char& transa, const lpint& n, const lpint& nrhs, const float  sa[], const lpint& lda, const lpint ipivot[], float sb[], const lpint& ldb, lpint& info)
  {sgetrs_(transa, n, nrhs, sa, lda, ipivot, sb, ldb, info);}

inline void getrs(const char& transa, const lpint& n, const lpint& nrhs, const std::complex<double> za[], const lpint& lda, const lpint ipivot[], std::complex<double> zb[], const lpint& ldb, lpint& info)
  {zgetrs_(transa, n, nrhs, za, lda, ipivot, zb, ldb, info);}

inline void getrs(const char& transa, const lpint& n, const lpint& nrhs, const std::complex<float> ca[], const lpint& lda, const lpint ipivot[], std::complex<float> cb[], const lpint& ldb, lpint& info)
  {cgetrs_(transa, n, nrhs, ca, lda, ipivot, cb, ldb, info);}

inline void geequ(const lpint& m, const lpint& n, const double da[], const lpint& lda, double r[], double c[], double& rowcnd, double& colcnd, double& amax, lpint& info)
  {dgeequ_(m, n, da, lda, r, c, rowcnd, colcnd, amax, info);}

inline void geequ(const lpint& m, const lpint& n, const float da[], const lpint& lda, float r[], float c[], float& rowcnd, float& colcnd, float& amax, lpint& info)
  {sgeequ_(m, n, da, lda, r, c, rowcnd, colcnd, amax, info);}

inline void geequ(const lpint& m, const lpint& n, const std::complex<float> da[], const lpint& lda, std::complex<float> r[], std::complex<float> c[], float& rowcnd, float& colcnd, float& amax, lpint& info)
  {cgeequ_(m, n, da, lda, r, c, rowcnd, colcnd, amax, info);}

inline void geequ(const lpint& m, const lpint& n, const std::complex<double> da[], const lpint& lda, std::complex<double> r[], std::complex<double> c[], double& rowcnd, double& colcnd, double& amax, lpint& info)
  {zgeequ_(m, n, da, lda, r, c, rowcnd, colcnd, amax, info);}

inline void gelqf(const lpint& m, const lpint& n, double da[], const lpint& lda, double dtau[], double work[], const lpint& ldwork, lpint& info)
  {dgelqf_(m, n, da, lda, dtau, work, ldwork, info);}

inline void gelqf(const lpint& m, const lpint& n, float da[], const lpint& lda, float dtau[], float work[], const lpint& ldwork, lpint& info)
  {sgelqf_(m, n, da, lda, dtau, work, ldwork, info);}

inline void gelqf(const lpint& m, const lpint& n, std::complex<float> da[], const lpint& lda, std::complex<float> dtau[], std::complex<float> work[], const lpint& ldwork, lpint& info)
  {cgelqf_(m, n, da, lda, dtau, work, ldwork, info);}

inline void gelqf(const lpint& m, const lpint& n, std::complex<double> da[], const lpint& lda, std::complex<double> dtau[], std::complex<double> work[], const lpint& ldwork, lpint& info)
  {zgelqf_(m, n, da, lda, dtau, work, ldwork, info);}

inline void orglq(const lpint& m, const lpint& n, const lpint& k, double da[], lpint& lda, double dtau[], double dwork[], const lpint& ldwork, lpint& info)
  {dorglq_(m, n, k, da, lda, dtau, dwork, ldwork, info);}

inline void orglq(const lpint& m, const lpint& n, const lpint& k, float da[], lpint& lda, float dtau[], float dwork[], const lpint& ldwork, lpint& info)
  {sorglq_(m, n, k, da, lda, dtau, dwork, ldwork, info);}

inline void orgqr(const lpint& m, const lpint& n, const lpint& k, double da[], const lpint& lda, double dtau[], double dwork[], const lpint& ldwork, lpint& info)
  {dorgqr_(m, n, k, da, lda, dtau, dwork, ldwork, info);}

inline void orgqr(const lpint& m, const lpint& n, const lpint& k, float da[], const lpint& lda, float dtau[], float dwork[], const lpint& ldwork, lpint& info)
  {sorgqr_(m, n, k, da, lda, dtau, dwork, ldwork, info);}

inline void geevx(const char & balanc, const char & jobvl, const char & jobvr, const char & sense, const lpint & n, double da[], const lpint & lda, double dwr[], double dwi[], double dvl[], const lpint & ldvl, double dvr[], const lpint & ldvr, lpint & ilo, lpint & ihi, double dscale[], double & dabnrm, double drcone[], double drconv[], double dwork[], const lpint & ldwork, lpint iwork2[], lpint & info)
  {dgeevx_(balanc, jobvl, jobvr, sense, n, da, lda, dwr, dwi, dvl, ldvl, dvr, ldvr, ilo, ihi, dscale, dabnrm, drcone, drconv, dwork, ldwork, iwork2, info);}

inline void gels(const char & trans, const lpint & m, const lpint & n, const lpint & nrhs, double A[], const lpint & lda, double b[], const lpint & ldb, double work[], const lpint & lwork, lpint & info)
  {dgels_(trans, m, n, nrhs, A, lda, b, ldb, work, lwork, info);}

inline void gels(const char & trans, const lpint & m, const lpint & n, const lpint & nrhs, float A[], const lpint & lda, float b[], const lpint & ldb, float work[], const lpint & lwork, lpint & info)
  {sgels_(trans, m, n, nrhs, A, lda, b, ldb, work, lwork, info);}

inline void gels(const char & trans, const lpint & m, const lpint & n, const lpint & nrhs, zcplx A[], const lpint & lda, zcplx b[], const lpint & ldb, zcplx work[], const lpint & lwork, lpint & info)
  {zgels_(trans, m, n, nrhs, A, lda, b, ldb, work, lwork, info);}

inline void gels(const char & trans, const lpint & m, const lpint & n, const lpint & nrhs, scplx A[], const lpint & lda, scplx b[], const lpint & ldb, scplx work[], const lpint & lwork, lpint & info)
  {cgels_(trans, m, n, nrhs, A, lda, b, ldb, work, lwork, info);}

inline void gelsd(const lpint & m, const lpint & n, const lpint & nrhs, double a[], const lpint & lda, double b[], const lpint & ldb, double s[], const double & rcond, lpint & rank, double work[], const lpint & lwork, lpint iwork[], lpint & info)
  {dgelsd_(m, n, nrhs, a, lda, b, ldb, s, rcond, rank, work, lwork, iwork, info);}

inline void gelsd(const lpint & m, const lpint & n, const lpint & nrhs, float a[], const lpint & lda, float b[], const lpint & ldb, float s[], const float & rcond, lpint & rank, float work[], const lpint & lwork, lpint iwork[], lpint & info)
  {sgelsd_(m, n, nrhs, a, lda, b, ldb, s, rcond, rank, work, lwork, iwork, info);}

inline void gglse(const lpint & m, const lpint & n, const lpint & p, double a[], const lpint & lda, double b[], const lpint & ldb, double c[], double d[], double x[], double work[], const lpint & lwork, lpint & info)
  {dgglse_(m, n, p, a, lda, b, ldb, c, d, x, work, lwork, info);}

inline void gglse(const lpint & m, const lpint & n, const lpint & p, float a[], const lpint & lda, float b[], const lpint & ldb, float c[], float d[], float x[], float work[], const lpint & lwork, lpint & info)
  {sgglse_(m, n, p, a, lda, b, ldb, c, d, x, work, lwork, info);}

inline void gglse(const lpint & m, const lpint & n, const lpint & p, zcplx a[], const lpint & lda, zcplx b[], const lpint & ldb, zcplx c[], zcplx d[], zcplx x[], zcplx work[], const lpint & lwork, lpint & info)
{zgglse_(m, n, p, a, lda, b, ldb, c, d, x, work, lwork, info);}

inline void gglse(const lpint & m, const lpint & n, const lpint & p, scplx a[], const lpint & lda, scplx b[], const lpint & ldb, scplx c[], scplx d[], scplx x[], scplx work[], const lpint & lwork, lpint & info)
{cgglse_(m, n, p, a, lda, b, ldb, c, d, x, work, lwork, info);}

inline void syevd(const char & jobz, const char & uplo, const lpint & n, double A[], const lpint & lda, double W[], double work[], const lpint & lwork, lpint iwork[], const lpint & liwork, lpint & info)
  {dsyevd_(jobz, uplo, n, A, lda, W, work, lwork, iwork, liwork, info);}

inline void syevd(const char & jobz, const char & uplo, const lpint & n, float A[], const lpint & lda, float W[], float work[], const lpint & lwork, lpint iwork[], const lpint & liwork, lpint & info)
  {ssyevd_(jobz, uplo, n, A, lda, W, work, lwork, iwork, liwork, info);}

inline void syevd(const char & jobz, const char & uplo, const lpint & n, std::complex<double> A[], const lpint & lda, std::complex<double> W[], std::complex<double> work[], const lpint & lwork, lpint iwork[], const lpint & liwork, lpint & info)
  {zsyevd_(jobz, uplo, n, A, lda, W, work, lwork, iwork, liwork, info);}

inline void syevd(const char & jobz, const char & uplo, const lpint & n, std::complex<float> A[], const lpint & lda, std::complex<float> W[], std::complex<float> work[], const lpint & lwork, lpint iwork[], const lpint & liwork, lpint & info)
  {csyevd_(jobz, uplo, n, A, lda, W, work, lwork, iwork, liwork, info);}

inline void geevd(const char & jobvl, const char & jobvr, const lpint & n, double a[], const lpint & lda, double wr[], double wi[], double vl[], const lpint & ldvl, double vr[], const lpint & ldvr, double work[], const lpint & lwork, lpint & info)
  {dgeevd_(jobvl, jobvr, n, a, lda, wr, wi, vl, ldvl, vr, ldvr, work, lwork, info);}

inline void geevd(const char & jobvl, const char & jobvr, const lpint & n, float a[], const lpint & lda, float wr[], float wi[], float vl[], const lpint & ldvl, float vr[], const lpint & ldvr, float work[], const lpint & lwork, lpint & info)
  {sgeevd_(jobvl, jobvr, n, a, lda, wr, wi, vl, ldvl, vr, ldvr, work, lwork, info);}

inline void geevd(const char & jobvl, const char & jobvr, const lpint & n, std::complex<float> a[], const lpint & lda, std::complex<float> wr[], std::complex<float> wi[], std::complex<float> vl[], const lpint & ldvl, std::complex<float> vr[], const lpint & ldvr, std::complex<float> work[], const lpint & lwork, lpint & info)
  {cgeevd_(jobvl, jobvr, n, a, lda, wr, wi, vl, ldvl, vr, ldvr, work, lwork, info);}

inline void geevd(const char & jobvl, const char & jobvr, const lpint & n, std::complex<double> a[], const lpint & lda, std::complex<double> wr[], std::complex<double> wi[], std::complex<double> vl[], const lpint & ldvl, std::complex<double> vr[], const lpint & ldvr, std::complex<double> work[], const lpint & lwork, lpint & info)
  {zgeevd_(jobvl, jobvr, n, a, lda, wr, wi, vl, ldvl, vr, ldvr, work, lwork, info);}

inline void gesdd(const char & jobz, const lpint & m, const lpint & n, double A[], const lpint & lda, double S[], double U[], const lpint & ldu, double VT[], const lpint & ldvt, double work[], const lpint & lwork, lpint & info)
  {dgesdd_(jobz, m, n, A, lda, S, U, ldu, VT, ldvt, work, lwork, info);}

inline void gesdd(const char & jobz, const lpint & m, const lpint & n, float A[], const lpint & lda, float S[], float U[], const lpint & ldu, float VT[], const lpint & ldvt, float work[], const lpint & lwork, lpint & info)
  {sgesdd_(jobz, m, n, A, lda, S, U, ldu, VT, ldvt, work, lwork, info);}

inline void gesdd(const char & jobz, const lpint & m, const lpint & n, std::complex<float> A[], const lpint & lda, std::complex<float> S[], std::complex<float> U[], const lpint & ldu, std::complex<float> VT[], const lpint & ldvt, std::complex<float> work[], const lpint & lwork, lpint & info)
  {cgesdd_(jobz, m, n, A, lda, S, U, ldu, VT, ldvt, work, lwork, info);}

inline void gesdd(const char & jobz, const lpint & m, const lpint & n, std::complex<double> A[], const lpint & lda, std::complex<double> S[], std::complex<double> U[], const lpint & ldu, std::complex<double> VT[], const lpint & ldvt, std::complex<double> work[], const lpint & lwork, lpint & info)
  {zgesdd_(jobz, m, n, A, lda, S, U, ldu, VT, ldvt, work, lwork, info);}

inline void ggev(const char & jobvl, const char & jobvr, const lpint & n, std::complex<float> A[], const lpint & lda, std::complex<float> B[], const lpint & ldb, std::complex<float> alpha[], std::complex<float> beta[], std::complex<float> vl[], const lpint & ldvl, std::complex<float> vr[], const lpint & ldvr, std::complex<float> work[], const lpint & lwork, float rwork[], lpint & info)
  {sggev_(jobvl, jobvr, n, A, lda, B, ldb, alpha, beta, vl, ldvl, vr, ldvr, work, lwork, rwork, info);}

inline void ggev(const char & jobvl, const char & jobvr, const lpint & n, std::complex<double> A[], const lpint & lda, std::complex<double> B[], const lpint & ldb, std::complex<double> alpha[], std::complex<double> beta[], std::complex<double> vl[], const lpint & ldvl, std::complex<double> vr[], const lpint & ldvr, std::complex<double> work[], const lpint & lwork, double rwork[], lpint & info)
  {zggev_(jobvl, jobvr, n, A, lda, B, ldb, alpha, beta, vl, ldvl, vr, ldvr, work, lwork, rwork, info);}

inline void gbsv(const lpint & n, const lpint & kl, const lpint & ku, const lpint & nrhs, float ab[], const lpint & ldab, lpint ipiv[], float b[], const lpint & ldb, lpint & info)
  {sgbsv_(n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info);}

inline void gbsv(const lpint & n, const lpint & kl, const lpint & ku, const lpint & nrhs, double ab[], const lpint & ldab, lpint ipiv[], double b[], const lpint & ldb, lpint & info)
  {dgbsv_(n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info);}

inline void gbsv(const lpint & n, const lpint & kl, const lpint & ku, const lpint & nrhs, std::complex<float> ab[], const lpint & ldab, lpint ipiv[], std::complex<float> b[], const lpint & ldb, lpint & info)
  {cgbsv_(n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info);}

inline void gbsv(const lpint & n, const lpint & kl, const lpint & ku, const lpint & nrhs, std::complex<double> ab[], const lpint & ldab, lpint ipiv[], std::complex<double> b[], const lpint & ldb, lpint & info)
  {zgbsv_(n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info);}

inline void scal(const lpint & n, const double & da, double dx[], const lpint & incx)
  {dscal_(n, da, dx, incx);}

inline void scal(const lpint & n, const float & da, float dx[], const lpint & incx)
  {sscal_(n, da, dx, incx);}

inline void scal(const lpint & n, const std::complex<float> & da, std::complex<float> dx[], const lpint & incx)
  {cscal_(n, da, dx, incx);}

inline void scal(const lpint & n, const std::complex<double> & da, std::complex<double> dx[], const lpint & incx)
  {zscal_(n, da, dx, incx);}

inline void axpy(const lpint & n, const double & alpha, const double x[], const lpint & incX, double y[], const lpint & incY)
  {daxpy_(n, alpha, x, incX, y, incY);}

inline void axpy(const lpint & n, const float & alpha, const float x[], const lpint & incX, float y[], const lpint & incY)
  {saxpy_(n, alpha, x, incX, y, incY);}

inline void axpy(const lpint & n, const std::complex<float> & alpha, const std::complex<float> x[], const lpint & incX, std::complex<float> y[], const lpint & incY)
  {caxpy_(n, alpha, x, incX, y, incY);}

inline void axpy(const lpint & n, const std::complex<double> & alpha, const std::complex<double> x[], const lpint & incX, std::complex<double> y[], const lpint & incY)
  {zaxpy_(n, alpha, x, incX, y, incY);}

inline void gemm(const char & ta, const char & tb, const lpint & cols, const lpint & rows, const lpint & mids, const double & alfa, const double B[], const lpint & ldb, const double A[], const lpint & lda, const double & beta, double C[], const lpint & ldc)
  {dgemm_(ta, tb, cols, rows, mids, alfa, B, ldb, A, lda, beta, C, ldc);}

inline void gemm(const char & ta, const char & tb, const lpint & cols, const lpint & rows, const lpint & mids, const float & alfa, const float B[], const lpint & ldb, const float A[], const lpint & lda, const float & beta, float C[], const lpint & ldc)
  {sgemm_(ta, tb, cols, rows, mids, alfa, B, ldb, A, lda, beta, C, ldc);}

inline void gemm(const char & ta, const char & tb, const lpint & cols, const lpint & rows, const lpint & mids, const std::complex<float> & alfa, const std::complex<float> B[], const lpint & ldb, const std::complex<float> A[], const lpint & lda, const std::complex<float> & beta, std::complex<float> C[], const lpint & ldc)
  {cgemm_(ta, tb, cols, rows, mids, alfa, B, ldb, A, lda, beta, C, ldc);}

inline void gemm(const char & ta, const char & tb, const lpint & cols, const lpint & rows, const lpint & mids, const std::complex<double> & alfa, const std::complex<double> B[], const lpint & ldb, const std::complex<double> A[], const lpint & lda, const std::complex<double> & beta, std::complex<double> C[], const lpint & ldc)
  {zgemm_(ta, tb, cols, rows, mids, alfa, B, ldb, A, lda, beta, C, ldc);}

inline void gemv(const char & trans, const lpint & m, const lpint & n, const double & alpha, const double A[], const lpint & lda, const double X[], const lpint & incx, const double & beta, double Y[], const lpint & incy)
  {dgemv_(trans, m, n, alpha, A, lda, X, incx, beta, Y, incy);}

inline void gemv(const char & trans, const lpint & m, const lpint & n, const float & alpha, const float A[], const lpint & lda, const float X[], const lpint & incx, const float & beta, float Y[], const lpint & incy)
  {sgemv_(trans, m, n, alpha, A, lda, X, incx, beta, Y, incy);}

inline void gemv(const char & trans, const lpint & m, const lpint & n, const std::complex<float> & alpha, const std::complex<float> A[], const lpint & lda, const std::complex<float> X[], const lpint & incx, const std::complex<float> & beta, std::complex<float> Y[], const lpint & incy)
  {cgemv_(trans, m, n, alpha, A, lda, X, incx, beta, Y, incy);}

inline void gemv(const char & trans, const lpint & m, const lpint & n, const std::complex<double> & alpha, const std::complex<double> A[], const lpint & lda, const std::complex<double> X[], const lpint & incx, const std::complex<double> & beta, std::complex<double> Y[], const lpint & incy)
  {zgemv_(trans, m, n, alpha, A, lda, X, incx, beta, Y, incy);}

inline void hseqr(const char &job, const char &compz, const lpint &n,
             const lpint &ilo, const lpint &ihi, double h[], const lpint &ldh,
             double wr[], double wi[], double z[], const lpint &ldz,
             double work[], const lpint &lwork, lpint &info)
  {dhseqr_(job, compz, n, ilo, ihi, h, ldh, wr, wi, z, ldz, work, lwork, info);}

inline void hseqr(const char &job, const char &compz, const lpint &n,
             const lpint &ilo, const lpint &ihi, float h[], const lpint &ldh,
             float wr[], float wi[], float z[], const lpint &ldz,
             float work[], const lpint &lwork, lpint &info)
  {shseqr_(job, compz, n, ilo, ihi, h, ldh, wr, wi, z, ldz, work, lwork, info);}

inline void gehd2(const lpint &n, const lpint &ilo, const lpint &ihi, double a[],
             const lpint &lda, double tau[], double work[], lpint &info)
  {dgehd2_(n, ilo, ihi, a, lda, tau, work, info);}

inline void gehd2(const lpint &n, const lpint &ilo, const lpint &ihi, float a[],
             const lpint &lda, float tau[], float work[], lpint &info)
  {sgehd2_(n, ilo, ihi, a, lda, tau, work, info);}

inline void orghr(const lpint &n, const lpint &ilo, const lpint &ihi, double a[],
             const lpint &lda, double tau[], double work[],
             const lpint &lwork, lpint &info)
  {dorghr_(n, ilo, ihi, a, lda, tau, work, lwork, info);}

inline void orghr(const lpint &n, const lpint &ilo, const lpint &ihi, float a[],
             const lpint &lda, float tau[], float work[],
             const lpint &lwork, lpint &info)
  {sorghr_(n, ilo, ihi, a, lda, tau, work, lwork, info);}

inline void gebal(const char &job, const lpint &n, double a[], const lpint &lda,
             lpint &ilo, lpint &ihi, double scale[], lpint &info)
  {dgebal_(job, n, a, lda, ilo, ihi, scale, info);}

inline void gebal(const char &job, const lpint &n, float a[], const lpint &lda,
             lpint &ilo, lpint &ihi, float scale[], lpint &info)
  {sgebal_(job, n, a, lda, ilo, ihi, scale, info);}
