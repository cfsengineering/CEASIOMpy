
#include <surf/topology.h>
#include <surf/airfoil.h>
#include <surf/linearsurf.h>
#include <surf/abstractuvcurve.h>
#include <surf/dcmeshcrit.h>
#include <genua/trimesh.h>
#include <genua/pattern.h>
#include <genua/xcept.h>
#include <fstream>
#include <iostream>

using namespace std;

int main()
{

  try {

    {
      // test spline splitting
      Vector up1(3), cp1(3), cp2;
      up1[0] = 0.0;
      up1[1] = 0.5;
      up1[2] = 1.0;
      cp1[0] = 0.0;
      cp1[1] = 1.0;
      cp1[2] = 4.0;
      cp2 = cp1;

      SplineBasis spb1;
      spb1.init(2, up1);
      cout << "Pre-insert knots: " << spb1.getKnots() << endl;
      spb1.insertKnot(0.3, cp1);
      cout << "Post-insert knots: " << spb1.getKnots() << endl;
      cout << "Post-insert cp: " << cp1 << endl;
      cout << "span(0.64) = " << spb1.findSpan(0.64) << endl;

      cp2.clear();
      SplineBasis spb2;
      spb1.split(0.64, cp1, spb2, cp2);
      cout << "Post-split low knots: " << spb1.getKnots() << endl;
      cout << "Post-split high knots: " << spb2.getKnots() << endl;
      cout << "Post-split low cp: " << cp1 << endl;
      cout << "Post-split high cp: " << cp2 << endl;
    }

    // generate example surfaces
    SurfacePtr pLeftSrf, pRightSrf;
    const Real sweep = rad(45.);
    const Real lambda = 0.3;
    const Real AR = 3;
    const Real rootChord = 1.0;
    const Real tipChord = lambda*rootChord;
    const Real semiSpan = 0.5*rootChord*AR*(1 + lambda);
    const Real xTip = semiSpan*std::tan(sweep);

    {
      Airfoil *af1 = new Airfoil("RightTip");
      af1->naca(1304);
      af1->scale(tipChord);
      af1->translate(xTip, semiSpan, 0.0);
      af1->apply();

      Airfoil *af2 = new Airfoil("RightRoot");
      af2->naca(4406);
      af2->scale(rootChord);
      af2->apply();

      LinearSurf *lsf = new LinearSurf("RightWing");
      lsf->init( CurvePtr(af1), CurvePtr(af2) );
      pRightSrf.reset( lsf );
    }

    {
      Airfoil *af1 = new Airfoil("LeftTip");
      af1->naca(1304);
      af1->scale(tipChord);
      af1->translate(xTip, -semiSpan, 0.0);
      af1->apply();

      Airfoil *af2 = new Airfoil("LeftRoot");
      af2->naca(4406);
      af2->scale(rootChord);
      af2->apply();

      LinearSurf *lsf = new LinearSurf("LeftWing");
      lsf->init( CurvePtr(af2), CurvePtr(af1) );
      pLeftSrf.reset( lsf );
    }

    Topology topo;
    uint flw = topo.appendFace(pLeftSrf, true, false);
    uint frw = topo.appendFace(pRightSrf, true, false);

    cout << "*** Before connection:" << endl;
    topo.print();

    bool worked = topo.connectFaces(flw, frw, 1, 5);

    cout << endl << endl;
    cout << "*** After connection: " << worked << endl;
    topo.print();

    // check whether the two curves on curve 1 match in space
    TopoEdge & e1( topo.edge(1) );
    uint icl = e1.findFace( flw ); assert(icl != NotFound);
    uint icr = e1.findFace( frw ); assert(icr != NotFound);
    AbstractUvCurvePtr clw = topo.edge(1).curve(icl);
    AbstractUvCurvePtr crw = topo.edge(1).curve(icr);

    const int ntp = 8;
    Vector tp = equi_pattern(ntp);
    for (int i=0; i<ntp; ++i) {
      Real ti = tp[i];
      cout << i << " t = " << ti << endl;
      cout << "left:  " << clw->uveval(ti) << " -:- " << clw->eval(ti) << endl;
      cout << "right: " << crw->uveval(ti) << " -:- " << crw->eval(ti) << endl;
    }

    // test discretization
    ofstream os("points.txt");

    DcMeshCritPtr pmc(new DcMeshCrit);
    pmc->maxNormalAngle( rad(20.) );
    pmc->xyzLength( 0.05, 1e-4 );
    pmc->uvLength( 0.1, 1e-6 );
    pmc->npass( 16 );
    pmc->nSmooth( 2 );
    const Vector & te = e1.discretize(*pmc);
    const int nte = te.size();
    cout << "Created " << nte << " points on edge e1" << endl;
    for (int i=0; i<nte; ++i) {
      Real ti = te[i];
      cout << i << " t = " << ti << endl;
      cout << "left:  " << clw->uveval(ti) << " -:- " << clw->eval(ti) << endl;
      cout << "right: " << crw->uveval(ti) << " -:- " << crw->eval(ti) << endl;
      os << clw->eval(ti) << endl;
    }
    os.close();

    TriMesh tm;
    topo.face(flw).criterion(pmc);
    topo.face(frw).criterion(pmc);
    topo.meshEdges();
    topo.meshFaces(tm);
    tm.toXml(true).zwrite("fullmesh.zml");

  } catch (Error & xcp) {
    cerr << xcp.what();
    return 1;
  }

  return 0;
}
