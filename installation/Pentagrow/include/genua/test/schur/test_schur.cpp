
#include <genua/dmatrix.h>
#include <genua/dvector.h>
#include <genua/timing.h>
#include <genua/eig.h>
#include <genua/smatrix.h>
#include <genua/schur.h>
#include <cstdlib>
#include <iostream>

using namespace std;

int main(int argc, char *argv[])
{
  const uint N(4);
  SMatrix<N,N> A, T, U;

  for (uint j=0; j<N; ++j)
    for (uint i=0; i<N; ++i)
      A(i,j) = Real(rand()) / RAND_MAX;
  A(N-1, N-1) = 1.5;

  cout << "A = " << endl << A << endl;

  schur_decomposition(A, T, U);

  cout << "Schur:" << endl;
  cout << "U = " << endl << U << endl;
  cout << "T = " << endl << T << endl;

  SVector<N,Complex> lambda;
  SMatrix<N,N> VL, VR;
  eig(A, lambda, VL, VR);

  cout << "eig:" << endl;
  cout << "VL = " << endl << VL << endl;
  cout << "VR = " << endl << VR << endl;
  cout << "lambda = " << endl << lambda << endl;

  cout << "A*VR - VR*diag(real(lambda)) = " << endl;
  cout << A*VR - VR*diag(realpart(lambda)) << endl;

  return EXIT_SUCCESS;
}
