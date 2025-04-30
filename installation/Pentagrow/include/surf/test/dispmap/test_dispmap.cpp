
#include <surf/surfinterpolator.h>
#include <genua/xcept.h>
#include <genua/mxmesh.h>
#include <genua/dbprint.h>
#include <genua/timing.h>
#include <iostream>

using namespace std;

int main(int argc, char *argv[])
{
  if (argc < 3) {
    cerr << "Usage: " << argv[0] << " modal.zml aeromesh.zml" << endl;
    return EXIT_FAILURE;
  }

  try {

    Wallclock clk;

    MxMeshPtr pstr = boost::make_shared<MxMesh>();
    pstr->loadAny(argv[1]);

    MxMeshPtr paer = boost::make_shared<MxMesh>();
    paer->loadAny(argv[2]);

    int smoothingRing = 1;
    Real smoothingRadius = 0.01;
    Real cvthreshold = 2.0;

    SurfInterpolator ipol;
    ipol.setStructural(pstr);
    ipol.setAerodynamic(paer);
    ipol.useGalerkin(true);
    ipol.concavityThreshold( cvthreshold );
    ipol.selectiveSmoothing(-1, smoothingRing, smoothingRadius);

    clk.start();
    ipol.map();
    clk.stop();
    cout << "Field mapping: " << clk.elapsed() << endl;

    paer->writeAs( "mapped.zml", Mx::NativeFormat, 1 );

  } catch (std::runtime_error &xcp) {
    cerr << xcp.what();
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
