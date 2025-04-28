
#include <genua/forward.h>
#include <genua/timing.h>
#include <genua/rng.h>
#include <genua/trnlsp.h>
#include <iostream>

using namespace std;

struct Powell {

  void eval(const Vector &x, Vector &f)
  {
    const int n = x.size();
    if (f.size() != n)
      f.allocate(n);
    for (int i = 0; i < n / 4; i++) {
      f[4 * i] = x[4 * i] + 10.0 * x[4 * i + 1];
      f[4 * i + 1] = 2.2360679774998 * (x[4 * i + 2] - x[4 * i + 3]);
      f[4 * i + 2] = (x[4 * i + 1] - 2.0 * x[4 * i + 2]) *
                     (x[4 * i + 1] - 2.0 * x[4 * i + 2]);
      f[4 * i + 3] = 3.1622776601684 * (x[4 * i] - x[4 * i + 3]) *
                     (x[4 * i] - x[4 * i + 3]);
    }
    ++neval;
  }

  void jacobian(const Vector &x, Matrix &jac)
  {
    const int n = x.size();

    Vector xh = x;
    Vector fo(n), fh(n);
    eval(x, fo);
    double h = 1e-5;
    for (int i=0; i<n; ++i) {
      xh = x;
      xh[i] += h;
      eval(xh, fh);
      for (int j=0; j<n; ++j)
        jac(j,i) = (fh[j] - fo[j]) / h;
    }
    ++njac;
  }

  void xjacobian(const Vector &x, Matrix &jac)
  {
    const int n = x.size();
    if (jac.nrows() != n or jac.ncols() != n)
      jac.resize(n, n);
    else
      jac = 0;
    for (int i = 0; i < n / 4; i++) {
      jac(4 * i, 4*i) = 1.0;
      jac(4 * i, 4*i+1) = x[4 * i + 1];
      jac(4*i+1, 4 * i + 2) =  2.2360679774998;
      jac(4*i+1, 4 * i + 3) = -2.2360679774998;
      jac(4*i+2, 4*i+1) = 2*(x[4 * i + 1] - 2.0 * x[4 * i + 2]);
      jac(4*i+2, 4*i+2) = -4*(x[4 * i + 1] - 2.0 * x[4 * i + 2]);
      jac(4*i+3, 4*i) = 2*3.1622776601684 * (x[4 * i] - x[4 * i + 3]);
      jac(4*i+3, 4*i+3) = -2*3.1622776601684 * (x[4 * i] - x[4 * i + 3]);
    }
    ++njac;
  }

  int neval = 0;
  int njac = 0;
};

int main(int argc, char *argv[])
{
  Wallclock clk;

  int n = 4*3;
  Vector x(n), xlo(n), xup(n), f(n);
  xlo = -20.0;
  xup = 50.0;

  FloatRng rng(0.0, 1.0);
  std::generate(x.begin(), x.end(), rng);

  mkl::DTrustRegionSolver solver(n, n);
  solver.bounds(xlo, xup);
  solver.initialRadius( norm(x) );
  solver.convergence(1e-3);

  Powell p;
  int stat = solver.solve(p, x);
  cout << "Status: " << stat << endl;
  cout << "Solution: " << x << endl;
  cout << "Evaluations: " << p.neval << " Jac: " << p.njac << endl;

  p.eval(x, f);
  cout << "Value: " << f << endl;
  cout << "|f| = " << norm(f) << endl;

  return EXIT_SUCCESS;

}
