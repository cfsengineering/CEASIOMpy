#include <eeigen/Core>
#include <unsupported/eeigen/SpecialFunctions>
#include <iostream>
using namespace eeigen;
int main()
{
  Array4d v(0.5,10,0,-1);
  std::cout << v.lgamma() << std::endl;
}
