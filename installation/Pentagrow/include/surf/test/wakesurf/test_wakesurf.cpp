
#include <genua/xcept.h>
#include <genua/pattern.h>
#include <genua/mxmesh.h>
#include <genua/configparser.h>
#include <surf/wakesurf.h>
#include <surf/meshgenerator.h>
#include <surf/meshcomponent.h>
#include <surf/wakecomponent.h>
#include <surf/dnrefine.h>
#include <surf/capcomponent.h>
#include <surf/dnwingcriterion.h>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    if (argc != 2) {
      cerr << "Usage: " << argv[0] << " surfaces.xml" << endl;
      return -2;
    }

    // extract surfaces, add wake to each and every of them
    XmlElement xe;
    xe.read(argv[1]);

    // retrieve parameters from configuration file
    ConfigParser cfg("wakesurf.cfg");

    // freestream velocity
    Real alpha = rad( cfg.getFloat("Alpha", 5.) );
    Vct3 uoo = vct(cos(alpha), 0.0, sin(alpha));

    // wake length, if prescribed
    Real wakeLength = cfg.getFloat("WakeLength", 0.0);

    MeshGenerator mg;

    // count bodies, record names
    StringArray sfnames;
    int ibody = 0;
    Real maxspan = 0;

    XmlElement::const_iterator itr, last;
    last = xe.end();
    for (itr = xe.begin(); itr != last; ++itr) {
      SurfacePtr psf = Surface::createFromXml(*itr);

      if (not psf)
        continue;
      sfnames.push_back( psf->name() );

      string word;
      cout << "Generate wake for " << psf->name() << "? [y/n]:";
      cin >> word;
      bool genwake = (word.find('y') == 0) or (word.find('Y') == 0);

      // see whether a mesh criterion can be found in this element
      // otherwise, create a default criterion
      XmlElement::const_iterator ite = itr->findChild("MeshCriterion");
      DnRegionCriterionPtr mcrit;
      if (ite != itr->end()) {
        if (ite->hasAttribute("terfactor"))
          mcrit.reset(new DnWingCriterion);
        else
          mcrit.reset(new DnRegionCriterion);
        mcrit->fromXml( *ite );
      } else {
        mcrit.reset(new DnRegionCriterion);
        mcrit->setCriteria(0.25, 0.01, rad(30.), 6.0);
      }

      // cout << "Mesh criterion for " << psf->name() << endl;
      // mcrit->toXml().xwrite(cout);

      if (genwake) {

        WakeSurfPtr ws(new WakeSurf("Wake"));

        // ask for ratio of streamwise tangent lengths
        Real tgStretch = 1.0;
        cout << "Upstream/downstream wake tangent length ratio: ";
        cin >> tgStretch;

        Real rscale = 2.0 / (tgStretch + 1.0);
        Real fscale = tgStretch * rscale;

//        // ask for bump dimensions
//        Real hbump(0), wbump(0);
//        cout << "Bump height: ";
//        cin >> hbump;
//        cout << "Bump width: ";
//        cin >> wbump;

//        if (hbump != 0)
//          ws->defineBump(hbump, wbump, 0.5);

        // determine shape flag
        int wakeShape = -1;
        while (wakeShape != 0 and wakeShape != 1) {
          cout << "Plain wake [0] or interpolating [1]: ";
          cin >> wakeShape;
        }

        if (wakeShape == 1) {

          Real vBump(0.5), bumpWidth(0.5);
          cout << "Bulge width: ";
          cin >> bumpWidth;
          cout << "Bulge location: ";
          cin >> vBump;
          ws->defineBump(1.0, bumpWidth, vBump);

          // ask for interpolation point
          cout << "Interpolation point (x,y,z): ";
          Real xi, yi, zi;
          cin >> xi >> yi >> zi;
          ws->interpolateBump( vBump, Vct3(xi,yi,zi) );

        }

        Real wlen, span = norm(psf->eval(0.0,0.0) - psf->eval(0.0,1.0));
        wlen = (wakeLength > 0) ? wakeLength : 2*span;
        // ws->init(psf, equi_pattern(41), uoo*wlen);
        ws->defineTangent(wlen*uoo, fscale, rscale);
        ws->init(psf);
        maxspan = max(span, maxspan);

        // a refinement criterion for the wake surface
        DnRefineCriterionPtr wcrit(new DnRefineCriterion());
        Real wmaxl = 0.05*span;
        wcrit->setCriteria(wmaxl, 0.001*wmaxl, rad(35.), 6.0);

        MeshComponentPtr mcp(new MeshComponent(psf, mcrit));
        mcp->tag(ibody);

        ws->rename( psf->name() + "Wake" );
        WakeComponentPtr wcp(new WakeComponent(ws, wcrit));
        wcp->tag(100 + ibody);
        mcp->registerNeighbor(wcp.get());
        wcp->registerNeighbor(mcp.get());
        wcp->registerParent(mcp.get());
        wcp->smoothingIterations(0);

        // generate simple caps
        CapComponentPtr rcap(new CapComponent(mcp, south,
                                              CapComponent::LongCap, 1.0));
        rcap->tag(ibody);
        rcap->registerParent(mcp.get());
        rcap->registerNeighbor(mcp.get());
        rcap->registerNeighbor(wcp.get());
        wcp->registerNeighbor(rcap.get());
        mcp->registerNeighbor(rcap.get());

        CapComponentPtr lcap(new CapComponent(mcp, north,
                                              CapComponent::LongCap, 1.0));
        lcap->registerParent(mcp.get());
        lcap->registerNeighbor(mcp.get());
        lcap->registerNeighbor(wcp.get());
        wcp->registerNeighbor(lcap.get());
        mcp->registerNeighbor(lcap.get());

        mg.addComponent(mcp);
        mg.addComponent(wcp);
        mg.addComponent(rcap);
        mg.addComponent(lcap);

      } else {

        // do not generate a wake for this
        MeshComponentPtr mcp(new MeshComponent(psf, mcrit));
        mcp->tag(ibody);
        mg.addComponent(mcp);

        // check for presence of cap definition
        XmlElement::const_iterator itc, elast;
        elast = itr->end();

        if (itr->findChild("Cap") == elast) {

          // ask for type of cap
          cout << "Cap type [polar/grid]:";
          cin >> word;

          CapComponent::Shape capShape;
          if (word.find('g') == 0)
            capShape = CapComponent::LongCap;
          else
            capShape = CapComponent::RingCap;

          // ask for height
          Real caphgt(1.0);
          cout << "Cap height: ";
          cin >> caphgt;

          // generate simple caps
          CapComponentPtr rcap(new CapComponent(mcp, south, capShape, caphgt));
          rcap->registerParent(mcp.get());
          rcap->registerNeighbor(mcp.get());
          mcp->registerNeighbor(rcap.get());

          CapComponentPtr lcap(new CapComponent(mcp, north, capShape, caphgt));
          lcap->registerParent(mcp.get());
          lcap->registerNeighbor(mcp.get());
          mcp->registerNeighbor(lcap.get());

          mg.addComponent(rcap);
          mg.addComponent(lcap);

        } else {

          // caps defined in xml file
          for (itc = itr->begin(); itc != elast; ++itc) {
            if (itc->name() != "Cap")
              continue;

            //itc->xwrite(cout);

            side_t mainside = south;
            CapComponent::Shape capShape;
            Real caphgt = itc->attr2float("height", 1.0);
            if (itc->attribute("side") == "south")
              mainside = south;
            else if (itc->attribute("side") == "north")
              mainside = north;
            if (itc->attribute("shape") == "RingCap")
              capShape = CapComponent::RingCap;
            else
              capShape = CapComponent::LongCap;

            CapComponentPtr lcap(new CapComponent(mcp, mainside,
                                                  capShape, caphgt));
            lcap->registerParent(mcp.get());
            lcap->registerNeighbor(mcp.get());
            mcp->registerNeighbor(lcap.get());
            mg.addComponent(lcap);
          }

        }
      }

      ibody++;
    }

    mg.toggleDropOrphanRidges(false);
    mg.toggleDropInternal(true);
    mg.premesh();
    mg.intersect();
    mg.refineLocally();
    mg.intersect();
    mg.refineGlobally();
    mg.finalize();

    // change name mapping
    for (int i=0; i<ibody; ++i)
      mg.tagName(i, sfnames[i]);

    // merge forcefully
    mg.cleanup(1e-6);
    mg.fixate(true);

    // create mx mesh (which can write tetgen output)
    MxMesh mx;
    mx.appendSection(mg);
    mx.toXml(true).zwrite("surfaces.zml");

    // enclose in spherical farfield
    Real ffRadius = cfg.getFloat("FarfieldRadius", 5*maxspan);
    Vct3 hl = cfg.getVct3("Hole", vct(1.5, 0.0, 0.0));
    Vct3 ffCtr = cfg.getVct3("FarfieldCenter", hl);
    int ffRefine = cfg.getInt("FarfieldRefinement", 3);

    TriMesh farfield;
    farfield.sphere(ffCtr, ffRadius, ffRefine);
    farfield.faceTag(999);
    farfield.reverse();

    // farfield stats
    cout << "Farfield triangles: " << farfield.nfaces() << endl;
    Real ftel =  sqrt(4.0/sqrt(3)*farfield.area() / farfield.nfaces());
    cout << "Farfield triangle edge length: " << ftel << endl;
    cout << "Suggested volume limit: " << cb(ftel)/(6*sqrt(2.)) << endl;

    uint ifar = mx.appendSection(farfield);
    mx.section(ifar).rename("Farfield");
    mx.toXml(true).zwrite("world.zml");

    PointList<3> holes(1);
    holes[0] = hl;
    mx.writeSmesh("tmp.smesh", holes);
    // mx.writeSmesh("tmp.smesh", PointList<3>());

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
