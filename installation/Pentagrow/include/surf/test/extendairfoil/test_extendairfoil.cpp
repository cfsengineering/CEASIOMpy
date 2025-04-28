
#include <surf/airfoil.h>
#include <iostream>
#include <fstream>

using namespace std;

int main(int argc, char *argv[])
{
  if (argc < 3) {
    cerr << "Usage: " << argv[0] << " airfoil.txt xn [yn] [xt] [yt]" << endl;
    return EXIT_FAILURE;
  }

  Real xn(0.0), yn(0.0);
  Real xt(0.0), yt(0.0);
  xn = strtod(argv[2], nullptr);
  if (argc > 3)
    yn = strtod(argv[3], nullptr);
  if (argc > 4)
    xt = strtod(argv[4], nullptr);
  if (argc > 5)
    yt = strtod(argv[5], nullptr);

  try {

    ifstream in(argv[1]);

    Airfoil af("Airfoil");
    af.read(in);
    af.extend(xn, yn, xt, yt);

    ofstream out("modified.txt");
    af.write(out);

  } catch (Error &xcp) {
    cerr << xcp.what();
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
