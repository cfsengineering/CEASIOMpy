
#include <surf/airfoil.h>
#include <surf/airfoilfitter.h>
#include <genua/pattern.h>

#include <iostream>
#include <fstream>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    // generate known airfoil to match
    const int nseg = 256;
    Vector t;
    PointList<3> segm(2*nseg);
    {
      Airfoil test("test");

      if (argc > 1)
        test.read( argv[1] );
      else
        test.naca(65, 65, 0.05, 0.5);

      // test scaling and rotation
      test.rotate(0.0, rad(3.5), 0.0);
      test.scale(3.0);
      test.apply();

      // write reference output
      {
        ofstream os("reference.txt");
        const PointList<2> &pts( test.sectionCoordinates() );
        for (uint i=0; i<pts.size(); ++i)
          os << pts[i] << endl;
      }

      airfoil_pattern(nseg+1, test.findLeadingEdge(), 1.2, 1.01, t);
      for (int i=0; i<nseg; ++i) {
        segm[2*i+0] = test.eval( t[i] );
        segm[2*i+1] = test.eval( t[i+1] );
      }

      // reshuffle segments
      for (int i=0; i<nseg/4; ++i) {
        uint a = rand() % nseg;
        uint b = rand() % nseg;
        if (a == b)
          continue;
        uint as = 2*a+0;
        uint at = 2*a+1;
        uint bs = 2*b+0;
        uint bt = 2*b+1;
        swap( segm[as], segm[bs] );
        swap( segm[at], segm[bt] );
      }
    }

    // write input for fitter
    {
      ofstream os("segments.txt");
      for (int i=0; i<2*nseg; ++i)
        os << segm[i] << endl;
    }

    AirfoilFitter fitter;
    fitter.principalDirections( Vct3(1.0, 0.0, 0.0), Vct3(0.0, 1.0, 0.0) );
    AirfoilPtr afp = fitter.fitSegments(segm);

    Vct3 rot;
    fitter.rotation(rot);
    cout << "Rotation: " << deg(rot) << endl;
    afp->scale( fitter.chord() );
    afp->rotate(rot[0], rot[1], rot[2]);
    afp->translate( fitter.origin() );
    afp->apply();

    // write output for comparison
    {
      ofstream os("fitted_xyz.txt");
      for (uint i=0; i<t.size(); ++i)
        os << afp->eval(t[i]) << endl;
    }

    {
      const PointList<2> & crd( afp->sectionCoordinates() );
      ofstream os("fitted_xy.txt");
      for (uint i=0; i<crd.size(); ++i)
        os << crd << endl;
    }

    // test reparametrization
    Vector uap;
    int nap = 64;
    afp->adaptiveParam(nap, uap);

    // evaluate points at uap
    {
      ofstream os("adaptive.txt");
      for (int i=0; i<nap; ++i)
        os << afp->eval(uap[i]) << endl;
    }

    Airfoil axp("Approx64", afp->sectionCoordinates(), nap);
    axp.scale( fitter.chord() );
    axp.rotate(rot[0], rot[1], rot[2]);
    axp.translate( fitter.origin() );
    axp.apply();

    // evaluate points at uap
    {
      ofstream os("remapped.txt");
      for (int i=0; i<nap; ++i)
        os << axp.eval(uap[i]) << endl;
    }


  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
