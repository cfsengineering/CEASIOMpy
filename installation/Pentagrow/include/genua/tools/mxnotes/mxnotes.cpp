
// convert zipped xml to plaintext

#include <iostream>
#include <genua/xmlelement.h>
#include <genua/xcept.h>
#include <genua/mxmesh.h>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    if (argc < 4) {
      cerr << "Usage: mxnotes command tag file1.zml [file2.zml] "
              " [file3.zml] ... " << endl;
      return -2;
    }
    
    string cmd(argv[1]);

    if (cmd == "extract") {
      const int nfile = argc-3;
      string tag(argv[2]);
      for (int i=0; i<nfile; ++i) {
        MxMesh mx;
        {
          XmlElement xe;
          xe.read(argv[3+i]);
          mx.fromXml(xe);
        }
        const XmlElement & note(mx.note());
        XmlElement::const_iterator itr = note.findChild(tag);
        if (itr != note.end())
          itr->xwrite(std::cout);
      }
    }
    
  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  
  return 0;
}
