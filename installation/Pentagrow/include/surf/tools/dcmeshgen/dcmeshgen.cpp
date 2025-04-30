
#include <surf/forward.h>
#include <surf/wingpart.h>
#include <surf/basicpart.h>
#include <surf/topology.h>
#include <surf/toposegmchain.h>
#include <surf/dcmeshcrit.h>
#include <surf/tgrefiner.h>
#include <surf/sides.h>
#include <surf/tgrefiner.h>
#include <surf/slavedwake.h>
#include <surf/curve.h>
#include <surf/linearsurf.h>
#include <genua/xcept.h>
#include <genua/configparser.h>
#include <genua/mxmesh.h>
#include <genua/trimesh.h>
#include <genua/dbprint.h>
#include <genua/timing.h>
#include <iostream>
#include <fstream>

using namespace std;

void test_wakegeometry(const XmlElement &xe)
{
  // first stage: test TE/FSL intersection estimate
  SurfacePtr pwing, pfsl;
  for (const XmlElement &xpart : xe) {
    if (xpart.attribute("name", "") == "MainWing")
      pwing = Surface::createFromXml(xpart);
    else if (xpart.attribute("name", "") == "Fuselage")
      pfsl = Surface::createFromXml(xpart);
  }
  if (pwing == nullptr) {
    cout << "No wing surface in file." << endl;
    return;
  } else if (pfsl == nullptr) {
    cout << "No fuselage in file." << endl;
    return;
  }

  Vct3 qi = SlavedWake::findIntersection(pwing, pfsl, 0.0, 0.5);
  cout << "Intersection located at (u,v,t) = " << qi << endl;
  cout << "  location " << pfsl->eval(qi[0], qi[1]) << endl;

  Vct3 anchor = pwing->eval(0.0, 0.5);
  Vct3 edgeDistance(36.0, 0.0, 0.0), farTangent(1.0, 0.0, 0.0);
  CurvePtr gc = SlavedWake::guideCurve(pfsl, Vct2(qi[0], qi[1]),
                                       anchor, edgeDistance, farTangent);

  const int np = 200;
  PointList3d pts(np);
  cout << "Guide curve:" << endl;
  for (int i=0; i<np; ++i) {
    pts[i] = gc->eval( Real(i)/(np-1) );
    cout << pts[i] << endl;
  }

  MxMesh mx;
  uint isec = mx.appendSection(pts);
  mx.section(isec).rename("GuideCurve");

  // generate Bezier segments at left and right tip
  CurvePtr right = SlavedWake::cubicGuide(pwing, 0.0, edgeDistance, farTangent);
  CurvePtr left = SlavedWake::cubicGuide(pwing, 1.0, edgeDistance, farTangent);

  LinearSurfPtr wplus = boost::make_shared<LinearSurf>("ThroughWake");
  wplus->init(CurvePtrArray({right, gc, left}));

  SlavedWake wake(pwing, wplus);
  const int nu = 64;
  const int nv = 65;
  PointGrid<3> grid(nu,nv);
  for (int j=0; j<nv; ++j)
    for (int i=0; i<nu; ++i)
      grid(i,j) = wake.eval(Real(i)/(nu-1), Real(j)/(nv-1));
  isec = mx.appendSection(grid);
  mx.section(isec).rename("ThroughWake");
  mx.writeAs("guidedwake.zml", Mx::NativeFormat, 1);
}

int main(int argc, char *argv[])
{
  Wallclock clk;

  if (argc < 2) {
    cerr << "Usage: " << argv[0] << " rawsurfaces.xml [settings.cfg]" << endl;
    return EXIT_FAILURE;
  }

  try {

    ConfigParser cfg;
    cfg["RelativeWakeLength"] = "3.0";
    cfg["TetGrowthFactor"] = "1.4";
    cfg["TetEdgeSmoothing"] = "64";
    cfg["TetEdgeDistrib"] = "8";

    if (argc > 2) {
      ifstream in(argv[2]);
      cfg.read(in);
    }

    TopoFace::backend( TopoFace::JrsTriangle );

    Topology topo;
    TopoPartArray parts;

    XmlElement xe;
    xe.read(argv[1]);
    if (xe.name() != "SurfaceCollection") {
      throw Error("Expected an XML file containing a SurfaceCollection.");
    } else {

      // test_wakegeometry(xe);
      // return EXIT_SUCCESS;

      SurfaceArray bodies;
      for (const XmlElement &xpart : xe) {

        // isolated SkinSurf (not inside a StitchedSurf) is taken to
        // be a plain body (no wake); everything else is a wing surface

        if (xpart.name() == "SkinSurf") {
          BasicPartPtr part = boost::make_shared<BasicPart>("Body");
          part->configure(cfg);
          part->meshBias(0.25, 0.25);
          part->importLegacy(xpart);
          parts.push_back(part);
          bodies.push_back( part->mainSurface() );
        } else {
          WingPartPtr part = boost::make_shared<WingPart>("Wing");
          part->configure(cfg);
          part->importLegacy(xpart);
          parts.push_back(part);
        }
      }

      // redefine wake segments, assemble topology
      for (const TopoPartPtr &tpp : parts) {
        WingPartPtr wpp = boost::dynamic_pointer_cast<WingPart>(tpp);
        if (wpp)
          wpp->createAttachedWakes(bodies);
        tpp->inject(topo);
      }
    }

    cout << "Meshing edges..." << endl;
    topo.meshEdges();

    cout << "Generating caps..." << endl;
    for (TopoPartPtr &p : parts)
      p->makeLegacyCaps(topo);

    cout << "Meshing faces..." << endl;
    topo.meshFaces();

    {
      ofstream tos("topo_pre.txt");
      topo.print(tos);
    }

    // intersections
    clk.start();
    TopoSegmChain chains;
    int nchain = chains.extractTopology(topo);
    clk.stop();
    cout << "Intersections: " << clk.elapsed() << endl;

    // edges (0,nepre] are topological, not intersection edges
    uint nepre = topo.nedges();
    for (int j=0; j<nchain; ++j)
      chains.generateEdge(topo, j);

    // edges (nepre,nepost] are intersections
    uint nepost = topo.nedges();

    dbprint(nepost-nepre," intersection edges,",nepre,"topological edges.");

    {
      ofstream tos("topo_post.txt");
      topo.print(tos);
    }

    for (uint i=0; i<nepre; ++i)
      for (uint j=nepre; j<nepost; ++j)
        topo.edge(i).injectIntersections(topo, topo.edge(j));

    cout << "Meshing intersection edges..." << endl;
    for (uint i=nepre; i<nepost; ++i)
      topo.edge(i).discretize(topo);

    cout << "Meshing faces..." << endl;
    topo.meshFaces(false);

    cout << "Joining face meshes" << endl;
    MxMesh tmx;
    for (TopoPartPtr &p : parts)
      p->appendTo(topo, tmx, true);
    tmx.mergeNodes();
    tmx.dropUnusedNodes();
    tmx.dropDegenerateElements();
    tmx.writeAs("final.zml", Mx::NativeFormat, 1);

    PointList3d holes;
    {
      TriMeshPtr trp = tmx.toTriMesh();
//      const size_t ne = trp->nedges();
//      for (size_t i=0; i<ne; ++i) {
//        if (trp->edegree(i) < 2) {
//          const Vct3 & pop = trp->vertex( trp->edge(i).source() );
//          cout << "[w] Open boundary near " << pop << endl;
//        }
//      }
      trp->findInternalPoints(holes);
    }

    // bounding box used to construct farfield
    Vct3 bblo, bbhi;
    tmx.nodes().bounds(bblo, bbhi);

    TriMesh farf;
    farf.sphere(0.5*(bblo+bbhi), 3*norm(bbhi-bblo), 4);
    uint fsec = tmx.appendSection(farf);
    tmx.section(fsec).rename("Farfield");
    tmx.writeAs("surfaces.zml", Mx::NativeFormat, 1);

    tmx.writeSmesh("boundaries.smesh", holes);

    // bail out
    return EXIT_FAILURE;

    {
      stringstream ss;
      ss.precision(4);
      ss << fixed;
      ss << "/Users/david/bin/tetgen-1.5 -pq1.5Y boundaries.smesh";
      cout << "Calling: " << ss.str() << endl;
      system(ss.str().c_str());
    }

    MxMesh tetmx;
    tetmx.readTetgen("boundaries.1.");
    tetmx.writeAs("tetmesh1.zml", Mx::NativeFormat, 1);

    TgRefiner tgr;
    tgr.configure(cfg);
    tgr.edgeLengths(tetmx);
    tgr.writeMetricFile("boundaries.1.mtr");

    {
      stringstream ss;
      ss.precision(4);
      ss << fixed;
      ss << "/Users/david/bin/tetgen-1.5 -rqmYS1000000 boundaries.1";
      cout << "Calling: " << ss.str() << endl;
      system(ss.str().c_str());
    }

    tetmx.clear();
    tetmx.readTetgen("boundaries.2.");
    tetmx.writeAs("tetmesh2.zml", Mx::NativeFormat, 1);

    //    clk.start();
    //    TopoSegmChain chains;
    //    int nchain = chains.extractTopology(topo);
    //    clk.stop();
    //    cout << "Intersections: " << clk.elapsed() << endl;

    //    // edges (0,nepre] are topological, not intersection edges
    //    uint nepre = topo.nedges();
    //    for (int j=0; j<nchain; ++j)
    //      chains.generateEdge(topo, j);

    //    // edges (nepre,nepost] are intersections
    //    uint nepost = topo.nedges();

    //    dbprint(nepost-nepre," intersection edges,",nepre,"topological edges.");

    //    {
    //      ofstream tos("topo_post.txt");
    //      topo.print(tos);
    //    }

    //    //    for (uint i=0; i<nepre; ++i)
    //    //      for (uint j=nepre; j<nepost; ++j)
    //    //        topo.edge(i).injectIntersections(topo, topo.edge(j));

    //    MxMesh tmx;
    //    topo.toMx(tmx);
    //    tmx.toXml(true).zwrite("intersections.zml");

    //    // edge intersections are prescribed - no need to split
    //    topo.meshEdges();
    //    topo.meshFaces(false);

    //    tmx.clear();
    //    topo.toMx(tmx);
    //    tmx.toXml(true).zwrite("final.zml");

  } catch (Error &xcp) {
    cerr << "Error: " << endl;
    cerr << xcp.what() << endl;
    return EXIT_FAILURE;
  } catch (std::exception &xcp) {
    cerr << "std::exception: " << endl;
    cerr << xcp.what() << endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
