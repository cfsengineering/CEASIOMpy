
/* ------------------------------------------------------------------------
 * file:       batchrun.cpp
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Run sumo in batch mode, smx --> smesh
 * ------------------------------------------------------------------------ */

#include "batchrun.h"
#include "sumo.h"
#include "assembly.h"
#include "util.h"

#include <iostream>
#include <genua/xcept.h>
#include <genua/trimesh.h>
#include <genua/timing.h>
#include <genua/mxmesh.h>
#include <genua/ioglue.h>
#include <surf/meshgenerator.h>
#include <surf/tetmesh.h>

#include <QProcess>
#include <QLocale>
#include <QApplication>

using std::string;

bool BatchRun::writeIges(true);
bool BatchRun::writeEdgeMesh( true );
bool BatchRun::writeCgnsMesh( false );
bool BatchRun::writeTauMesh( false );
bool BatchRun::writeDwfsMesh( true );
bool BatchRun::writeSu2Mesh( false );

QString BatchRun::tetgen_opt;
QString BatchRun::baseFile;

bool BatchRun::run(int argc, char *argv[])
{
  // check if batch mode is requested
  bool doBatch = parseOptions(argc, argv);
  if (not doBatch)
    return false;
  
  // determine base file name
  string bname, fname = str(baseFile);
  string::size_type pos = fname.find_last_of(".");
  if (pos != string::npos)
    bname = fname.substr(0, pos);
  else
    bname = fname;

  // open a log file
  ofstream os( asPath(bname + "_sumolog.txt").c_str() );
  cout << "Batch mode active, writing log to '"
       << bname + "_sumolog.txt'" << endl;

#if !defined(HAVE_NETCDF)
  if (writeTauMesh) {
    writeTauMesh = false;
    os << "This version of sumo was compiled without support for NetCDF. " << endl;
    os << "The TAU mesh format is therefore not supported." << endl;
  }
#endif

  // check whether we need to mesh at all
  bool needVolMesh = writeEdgeMesh or writeTauMesh
                     or writeCgnsMesh or writeSu2Mesh;
  bool needSurfMesh = writeDwfsMesh or needVolMesh;

  try {

    Wallclock wc;
    
    os << "Reading .smx file: " << fname << endl;

    wc.start();
    Assembly asy;
    asy.loadAndReplace( fname );
    wc.stop();
    os << "Geometry generation: " << wc.elapsed() << "s." << endl;

    // store iges file
    if (writeIges) {
      wc.start();
      os << "Writing IGES file..." << endl;
      asy.exportIges(bname + ".igs");
      wc.stop();
      os << "IGES export: " << wc.elapsed() << "s." << endl;
    }

    // if no mesh output is requested, we can exit here
    if (not needSurfMesh)
      return true;

    // run surface mesh generation
    wc.start();
    os << "Generating surface mesh..." << endl;
    MgProgressPtr mgp(new MgProgressCtrl);
    asy.processSurfaceMesh(mgp);
    wc.stop();
    asy.ctsystem().updateGeometry();
    const TriMesh & sfm(asy.mesh());
    os << "Surface mesh: " << sfm.nfaces() << " triangles. (";
    os << wc.elapsed() << " s.)" << endl;
    
    // store dwfs mesh
    if (writeDwfsMesh) {
      wc.start();
      os << "Writing surface mesh for dwfs..." << endl;
      asy.toDwfsMesh().write(bname + ".msh", XmlElement::PlainText);
      wc.stop();
      os << "dwfs mesh export: " << wc.elapsed() << "s." << endl;
    }

    if (not needVolMesh)
      return true;

    // setup farfield boundaries for volume mesh
    os << "Initializing mesh boundaries for tetgen ... ";
    Real ffr = asy.tgFarfieldRadius();
    if (ffr <= 0.0)
      ffr = 8*sqrt(sfm.area());

    wc.start();
    TetMesh & tvm( asy.volumeMesh() );
    tvm.clear();
    asy.initMeshBoundaries(ffr, 3);
    wc.stop();
    os << wc.elapsed() << "s." << endl;

    // build tetgen options for the case that they are not defined
    if (tetgen_opt.isEmpty()) {

      // assemble options string requires number-string conversion
      QLocale cloc(QLocale::English, QLocale::UnitedStates);
      cloc.setNumberOptions(QLocale::OmitGroupSeparator);

      // convert radius-to-edge ratio to number using current locale
      double r2e = asy.tgTetQuality();

      // and write to string using 'C' locale
      tetgen_opt = "pq" + cloc.toString(r2e, 'f', 3);
      tetgen_opt += "V";
    }
    
    wc.start();
    string fsmesh = bname + ".smesh";
    os << "Writing tetgen input file: " << fsmesh << " ... ";
    tvm.writeSmesh(fsmesh);
    wc.stop();
    os << wc.elapsed() << "s." << endl;

    wc.start();
    os << "Running tetgen with options: -" << tetgen_opt.toStdString() << endl;
    os << "tetgen output is written to " << (bname + "_tetgenlog.txt") << endl;
    if ( callTetgen(bname) ) {
      wc.stop();
      os << "tetgen runtime: " << wc.elapsed() << "s." << endl;

      wc.start();
      os << "Reading tetgen output files... ";
      tvm.readTetgen(bname+".1");
      wc.stop();
      os << wc.elapsed() << "s." << endl;

      if (writeEdgeMesh) {
        wc.start();
        os << "Writing EDGE mesh... ";
        tvm.writeMsh(bname+".bmsh");
        tvm.writeBoc(bname+".aboc");
        wc.stop();
        os << wc.elapsed() << "s." << endl;
      }

      if (writeCgnsMesh) {
        wc.start();
        os << "Writing CGNS mesh... ";
        tvm.writeCgns(bname+".cgns");
        wc.stop();
        os << wc.elapsed() << "s." << endl;
      }

      if (writeSu2Mesh) {
        wc.start();
        os << "Writing SU2 mesh... ";
        MxMesh mx;
        tvm.toMx(mx);
        mx.writeSU2(append_suffix(bname, ".su2"));
        wc.stop();
        os << wc.elapsed() << "s." << endl;
      }

#ifdef HAVE_NETCDF
      if (writeTauMesh) {
        wc.start();
        os << "Writing TAU mesh... ";
        MxMesh mx;
        tvm.toMx(mx);
        mx.writeTau(bname+".taumesh");
        wc.stop();
        os << wc.elapsed() << "s." << endl;
      }
#endif

    } else {
      os << "tetgen aborted with error." << endl;
    }

  } catch (Error & xcp) {
    os << "Batch mode terminated with error:" << endl;
    os << xcp.what();
    exit(EXIT_FAILURE);
  }
  
  return true;
}

bool BatchRun::parseOptions(int argc, char *argv[])
{
  bool doBatch = false;
  for (int i=0; i<argc; ++i) {

    QString val, opt = QString::fromUtf8( argv[i] );
    int pos = opt.indexOf('=');
    if (pos != -1) {
      val = opt.right( opt.length() - (pos+1) );
    }

    if (opt.contains("batch")) {
      doBatch = true;
    } else if (opt.contains("tetgen-options")) {
      tetgen_opt = val;
    } else if (opt.contains("output")) {
      writeIges = val.contains("iges");
      writeEdgeMesh = val.contains("edge");
      writeCgnsMesh = val.contains("cgns");
      writeTauMesh = val.contains("tau");
      writeDwfsMesh = val.contains("dwfs");
      writeSu2Mesh = val.contains("su2");
    } else if (opt.endsWith(".smx")) {
      baseFile = opt;
    } else if (opt.contains("help")) {
      printHelp();
      exit(EXIT_SUCCESS);
    }

  }

  if (baseFile.isEmpty())
    return false;

  return doBatch;
}

bool BatchRun::callTetgen(const string &bname)
{
  QStringList args;
  args << "-" + tetgen_opt << QString::fromStdString(bname + ".smesh");

  // path to tetgen must be stored in settings
  QString xpath;
  QString defpath = QCoreApplication::applicationDirPath() + "/tetgen";
  xpath = SumoMain::setting("tetgenpath", defpath).value<QString>();

  QProcess proc;
  proc.setWorkingDirectory(".");
  proc.start(xpath, args);
  bool stat = proc.waitForFinished(-1);

  // write tetgen output to separate file
  ofstream os( asPath(bname + "_tetgenlog.txt").c_str() );
  os << QString( proc.readAllStandardOutput() ).toStdString() << endl;
  os << QString( proc.readAllStandardError() ).toStdString() << endl;

  return stat;
}

void BatchRun::printHelp()
{
  const char helpText[] =
      "Surface modeling tool and mesh generator for aircraft configurations.\n"
      "Usage: dwfsumo -batch [options] aircraft.smx\n"
      "\n"
      "Options:\n"
      "-output=iges,dwfs,edge,cgns,tau,su2 \n"
      "        Generate output files for the \n"
      "        named formats. Will not start mesh generation unless at least\n"
      "        one mesh format (dwfs,edge,tau,cgns,su2) is named.\n"
      "        Default is -output=iges,dwfs,edge\n"
    #if !defined(HAVE_NETCDF)
      "Note: This version of sumo was compiled *without* support for NetCDF;\n"
      "therefore, the TAU mesh format is *not* supported.\n"
    #endif
      "-tetgen-options=flags \n"
      "        Call tetgen as in 'tetgen -flags model.smesh' when generating \n"
      "        a volume mesh.The default is -tetgen-options=pq1.4V\n"
      "\n"
      "Examples:\n"
      "dwfsumo -batch -output=iges aircraft.smx\n"
      "        Convert geometry of aircraft.smx to IGES and exit. Will not \n"
      "        generate any mesh.\n"
      "dwfsumo -batch -output=cgns,edge -tetgen-options=pq1.16VY aircraft.smx\n"
      "        First, generate a surface mesh (not written) for aircraft.smx,\n"
      "        then produce a volume mesh by calling\n"
      "        tetgen -pq1.16VY aircraft.smesh\n"
      "        on it, then convert the tetgen output to CGNS and EDGE files.\n";

  cout << helpText << endl;
}


