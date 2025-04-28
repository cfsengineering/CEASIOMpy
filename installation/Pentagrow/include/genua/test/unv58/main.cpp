
#include <genua/forward.h>
#include <genua/timing.h>
#include <genua/xcept.h>
#include <genua/hdf5file.h>
#include <genua/unv58dataset.h>
#include <iostream>
#include <fstream>

using namespace std;

int main(int argc, char *argv[])
{

  try {

    for (int i=1; i<argc; ++i) {
      Unv58Dataset::convertFile(argv[i]);
    }

  } catch (std::exception &xcp) {
    cerr << "Exception: " << xcp.what() << endl;
    return EXIT_FAILURE;
  }


  return EXIT_SUCCESS;
}
