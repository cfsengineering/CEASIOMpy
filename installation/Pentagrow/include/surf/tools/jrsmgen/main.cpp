
#include <surf/jrstriangle/jrstrianglewrapper.h>
#include <surf/jrstriangle/jrsmeshgenerator.h>
#include <surf/patchmeshgenerator.h>
#include <surf/surface.h>
#include <surf/dcmeshcrit.h>
#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <genua/configparser.h>
#include <genua/timing.h>
#include <genua/rng.h>
#include <fstream>
#include <iostream>
#include <sstream>

using namespace std;

// simple test to check for interface errors
size_t test_jrs()
{
  const int nx = 500;
  const int ny = 100;
  const Real lx = 100;
  const Real ly = 10;
  PointList2d pts(nx*ny);
  for (int j=0; j<ny; ++j) {
    Real cy = j*ly/(ny-1);
    for (int i=0; i<nx; ++i) {
      Real cx = i*lx/(nx-1);
      pts[j*nx+i] = Vct2(cx,cy);
    }
  }

  uint sg[4];
  Indices segments;
  for (int j=1; j<ny; ++j) {
    sg[0] = (j-1)*nx + 0;
    sg[1] = (j)*nx + 0;
    sg[2] = (j-1)*nx + (nx-1);
    sg[3] = (j)*nx + (nx-1);
    segments.insert(segments.end(), std::begin(sg), std::end(sg));
  }
  for (int i=1; i<nx; ++i) {
    sg[0] = (i-1);
    sg[1] = i;
    sg[2] = (ny-1)*nx + (i-1);
    sg[3] = (ny-1)*nx + (i);
    segments.insert(segments.end(), std::begin(sg), std::end(sg));
  }

  JrsTriangleWrapper wrp;
  wrp.allocate(pts, segments);
  wrp.generate( 25.0, 0.006, false, 100*1000 );

  Indices tri;
  wrp.extract(pts, tri, segments);

  PointList3d p3;
  p3.reserve(pts.size());
  std::for_each(pts.begin(), pts.end(),
                [&](const Vct2 &p){ p3.push_back(Vct3(p[0], p[1], 0.0)); });

  MxMesh mx;
  mx.appendNodes(p3);
  mx.appendSection(Mx::Tri3, tri);
  mx.writeAs("simple.zml", Mx::NativeFormat, 1);

  return tri.size() / 3;
}

void test_invert(SurfacePtr psf)
{
  UvMapping uvmap;
  Vector up, vp;
  psf->initGridPattern(up, vp);
  uvmap.init(*psf, up, vp);

  // test inversion accuracy for random points
  const Real tol = 1e-9;
  const int np = 32;
  FloatRng rng(0.0, 1.0);
  rng.seed(3197554);
  for (int i=0; i<np; ++i) {
    Vct2 uv1( rng(), rng() );
    Vct2 st = uvmap.eval(uv1);
    Vct2 uv2 = uvmap.lookup(st);
    clog << uv1 << " Lookup error: " << uv2-uv1 << endl;
    Vct2 uv3(uv2);
    bool ok = uvmap.invert(st, uv3, tol);
    clog << " Invert error: " << uv3 - uv1 << " status " << ok << endl;
  }
}

void test_mesh1(SurfacePtr psf)
{
  JrsMeshGenerator pmg;

  DcMeshCritPtr pmc = boost::make_shared<DcMeshCrit>();
  pmc->xyzLength(0.1, 1e-4);
  pmc->apexAngle( rad(19.) );
  pmc->maxNormalAngle( rad(20.) );
  pmc->nSmooth(2);
  pmc->wSmooth(0.5);
  pmc->npass(3);

  pmg.criterion(pmc);
  pmg.initMap(psf);
  pmg.generate(PointList2d());

  MxMesh mx;
  mx.appendSection(pmg);
  mx.writeAs("mesh1.zml", Mx::NativeFormat, 1);
}

int main(int argc, char *argv[])
{
  Wallclock clk;
  clk.start();
  size_t nt = test_jrs();
  double dt = clk.stop();
  clog << "Total time " << dt << " - " << nt/dt << " tri/sec." << endl;

  if (argc > 1) {
    XmlElement xe;
    xe.read(argv[1]);
    SurfacePtr psf = Surface::createFromXml(xe);
    if (psf) {
      // test_invert(psf);
      test_mesh1(psf);
    }
  }

  return EXIT_SUCCESS;
}
