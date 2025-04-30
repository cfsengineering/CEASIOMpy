
#include <genua/arpack.h>
#include <genua/sparsebuilder.h>
#include <genua/rng.h>
#include <genua/algo.h>

#include <iostream>
#include <fstream>

using namespace std;


struct DenseOperator
{
  DenseOperator(const Matrix &A) : m_a(A) {}
  void operator() (const double *px, double *py) const {
    lapack::gemv('N', m_a.nrows(), m_a.ncols(), 1.0,
                 m_a.pointer(), m_a.nrows(),
                 px, 1, 0.0, py, 1);
  }
  size_t size() const {return m_a.nrows();}
  const Matrix &m_a;
};

int main(int argc, char *argv[])
{
  try {

    // try a diagonal matrix first
    const int n = 20;
    SparseBuilder<double> builder;
    builder.resize(n);
    typedef SparseBuilder<double>::Triplet Value;
    FloatRng rng(1.0, 9.0);
    for (int i=0; i<n; ++i) {
      builder[i] = Value(i,i, rng());
    }

//    rng = FloatRng(-0.5, 0.5);
//    IntRng irng(0,n-1);
//    for (int k=0; k<9*n; ++k)
//      builder.append( irng()%n, irng()%n, rng() );
    builder.sort(false);

    CsrMatrix<double> A;
    A.assign(n,n,builder);

    A.writeMarket(std::cout);

    ArpackSolver<double> solver;
    SpOperator op(A);
    // DenseOperator op(acheck);
    solver.direct(op, std::max(4,n/8), "LM");

    cout << "Eigenvalues: " << solver.eigenvalues() << endl;
    for (size_t j=0; j<solver.eigenvalues().size(); ++j)
      cout << "Residual in " << j << " = " << solver.residual(op, j) << endl;

    cout << "First eigenvector:" << endl
         << DVector<std::complex<double>>(solver.eigenvectors().colpointer(0), op.size())
         << endl;

  } catch (Error & xcp) {
    cerr << xcp.what();
    return -1;
  }

  return 0;
}
