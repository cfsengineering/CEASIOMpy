
// print summary for zml file

#include <iostream>
#include <genua/xmlelement.h>
#include <genua/binfilenode.h>
#include <genua/xcept.h>
#include <genua/strutils.h>

using namespace std;

static void print_summary(const XmlElement &xe, int indent)
{
  string pfx(indent, ' ');
  cout << pfx << xe.name()
       << ", children: " << std::distance(xe.begin(), xe.end())
       << ", attributes: " << std::distance(xe.attrBegin(), xe.attrEnd())
       << endl;

  XmlElement::attr_iterator ait, alast = xe.attrEnd();
  for (ait = xe.attrBegin(); ait != alast; ++ait)
    cout << pfx << "  " << ait->first << " = " << ait->second << endl;

  XmlElement::const_iterator itr, elast = xe.end();
  for (itr = xe.begin(); itr != elast; ++itr)
    print_summary(*itr, indent+2);
}

int main(int argc, char *argv[])
{
  try {
  
    if (argc < 2) {
      cout << "Usage: " << argv[0] << " file.zml" << endl;
      return -1;
    }

    XmlElement xe;
    xe.read(argv[1]);
    print_summary(xe, 0);
    
  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  
  return 0;
}
