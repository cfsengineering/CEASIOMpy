
#include <genua/xcept.h>
#include <genua/pattern.h>
#include <surf/wakesurf.h>
#include <surf/airfoil.h>
#include <fstream>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    if (argc < 3) {
      cerr << "Usage: " << argv[0] << " t/c xtcmax [cli]" << endl;
      return -2;
    }

    Real tcmax, xtcmax(0.5), cli(0.5);
    if (argc > 1)
      tcmax = atof(argv[1]);
    if (argc > 2)
      xtcmax = atof(argv[2]);
    if (argc > 3)
      cli = atof(argv[3]);

    Airfoil af;
    af.naca16(tcmax, xtcmax, cli);

    ofstream os("naca16.txt");
    af.write(os);


  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
