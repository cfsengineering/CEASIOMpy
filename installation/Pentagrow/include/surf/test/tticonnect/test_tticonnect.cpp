
#include <surf/tticonnection.h>
#include <surf/airfoil.h>
#include <surf/linearsurf.h>
#include <surf/dnwingcriterion.h>
#include <surf/meshcomponent.h>
#include <surf/meshgenerator.h>
#include <iostream>

using namespace std;

MeshComponentPtr initComponent(SurfacePtr sfp,
                              DnRefineCriterionPtr rfc)
{
  MeshComponentPtr mcp(new MeshComponent(sfp, rfc));
  PointGrid<2> pgi;
  sfp->initGrid(rfc->maxLength(), rfc->minLength(), rfc->maxPhi(), pgi);
  mcp->premesh(pgi);
  return mcp;
}

int main(int argc, char *argv[])
{
  try {

    // create surfaces
    CurvePtrArray cpa(2), cpb(2);
    {
      Airfoil *af = new Airfoil("Right");
      af->naca(2315);
      af->translate(0.5, 1.0, 0.0);
      af->apply();
      cpa[0] = CurvePtr(af);
    }
    {
      Airfoil *af = new Airfoil("Left");
      af->naca(2315);
      af->translate(0.0, 0.0, 0.0);
      af->apply();
      cpa[1] = CurvePtr(af);
    }
    {
      Airfoil *af = new Airfoil("Right");
      af->naca(2315);
      af->translate(0.0, 0.0, 0.0);
      af->apply();
      cpb[0] = CurvePtr(af);
    }
    {
      Airfoil *af = new Airfoil("Left");
      af->naca(2315);
      af->translate(0.5, -1.0, 0.0);
      af->apply();
      cpb[1] = CurvePtr(af);
    }

    SurfacePtr pright, pleft;
    {
      LinearSurf *psf = new LinearSurf("RightWing");
      psf->init(cpa);
      pright.reset(psf);
    }

    {
      LinearSurf *psf = new LinearSurf("LeftWing");
      psf->init(cpb);
      pleft.reset(psf);
    }

    // meshing criteria
    DnWingCriterionPtr wcrit(new DnWingCriterion);
    wcrit->edgeRefinement(1.5, 1.5);
    wcrit->setCriteria(0.15, 0.003, rad(33.0), 5.5);

    DnWingCriterionPtr xcrit(new DnWingCriterion);
    xcrit->edgeRefinement(3.5, 4.0);
    xcrit->setCriteria(0.07, 0.001, rad(20.0), 4.5);

//    // unconnected
//    {
//      MeshComponentPtr cright = initComponent(pright, wcrit);
//      MeshComponentPtr cleft = initComponent(pleft, xcrit);
//      cright->registerNeighbor( cleft.get() );
//      cleft->registerNeighbor( cright.get() );
//
//      MeshGenerator mg;
//      mg.addComponent( cright );
//      mg.addComponent( cleft );
//      mg.intersect();
//      mg.refineLocally();
//      mg.refineGlobally();
//      mg.finalize();
//      mg.toXml(true).zwrite("unconnected.zml");
//    }

    // connected
    {
      MeshComponentPtr cright = initComponent(pright, wcrit);
      MeshComponentPtr cleft = initComponent(pleft, xcrit);
      cright->registerNeighbor( cleft.get() );
      cleft->registerNeighbor( cright.get() );

      MeshGenerator mg;
      mg.addComponent( cright );
      mg.addComponent( cleft );

      TTiConnection con;
      con.vconnect(cright.get(), cleft.get(), true);
      mg.addConnection(con);

      cright->fixate();
      cleft->fixate();

      mg.intersect();
      mg.refineLocally();
      mg.refineGlobally();
      mg.finalize();
      mg.toXml(true).zwrite("connected.zml");
    }


  } catch (Error & xcp) {
    cerr << xcp.what();
    return -1;
  }

  return 0;
}
