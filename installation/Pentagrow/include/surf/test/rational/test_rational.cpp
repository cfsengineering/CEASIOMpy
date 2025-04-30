
#include <iostream>
#include <fstream>
#include <genua/xcept.h>
#include <genua/timing.h>
#include <genua/pattern.h>
#include <genua/dbprint.h>
#include <genua/trimesh.h>
#include <surf/rationalsplinecurve.h>
#include <surf/rationalsplinesurface.h>

using namespace std;

int main(int, char **)
{
  try {

    RationalSplineCurve c1("PlaneCircle");
    // c1.createCircle();
    c1.createCircle( Vct3(2.0, 1.0, 0.0), Vct3(0.0,1.0,0.0), 3.5 );

    // evaluate
    const int n = 97;
    for (int i=0; i<n; ++i) {
      Real u = Real(i) / (n-1);
      Vct3 p = c1.eval(u);
      Vct3 t = c1.derive(u, 1);
      cout << u << p << t << endl;
    }

    RationalSplineSurf s1;
    s1.createCylinder();

    // generate grid
    const int nu(20), nv(5);
    PointGrid<3> pg(nu,nv);
    for (int j=0; j<nv; ++j)
      for (int i=0; i<nu; ++i)
        pg(i,j) = s1.eval( Real(i)/(nu-1), Real(j)/(nv-1) );

    // write out grid
    TriMesh tm;
    tm.triangulate(pg);
    tm.toXml(true).write("cylinder.xml");

    // first derivatives at v = 0.25
    {
      Vct3 S, Su, Sv;
      const int n = 20;
      ofstream os("cylderiv_vconst.txt");
      for (int i=0; i<n; ++i) {
        Real u = Real(i)/(n-1);
        s1.plane(u, 0.25, S, Su, Sv);
        os << u << " ::: " << Su << " --- " << Sv << endl;
      }
    }

    // first derivatives at u = 0.25
    {
      Vct3 S, Su, Sv;
      const int n = 20;
      ofstream os("cylderiv_uconst.txt");
      for (int i=0; i<n; ++i) {
        Real v = Real(i)/(n-1);
        s1.plane(0.25, v, S, Su, Sv);
        os << v << " ::: " << Su << " --- " << Sv << endl;
      }
    }

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
