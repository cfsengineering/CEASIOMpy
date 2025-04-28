
// convert any supported mesh format to taumesh, or complain

#include <iostream>
#include <genua/xmlelement.h>
#include <genua/xcept.h>
#include <genua/strutils.h>
#include <genua/mxmesh.h>
#include <genua/zipfile.h>
#include <genua/cgnsfile.h>

#if !defined(HAVE_NETCDF)
#error "netCDF support required."
#endif

using namespace std;

int main(int argc, char *argv[])
{
  try {
  
    if (argc != 2) {
      cerr << "Usage: taumesh meshfile.dat" << endl;
      return -2;
    }
    
    string infile(argv[1]);
    string suffix = infile.substr(infile.find_last_of('.'), string::npos);
    suffix = toLower(suffix);

    MxMesh mx;
    if (ZipFile::isZip(infile) or suffix == ".zml" or suffix == ".xml") {
      XmlElement xe;
      xe.read(argv[1]);
      if (xe.name() == "MxMesh") {
        mx.fromXml(xe);
      } else {
        cerr << "Unrecognized format for file: " << infile << endl;
        return 1;
      }
    } else if (CgnsFile::isCgns(infile)) {
      mx.readCgns(infile);
    } else {
      cerr << "Mesh file format nor recognized: " << infile << endl;
      return 1;
    }

    string ofile = append_suffix(infile, ".taumesh");
    mx.writeTau( ofile );
    
  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  
  return 0;
}
