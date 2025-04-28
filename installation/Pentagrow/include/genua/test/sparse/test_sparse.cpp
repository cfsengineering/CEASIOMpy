
#ifdef HAVE_MKL
#include <genua/pardisosolver.h>
#pragma message("Found MKL")
#else
#pragma message("No MKL present")
#endif

#ifdef HAVE_SPQR
#include <genua/sparseqr.h>
#include <genua/umfpacksolver.h>
#include <genua/cholmodsolver.h>
#endif

//#include <genua/spoolessolver.h>
#include <genua/convertingsolver.h>
#include <genua/eigensparsesolver.h>
#include <genua/splinebasis.h>
#include <genua/lls.h>
#include <genua/pattern.h>
#include <genua/timing.h>
#include <genua/csrmatrix.h>
#include <genua/sparsebuilder.h>
#include <genua/parbilu.h>
#include <genua/rng.h>
#include <genua/lapack.h>
#include <lsfem/lingmres.h>
#include <genua/rng.h>
#include <iostream>
#include <random>
#include <fstream>

using namespace std;

// thin wrapper around ILU
template <typename FloatType, int BlockSize>
class IluPreconditioner
{
public:
  typedef SparseBlockMatrix<FloatType, BlockSize> BlockMatrix;

  void factor(const CsrMatrix<FloatType,1> *pa) {
    m_pa = pa;
    m_ablock.assign(*pa);
    m_pbilu.initStandard(m_ablock);
    m_pbilu.factorSweep(m_ablock, m_nsweep);
    m_xpad.resize( BlockSize*m_ablock.nbrows() );
    m_bpad.resize( BlockSize*m_ablock.nbrows() );
  }

  void refactor(const CsrMatrix<FloatType,1> *pa) {
    m_ablock.injectValues(*pa);
    m_pbilu.factorSweep(m_ablock, m_nsweep);
  }

  // interface for LinGMRES
  void eval(const DVector<FloatType> &x, DVector<FloatType> &b) const {
    // std::fill(b.begin(), b.end(), 0.0);
    // m_ablock.muladd(x,b);
    m_pa->multiply(x, b);
  }

  // interface for LinGMRES
  void psolve(const DVector<FloatType> &b, DVector<FloatType> &x) const {
    std::copy(b.begin(), b.end(), m_bpad.begin());
    m_pbilu.lusolve(m_bpad, m_xpad);
    std::copy(m_xpad.begin(), m_xpad.begin()+b.size(), x.begin());
    clog << "ILU solve |x| = " << norm(x) << endl;
  }

private:
  const CsrMatrix<FloatType,1> *m_pa;
  mutable DVector<double> m_xpad, m_bpad;
  BlockMatrix m_ablock;
  ParBILU<FloatType, BlockSize> m_pbilu;
  size_t m_nsweep = 4;
};

#define PU  3
#define PV  3

Real falpine(Real u, Real v)
{
  Real tx = (u - 0.5);
  Real ty = (v - 0.5);
  return (sq(ty) - tx + 1)*sin((4*u + 0.25)*M_PI)
      + (sq(tx) + ty - 1)*cos((2*v + 0.75)*M_PI);
}

void find_pattern(const Vector &kts, uint np, Vector &t)
{
  Vector tmp(kts);
  sort_unique(tmp);
  interpolate_pattern(tmp, np, t);
}

void gemm_timing()
{
  Wallclock clk;
  const int nmax = 512;
  IntRng rng(16, nmax);
  int m, n, k;
  uint64_t flops = 0;
  double t = 0;
  Matrix a(nmax,nmax), b(nmax,nmax), c(nmax,nmax);
  a = 3.4;
  b = -1.2;
  c = 4.5;
  for (int j=0; j<1000; ++j) {
    m = rng();
    n = rng();
    k = rng();
    flops += 2*m*n*k;
    c = 0.0;
    clk.start();
    lapack::dgemm_('N', 'N', m, n, k, 1.0, b.pointer(), b.ldim(),
                   a.pointer(), a.ldim(), -1.0, c.pointer(), c.ldim());
    t += clk.stop();
  }
  cout << "Mixed size GEMM: " << 1e-9*flops/t << " GFlop/s" << endl;
}

void dense_fit(const SplineBasis &ub,
               const SplineBasis &vb, Matrix &cp)
{
  Vector up, vp;
  find_pattern( ub.getKnots(), ub.ncontrol(), up );
  find_pattern( vb.getKnots(), vb.ncontrol(), vp );

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
  find_pattern( ub.getKnots(), ub.ncontrol(), up );
  find_pattern( vb.getKnots(), vb.ncontrol(), vp );

  SVector<PU+1> bu;
  SVector<PV+1> bv;
  const int ncpu = ub.ncontrol();
  const int ncpv = vb.ncontrol();

  const int nup = up.size();
  const int nvp = vp.size();
  const int nrow = nup*nvp;
  const int ncol = ncpu*ncpv;

  cout << "Problem size: " << nrow << " x " << ncol << endl;

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
  Vector x(b.size());


  //  SparseQR<double> spqr;
  //  spqr.factor(&A);
  //  spqr.solve(b, x);

//  {
//    cout << "Sparse solver: SPOOLES" << endl;
//    SpoolesSolver<double> spooles(SpoolesBase::Unsymmetric);
//    spooles.factor(&A);
//    spooles.solve(b, x);
//  }

  //    {
  //      cout << "Sparse solver: PARDISO" << endl;
  //      PardisoSolver<double> pardiso;
  //      pardiso.setDefaults(PardisoBase::RealUnsymmetric);
  //      pardiso.solve(&A, b, x);
  //    }

  clk.stop();
  cout << "Sparse time: " << clk.elapsed() << endl;

  cp.resize(ncpu, ncpv);
  for (int j=0; j<ncpv; ++j)
    for (int i=0; i<ncpu; ++i)
      cp(i,j) = x[j*ncpu + i];
}

void test_splinefit(int nku, int nkv)
{
  SplineBasis ubas, vbas;
  ubas.init( PU, equi_pattern(nku) );
  vbas.init( PV, equi_pattern(nkv) );

  Wallclock clk;

  clk.start();
  Matrix dcp;
  dense_fit(ubas, vbas, dcp);
  clk.stop();
  cout << "Dense solution: " << clk.elapsed() << endl;

  clk.start();
  Matrix scp;
  sparse_fit(ubas, vbas, scp);
  clk.stop();
  cout << "Sparse solution: " << clk.elapsed() << endl;

  // compare a few values
  for (int i=0; i<5; ++i) {
    for (int j=0; j<5; ++j) {
      cout << "(" << i << ", " << j << ") = "
           << dcp(i,j) << " : " << scp(i,j) << endl;
    }
  }
}

void test_sparse_direct(DSparseSolver &solver, const CsrMatrix<double> &a)
{
  // configure solver
  ConfigParser cfg("test.cfg");
  solver.configure(cfg);
  solver.transposed(false);

  // random rhs
  const size_t n = a.nrows();
  Vector x(n), b(n);

  std::random_device rd;
  std::minstd_rand mt(rd());
//  std::uniform_real_distribution<double> dist(0.0, 1.0);
//  for (size_t i=0; i<n; ++i)
//    b[i] = dist(mt);

  x = 0.0;
  b = 1.0;

  Wallclock clk;
  cout << "Direct solver: " << solver.name() << endl;
  cout << "Problem size : " << a.nrows() << endl;
  clk.start();
  bool ok = solver.factor(&a);
  cout << "Factorization: " << clk.stop() << endl;
  cout << "Status: " << (ok ? " success" : " failed") << endl;
  if (not ok)
    return;

  clk.start();
  ok = solver.solve(b, x);
  cout << "Solution, nrhs=1: " << clk.stop() << endl;
  cout << "Status: " << (ok ? " success" : " failed") << endl;
  if (not ok)
    return;

  if (x.size() < 10) {
    for (uint i=0; i<x.size(); ++i)
      cout << i << " : " << b[i] << " -> " << x[i] << endl;
  }

  b = 1.0;

  // check result: r = a*x
  Vector r(n);
  a.multiply(x, r);
  double f = norm(b - r);
  cout << "Error norm: " << f / norm(b) << endl;

//  r = 0;
//  a.multiplyTransposed(x, r);
//  f = norm(b - r);
//  cout << "|A^T * x - b| " << f / norm(b) << endl;

  return;

  // new factorization with the same pattern
  CsrMatrix<double> c( a.sparsity(), a.ncols() );
  double *pv = c.pointer();
  const double *av = a.pointer();

  const size_t nnz = c.nonzero();
  std::uniform_real_distribution<double> fdist(0.9, 1.1);
  for (size_t i=0; i<nnz; ++i)
    pv[i] = fdist(mt) * av[i];

  clk.start();
  ok = solver.refactor(&c);
  cout << "Re-factorization: " << clk.stop() << endl;
  cout << "Status: " << (ok ? " success" : " failed") << endl;
  if (not ok)
    return;

  // test solving the transposed problem A^T x = b
  x = 0;
  solver.transposed(true);
  clk.start();
  ok = solver.solve(b, x);
  cout << "Transposed solution, nrhs=1: " << clk.stop() << endl;
  cout << "Status: " << (ok ? " success" : " failed") << endl;
  if (not ok)
    return;

  r = 0;
  c.multiplyTransposed(x, r);
  f = norm(b - r);
  cout << "Error norm: " << f / norm(b) << endl;
}

void test_iterative(const CsrMatrix<double> &A)
{
  Wallclock clk;

  clk.start();
  SparseBlockMatrix<double,4> B(A);
  cout << "Transfer to block matrix: " << clk.stop() << endl;

  clk.start();
  ParBILU<double,4> p;
  p.initStandard(B);
  cout << "Initialization: " << clk.stop() << endl;

  clk.start();
  p.factorSweep(B, 4);
  cout << "4 Sweeps: " << clk.stop() << endl;

  const size_t n = A.nrows();
  Vector x(n), b(n);
  x = 1.0;
  A.muladd(x, b);

  clk.start();
  p.lusolve(b, x);
  cout << "L/U solve: " << clk.stop() << endl;

  // set up a wrapper for GMRES
  IluPreconditioner<double, 4> pc;
  pc.factor(&A);

  x = 2.0;

  clk.start();
  LinGmres< DVector<double> > gmres;
  gmres.setParameter(1e-4, 128, 16);
  gmres.solve(pc, x, b);
  cout << "GMRES/ILU: " << clk.stop() << endl;
  cout << "Iterations: " << gmres.iterations()
       << " residual: " << gmres.rfinal() << endl;
}

void reorder_nd(CsrMatrix<double> &a)
{
  Wallclock clk;
  {
    ofstream os("original.txt");
    a.writeMarket(os);
  }

  // reorder
  Indices perm, iperm;
  clk.start();
  bool status = a.permuteByMetis(perm, iperm);
  clk.stop();
  if (status) {
    cout << "Reordering ok: " << clk.elapsed() << endl;
  } else {
    cout << "Reordering failed." << endl;
  }

  // test fill computation
  cout << "Before fill-in: " << a.nonzero() << " nnz" << endl;
  clk.start();
  ConnectMap tmap;
  a.sparsity().transpose(a.nrows(), tmap);
  cout << "Computation of transpose pattern: " << clk.stop() << endl;
  clk.start();
  std::vector<uint64_t> f;
  ConnectMap::fillIn(a.sparsity(), tmap, f);
  cout << "Computation of level-1 fill-in: " << clk.stop() << endl;
  cout << "Fill-in entries: " << f.size() << endl;

  {
    ofstream os("reordered.txt");
    a.writeMarket(os);
  }
}

void generate_problem(int n, CsrMatrix<double> &a)
{
  const int ncmin = 7;
  const int ncmax = 21;
  const int band = sqrt(double(n));

  FloatRng frng(0.1, 3.0);
  IntRng crng(ncmin, ncmax);
  SparseBuilder<double> builder;
  for (int i=0; i<n; ++i) {
    IntRng irng( std::max(0,i-band), std::min(i+band,n-1) );
    builder.append(i, i, 9.1);
    const int nc = crng();
    for (int j=0; j<nc; ++j)
      builder.append(i, irng(), frng());
  }

  builder.sort(true);
  a.assign(n, n, builder);

  reorder_nd(a);
}

CsrMatrix<double> make_small_matrix()
{
  // scipy:
  // a = matrix([[ 3. ,  1.5, -0.1,  0.3],
  //             [-0.6,  2. , -0.1,  0.5],
  //             [ 0.3,  0. ,  1.9, -0.8],
  //             [ 0.1, -0.4,  0.9,  4.7]])

  // generate a dense problem so that ilu(A) = L,U is exact
  SparseBuilder<double> builder;
  builder.append( 0, 0,  3.0 );
  builder.append( 0, 1,  1.5 );
  builder.append( 0, 2, -0.1 );
  builder.append( 0, 3,  0.3 );

  builder.append( 1, 0, -0.6 );
  builder.append( 1, 1,  2.0 );
  builder.append( 1, 2, -0.1 );
  builder.append( 1, 3,  0.5 );

  builder.append( 2, 0,  0.3 );
  builder.append( 2, 1,  0.0 );
  builder.append( 2, 2,  1.9 );
  builder.append( 2, 3, -0.8 );

  builder.append( 3, 0,  0.1 );
  builder.append( 3, 1, -0.4 );
  builder.append( 3, 2,  0.9 );
  builder.append( 3, 3,  4.7 );

  CsrMatrix<double> as;
  as.assign(4,4,builder);
  return as;
}

void check_ilu()
{
  CsrMatrix<double> as = make_small_matrix();
  SparseBlockMatrix<double,2> ab(as);

  cout << "BlockMatrix: " << endl;
  ab.writePlain(cout);

  ParBILU<double,2> p;
  p.initStandard(ab);

  p.factorSweep(ab, 2);

  cout << "Lower: " << endl;
  p.lower().writePlain(cout);
  cout << "Upper: " << endl;
  p.upper().writePlain(cout);

  // check solution
  DVector<double> xtrue(4), b(4), x(4);
  xtrue = 8.0;
  as.multiply(xtrue, b);

  cout << "b = " << b << endl;
  p.lusolve(b, x);
  cout << "Solution: " << x << endl;
}

int main(int argc, char *argv[])
{
  try {

    gemm_timing();

    if ( strstr(argv[0], "splinefit") ) {

      int nku(40), nkv(40);
      if (argc > 1)
        nku = atoi( argv[1] );
      if (argc > 2)
        nkv = atoi( argv[2] );
      test_splinefit(nku, nkv);

    } else {

      //check_ilu();

      CsrMatrix<double> a;

      if (argc > 1) {
        ifstream in(argv[1]);
        if (not in)
          throw Error("Cannot open file: "+string(argv[1]));
        a.readBin(in);
        // reorder_nd(a);
      } else {
        size_t n = 300;
        // generate_problem(n, a);
        a = make_small_matrix();
      }

      cout << "Rows: " << a.nrows() << " Cols: " << a.ncols()
           << " nnz: " << a.nonzero() << endl;

      //test_iterative(a);

#ifdef HAVE_MKL
      {
        cout << "Pardiso/double" << endl;
        PardisoSolver<double> solver( SpMatrixFlag::RealUnsymmetric );
        test_sparse_direct(solver, a);
      }

      {
        cout << "Pardiso/float" << endl;
        PardisoSolver<float> *pfs;
        pfs = new PardisoSolver<float>( SpMatrixFlag::RealUnsymmetric );
        boost::shared_ptr<PardisoSolver<float> >  ppfs(pfs);
        ConvertingSolver<double,float> css(ppfs);
        test_sparse_direct(css, a);
      }
#endif

//      {
//        cout << "EigenSparseLU" << endl;
//        EigenSparseLU<double> solver( SpMatrixFlag::RealUnsymmetric );
//        test_sparse_direct(solver, a);
//        cout << "Last message: " << solver.message() << endl;
//      }

#ifdef HAVE_SPQR
      {
        cout << "UMFPACK" << endl;
        UmfpackSolver<double> solver( SpMatrixFlag::RealUnsymmetric );
        test_sparse_direct(solver, a);
        cout << "Last message: " << solver.lastMessage() << endl;
      }
      {
        cout << "SparseQR" << endl;
        SparseQR<double> solver( SpMatrixFlag::RealUnsymmetric );
        test_sparse_direct(solver, a);
        // cout << "Last message: " << solver.lastMessage() << endl;
      }
#endif

//      {
//        cout << "Spooles" << endl;
//        SpoolesSolver<double> solver( SpMatrixFlag::RealUnsymmetric );
//        test_sparse_direct(solver, a);
//      }

    }

  } catch (Error &xcp) {
    cerr << xcp.what() << endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;

  return 0;
}
