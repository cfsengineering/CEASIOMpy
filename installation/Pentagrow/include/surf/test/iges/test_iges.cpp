
#include <iostream>
#include <fstream>
#include <genua/xcept.h>
#include <genua/timing.h>
#include <genua/cgmesh.h>
#include <genua/trimesh.h>
#include <surf/trimmedsurf.h>
#include <surf/igesfile.h>
#include <surf/igesdirentry.h>

using namespace std;

int main(int argc, char *argv[])
{

  try {

    if (argc != 2) {
      cerr << argv[0] << " testfile.igs" << endl;
      return -2;
    }

    Wallclock c;
    c.start("Reading IGES file... ");
    IgesFile file;
    file.read(argv[1]);
    c.stop("done. ");

    TriMesh all, part;

    c.start("Instatiating trimmed surfaces... ");
    IgesDirEntry entry;
    const int ndir = file.nDirEntries();
    for (int i=0; i<ndir; ++i) {
      file.dirEntry(2*i+1, entry);
      if (entry.etype == 144) {
        TrimmedSurf ts;
        string sfid = str(2*i+1) + 'P';
        if (ts.fromIges(file, entry)) {
          cout << "Successfully retrieved TrimmedSurf " << sfid;
          ts.rename(sfid);

          CgMesh cgm;
          ts.cgRep(cgm);

          part.clear();
          cgm.exportMesh(part);
          part.faceTag( 2*i+1 );
          all.merge(part);
          cout << ", " << part.nfaces() << '/' << all.nfaces() << endl;

        } else {
          cout << "Failed to read TrimmedSurf " << sfid << endl;
        }
      }

      // debug
      if (all.nfaces() > 6000000)
        break;

    }
    c.stop("done. ");

    all.toXml(true).zwrite( append_suffix(argv[1], ".zml") ,0 );

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
