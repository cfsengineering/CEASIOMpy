
// convert to zml format

#include <iostream>
#include <genua/mxmesh.h>
#include <genua/mxmeshtypes.h>
#include <genua/mxsolutiontree.h>
#include <genua/xcept.h>
#include <genua/strutils.h>
#include <genua/xmlelement.h>

using namespace std;

void split_arg(const std::string &s, std::string &fname, std::string &cname)
{
  const char *p = strchr(s.c_str(), '=');
  if (p == nullptr) {
    fname = s;
    cname = s;
  } else {
    int q = p-s.c_str();
    fname = s.substr(0, q);
    cname = s.substr(q+1);
    if (cname.empty())
      cname = fname;
    else if (cname.front() == '"' and cname.back() == '"')
      cname.substr(1, cname.size()-2);
  }
}

int main(int argc, char *argv[])
{
  try {
  
    if (argc < 3) {
      cout << "Usage: " << argv[0] << " file1 file2 [file3...]" << endl;
      return -1;
    }

    // XmlElement cfg;
    // cfg.read(argv[1]);

    string fname, cname;

    // result file based on first argument
    MxMesh mx;
    split_arg(argv[1], fname, cname);
    mx.loadAny(fname);

    MxSolutionTreePtr root = MxSolutionTree::create("Subcases");
    MxSolutionTreePtr stree = MxSolutionTree::create(cname);


    uint offset = 0;
    for (uint i=0; i<mx.nfields(); ++i)
      stree->appendField(offset+i);
    offset += mx.nfields();
    root->append(stree);

    for (int i=2; i<argc; ++i) {

      split_arg(argv[i], fname, cname);

      MxMesh mxi;
      mxi.loadAny(fname);
      if (mxi.nnodes() != mx.nnodes())
        throw Error("Mesh in '"+fname+"' is incompatible with first argument.");

      stree = MxSolutionTree::create(cname);
      for (uint i=0; i<mxi.nfields(); ++i) {
        stree->appendField( mx.appendField( mxi.field(i) ) );
      }
      offset += mxi.nfields();
      root->append(stree);
    }

    mx.solutionTree(root);
    mx.writeAs("merged.zml", Mx::NativeFormat, 1);
    
  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  
  return 0;
}
