
#include <surf/basicpart.h>
#include <surf/topology.h>
#include <surf/dcmeshcrit.h>
#include <surf/tgrefiner.h>
#include <surf/sides.h>
#include <genua/xcept.h>
#include <genua/mxmesh.h>
#include <genua/dbprint.h>
#include <iostream>

using namespace std;

void mesh_part(const XmlElement &xe)
{
  BasicPart part("Body");
  part.meshBias(0.4, 0.2);
  part.importLegacy(xe);

  Topology topo;
  cout << "Injecting topology..." << endl;
  part.inject(topo);

  cout << "Meshing edges..." << endl;
  topo.meshEdges();

  cout << "Generating caps..." << endl;
  part.makeLegacyCaps(topo);

  // part.makeRoundedCap(topo, south, 1.0);
  // part.makeRoundedCap(topo, north, 1.0);

  // part.makeFlatCap(topo, south);
  // part.makeFlatCap(topo, north);

  topo.print();

  cout << "Meshing faces..." << endl;
  topo.meshFaces();

  cout << "Mesh output..." << endl;
  MxMesh mx;
  part.appendTo(topo, mx, true);

  mx.writeAs(part.name(), Mx::NativeFormat, 1);
}

int main(int argc, char *argv[])
{
  if (argc < 2) {
    cerr << "Usage: " << argv[0] << " rawsurfaces.xml" << endl;
    return EXIT_FAILURE;
  }

  try {

    XmlElement xe;
    xe.read(argv[1]);
    if (xe.name() != "SurfaceCollection") {
      mesh_part(xe);
    } else {
      XmlElement::const_iterator itr, last = xe.end();
      for (itr = xe.begin(); itr != last; ++itr) {
        if (itr->name() == "SkinSurf") {
          mesh_part(*itr);
        }
      }
    }

  } catch (Error &xcp) {
    cerr << xcp.what();
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
