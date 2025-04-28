
// convert zipped xml to plaintext

#include <iostream>
#include <genua/xmlelement.h>
#include <genua/xcept.h>
#include <genua/strutils.h>
#include <genua/binfilenode.h>

using namespace std;

int main(int argc, char *argv[])
{
  try {
  
    if (argc != 2) {
      cerr << "Usage: zml2xml file.zml" << endl;
      return -2;
    }
    
    XmlElement xe;
    xe.read(argv[1]);
    xe.write( append_suffix(argv[1], ".xml"), XmlElement::PlainText );
    
  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  
  return 0;
}
