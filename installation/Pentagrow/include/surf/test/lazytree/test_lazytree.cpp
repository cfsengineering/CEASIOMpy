
#include <surf/topology.h>
#include <surf/lazyisectree.h>
#include <surf/surface.h>
#include <surf/dcmeshcrit.h>
#include <surf/topoisecsegment.h>
#include <surf/toposegmchain.h>
#include <genua/xcept.h>
#include <genua/xmlelement.h>
#include <genua/mxmesh.h>
#include <genua/timing.h>
#include <fstream>
#include <iostream>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    if (argc < 2) {
      cerr << "Usage: " << argv[0] << " surfaces.xml" << endl;
      return -1;
    }

    // mesh quality criterion for main surfaces
    DcMeshCritPtr pmc = boost::make_shared<DcMeshCrit>();
    pmc->maxNormalAngle( rad(18.) );
    pmc->xyzLength( 0.15, 1e-3 );
    pmc->uvLength( 0.1, 1e-4 );
    pmc->npass( 16 );
    pmc->nSmooth( 4 );

    // mesh quality criterion for flat caps
    DcMeshCritPtr pmcap = boost::make_shared<DcMeshCrit>();
    // pmcap->minApexAngle( rad(10.) );
    pmcap->xyzLength( 0.15, 1e-3 );
    pmcap->uvLength( 0.2, 0.02 );
    pmcap->npass( 8 );
    pmcap->nSmooth( 2 );

    Topology topo;
    {
      XmlElement xe;
      xe.read(argv[1]);

      XmlElement::const_iterator itr, last = xe.end();
      for (itr = xe.begin(); itr != last; ++itr) {
        SurfacePtr psf = Surface::createFromXml( *itr );
        if (psf) {
          bool uperiodic = sq(psf->eval(0.0,0.5) - psf->eval(1.0,0.5)) < gmepsilon;
          cout << "Created surface: " << psf->name()
               << " uperiodic: " << (uperiodic ? "yes" : "no") << endl;
          uint iface = topo.appendFace(psf, uperiodic, false);
          topo.face(iface).criterion(pmc);
        }
      }
    }

    MxMesh mx;
    Wallclock clk;

    clk.start();
    topo.meshEdges();
    clk.stop();
    cout << "Edge meshing: " << clk.elapsed() << endl;

    // generate caps
    int nf = topo.nfaces();
    for (int iface=0; iface<nf; ++iface) {
      cout << "Plane cap for " << topo.face(iface).surface()->name() << endl;
      uint ibv0 = topo.face(iface).findConnection(topo,
                                                  Vct2(0.0,0.0), Vct2(1.0,0.0));
      uint icap = NotFound;
      if (ibv0 != NotFound)
        icap = topo.fillPlaneBoundary(ibv0);

      if (icap != NotFound)
        topo.face(icap).criterion( pmcap );

      uint ibv1 = topo.face(iface).findConnection(topo,
                                                  Vct2(0.0,1.0), Vct2(1.0,1.0));
      icap = NotFound;
      if (ibv1 != NotFound)
        icap = topo.fillPlaneBoundary(ibv1);

      if (icap != NotFound)
        topo.face(icap).criterion( pmcap );
    }

    topo.print();

    TriMesh globMesh;
    clk.start();
    topo.meshFaces();
    topo.mergeFaceMeshes(globMesh);
    clk.stop();
    cout << "Face meshing: " << clk.elapsed() << endl;
    cout << globMesh.nfaces() << " triangles." << endl;

    mx.appendSection(globMesh);

    clk.start();
    TopoSegmChain chains;
    int nchain = chains.extractTopology(topo);
    clk.stop();
    cout << "Intersections: " << clk.elapsed() << endl;

    for (int j=0; j<nchain; ++j)
      chains.generateEdge(topo, j);

    MxMesh tmx;
    topo.toMx(tmx);
    tmx.toXml(true).zwrite("intersections.zml");

    topo.meshEdges();
    topo.meshFaces();

    tmx.clear();
    topo.toMx(tmx);
    tmx.toXml(true).zwrite("final.zml");

    // topo.meshEdges();
    // for (uint i=0; i<topo.nfaces(); ++i)
    //  topo.face(i).splitBoundaries(topo);

//    // run the entire mesh generation process once more, with intersection edges
//    globMesh.clear();
//    topo.meshEdges();
//    topo.meshFaces();
//    topo.mergeFaceMeshes(globMesh);

//    // MxMesh tmx;
//    tmx.clear();
//    topo.toMx(tmx);
//    tmx.toXml(true).zwrite("imprinted.zml");

//    for (uint i=0; i<topo.nfaces(); ++i) {
//      const TopoFace & tface( topo.face(i) );
//      tface.uvDump( topo, tface.surface()->name() + "_uvtopo.zml" );
//    }


  } catch (Error & xcp) {
    cerr << xcp.what();
    return 1;
  }

  return 0;
}
