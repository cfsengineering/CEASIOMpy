
// convert to zml format

#include <iostream>
#include <genua/mxmesh.h>
#include <genua/mxmeshtypes.h>
#include <genua/xcept.h>
#include <genua/strutils.h>

using namespace std;

int main(int argc, char *argv[])
{
  try {
  
    if (argc < 2) {
      cout << "Usage: " << argv[0] << " file [output.zml]" << endl;
      return -1;
    }

    string infile( argv[1] );
    string outfile( append_suffix(infile, ".zml") );
    if (argc > 2)
      outfile = string(argv[2]);

    MxMesh mx;
    mx.loadAny(infile);
    mx.writeAs(outfile, Mx::NativeFormat, 1);
    
  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  
  return 0;
}
