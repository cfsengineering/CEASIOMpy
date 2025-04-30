
#include <genua/surfacestreamlines.h>
#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <iostream>
#include <fstream>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    if (argc < 4) {
      cerr << "Usage: " << argv[0] <<
              " meshfile field basename [nlines]" << endl;
      return EXIT_FAILURE;
    }

    int n = 100;
    if (argc > 4)
      n = atoi(argv[4]);

    MxMesh mx;
    bool loaded = mx.loadAny(argv[1]);
    if (not loaded)
      throw Error(string("Could not load data from '") + argv[1] +
                         "' - format unknown.");

    uint ifield = mx.findField(argv[2]);
    if (ifield == NotFound)
      throw Error(string("Field not found: ")+argv[2]);

    string baseName(argv[3]);

    SurfaceStreamlines ssl;
    ssl.surfacesFromMesh(mx);
    ssl.extractField( mx.field(ifield) );
    ssl.writeRandomLines(n, baseName);
    ssl.appendRandomLines(mx, n, baseName);

    mx.writeAs("output.zml", Mx::NativeFormat, 1);

  } catch (Error &xcp) {
    cerr << xcp.what() << endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;

  return 0;
}
