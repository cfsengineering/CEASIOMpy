
#include <surf/nstreader.h>
#include <genua/csrmatrix.h>
#include <genua/xcept.h>
#include <genua/ioglue.h>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    if (argc < 2) {
      cerr << "Usage: " << argv[0] << " op4_matrix.dat" << endl;
      return -1;
    }

    CsrMatrix<Real> mtx;
    NstReader::readOp4Ascii(argv[1], mtx);
    mtx.toXml(true).zwrite( append_suffix(argv[1], ".zml") );

    ofstream bos( append_suffix(argv[1], ".b").c_str() );
    mtx.writeBin(bos);
    //mtx.toXml(true).write( append_suffix(argv[1], ".xml") );

//    // debugging
//    ofstream dbout( append_suffix(argv[1], ".dbg.txt").c_str() );
//    dbout << scientific;
//    dbout.precision(16);
//    mtx.writePlain( dbout );
//    dbout.close();

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
