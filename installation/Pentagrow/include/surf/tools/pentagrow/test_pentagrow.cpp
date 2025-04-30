
#include "frontend.h"

#include <genua/programversion.h>
#include <iostream>

// version string
#define PG_VERSION           _UINT_VERSION(1, 6, 2)
#define pentagrow_version    version_string(PG_VERSION)

using namespace std;

int main(int argc, char *argv[])
{
  cout << "This is pentagrow " << pentagrow_version
       << ", compiled " << __DATE__ << endl;

  try {

    if (argc < 2 or argc > 3) {
      cerr << argv[0] << " wallmesh[.msh|.stl|.cgns|.zml] [config.cfg]" << endl;
      return -2;
    }

    FrontEnd front(argc, argv);
    front.run(argv[1]);

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  } catch (std::bad_alloc &) {
    cerr << "Out of memory. " << endl;
    return -1;
  }

  return 0;
}
