
// convert MxMesh to FFA format

#include <iostream>
#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <genua/strutils.h>
#include <genua/timing.h>

using namespace std;

MxMeshPtr create_big_mesh(size_t nv, size_t ne)
{
  MxMeshPtr mxp = boost::make_shared<MxMesh>();

  mxp->appendNodes( PointList<3>(nv) );

  // keep indices in range, cgns may check index range...
  Indices idx(4*ne);
  for (size_t i=0; i<4*ne; ++i)
    idx[i] = lrand48() % nv;

  mxp->appendSection( Mx::Tet4, idx );
  return mxp;
}

int main(int argc, char *argv[])
{
  Wallclock clk;

  try {

    /*

    if (argc != 2) {
      cerr << "Usage: zml2bmsh file.zml" << endl;
      return -2;
    }

    MxMesh mx;
    cout << "Reading ZML file: " << argv[1] << endl;
    {
      XmlElement xe;
      cout << "XmlElement::read()" << endl;
      xe.read(argv[1]);
      cout << "MxMesh::fromXml()" << endl;
      mx.fromXml(xe);
    }
    cout << "Writing FFA file..." << endl;
    mx.writeFFA( string(argv[1]) + ".conv" );
    
    */

    size_t n = 1024*1024;
    for (int i=0; i<4; ++i) {

      cout << "Creating mesh with " << n/1000000 << " MNodes, "
           << 5*n/1000000 << " MTets..." << endl;
      MxMeshPtr mxp = create_big_mesh(n, 5*n);
      cout << "Reported mesh size: " << mxp->megabytes() << " MBytes." << endl;

      string fname = "mesh" + str(i+1);

      //      cout << "Writing CGNS file: " << fname << " ... ";
      //      mxp->writeCgns(fname);
      //      cout << " OK." << endl;

      cout << "Writing ZML through GBF file ... ";
      string gbfFile = append_suffix(fname, ".zml");
      string lz4File = append_suffix(fname, ".lz4");
      {
        clk.start();
        BFNodePtr zbf = mxp->toXml(true).toGbf(true);
        clk.stop();
        cout << "Conversion: " << clk.elapsed() << endl;

        clk.start();
        zbf->write( gbfFile, BinFileNode::PlainBinary);
        clk.stop();
        cout << "Plain binary: " << clk.elapsed() << endl;

        clk.start();
        zbf->write( lz4File, BinFileNode::CompressedLZ4 );
        clk.stop();
        cout << "Compressed: " << clk.elapsed() << endl;
      }

      cout << "Re-reading ZML through LZ4 file ... ";
      clk.start();
      BFNodePtr bfp = BinFileNode::read( lz4File );
      clk.stop();
      cout << "Reading LZ4: " << clk.elapsed() << endl;

      if (bfp) {
        // cout << "Read summary: " << endl;
        // bfp->summary(std::cout);
        MxMeshPtr rrm = boost::make_shared<MxMesh>();
        {
          clk.start();
          XmlElement xe;
          xe.fromGbf(bfp);
          clk.stop();
          cout << "XmlElement::fromGbf(): " << clk.elapsed() << endl;

          clk.start();
          rrm->fromXml(xe);
          clk.stop();
          cout << "MxMesh::fromXml(): " << clk.elapsed() << endl;
        }
        if (rrm->nnodes() != mxp->nnodes())
          cout << "Node count mismatch: " << rrm->nnodes() << endl;
        else
          cout << "OK: Node count." << endl;
        if (rrm->nelements() != mxp->nelements())
          cout << "Element count mismatch: " << rrm->nelements() << endl;
        else
          cout << "OK: Element count." << endl;
      } else {
        cout << "Read failed: format not recognized." << endl;
      }

      //      cout << "Writing FFA file: " << fname << " ... ";
      //      mxp->writeFFA(fname);
      //      cout << " OK." << endl;

      n *= 2;
    }


  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  
  return 0;
}
