
#include "../pentagrow/frontend.h"
#include <surf/pentagrow.h>
#include <genua/configparser.h>
#include <genua/timing.h>
#include <nlopt.hpp>
#include <iostream>

using namespace std;

//// debug constraint function
//void test_inversion_constraint()
//{
//  Vct3 u[2] = { Vct3( 2.3, 1.2, -7.3 ), Vct3( 2.3, 1.3, -7.2 ) };
//  Vct3 v[2] = { Vct3( 0.0, -3.4, -1.1), Vct3( 0.1, -3.3, -1.0 ) };

//  Vct3 fu, fv;
//  double f0 = penta_inv_gradient(u, v, fu, fv);

//  cout << "Initial constraint value: " << f0 << endl;

//  Vct3 uh[2] = {u[0], u[1]};
//  Vct3 vh[2] = {v[0], v[1]};
//  Vct3 gu, gv;
//  Real h = 1e-4;
//  for (int k=0; k<3; ++k) {
//    Vct3 du, dv;
//    dv[k] = h;
//    uh[1] = u[1] + du;
//    vh[1] = v[1] + dv;
//    double dfg = dot(fu,du) + dot(fv,dv);
//    double fh = penta_inv_gradient(uh, vh, gu, gv);
//    cout << k << "-perturbation: " << (fh -f0) << " grad: " << dfg << endl;
//  }
//}

//// debug objective function
//void test_quality_objective()
//{
//  Vct3 nf(0.1, 0.2, 1.0);
//  normalize(nf);
//  Vct3 ds[3] = { Vct3( -0.7, -0.34, 1.1),
//                 Vct3( 0.1, 0.33, 1.5 ),
//                 Vct3( -0.5,  0.3, 1.2) };

//  Vct3 fs[3];
//  double f0 = penta_quality_objective(nf, ds, fs);

//  cout << "Initial objective value: " << f0 << endl;

//  Vct3 gs[3];
//  Real h = 1e-4;
//  for (int k=0; k<3; ++k) {
//    Vct3 sh[3] = {ds[0], ds[1], ds[2]};
//    for (int j=0; j<3; ++j) {
//      sh[k] = ds[k];
//      sh[k][j] += h;
//      double dfg = fs[k][j]*h;
//      double fh = penta_quality_objective(nf, sh, gs);
//      cout << k << "," << j << "-perturbation: "
//           << (fh-f0) << " grad: " << dfg << endl;
//    }
//  }
//}

int main(int argc, char *argv[])
{
  //  test_quality_objective();
  //  return EXIT_SUCCESS;

  try {

    if (argc != 3) {
      cerr << argv[0] << " wallmesh[.msh|.stl|.cgns|.zml] config.cfg" << endl;
      return -2;
    }

    FrontEnd front(argc, argv);
    front.generateBoundaries( argv[1] );

    // debugging
    PentaGrow & pg( front.meshGenerator() );

    const size_t nv =3*pg.nWallNodes();
    std::vector<double> x(nv), lb(nv), ub(nv);
    pg.initializeBounds(&x[0], &lb[0], &ub[0]);

    // modify so that intersection constraint is nonzero
    for (int i=0; i<1024; ++i) {
      size_t k = rand() % pg.nWallNodes();
      x[3*k+2] = -6e-3;
    }

    // verify global gradient
    std::vector<double> xh(x), fg(nv, 0);
    double f0 = pg.intersectionConstraint(&xh[0], &fg[0]);

    const double h(1e-4);
    cout << "Verification: " << endl;

    int nprint = 0;
    while (nprint < 20) {
      xh = x;
      size_t k = size_t(rand()) % nv;
      if (fg[k] == 0)
        continue;
      xh[k] += h;
      double fh = pg.intersectionConstraint(&xh[0], nullptr);
      if (fg[k] == 0 and fh == f0)
        continue;
      cout << k << " df/h = " << (fh - f0)/h
           << " grad(f) = " << fg[k] << endl;
      ++nprint;
    }

    return EXIT_SUCCESS;

    try {

      pg.optimizeEnvelope();
      pg.writeShell( "optimized.zml" );

    } catch (std::exception &e) {
      cerr << "NLOPT exception:" << endl << e.what() << endl;
      return -3;
    } catch (Error & xcp) {
      cerr << xcp.what() << endl;
      return -3;
    }

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  } catch (std::bad_alloc &) {
    cerr << "Out of memory. " << endl;
    return -1;
  }

  return EXIT_SUCCESS;
}
