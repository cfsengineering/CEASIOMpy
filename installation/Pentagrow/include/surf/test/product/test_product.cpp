
#include <iostream>
#include <fstream>
#include <genua/xcept.h>
#include <genua/timing.h>
#include <genua/cgmesh.h>
#include <genua/trimesh.h>
#include <surf/igesfile.h>
#include <surf/stepfile.h>
#include <surf/product.h>
#include <genua/mxmesh.h>

using namespace std;

int main(int argc, char *argv[])
{

  try {

    if (argc > 3 or argc < 2) {
      cerr << argv[0] << " testfile.igs maxktri" << endl;
      return -2;
    }

    IgesFile ifile;
    StepFile sfile;

    string fname(argv[1]);
    string lname = toLower(fname);
    bool isIges =  (lname.find(".igs") != string::npos)
                or (lname.find(".iges") != string::npos);
    bool isStep = (lname.find(".stp") != string::npos)
                  or (lname.find(".step") != string::npos);

    if ((not isIges) and (not isStep)) {
      cerr << "File format not recognized." << endl;
      return -3;
    }

    Wallclock c;
    c.start("Reading file... ");
    if (isIges)
      ifile.read(fname);
    else if (isStep)
      sfile.read(fname);
    c.stop("done. ");

    c.start("Constructing surfaces...");
    Product prod;
    if (isIges)
      prod.fromIges(ifile, IgesEntity::SurfaceClass|IgesEntity::StructureClass);
    else
      prod.fromStep(sfile);
    c.stop("done. ");

    uint maxtri = 4000000;
    if (argc > 2) {
      maxtri = 1000*atol(argv[2]);
      cout << "Limit: " << maxtri << " triangles. " << endl;
    }

    c.start("Tessellation...");
    uint ntri = prod.tessellate(maxtri);
    c.stop("done.");
    cout << ntri << " triangles." << endl;

    c.start("Collapsing mesh...");
    prod.collapseMesh();
    c.stop("done.");

//    //if (isStep) {
//      c.start("Collapsing...");
//      prod.collapseMesh();
//      cout << "Root node: " << prod.rootNode()->cgRep()->ntriangles() << endl;
//      c.stop("done.");
//    //}

    // prod.print();
    prod.toXml(true).zwrite("cgmeshes.zml");

    // convert to mx
    MxMesh mx;
    prod.toMx(mx);
    mx.toXml(true).zwrite("imported.zml");

    cout << ntri/1000 << "k triangles." << endl;

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
