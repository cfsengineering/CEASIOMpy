#include <iostream>
#include <eeigen/Dense>

using namespace std;
int main()
{
  eeigen::MatrixXf mat(2,4);
  eeigen::VectorXf v(2);
  
  mat << 1, 2, 6, 9,
         3, 1, 7, 2;
         
  v << 0,
       1;
       
  //add v to each column of m
  mat.colwise() += v;
  
  std::cout << "Broadcasting result: " << std::endl;
  std::cout << mat << std::endl;
}
