
#include <surf/nstmesh.h>
#include <surf/nstreader.h>
#include <surf/surfinterpolator.h>
#include <surf/rbfinterpolator.h>
#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <genua/timing.h>
#include <genua/configparser.h>
#include <genua/programversion.h>
#include <genua/primitives.h>
#include <genua/strutils.h>
#include <iostream>
#include <fstream>

#define surfmap_int_version _UINT_VERSION(1,6,1)
#define surfmap_version version_string(surfmap_int_version)

using namespace std;

uint find_boco(const MxMesh &msh, const std::string &bname)
{
  for (uint i=0; i<msh.nbocos(); ++i) {
    string s = toLower( msh.boco(i).name() );
    if (s == bname)
      return i;
  }
  return NotFound;
}

uint find_section(const MxMesh &msh, const std::string &bname)
{
  for (uint i=0; i<msh.nsections(); ++i) {
    string s = toLower( msh.section(i).name() );
    if (s == bname)
      return i;
  }
  return NotFound;
}

int main(int argc, char *argv[])
{
  try {

    Wallclock clk;

    cout << "This is surfmap " << surfmap_version
         << ", compiled " << __DATE__ << endl;
    if (argc < 2) {
      cerr << "Usage: " << argv[0] << " configfile.txt" << endl;
      return -1;
    }

    // mandatory entries in configuration file
    ConfigParser cfg(argv[1]);
    string strFile = cfg["StructuralMesh"];
    string aerFile = cfg["AeroMesh"];

    // optional entries
    Indices pidwet, pidinternal;
    if (cfg.hasKey("IncludePID")) {
      stringstream ss;
      ss << cfg["IncludePID"];
      uint pid;
      while (ss >> pid)
        pidwet.push_back(pid);
      sort_unique(pidwet);
      cout << pidwet.size() << " PIDs selected for inclusion." << endl;
    } else if (cfg.hasKey("ExcludePID")) {
      stringstream ss;
      ss << cfg["ExcludePID"];
      uint pid;
      while (ss >> pid)
        pidinternal.push_back(pid);
      sort_unique(pidinternal);
      cout << pidinternal.size() << " PIDs selected for exclusion." << endl;
    }

    string caseName;
    if (cfg.hasKey("Case"))
      caseName = cfg["Case"];
    else
      caseName = "mapped";

    enum IpolMethod {RBF, Projection, ApplyH};
    IpolMethod ipmethod(Projection);
    if (cfg.hasKey("Method")) {
      if (toLower(cfg["Method"]) == "rbf")
        ipmethod = RBF;
      else if  (toLower(cfg["Method"]) == "applyh")
        ipmethod = ApplyH;
    }
    bool bDumpProjection = cfg.getBool("WriteProjectionSurface", false);
    bool bUseGalerkin = cfg.getBool("GalerkinAveraging", false);
    uint maxModeCount = cfg.getInt("MaxModeCount", 1000000);
    Real minFreq = cfg.getFloat("MinFrequency", -1.0);
    Real maxFreq = cfg.getFloat("MaxFrequency",
                                std::numeric_limits<Real>::max());
    bool writeZml = true;
    bool writeBdis = false;
    if (cfg.hasKey("OutputFormat")) {
      string formats = toLower( cfg["OutputFormat"] );
      writeZml = (formats.find("zml") != string::npos);
      writeBdis = (formats.find("bdis") != string::npos);
    }

    int smoothingIter = cfg.getInt("PostSmoothing", 0);
    int smoothingRing = cfg.getInt("SmoothingRing", 1);
    Real smoothingRadius = cfg.getFloat("SmoothingRadius", 0.0);
    Real smoothingOmega = cfg.getFloat("SmoothingRelaxation", 0.5);
    Real nrmDev = rad( cfg.getFloat("MapNormalDeviation", 180.0) );
    Real maxDst = cfg.getFloat("MapMaxDistance", -1.0);
    Real cvthreshold = cfg.getFloat("ConcavityCriterion", 2.0);
    bool autorescale = cfg.getBool("AutomaticScaling", false);

    // read both meshes
    MxMesh mstr, maer;
    if ( strstr(strFile.c_str(), ".f06") != 0 ) {
      NstMesh nst;
      clk.start();
      nst.nstread( strFile );
      clk.stop();
      cout << "Parsing NASTRAN file: " << clk.elapsed() << endl;
      clk.start();
      nst.toMx(mstr);
      clk.stop();
      cout << "Format conversion: " << clk.elapsed() << endl;
    } else {
      clk.start();
      mstr.loadAny(strFile);
      clk.stop();
      cout << "Reading structural mesh: " << clk.elapsed() << endl;
    }
    cout << "Structural mesh: " << mstr.nnodes() << " nodes, "
         << mstr.nelements() << " elements." << endl;

    if (strstr(aerFile.c_str(), ".bmsh") != 0) {
      clk.start();
      maer.readFFA(aerFile);
      clk.stop();
      writeBdis = true;
    } else {
      maer.loadAny(aerFile);
    }
    cout << "Reading aerodynamic mesh: " << clk.elapsed() << endl;
    cout << "Aerodynamic mesh: " << maer.nnodes() << " nodes, "
         << maer.nelements() << " elements." << endl;

    // check whether any output will be generated
    if (not (writeZml or writeBdis)) {
      cout << "No output requested by user, terminating." << endl;
      return 1;
    }

    // look for boundaries identified by name
    Indices movingBocos, slidingBocos;
    Indices movingSections, slidingSections;
    if (cfg.hasKey("MovingBoundaries")) {
      StringArray slist = split(cfg["MovingBoundaries"], ",");
      for (uint i=0; i<slist.size(); ++i) {
        uint ibc = find_boco(maer, toLower( strip(slist[i]) ));
        if (ibc != NotFound) {
          movingBocos.push_back(ibc);
          continue;
        }

        ibc = find_section(maer, toLower( strip(slist[i]) ));
        if (ibc != NotFound)
          movingSections.push_back(ibc);
        else
          throw Error("Boundary/section not found: "+slist[i]);
      }
    }
    if (cfg.hasKey("SlidingBoundaries")) {
      StringArray slist = split(cfg["SlidingBoundaries"], ",");
      for (uint i=0; i<slist.size(); ++i) {
        uint ibc = find_boco(maer, toLower( strip(slist[i]) ));
        if (ibc != NotFound) {
          slidingBocos.push_back(ibc);
          continue;
        }

        ibc = find_section(maer, toLower( strip(slist[i]) ));
        if (ibc != NotFound)
          slidingSections.push_back(ibc);
        else
          throw Error("Boundary/section not found: "+slist[i]);
      }
    }

    DispInterpolator *pdi(0);

    if (ipmethod == Projection) {

      SurfInterpolator *pipol = new SurfInterpolator;
      pipol->jumpCriteria(nrmDev, maxDst);
      pipol->useGalerkin(bUseGalerkin);
      pipol->selectiveSmoothing(smoothingIter, smoothingRing,
                                smoothingRadius, smoothingOmega );
      pipol->concavityThreshold( cvthreshold );
      pipol->setAerodynamic( MxMeshPtr(&maer, null_deleter()) );
      pipol->setStructural( MxMeshPtr(&mstr, null_deleter()) );
      pipol->useEigenmodes( maxModeCount, minFreq, maxFreq );

      clk.start();
      if (pidwet.empty() and pidinternal.empty())
        pipol->buildTreeFromSections();
      else
        pipol->buildTreeByPid(pidwet, pidinternal);
      clk.stop();
      cout << "Search tree construction: " << clk.elapsed() << endl;

      if (bDumpProjection)
        pipol->writeProjection(caseName + "Projection.zml");

      if (not movingBocos.empty())
        pipol->collectWallBocos(movingBocos, slidingBocos);
      else if (not movingSections.empty())
        pipol->collectWallSections(movingSections, slidingSections);

      pdi = pipol;

    } else if (ipmethod == RBF) {

      RbfInterpolator *pipol = new RbfInterpolator;
      pipol->setAerodynamic( MxMeshPtr(&maer, null_deleter()) );
      pipol->setStructural( MxMeshPtr(&mstr, null_deleter()) );
      pipol->useEigenmodes( maxModeCount, minFreq, maxFreq );

      if (not movingBocos.empty())
        pipol->collectWallBocos(movingBocos, slidingBocos);
      else if (not movingSections.empty())
        pipol->collectWallSections(movingSections, slidingSections);

      int targetNodeCount = cfg.getInt("TargetNodeCount", 0);
      if (targetNodeCount != 0) {
        pipol->centersFromTree( targetNodeCount );
      } else {
        bool usePoints = cfg.getBool("UsePoints", false);
        bool useBeams = cfg.getBool("UseBeams", true);
        bool useShells = cfg.getBool("UseShells", false);
        pipol->useStrNodes(usePoints, useBeams, useShells);
      }

      Real mergeThr = cfg.getFloat("MergeThreshold", gmepsilon);
      pipol->threshold( mergeThr );

      clk.start();
      pipol->buildRbfBasis();
      clk.stop();
      cout << "RBF Basis construction: " << clk.elapsed() << endl;

      pdi = pipol;

    } else { // ApplyH only for surface projection method for now

      SurfInterpolator *pipol = new SurfInterpolator;
      pipol->jumpCriteria(nrmDev, maxDst);
      pipol->useGalerkin(bUseGalerkin);
      pipol->selectiveSmoothing(smoothingIter, smoothingRing,
                                smoothingRadius, smoothingOmega );
      pipol->concavityThreshold( cvthreshold );
      pipol->setAerodynamic( MxMeshPtr(&maer, null_deleter()) );
      pipol->setStructural( MxMeshPtr(&mstr, null_deleter()) );
      pipol->useEigenmodes( maxModeCount, minFreq, maxFreq );

      if (not movingBocos.empty())
        pipol->collectWallBocos(movingBocos, slidingBocos);
      else if (not movingSections.empty())
        pipol->collectWallSections(movingSections, slidingSections);

      pdi = pipol;

    }

    uint nmap = pdi->nodesToMap();
    cout << "Mapping deflections to " << nmap << " aerodynamic nodes." << endl;

    string hmapFile = cfg.value("HMapFile", "");

    if (ipmethod != ApplyH) {

      clk.start();
      pdi->map();
      clk.stop();
      cout << "Field mapping: " << clk.elapsed() << endl;

      if (autorescale) {
        pdi->autoScale();
      } else {
        Vector maxscale;
        pdi->maxBenignScale(maxscale);
        cout << "Maximum reasonable scales: " << endl;
        for (size_t i=0; i<maxscale.size(); ++i)
          cout << "Field " << i+1 << " -> " << maxscale[i] << endl;
      }

      // store H if requested
      if ( not hmapFile.empty() ) {
        if (ipmethod == Projection) {
          DispInterpolator::MapMatrix H;
          clk.start();
          pdi->hmap(H);
          clk.stop();
          cout << "[t] H-matrix generation: " << clk.elapsed() << endl;
          clk.start();
          FFANodePtr hptr = pdi->mapToFFA(H);
          hptr->write( append_suffix(hmapFile, ".bmap") );
          clk.stop();
          cout << "[t] H-matrix FFA export: " << clk.elapsed() << endl;
        } else if (ipmethod == RBF) {
          cout << "Sorry, H matrix storage implemented for surface "
                  "element projection method only." << endl;
        }
      }

    } else {

      if (hmapFile.empty())
        throw Error("Must specify HMapFile to apply existing H matrix.");

      FFANodePtr root = FFANode::create();
      root->read(hmapFile);

      DispInterpolator::MapMatrix H;
      pdi->mapFromFFA(root, H);

      DMatrix<float> m;
      pdi->map(H, m);
      pdi->appendFields(m);

    }

    if (writeZml) {
      clk.start();
      maer.writeAs(append_suffix(caseName, ".zml"), Mx::NativeFormat, 1);
      clk.stop();
      cout << "Writing zml output: " << clk.elapsed() << endl;
    }

    if (writeBdis) {
      clk.start();
      pdi->writeBdis(caseName);
      clk.stop();
      cout << "Writing .bdis output: " << clk.elapsed() << endl;
    }

    delete pdi;

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
