#include <eeigen/Core>
#include <unsupported/eeigen/SpecialFunctions>
#include <iostream>
using namespace eeigen;
int main()
{
  Array4d v(-0.5,2,0,-7);
  std::cout << v.erf() << std::endl;
}
