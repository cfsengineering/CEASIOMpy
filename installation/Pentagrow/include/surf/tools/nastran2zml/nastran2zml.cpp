
#include <surf/nstmesh.h>
#include <surf/nstreader.h>
#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <genua/defines.h>
#include <genua/timing.h>
#include <genua/csrmatrix.h>
#include <genua/strutils.h>
#include <iostream>
#include <fstream>

using namespace std;

string assemble_filename(const std::string &naspath, const std::string &fname)
{
#ifdef GENUA_WIN32
  const char path_sep(92);  // backslash
#else
  const char path_sep('/');
#endif
  string::size_type pos;

  pos = naspath.find_last_of(path_sep);
  if (pos == string::npos)
    return fname;
  else
    return naspath.substr(0, pos+1) + fname;
}

int main(int argc, char *argv[])
{
  try {

    if (argc < 2) {
      cerr << "Usage: " << argv[0] << " nastran_output.f06|.bdf|.pch" << endl;
      return -1;
    }

    Wallclock clk;

    clk.start();
    NstMesh nst;
    nst.nstread( argv[1] );
    cout << "[t] Parsing of Nastran output file: " << clk.stop() << endl;

    clk.start();
    MxMesh mx;
    nst.toMx(mx);
    cout << "[t] Format conversion: " << clk.stop() << endl;

    CsrMatrix<Real> mgg, kgg;

    // look for mass/stiffness matrix files to put into annotation
    string mggfile = assemble_filename(argv[1], "mgg.dat");
    if ( file_exists(mggfile) ) {
      XmlElement xm("MassMatrix");
      try {
        NstReader::readOp4Ascii(mggfile, mgg);
        cout << "Found mass matrix: " << mgg.nrows()
             << " rows, nnz: " << mgg.nonzero() << endl;
      } catch (Error & xcp) {
        cerr << "Error while attempting to read mass matrix from '" << mggfile;
        cerr << "':" << endl;
        cerr << xcp.what();
      }
      xm.append( mgg.toXml(true) );
      mx.annotate( xm );
      cout << "Annotated mesh with mass matrix." << endl;
    }

    string kggfile = assemble_filename(argv[1], "kgg.dat");
    if ( file_exists(kggfile) ) {
      XmlElement xm("StiffnessMatrix");
      try {
        NstReader::readOp4Ascii(kggfile, kgg);
        cout << "Found stiffness matrix: " << kgg.nrows()
             << " rows, nnz: " << kgg.nonzero() << endl;
      } catch (Error & xcp) {
        cerr << "Error while attempting to read "
                "stiffness matrix from '" << mggfile;
        cerr << "':" << endl;
        cerr << xcp.what();
      }
      xm.append( kgg.toXml(true) );
      mx.annotate( xm );
      cout << "Annotated mesh with stiffness matrix." << endl;
    }

    clk.start();
    mx.toXml(true).zwrite( append_suffix(argv[1], ".zml") );
    cout << "[t] Writing ZML file: " << clk.stop() << endl;

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
