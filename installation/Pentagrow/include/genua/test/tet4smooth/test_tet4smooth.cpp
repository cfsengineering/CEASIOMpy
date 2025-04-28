
#include <genua/mxmesh.h>
#include <genua/timing.h>
#include <genua/xcept.h>

#include <iostream>

using namespace std;


int main(int argc, char *argv[])
{
  if (argc != 2) {
    cerr << "Usage: " << argv[0] << " mesh.zml" << endl;
    return -1;
  }

  try {

    XmlElement xe;
    xe.read( argv[1] );

    MxMesh mx;
    mx.fromXml(xe);
    mx.smoothTetNodes(3, 0.5);
    mx.toXml(true).zwrite("smoothed.zml",1);

  } catch (Error & xcp) {
    cerr << xcp.what();
    return -1;
  }

  return 0;
}
