
#include <genua/timing.h>
#include <genua/mxelementtree.h>
#include <genua/xmlelement.h>
#include <genua/xcept.h>
#include <iostream>
#include <cstdlib>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    if (argc != 2) {
      cerr << "Usage: " << argv[0] << " mxmesh.zml" << endl;
      return -1;
    }

    XmlElement xe;
    xe.read(argv[1]);

    MxMeshPtr pmx(new MxMesh);
    pmx->fromXml(xe);

    Wallclock clk;

//    {
//      MxElementTree mtree;

//      clk.start("Sorting MxElementTree... ");
//      mtree.allocate(pmx, 8);
//      mtree.sort();
//      clk.stop("done. ");

//      // test nearest element search
//      const int np = 5;
//      for (int i=0; i<np; ++i) {
//        uint idx = rand() % pmx->nnodes();
//        uint inear = mtree.nearest( pmx->node(idx) );

//        uint nv, isec;
//        const uint *vi = pmx->globalElement(inear, nv, isec);
//        cout << "node " << idx << " nearest: " << inear << " vi: ";
//        for (uint j=0; j<nv; ++j)
//          cout << vi[j] << ',';
//        cout << endl;
//      }
//    }

    {
      clk.start();
      MxTriTree tree(*pmx);
      clk.stop();
      cout << "MxTriTree construction: " << clk.elapsed() << endl;

      const Indices & gni( tree.globalNodes() );
      cout << "TriTree uses " << gni.size() << " nodes." << endl;

      for (int i=0; i<8; ++i) {
        cout << "dop " << i << " diag: " << tree.dop(i).sqsize() << endl;
      }

      const int np = 10;
      for (int i=0; i<np; ++i) {
        uint idx = rand() % gni.size();
        uint inear = tree.nearestTriangle( pmx->node(gni[idx]) );
        const uint *vi = tree.vertices(inear);
        cout << "node " << gni[idx] << " dst: "
             << tree.tridist(inear, Vct3f(pmx->node(gni[idx])))
             << " nearest: " << inear << " vi: ";
        for (uint j=0; j<3; ++j)
          cout << gni[vi[j]] << ',';
        cout << endl;
      }
    }

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  return 0;
}
