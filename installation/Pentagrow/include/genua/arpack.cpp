
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
 
#include "arpack.h"
#include <complex>
#include <iostream>

using namespace std;

extern "C" {

typedef int arint;
typedef int logical;

// double precision symmetric routines.

void dsaupd_(arint *ido, char *bmat, arint *n, const char *which,
             arint *nev, double *tol, double *resid,
             arint *ncv, double *V, arint *ldv,
             arint *iparam, arint *ipntr, double *workd,
             double *workl, arint *lworkl, arint *info);

void dseupd_(logical *rvec, char *HowMny, logical *select,
             double *d, double *Z, arint *ldz,
             double *sigma, char *bmat, arint *n,
             char *which, arint *nev, double *tol,
             double *resid, arint *ncv, double *V,
             arint *ldv, arint *iparam, arint *ipntr,
             double *workd, double *workl,
             arint *lworkl, arint *info);

// double precision nonsymmetric routines.

void dnaupd_(arint *ido, char *bmat, arint *n, const char *which,
             arint *nev, double *tol, double *resid,
             arint *ncv, double *V, arint *ldv,
             arint *iparam, arint *ipntr, double *workd,
             double *workl, arint *lworkl, arint *info);

void dneupd_(logical *rvec, char *HowMny, logical *select,
             double *dr, double *di, double *Z,
             arint *ldz, double *sigmar,
             double *sigmai, double *workev,
             char *bmat, arint *n, const char *which,
             arint *nev, double *tol, double *resid,
             arint *ncv, double *V, arint *ldv,
             arint *iparam, arint *ipntr,
             double *workd, double *workl,
             arint *lworkl, arint *info);

// single precision symmetric routines.

void ssaupd_(arint *ido, char *bmat, arint *n, const char *which,
             arint *nev, float *tol, float *resid,
             arint *ncv, float *V, arint *ldv,
             arint *iparam, arint *ipntr, float *workd,
             float *workl, arint *lworkl, arint *info);

void sseupd_(logical *rvec, char *HowMny, logical *select,
             float *d, float *Z, arint *ldz,
             float *sigma, char *bmat, arint *n,
             const char *which, arint *nev, float *tol,
             float *resid, arint *ncv, float *V,
             arint *ldv, arint *iparam, arint *ipntr,
             float *workd, float *workl,
             arint *lworkl, arint *info);

// single precision nonsymmetric routines.

void snaupd_(arint *ido, char *bmat, arint *n, const char *which,
             arint *nev, float *tol, float *resid,
             arint *ncv, float *V, arint *ldv,
             arint *iparam, arint *ipntr, float *workd,
             float *workl, arint *lworkl, arint *info);

void sneupd_(logical *rvec, char *HowMny, logical *select,
             float *dr, float *di, float *Z,
             arint *ldz, float *sigmar,
             float *sigmai, float *workev, char *bmat,
             arint *n, const char *which, arint *nev,
             float *tol, float *resid, arint *ncv,
             float *V, arint *ldv, arint *iparam,
             arint *ipntr, float *workd, float *workl,
             arint *lworkl, arint *info);

// single precision complex routines.

void cnaupd_(arint *ido, char *bmat, arint *n, const char *which,
             arint *nev, float *tol, std::complex<float> *resid,
             arint *ncv, std::complex<float> *V, arint *ldv,
             arint *iparam, arint *ipntr, std::complex<float> *workd,
             std::complex<float> *workl, arint *lworkl,
             float *rwork, arint *info);

void cneupd_(logical *rvec, char *HowMny, logical *select,
             std::complex<float> *d, std::complex<float> *Z, arint *ldz,
             std::complex<float> *sigma, std::complex<float> *workev,
             char *bmat, arint *n, const char *which, arint *nev,
             float *tol, std::complex<float> *resid, arint *ncv,
             std::complex<float> *V, arint *ldv, arint *iparam,
             arint *ipntr, std::complex<float> *workd,
             std::complex<float> *workl, arint *lworkl,
             float *rwork, arint *info);

// double precision complex routines.

void znaupd_(arint *ido, char *bmat, arint *n, const char *which,
             arint *nev, double *tol, std::complex<double> *resid,
             arint *ncv, std::complex<double> *V, arint *ldv,
             arint *iparam, arint *ipntr, std::complex<double> *workd,
             std::complex<double> *workl, arint *lworkl,
             double *rwork, arint *info);

void zneupd_(logical *rvec, char *HowMny, logical *select,
             std::complex<double> *d, std::complex<double> *Z, arint *ldz,
             std::complex<double> *sigma, std::complex<double> *workev,
             char *bmat, arint *n, const char *which, arint *nev,
             double *tol, std::complex<double> *resid, arint *ncv,
             std::complex<double> *V, arint *ldv, arint *iparam,
             arint *ipntr, std::complex<double> *workd,
             std::complex<double> *workl, arint *lworkl,
             double *rwork, arint *info);

} // extern Fortran arpack routines

void arpackf::naupd(int &ido, char bmat, int n, const char *which, int nev,
                    double &tol, double resid[], int ncv, double V[],
                    int ldv, int iparam[], int ipntr[], double workd[],
                    double workl[], int lworkl, int &info)
{
//#ifndef NDEBUG
//  cout << "dnaupd_" << endl;
//  cout << "IDO = " << ido << endl;
//  cout << "BMAT = " << bmat << endl;
//  cout << "N = " << n << endl;
//  cout << "WHICH = " << which << endl;
//  cout << "NEV = " << nev << endl;
//  cout << "TOL = " << tol << endl;
//  cout << "NCV = " << ncv << endl;
//  cout << "LDV = " << ldv << endl;
//  cout << "LWORKL = " << lworkl << endl;
//  for (int i=0; i<12; ++i)
//    cout << "IPARAM[" << i+1 << "] = " << iparam[i] << endl;
//#endif

  dnaupd_(&ido, &bmat, &n, which, &nev, &tol, resid, &ncv,
          &V[0], &ldv, &iparam[0], &ipntr[0], &workd[0], &workl[0],
      &lworkl, &info);
}

void arpackf::naupd(int& ido, char bmat, int n, const char *which, int nev,
                    float& tol, float resid[], int ncv, float V[],
                    int ldv, int iparam[], int ipntr[], float workd[],
                    float workl[], int lworkl, int& info)
{
  snaupd_(&ido, &bmat, &n, which, &nev, &tol, resid, &ncv,
          &V[0], &ldv, &iparam[0], &ipntr[0], &workd[0], &workl[0],
      &lworkl, &info);
}

void arpackf::neupd(bool rvec, char HowMny, double dr[],
                    double di[], double Z[], int ldz, double sigmar,
                    double sigmai, double workv[], char bmat, int n,
                    const char* which, int nev, double tol, double resid[],
                    int ncv, double V[], int ldv, int iparam[],
                    int ipntr[], double workd[], double workl[],
                    int lworkl, int& info)
{
  DVector<logical> iselect(ncv, 1);
  double *iZ = (Z == nullptr) ? &V[0] : Z;
  int      irvec = (int) rvec;

  dneupd_(&irvec, &HowMny, iselect.pointer(), dr, di, iZ, &ldz, &sigmar,
          &sigmai, &workv[0], &bmat, &n, which, &nev, &tol,
          resid, &ncv, &V[0], &ldv, &iparam[0], &ipntr[0],
          &workd[0], &workl[0], &lworkl, &info);
}

void arpackf::neupd(bool rvec, char HowMny, float dr[],
                    float di[], float Z[], int ldz, float sigmar,
                    float sigmai, float workv[], char bmat, int n,
                    const char* which, int nev, float tol, float resid[],
                    int ncv, float V[], int ldv, int iparam[],
                    int ipntr[], float workd[], float workl[],
                    int lworkl, int& info)
{
  DVector<logical> iselect(ncv, 1);
  float *iZ = (Z == nullptr) ? &V[0] : Z;
  int      irvec = (int) rvec;

  sneupd_(&irvec, &HowMny, iselect.pointer(), dr, di, iZ, &ldz, &sigmar,
          &sigmai, &workv[0], &bmat, &n, which, &nev, &tol,
          resid, &ncv, &V[0], &ldv, &iparam[0], &ipntr[0],
          &workd[0], &workl[0], &lworkl, &info);
}
