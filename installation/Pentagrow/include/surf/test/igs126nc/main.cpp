
#include <surf/igesfile.h>
#include <surf/polysplinecurve.h>
#include <fstream>
#include <exception>
#include <iostream>
#include <string>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    if (argc < 2) {
      cerr << "Usage: iges2nc file.igs [output.mpf]" << endl;
      cerr << "  Generates 3-axis g-code for spline entities (126) in" << endl;
      cerr << "  file.igs and write BSPLINE blocks to output.mpf.";
      return EXIT_FAILURE;
    }

    IgesFile ifile;
    ifile.read(argv[1]);

    std::string outfile("out.mpf");
    if (argc > 2)
      outfile = argv[2];
    std::ofstream os(outfile);
    os.precision(7);
    IgesDirEntry entry;
    const int ndir = ifile.nDirEntries();
    for (int i=0; i<ndir; ++i) {
      ifile.dirEntry(2*i+1, entry);
      if (entry.etype == 126) {
        PolySplineCurve spl;
        if (spl.fromIges(ifile, entry)) {
          int p = spl.basis().degree();
          if (p < 4)
            spl.writeGCode(os);
          else
            cout << "Entity " << 2*i+1 << " at " << entry.pdata
                 << "P, has degree " << p << " > 3" << endl;
        }
      }
    }

  } catch (const std::exception &xcp) {
    cerr << xcp.what() << endl;
  }
  return EXIT_SUCCESS;
}
