
#include <genua/benzispai.h>
#include <genua/sparseblockmatrix.h>
#include <genua/timing.h>
#include <genua/configparser.h>
#include <genua/csrmatrix.h>
#include <genua/xcept.h>
#include <iostream>
#include <fstream>

using namespace std;

typedef SparseBlockMatrix<double,1> PseudoMatrix;
typedef SparseBlockMatrix<double,2> BlockMatrix2d;
typedef SparseBlockMatrix<float,4> BlockMatrix4f;

int main(int argc, char *argv[])
{
  try {

    if (argc < 2) {
      cerr << "Usage: " << argv[0] << " sparsematrix.txt [droptol]" << endl;
      return -1;
    }

    // read scalar matrix from file
    CsrMatrix<float> ascal;

    ifstream in(argv[1]);
    if (strstr(argv[1], ".b"))
      ascal.readBin(in);
    else
      ascal.readPlain(in);
    cout << "nnz(A) = " << ascal.nonzero() << endl;

    double relDropTol = 0.0;
    if (argc > 2)
      relDropTol = atof(argv[2]);

    BlockMatrix4f ablock(ascal);

    BenziSparseInverse<float,4> ainv;
    //    bool ok = ainv.staticFactor(ablock);
    //    if (ok)
    //      cerr << "Static AINV succeeded." << endl;
    //    else
    //      cerr << "Static AINV failed." << endl;

    // bool ok = ainv.dynamicFactor(ablock, relDropTol);
    bool ok = ainv.dynamicFactor(ablock, relDropTol);
    if (ok)
      cerr << "Dynamic AINV succeeded." << endl;
    else
      cerr << "Dynamic AINV failed." << endl;

    cout << "nnz(Z) = " << ainv.zfactor().nonzero() << endl;
    cout << "nnz(W) = " << ainv.wtfactor().nonzero() << endl;

#ifndef NDEBUG

    if (ascal.nrows() < 20) {

      Matrix Z, W;
      ainv.zfactor().toDense(Z);
      ainv.wtfactor().toDense(W);
      W.transpose();

      cout << "Factor Z: " << endl << Z << endl;
      cout << "Factor W: " << endl << W << endl;

    } else {

      ofstream osz("z.txt");
      ainv.zfactor().writePlain(osz);

      ofstream osw("wt.txt");
      ainv.wtfactor().writePlain(osw);

    }

#endif

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
