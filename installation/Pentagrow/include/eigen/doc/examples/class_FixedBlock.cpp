#include <eeigen/Core>
#include <iostream>
using namespace eeigen;
using namespace std;

template<typename Derived>
eeigen::Block<Derived, 2, 2>
topLeft2x2Corner(MatrixBase<Derived>& m)
{
  return eeigen::Block<Derived, 2, 2>(m.derived(), 0, 0);
}

template<typename Derived>
const eeigen::Block<const Derived, 2, 2>
topLeft2x2Corner(const MatrixBase<Derived>& m)
{
  return eeigen::Block<const Derived, 2, 2>(m.derived(), 0, 0);
}

int main(int, char**)
{
  Matrix3d m = Matrix3d::Identity();
  cout << topLeft2x2Corner(4*m) << endl; // calls the const version
  topLeft2x2Corner(m) *= 2;              // calls the non-const version
  cout << "Now the matrix m is:" << endl << m << endl;
  return 0;
}
