
#include <genua/dmatrix.h>
#include <genua/dvector.h>
#include <genua/timing.h>
#include <genua/lu.h>
#include <genua/lls.h>
#include <genua/pattern.h>
#include <genua/splinebasis.h>
#include <genua/eigensparsesolver.h>
#include <eeigen/Core>
#include <eeigen/LU>
#include <eeigen/QR>
#include <eeigen/SparseLU>
#include <eeigen/Geometry>
#include <cstdlib>
#include <iostream>

using namespace std;

typedef eeigen::Matrix<double, eeigen::Dynamic, eeigen::Dynamic> EigenMatrix;
typedef eeigen::Map<EigenMatrix, eeigen::Aligned> EigenMatrixMap;
typedef eeigen::PartialPivLU<EigenMatrix> EigenLU;
typedef eeigen::HouseholderQR<EigenMatrix> EigenQR;

EigenMatrixMap toEigen(Matrix &m) { return EigenMatrixMap(m.pointer(), m.nrows(), m.ncols()); }
EigenMatrixMap toEigen(Vector &m) { return EigenMatrixMap(m.pointer(), m.size(), 1); }

inline void toEigen(const Matrix &m, EigenMatrix &me)
{
  me.resize(m.nrows(), m.ncols());
  memcpy(me.data(), m.pointer(), m.size() * sizeof(double));
}

inline void toEigen(const Vector &m, EigenMatrix &me)
{
  me.resize(m.size(), 1);
  memcpy(me.data(), m.pointer(), m.size() * sizeof(double));
}

// spline degree
#define PU 3
#define PV 3

Real falpine(Real u, Real v)
{
  Real tx = (u - 0.5);
  Real ty = (v - 0.5);
  return (sq(ty) - tx + 1) * sin((4 * u + 0.25) * M_PI) + (sq(tx) + ty - 1) * cos((2 * v + 0.75) * M_PI);
}

void find_pattern(const Vector &kts, uint np, Vector &t)
{
  Vector tmp(kts);
  sort_unique(tmp);
  interpolate_pattern(tmp, np, t);
}

void eigen_qr_solve(Matrix &A, Vector &b)
{
  if (A.nrows() != A.ncols())
  {

    // EigenMatrix Ae, be, xe;
    // toEigen(A, Ae);
    // toEigen(b, be);

    EigenQR qr(toEigen(A));
    EigenMatrix xe = qr.solve(toEigen(b));
    b = Vector(xe.data(), xe.rows());
  }
  else
  {
    EigenLU lu;
    lu.compute(toEigen(A));
    EigenMatrix xe = lu.solve(toEigen(b));
    b = Vector(xe.data(), xe.rows());
  }
}

void dense_fit(const SplineBasis &ub,
               const SplineBasis &vb, Matrix &cp, bool useLapack)
{
  Vector up, vp;
  find_pattern(ub.getKnots(), ub.ncontrol(), up);
  find_pattern(vb.getKnots(), vb.ncontrol(), vp);

  SVector<PU + 1> bu;
  SVector<PV + 1> bv;
  const int ncpu = ub.ncontrol();
  const int ncpv = vb.ncontrol();

  const int nup = up.size();
  const int nvp = vp.size();
  Matrix A(nup * nvp, ncpu * ncpv);
  Vector b(nup * nvp);
  for (int j = 0; j < nvp; ++j)
  {
    int vspan = vb.eval(vp[j], bv);
    for (int i = 0; i < nup; ++i)
    {
      b[j * nup + i] = falpine(up[i], vp[j]);
      int uspan = ub.eval(up[i], bu);
      for (int ki = 0; ki < PU + 1; ++ki)
      {
        for (int kj = 0; kj < PV + 1; ++kj)
        {
          int kcp = (vspan - PV + kj) * ncpu + (uspan - PU + ki);
          A(j * nup + i, kcp) = bu[ki] * bv[kj];
        }
      }
    }
  }

  cout << "Dense problem size: " << A.nrows() << " x " << A.ncols() << endl;

  Wallclock clk;
  if (useLapack)
  {
    clk.start();
    lls_solve(A, b);
    clk.stop();
    cout << "LAPACK QR time: " << clk.elapsed() << endl;
  }
  else
  {
    clk.start();
    eigen_qr_solve(A, b);
    clk.stop();
    cout << "eeigen QR time: " << clk.elapsed() << endl;
  }

  cp.resize(ncpu, ncpv);
  for (int j = 0; j < ncpv; ++j)
    for (int i = 0; i < ncpu; ++i)
      cp(i, j) = b[j * ncpu + i];
}

void sparse_fit(const SplineBasis &ub,
                const SplineBasis &vb, Matrix &cp)
{
  Vector up, vp;
  find_pattern(ub.getKnots(), ub.ncontrol(), up);
  find_pattern(vb.getKnots(), vb.ncontrol(), vp);

  SVector<PU + 1> bu;
  SVector<PV + 1> bv;
  const int ncpu = ub.ncontrol();
  const int ncpv = vb.ncontrol();

  const int nup = up.size();
  const int nvp = vp.size();
  // Matrix A(nup*nvp, ncpu*ncpv);
  Vector b(nup * nvp);

  eeigen::SparseMatrix<double> A(nup * nvp, ncpu * ncpv);
  {
    size_t ntrip = nvp * nup * (PU + 1) * (PV + 1);
    typedef eeigen::Triplet<double, int> Trip;
    std::vector<Trip> trips(ntrip);

    size_t itrip(0);
    for (int j = 0; j < nvp; ++j)
    {
      int vspan = vb.eval(vp[j], bv);
      for (int i = 0; i < nup; ++i)
      {
        b[j * nup + i] = falpine(up[i], vp[j]);
        int uspan = ub.eval(up[i], bu);
        for (int ki = 0; ki < PU + 1; ++ki)
        {
          for (int kj = 0; kj < PV + 1; ++kj)
          {
            int kcp = (vspan - PV + kj) * ncpu + (uspan - PU + ki);
            trips[itrip++] = Trip(j * nup + i, kcp, bu[ki] * bv[kj]);
          }
        }
      }
    }
    assert(itrip == trips.size());

    A.setFromTriplets(trips.begin(), trips.end());
    A.makeCompressed();
  }

  Wallclock clk;
  clk.start();

  // eeigen::SparseQR<eeigen::SparseMatrix<double>, eeigen::AMDOrdering<int> > slu;
  eeigen::SparseLU<eeigen::SparseMatrix<double>> slu;
  slu.compute(A);
  EigenMatrix xe = slu.solve(toEigen(b));
  b = Vector(xe.data(), xe.rows());

  clk.stop();
  cout << "eeigen::SparseLU: " << clk.elapsed() << endl;

  cp.resize(ncpu, ncpv);
  for (int j = 0; j < ncpv; ++j)
    for (int i = 0; i < ncpu; ++i)
      cp(i, j) = b[j * ncpu + i];
}

int main(int argc, char *argv[])
{
  int nku(40), nkv(40);
  if (argc > 1)
    nku = atoi(argv[1]);
  if (argc > 2)
    nkv = atoi(argv[2]);

  SplineBasis ubas, vbas;
  ubas.init(PU, equi_pattern(nku));
  vbas.init(PV, equi_pattern(nkv));

  Wallclock clk;

  clk.start();
  Matrix lcp, ecp, scp;
  dense_fit(ubas, vbas, lcp, true);
  clk.stop();
  cout << "LAPACK solution: " << clk.elapsed() << endl;

  clk.start();
  dense_fit(ubas, vbas, ecp, false);
  clk.stop();
  cout << "Dense eeigen solution: " << clk.elapsed() << endl;

  clk.start();
  sparse_fit(ubas, vbas, scp);
  clk.stop();
  cout << "Sparse eeigen solution: " << clk.elapsed() << endl;

  // compare a few values
  for (int i = 0; i < 5; ++i)
  {
    for (int j = 0; j < 5; ++j)
    {
      cout << "(" << i << ", " << j << ") = "
           << lcp(i, j) << " : " << scp(i, j) << endl;
    }
  }

  /*

  int m(100), n(100);
  if (argc > 1)
    m = n = atoi(argv[1]);
  if (argc > 2)
    n = atoi(argv[2]);

  Matrix A(m,n);
  Vector xr, b(m);

  for (int j=0; j<n; ++j) {
    for (int i=0; i<m; ++i)
      A(i,j) = double( rand() ) / RAND_MAX;
  }
  b = 1.0;

  Wallclock clk;

  // reference solution using lapack
  {
    Matrix B(A);
    xr = b;
    clk.start("LAPACK solution: ");
    lu_solve(B, xr);
    clk.stop("Time: ");
    cout << "Reference residual: " << norm(A*xr - b) / norm(b) << endl;
  }

  // compare to eigen
  {
    clk.start("EIGEN 3.2 solution: ");
    EigenMatrixMap Ae( toEigen(A) ), be( toEigen(b) );
    EigenMatrix xe;

    EigenLU lu;
    lu.compute(Ae);
    xe = lu.solve(be);

    clk.stop("Time: ");
    cout << "eeigen residual: " << (Ae*xe - be).norm() / be.norm() << endl;
  }


  */

  return EXIT_SUCCESS;
}
