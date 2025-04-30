
#include <surf/wingpart.h>
#include <surf/topology.h>
#include <surf/slavedwake.h>
#include <surf/airfoil.h>
#include <surf/linearsurf.h>
#include <surf/dcmeshcrit.h>
#include <surf/tgrefiner.h>
#include <surf/hexboxpart.h>
#include <surf/igesfile.h>
#include <genua/xcept.h>
#include <genua/trimesh.h>
#include <genua/configparser.h>
#include <genua/mxmesh.h>
#include <genua/dbprint.h>
#include <genua/plane.h>
#include <genua/transformation.h>
#include <iostream>
#include <fstream>

using namespace std;

void test_manifold(const MxMesh &mx)
{
  TriMesh msh;
  for (const auto &p : mx.nodes())
    msh.addVertex(p);
  for (size_t isec=0; isec<mx.nsections(); ++isec) {
    const MxMeshSection &sec(mx.section(isec));
    const size_t ne = sec.nelements();
    for (size_t j=0; j<ne; ++j)
      msh.addFace(sec.element(j));
  }
  msh.fixate();
  bool ok = msh.isClosedManifold();
  cout << (ok ? ("Mesh is manifold.") : ("Mesh is not watertight.")) << endl;
  if (not ok)
    abort();
}

int main(int argc, char *argv[])
{
  // Usage: airfoilmesh [airfoil.dat] [refinement] [AoA] [sweep] [twist]
  TopoFace::backend( TopoFace::DcMeshGen );

  // global refinement parameter
  Real refine = 1.0;
  if (argc > 2)
    refine = atof(argv[2]);

  // settings angle in widn tunnel
  Real AoA = 0.0;
  if (argc > 3)
    AoA = rad(atof(argv[3]));

  // sweep angle
  Real phisweep = 0.0;
  if (argc > 4)
    phisweep = rad(atof(argv[4]));

  // twist angle
  Real betatwist = 0.0;
  if (argc > 5)
    betatwist = rad(atof(argv[5]));

  // parameters
  //
  // downstream direction for straight wake
  Vct3 udr(7.0, 0.0, 0.0);
  // airfoil meshing criteria
  const Real chord = 1.0;
  const Real lmax = 0.1 / refine;
  const Real maxAngle = rad(20.) / std::sqrt(refine);
  const Real minApex = rad(18.0) * std::pow(refine, 0.25);
  const Real maxApex = rad(120.0);
  const Real boxLength = 25.0;

  // span, chord is always == 1.0
  const Real span = 1.0;
  const Real boxHeight = 25.0;

  // NACA TN-2160
  // unswept
  // const Real span = 1.75;
  // const Real boxHeight = 2.5;
  // swept
  // const Real span = 2.8284;
  //const Real boxHeight = 1.9799;

  try {

    Airfoil afp("Airfoil");
    if (argc > 1) {
      string foilname(argv[1]);
      bool is4digit = false;
      if (foilname.find('.') == string::npos) {
        int digits = genua_strtol(argv[1], 0, 10);
        if (digits > 3 and digits < 9999) {
          is4digit = true;
          cout << "Generating NACA 4-digit: " << digits << endl;
          afp.naca(digits);
        }
      }

      if (not is4digit) {
        cout << "Reading airfoil from file: " << foilname << endl;
        ifstream in(foilname);
        afp.read(in);
      }
    } else {
      cout << "Generating airfoil NACA 63-215" << endl;
      afp.naca(63, 63, 0.15, 0.2);

      ofstream os("airfoil.dat");
      afp.write(os, "NACA 63-215");
    }
    afp.closeTrailingEdge();

    // longitudinal distance of rotation center to tip LE
    // Real cdx = 0.25*chord + 0.5*span * std::sin(phisweep);

    // geometry
    AirfoilPtr cright = boost::make_shared<Airfoil>(afp);
    Real dx = 0.5*span*std::tan(phisweep);
    Real dz = 0.25*chord*std::sin(0.5*betatwist);
    cright->rotate(0.0, AoA+0.5*betatwist, 0.0);
    cright->translate(dx, span, dz);
    cright->apply();

    AirfoilPtr cleft = boost::make_shared<Airfoil>(afp);
    dx = -0.5*span*std::tan(phisweep);
    dz = 0.25*chord*std::sin(-0.5*betatwist);
    cleft->rotate(0.0, AoA-0.5*betatwist, 0.0);
    cleft->translate(dx, 0.0, dz);
    cleft->apply();

    LinearSurfPtr seg1 = boost::make_shared<LinearSurf>("AirfoilSegment");
    seg1->init(cright, cleft);

    SurfacePtr wak1;
    if (AoA != 0 or betatwist != 0) {
      Real incidence = fabs(AoA) + 0.5*fabs(betatwist);
      Real fdz = std::min( 1.0,
                           0.4*boxHeight
                         - (1.0 + 0.5*span*tan(phisweep))*tan(incidence) );
      Vct3 edgeDistance(udr[0], 0.0, -fdz);
      SlavedWake *pwak = new SlavedWake;
      pwak->initRuledBezier(seg1, edgeDistance, Vct3(1,0,0), 0.35);
      wak1.reset(pwak);
    } else {
      wak1 = boost::make_shared<SlavedWake>(seg1, udr);
    }
    wak1->rename("WingWake");

    // mesh criterion
    DcMeshCritPtr pmc = boost::make_shared<DcMeshCrit>();
    pmc->xyzLength(lmax, 1e-4);
    pmc->maxNodes(128*1024);
    pmc->maxNormalAngle(maxAngle);
    pmc->npass(16);
    pmc->nSkipSmooth(1);
    pmc->nSmooth(1);
    pmc->wSmooth(0.3);
    pmc->apexAngle(minApex, maxApex);

    DcMeshCritPtr pmw = boost::make_shared<DcMeshCrit>(*pmc);
    pmw->xyzLength(3*lmax, 1e-3);

    WingPart part("MainWing");
    part.meshBias( 0.08, 0.15, 1.0);
    part.meshQuality( pmc, pmw );
    part.appendSegment(seg1, wak1);

    {
      IgesFile igsfile;
      part.toIges(igsfile);
      igsfile.write("part.igs");
    }

    Topology topo;
    part.inject(topo);

    // farfield box
    HexBoxPart box("Farfield");
    box.boco( HexBoxPart::RightSide, Mx::BcWall );
    box.boco( HexBoxPart::TopSide, Mx::BcFarfield );
    box.boco( HexBoxPart::LeftSide, Mx::BcWall );
    box.boco( HexBoxPart::BottomSide, Mx::BcFarfield );

    DcMeshCritPtr bmc = boost::make_shared<DcMeshCrit>();
    bmc->maxNodes(16*1024);
    bmc->npass(8);
    bmc->nSkipSmooth(1);
    bmc->nSmooth(1);
    bmc->xyzLength( 0.4/refine, 0.0 );
    bmc->apexAngle( minApex, maxApex );
    box.meshQuality(bmc);

    box.rescale(boxLength, span, boxHeight);
    box.center( Vct3(0.25, 0.5*span, 0.0) + 0.25*udr );
    box.inject(topo);

    topo.meshEdges();

    // imprint edges on left/right wind tunnel walls
    uint leftEdge = part.findWingTipEdge(topo, 1.0);
    box.imprint(topo, leftEdge, HexBoxPart::LeftSide );
    uint leftWakeEdge = part.findWakeTipEdge(topo, 1.0);
    box.imprint(topo, leftWakeEdge, HexBoxPart::LeftSide );

    uint rightEdge = part.findWingTipEdge(topo, 0.0);
    box.imprint(topo, rightEdge, HexBoxPart::RightSide );
    uint rightWakeEdge = part.findWakeTipEdge(topo, 0.0);
    box.imprint(topo, rightWakeEdge, HexBoxPart::RightSide );

    topo.meshFaces(false);
    topo.print(cout);

    MxMesh mx;
    part.appendTo(topo, mx, true);
    box.appendTo(topo, mx);

    mx.mergeNodes();
    mx.dropUnusedNodes(); // vital!

    // debug
    mx.writeAs("firststep.zml", Mx::NativeFormat, 1);
    mx.writeSmesh("boundaries.smesh");

    {
      stringstream ss;
      ss.precision(4);
      ss << fixed;
      ss << "/Users/david/bin/tetgen-1.5 -pq1.5Y boundaries.smesh";
      // ss << maxtetvol << " boundaries.smesh";
      cout << "Calling: " << ss.str() << endl;
      system(ss.str().c_str());
    }

    MxMesh tetmx;
    tetmx.readTetgen("boundaries.1.");
    tetmx.toXml(true).write("tetmesh1.zml", XmlElement::Lz4Compressed);

    return EXIT_SUCCESS;

    ConfigParser cfg;
    Real growth = std::min(4.0, 1.3*std::pow(refine, -0.2));
    int smiter = 64 * std::pow(refine, 0.2);
    cout << " * TetGrowthFactor = " << growth << endl;
    cout << " * TetEdgeSmoothing = " << smiter << endl;
    cfg["TetGrowthFactor"] = str(growth);
    cfg["TetEdgeSmoothing"] = str( std::max(4, smiter) );
    cfg["TetEdgeDistrib"] = "8";
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

    // identify sections and bocos by integer tags
    for (size_t i=0; i<mx.nsections(); ++i) {
      if (i < tetmx.nsections())
        tetmx.section(i).rename( mx.section(i).name() );
    }
    for (size_t i=0; i<mx.nbocos(); ++i) {
      const MxMeshBoco &bc( mx.boco(i) );
      if (i < tetmx.nbocos()) {
        tetmx.boco(i).rename( bc.name() );
        tetmx.boco(i).bocoType( bc.bocoType() );
      }
    }

    tetmx.toXml(true).write("tetmesh2.zml", XmlElement::Lz4Compressed);

  } catch (Error &xcp) {
    cerr << xcp.what();
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
