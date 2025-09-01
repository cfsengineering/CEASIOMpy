#include <eeigen/Sparse>
#include <vector>
#include <iostream>

typedef eeigen::SparseMatrix<double> SpMat; // declares a column-major sparse matrix type of double
typedef eeigen::Triplet<double> T;

void buildProblem(std::vector<T>& coefficients, eeigen::VectorXd& b, int n);
void saveAsBitmap(const eeigen::VectorXd& x, int n, const char* filename);

int main(int argc, char** argv)
{
  if(argc!=2) {
    std::cerr << "Error: expected one and only one argument.\n";
    return -1;
  }
  
  int n = 300;  // size of the image
  int m = n*n;  // number of unknows (=number of pixels)

  // Assembly:
  std::vector<T> coefficients;            // list of non-zeros coefficients
  eeigen::VectorXd b(m);                   // the right hand side-vector resulting from the constraints
  buildProblem(coefficients, b, n);

  SpMat A(m,m);
  A.setFromTriplets(coefficients.begin(), coefficients.end());

  // Solving:
  eeigen::SimplicialCholesky<SpMat> chol(A);  // performs a Cholesky factorization of A
  eeigen::VectorXd x = chol.solve(b);         // use the factorization to solve for the given right hand side

  // Export the result to a file:
  saveAsBitmap(x, n, argv[1]);

  return 0;
}

