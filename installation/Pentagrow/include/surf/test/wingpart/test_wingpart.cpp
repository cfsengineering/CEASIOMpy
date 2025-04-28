
#include <surf/wingpart.h>
#include <surf/topology.h>
#include <surf/slavedwake.h>
#include <surf/airfoil.h>
#include <surf/linearsurf.h>
#include <surf/dcmeshcrit.h>
#include <surf/tgrefiner.h>
#include <surf/hexboxpart.h>
#include <genua/xcept.h>
#include <genua/trimesh.h>
#include <genua/configparser.h>
#include <genua/mxmesh.h>
#include <genua/dbprint.h>
#include <genua/plane.h>
#include <genua/transformation.h>
#include <iostream>

using namespace std;

bool cambered = false;

CurvePtr make_section(const Vct3 &p, Real c, Real twist = 0.0)
{
  Airfoil *paf = new Airfoil("Section");
  if (cambered)
    paf->naca(165, 65, 0.05, 0.2, 1.0);
  else
    paf->naca(165, 65, 0.05, 0.0);
  paf->closeTrailingEdge();
  paf->scale(c);
  paf->rotate(0.0, twist, 0.0);
  Vct3 shift;
  shift[2] = 0.25*c*sin(twist);
  paf->translate(p + shift);
  paf->apply();
  return CurvePtr(paf);
}

SurfacePtr make_segment(const Vct3 &p1, const Vct3 &p2,
                        Real c1, Real c2, Real tw1 = 0.0, Real tw2 = 0.0)
{
  LinearSurf *lsf = new LinearSurf("Segment");
  lsf->init(make_section(p1, c1, tw1),
            make_section(p2, c2, tw2));
  return SurfacePtr(lsf);
}

void edge_sources(const Surface &srf, DcMeshSourceCrit &crit)
{
  // trailing edge
  crit.addLineSource( srf.eval(0.0, 0.0), srf.eval(0.0, 1.0), 0.3, 3.0 );

  // leading edge
  crit.addLineSource( srf.eval(0.5, 0.0), srf.eval(0.5, 1.0), 0.2, 5.0 );
}

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
  if (argc > 1) {
    int iarg = atoi(argv[1]);
    cambered = (iarg > 0);
  }

  if (cambered)
    cout << "Generating cambered & twisted wing" << endl;
  else
    cout << "Generating symmetric wing" << endl;

  try {

    // chord lengths
    const Real lchord[3] = { 1317.3e-3 - 1034.4e-3,
                             1101.6e-3 - 473.5e-3,
                             1158.7e-3 - 191.5e-3};
    // const Vct3 offset(1699.3718e-3, 4.4466e-3, 83.3125e-3);
    const Vct3 offset(-775.55e-3, 1e-3, -25.4e-3);

    // constants
    const Real farRadius = 15.0;
    const uint farLevel = 4;

    // downstream direction for straight wake
    Vct3 udr(5.0, 0.0, 0.0);
    Vct3 tip(1.0344, 1.0344, 0.0);
    Vct3 pkn(0.4735, 0.4735, 0.0);
    Vct3 inb(0.1915, 0.1915, 0.0);
    Vct3 apx(0.1915, 0.0, 0.0);

    // apply offset already here
    tip += offset;
    pkn += offset;
    inb += offset;
    apx += offset;

    // apex point is in symmetry plane
    apx[1] = 0.0;

    // twist angles
    Real tinb = (cambered ? rad(1.5) : 0.0);
    Real tpkn = 0.0;
    Real ttip = (cambered ? rad(-2.5) : 0.0);

    // stats
    Real area = 0;

    // rigid-body rotation applied to the entire geometry
    Real rbr = rad(5.0);

    // geometry
    SurfacePtr seg1 = make_segment(tip, pkn, lchord[0], lchord[1], ttip, tpkn);
    seg1->rename("RightOutboardPanel");
    seg1->rotate(0.0, rbr, 0.0);
    seg1->apply();
    SurfacePtr wak1( new SlavedWake(seg1, udr) );
    wak1->rename("RightOutboardWake");
    area -= (pkn[1] - tip[1])*(lchord[1] + lchord[0])*0.5;

    SurfacePtr seg2 = make_segment(pkn, inb, lchord[1], lchord[2], tpkn, tinb);
    seg2->rename("RightCenterPanel");
    seg2->rotate(0.0, rbr, 0.0);
    seg2->apply();
    SurfacePtr wak2( new SlavedWake(seg2, udr) );
    wak2->rename("RightCenterWake");
    area -= (inb[1] - pkn[1])*(lchord[2] + lchord[1])*0.5;

    SurfacePtr seg3 = make_segment(inb, apx, lchord[2], lchord[2], tinb, tinb);
    seg3->rename("RightInboardPanel");
    seg3->rotate(0.0, rbr, 0.0);
    seg3->apply();
    SurfacePtr wak3( new SlavedWake(seg3, udr) );
    wak3->rename("RightInboardWake");
    area -= (apx[1] - inb[1])*(lchord[2] + lchord[2])*0.5;

    cout << "Wing area: " << area << endl;

    // mesh criterion
    DcMeshCritPtr pmc = boost::make_shared<DcMeshCrit>();
    pmc->xyzLength(0.06, 1e-4);
    //pmc->uvLength(0.2, 1e-6);
    pmc->maxNodes(100000);
    pmc->maxNormalAngle(rad(30.0));
    pmc->npass(16);
    pmc->nSkipSmooth(1);
    pmc->nSmooth(1);
    pmc->wSmooth(0.3);
    pmc->apexAngle(rad(18.), rad(112.));
    // pmc->minApexAngle( rad(15.) );
    // pmc->apexAngle(0.0, rad(135.0));
    //pmc->maxGrowthRatio(10.0);

    DcMeshCritPtr pmw = boost::make_shared<DcMeshCrit>(*pmc);
    pmw->xyzLength(0.10, 2e-4);

    WingPart part("MainWing");
    part.meshBias( 0.05, 0.2, 0.1 );
    part.meshQuality( pmc, pmw );
    part.appendSegment(seg1, wak1);
    part.appendSegment(seg2, wak2);
    part.appendSegment(seg3, wak3);

    Topology topo;
    part.inject(topo);

    // farfield box
    HexBoxPart box;
    box.boco( HexBoxPart::RightSide, Mx::BcWall );
    box.boco( HexBoxPart::TopSide, Mx::BcWall );
    box.boco( HexBoxPart::LeftSide, Mx::BcWall );
    box.boco( HexBoxPart::BottomSide, Mx::BcWall );

    DcMeshCritPtr bmc = boost::make_shared<DcMeshCrit>();
    bmc->maxNodes(16*1024);
    bmc->npass(8);
    bmc->nSkipSmooth(1);
    bmc->nSmooth(1);
    bmc->xyzLength( 1.3, 0.0 );
    bmc->apexAngle( rad(25.), rad(105.) );
    box.meshQuality(bmc);

    // box.rescale(11.0, 2.0, 2.0);
    // box.center( box.center() + Vct3(4.0, 1.0, 0.0) );
    box.rescale(20.0, 20.0, 20.0);
    box.center( box.center() + Vct3(0.0, 10.0, 0.0) );
    box.inject(topo);

    // inconvenient - cap generation requires that topo has edges meshed
    topo.meshEdges();
    part.makeFlatCaps(topo, false, true);

    // imprint left wing edge on left wind tunnel wall
    uint rootEdge = part.findWingTipEdge(topo, 1.0);
    cout << "Wing tip edge injected: " << rootEdge << endl;
    box.imprint(topo, rootEdge, HexBoxPart::LeftSide );
    uint wakeRootEdge = part.findWakeTipEdge(topo, 1.0);
    cout << "Wake edge injected: " << wakeRootEdge << endl;
    box.imprint(topo, wakeRootEdge, HexBoxPart::LeftSide );

    topo.meshFaces(false);
    topo.print();

    MxMesh mx;
    part.appendTo(topo, mx, true);
    box.appendTo(topo, mx);

    mx.mergeNodes();
    mx.dropUnusedNodes(); // vital!

    // debug
    mx.writeAs("firststep.zml", Mx::NativeFormat, 1);
    // return EXIT_SUCCESS

    mx.writeSmesh("boundaries.smesh");

    // is not manifold with wake
    // test_manifold(mx);

    //    // create mirror copies
    //    Plane ypln(Vct3(0.0,1.0,0.0), 0.0);
    //    int nsec = mx.nsections();
    //    Indices snodes;
    //    for (int i=0; i<nsec; ++i) {
    //      Indices tmp;
    //      mx.section(i).usedNodes(tmp);
    //      size_t mid = snodes.size();
    //      snodes.insert(snodes.end(), tmp.begin(), tmp.end());
    //      std::inplace_merge(snodes.begin(), snodes.begin()+mid, snodes.end());
    //    }
    //    uint voff = mx.nnodes();
    //    mx.mirrorCopyNodes(snodes, ypln);
    //    for (int i=0; i<nsec; ++i)
    //      mx.mirrorCopySection(i, voff, snodes, true);

    //    mx.mergeNodes();

    //    // generate farfield mesh
    //    Real maxtetvol;
    //    {
    //      TriMesh farfield;
    //      farfield.sphere(offset + 0.2*udr, farRadius, farLevel );
    //      Real ta = farfield.area() / farfield.nfaces();
    //      Real tl = sqrt( 4*ta / sqrt(3.0) );
    //      maxtetvol = cb(tl) / (6*sqrt(2.));
    //      cout << "Farfield edge length: " << tl << endl;
    //      cout << "Max volume: " << maxtetvol << endl;

    //      uint ffi = mx.appendSection(farfield);
    //      MxMeshBoco fbc( Mx::BcFarfield );
    //      uint sbegin = mx.section(ffi).indexOffset();
    //      uint send = sbegin + mx.section(ffi).nelements();
    //      fbc.setRange(sbegin, send);
    //      mx.appendBoco(fbc);
    //    }

    //    mx.toXml(true).write("mesh.zml", XmlElement::Lz4Compressed);

    //    //    cout << "Debug: returning before calling tetgen." << endl;
    //    //    return EXIT_SUCCESS;

    //    PointList<3> holes(1);
    //    holes[0] = apx + Vct3(0.1, 0.0, 0.0);
    //    mx.writeSmesh("boundaries.smesh", holes);

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

    ConfigParser cfg;
    cfg["TetGrowthFactor"] = "1.45";
    cfg["TetEdgeSmoothing"] = "96";
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
    tetmx.toXml(true).write("tetmesh2.zml", XmlElement::Lz4Compressed);

  } catch (Error &xcp) {
    cerr << xcp.what();
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
