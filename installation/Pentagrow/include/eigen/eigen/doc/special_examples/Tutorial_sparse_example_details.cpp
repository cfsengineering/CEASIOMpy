#include <eeigen/Sparse>
#include <vector>
#include <QImage>

typedef eeigen::SparseMatrix<double> SpMat; // declares a column-major sparse matrix type of double
typedef eeigen::Triplet<double> T;

void insertCoefficient(int id, int i, int j, double w, std::vector<T>& coeffs,
                       eeigen::VectorXd& b, const eeigen::VectorXd& boundary)
{
  int n = int(boundary.size());
  int id1 = i+j*n;

        if(i==-1 || i==n) b(id) -= w * boundary(j); // constrained coefficient
  else  if(j==-1 || j==n) b(id) -= w * boundary(i); // constrained coefficient
  else  coeffs.push_back(T(id,id1,w));              // unknown coefficient
}

void buildProblem(std::vector<T>& coefficients, eeigen::VectorXd& b, int n)
{
  b.setZero();
  eeigen::ArrayXd boundary = eeigen::ArrayXd::LinSpaced(n, 0,M_PI).sin().pow(2);
  for(int j=0; j<n; ++j)
  {
    for(int i=0; i<n; ++i)
    {
      int id = i+j*n;
      insertCoefficient(id, i-1,j, -1, coefficients, b, boundary);
      insertCoefficient(id, i+1,j, -1, coefficients, b, boundary);
      insertCoefficient(id, i,j-1, -1, coefficients, b, boundary);
      insertCoefficient(id, i,j+1, -1, coefficients, b, boundary);
      insertCoefficient(id, i,j,    4, coefficients, b, boundary);
    }
  }
}

void saveAsBitmap(const eeigen::VectorXd& x, int n, const char* filename)
{
  eeigen::Array<unsigned char,eeigen::Dynamic,eeigen::Dynamic> bits = (x*255).cast<unsigned char>();
  QImage img(bits.data(), n,n,QImage::Format_Indexed8);
  img.setColorCount(256);
  for(int i=0;i<256;i++) img.setColor(i,qRgb(i,i,i));
  img.save(filename);
}
