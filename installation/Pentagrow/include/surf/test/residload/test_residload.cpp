
#include <iostream>
#include <fstream>
#include <genua/xcept.h>
#include <genua/timing.h>
#include <genua/dbprint.h>
#include <genua/mxmesh.h>
#include <genua/configparser.h>
#include <surf/fsimesh.h>
#include <surf/nstmesh.h>
#include <surf/nstreader.h>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    if (argc != 2) {
      cerr << "Usage: " << argv[0] << " configuration.cfg "
           << endl;
      return 1;
    }

    // load configuration
    ConfigParser cfg( argv[1] );

    // read PID configuration from file
    Indices pidwet, pidintern;
    if (cfg.hasKey("UsePID")) {
      stringstream ss;
      ss.str(cfg["UsePID"]);
      uint x;
      while (ss >> x)
        pidwet.push_back( x );
    } else if (cfg.hasKey("ExcludePID")) {
      stringstream ss;
      ss.str(cfg["ExcludePID"]);
      uint x;
      while (ss >> x)
        pidintern.push_back( x );
    }

    // import aerodynamic mesh
    MxMeshPtr fmx(new MxMesh);
    Indices wallBc;
    {
      XmlElement xe;
      xe.read( cfg["PhiResults"] );
      fmx->fromXml( xe );
      for (uint i=0; i<fmx->nbocos(); ++i) {
        if (fmx->boco(i).bocoType() == Mx::BcWall)
          wallBc.push_back(i);
      }
    }

    // check what to do
    bool generateLoads = cfg.getBool("GenerateLoads", true);
    bool computeShapes = cfg.getBool("ComputeShapes", false);

    if (not (generateLoads or computeShapes))
      return 0;

    // import structural mesh
    MxMeshPtr smx(new MxMesh);
    {
      NstMesh nst;
      nst.nstread( cfg["NastranModal"] );
      nst.toMx( *smx );
    }

    // interpolator fluid -> structural mesh
    FsiMesh fsi;
    fsi.mergeStruct( smx, pidwet, pidintern );
    fsi.mergeFluid( fmx, wallBc );
    fsi.buildInterpolator();

    CsrMatrix<Real> K, M;

    if (generateLoads) {

      const int nf = fmx->nfields();
      Indices iCpFields;
      for (int i=0; i<nf; ++i) {
        const std::string & s( fmx->field(i).name() );
        if (s.find("CoefPressure") != std::string::npos) {
          iCpFields.push_back(i);
        } else if (s.find("DeltaCp") != std::string::npos) {
          iCpFields.push_back(i);
        }
      }

      // generate loads for unit dynamic pressure
      const Real qoo(1.0);

      // extract Cp vectors
      const int nfi = iCpFields.size();
      Matrix cpm(fsi.fluidNodes().size(), nfi);
      for (int i=0; i<nfi; ++i) {
        Vector pf;
        fsi.extractPressure(qoo, iCpFields[i], pf);
        assert(pf.size() == cpm.nrows());
        std::copy(pf.begin(), pf.end(), cpm.colpointer(i));
        cout << iCpFields[i] << " |pf| = " << norm(pf) << endl;
      }

      // integrate nodal forces
      PointGrid<6> fgrid;
      fsi.integrate(cpm, fgrid);
      assert(fgrid.ncols() == uint(nfi));

      // generate reference load fields
      Indices loadFields;
      PointList<3> forces(fgrid.nrows());
      for (int i=0; i<nfi; ++i) {
        Real fnorm = 0;
        const int np = fgrid.nrows();
        for (int j=0; j<np; ++j) {
          for (int k=0; k<3; ++k)
            forces[j][k] = fgrid(j,i)[k];
          fnorm += sq(forces[j]);
        }
        fnorm = sqrt(fnorm);

        string fname = "RefLoad " + fmx->field(iCpFields[i]).name();
        // uint fi = smx->appendField(fname, forces);
        // smx->field(fi).valueClass( MxMeshField::Force );

        uint fi = fsi.appendSifField(forces, fmx->field(iCpFields[i]).name());
        loadFields.push_back( fi );

        cout << "Mapped pressure field: " << fmx->field(iCpFields[i]).name()
             << " |f| = " << fnorm << endl;
      }

      // store for comparison
      smx->toXml(true).zwrite("refloads.zml");



      // residualize load vectors
      fsi.residualizeLoads(M);

      // store result for comparison
      smx->toXml(true).zwrite("residualized.zml");

      // export residualized loads for NASTRAN solution
      {
        ofstream osl("resid_loadset.blk");
        const int nload = loadFields.size();
        for (int i=0; i<nload; ++i) {
          fsi.exportForces(loadFields[i], osl, i+1);
        }
      }

    } // generateLoads

    if (computeShapes) {

      {
        NstMesh nst;
        nst.nstread( cfg["NastranStatic"] );
        smx.reset(new MxMesh);
        nst.toMx(*smx);
      }

      smx->toXml(true).zwrite("staticsol.zml");

      // interpolator fluid -> structural mesh
      FsiMesh fsi;
      fsi.mergeStruct( smx, pidwet, pidintern );
      fsi.mergeFluid( fmx, wallBc );
      fsi.buildInterpolator();

      // load sparse mass matrix
      if (M.nrows() != 6*smx->nnodes()) {
        if (cfg.hasKey("MassMatrix")) {
          string fname = cfg["MassMatrix"];
          if (fname.find(".zml") != string::npos) {
            XmlElement xe;
            xe.read( cfg["MassMatrix"] );
            M.fromXml(xe);
          } else {
            NstReader::readOp4Ascii( fname, M );
            cout << "M rows:" << M.nrows() << " nnz: " << M.nonzero() << endl;
            M.toXml(true).zwrite( append_suffix(fname, ".zml") );
          }
        } else {
          return 0;
        }
      }

      if (K.nrows() != 6*smx->nnodes()) {
        if (cfg.hasKey("StiffnessMatrix")) {
          string fname = cfg["StiffnessMatrix"];
          if (fname.find(".zml") != string::npos) {
            XmlElement xe;
            xe.read( fname );
            K.fromXml(xe);
          } else {
            NstReader::readOp4Ascii( fname, K );
            cout << "K rows:" << K.nrows() << " nnz: " << K.nonzero() << endl;
            K.toXml(true).zwrite( append_suffix(fname, ".zml") );
          }
        } else {
          return 0;
        }
      }

      fsi.augmentedStates(M, K);
      smx->toXml(true).zwrite("augmented.zml");

    } // computeShapes

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
