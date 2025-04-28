
#include <genua/sparseqr.h>
#include <genua/splinebasis.h>
#include <genua/lls.h>
#include <genua/pattern.h>
#include <genua/timing.h>
#include <genua/csrmatrix.h>
#include <iostream>
#include <fstream>

using namespace std;
// using suite_sparse::SparseQR;

#define PU  3
#define PV  3

Real falpine(Real u, Real v)
{
  Real tx = (u - 0.5);
  Real ty = (v - 0.5);
  return (sq(ty) - tx + 1)*sin((4*u + 0.25)*M_PI)
      + (sq(tx) + ty - 1)*cos((2*v + 0.75)*M_PI);
}

void find_pattern(const Vector &kts, Vector &t)
{
  Vector tmp(kts);
  sort_unique(tmp);
  const int p = std::max(PU, PV);
  interpolate_pattern(tmp, p*tmp.size(), t);
}

void dense_fit(const SplineBasis &ub,
               const SplineBasis &vb, Matrix &cp)
{
  Vector up, vp;
  find_pattern( ub.getKnots(), up );
  find_pattern( vb.getKnots(), vp );

  SVector<PU+1> bu;
  SVector<PV+1> bv;
  const int ncpu = ub.ncontrol();
  const int ncpv = vb.ncontrol();

  const int nup = up.size();
  const int nvp = vp.size();
  Matrix A(nup*nvp, ncpu*ncpv);
  Vector b(nup*nvp);
  for (int j=0; j<nvp; ++j) {
    int vspan = vb.eval(vp[j], bv);
    for (int i=0; i<nup; ++i) {
      b[j*nup+i] = falpine(up[i], vp[j]);
      int uspan = ub.eval(up[i], bu);
      for (int ki=0; ki<PU+1; ++ki) {
        for (int kj=0; kj<PV+1; ++kj) {
          int kcp = (vspan - PV + kj)*ncpu + (uspan - PU + ki);
          A(j*nup+i, kcp) = bu[ki]*bv[kj];
        }
      }
    }
  }

//  {
//    ofstream os("A.txt");
//    os << A;
//  }

//  {
//    ofstream os("b.txt");
//    os << b;
//  }

  cout << "Dense problem size: " << A.nrows() << " x " << A.ncols() << endl;

  Wallclock clk;
  clk.start();
  lls_solve(A, b);
  clk.stop();
  cout << "LAPACK QR time: " << clk.elapsed() << endl;

  cp.resize(ncpu, ncpv);
  for (int j=0; j<ncpv; ++j)
    for (int i=0; i<ncpu; ++i)
      cp(i,j) = b[j*ncpu + i];
}

void sparse_fit(const SplineBasis &ub,
                const SplineBasis &vb, Matrix &cp)
{
  Vector up, vp;
  find_pattern( ub.getKnots(), up );
  find_pattern( vb.getKnots(), vp );

  SVector<PU+1> bu;
  SVector<PV+1> bv;
  const int ncpu = ub.ncontrol();
  const int ncpv = vb.ncontrol();

  const int nup = up.size();
  const int nvp = vp.size();
  const int nrow = nup*nvp;
  const int ncol = ncpu*ncpv;

  CsrMatrix<double> A;
  {
    ConnectMap spty;
    spty.beginCount(nrow);
    for (int j=0; j<nvp; ++j)
      for (int i=0; i<nup; ++i)
        spty.incCount(j*nup+i, (PU+1)*(PV+1));
    spty.endCount();
    for (int j=0; j<nvp; ++j) {
      int vspan = vb.eval(vp[j], bv);
      for (int i=0; i<nup; ++i) {
        int uspan = ub.eval(up[i], bu);
        for (int ki=0; ki<PU+1; ++ki) {
          for (int kj=0; kj<PV+1; ++kj) {
            int kcp = (vspan - PV + kj)*ncpu + (uspan - PU + ki);
            spty.append(j*nup+i, kcp);
          }
        }
      }
    }
    spty.compress();
    A.swap(spty, ncol);
  }

  Vector b(nup*nvp);
  for (int j=0; j<nvp; ++j) {
    int vspan = vb.eval(vp[j], bv);
    for (int i=0; i<nup; ++i) {
      b[j*nup+i] = falpine(up[i], vp[j]);
      int uspan = ub.eval(up[i], bu);
      for (int ki=0; ki<PU+1; ++ki) {
        for (int kj=0; kj<PV+1; ++kj) {
          int kcp = (vspan - PV + kj)*ncpu + (uspan - PU + ki);
          uint lix = A.lindex(j*nup+i, kcp);
          assert(lix != NotFound);
          A[lix] = bu[ki]*bv[kj];
        }
      }
    }
  }

  Wallclock clk;
  clk.start();
  Vector x;
  SparseQR<double> spqr;
  // spqr.factor(A);
  spqr.solve(A, b, x);
  clk.stop();
  cout << "SparseQR time: " << clk.elapsed() << endl;

  cp.resize(ncpu, ncpv);
  for (int j=0; j<ncpv; ++j)
    for (int i=0; i<ncpu; ++i)
      cp(i,j) = x[j*ncpu + i];
}

int main(int argc, char *argv[])
{

  int nku(10), nkv(10);
  if (argc > 1)
    nku = atoi( argv[1] );
  if (argc > 2)
    nkv = atoi( argv[2] );

  SplineBasis ubas, vbas;
  ubas.init( PU, equi_pattern(nku) );
  vbas.init( PV, equi_pattern(nkv) );

  Wallclock clk;

  clk.start();
  Matrix dcp;
  dense_fit(ubas, vbas, dcp);
  clk.stop();
  cout << "Dense QR solution: " << clk.elapsed() << endl;

  clk.start();
  Matrix scp;
  sparse_fit(ubas, vbas, scp);
  clk.stop();
  cout << "Sparse QR solution: " << clk.elapsed() << endl;

  // compare a few values
  for (int i=0; i<5; ++i) {
    for (int j=0; j<5; ++j) {
      cout << "(" << i << ", " << j << ") = "
           << dcp(i,j) << " : " << scp(i,j) << endl;
    }
  }

  return 0;
}
