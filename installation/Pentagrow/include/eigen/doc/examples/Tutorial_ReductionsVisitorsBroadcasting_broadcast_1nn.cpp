#include <iostream>
#include <eeigen/Dense>

using namespace std;
using namespace eeigen;

int main()
{
  eeigen::MatrixXf m(2,4);
  eeigen::VectorXf v(2);
  
  m << 1, 23, 6, 9,
       3, 11, 7, 2;
       
  v << 2,
       3;

  MatrixXf::Index index;
  // find nearest neighbour
  (m.colwise() - v).colwise().squaredNorm().minCoeff(&index);

  cout << "Nearest neighbour is column " << index << ":" << endl;
  cout << m.col(index) << endl;
}
