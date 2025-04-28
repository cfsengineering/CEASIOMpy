
#include <genua/defines.h>
#include <genua/theodorsen.h>
#include <iostream>

using namespace std;

Complex heave(Real k)
{
  Complex Ck = theodorsen(k);
  return -M_PI*(Ck*Complex(0,2*k) - sq(k));
}

Complex pitch(Real k)
{
  Real a = 0.25;
  Complex Ck = theodorsen(k);
  return -M_PI*(- sq(k)*a - (1.0 + (1 - 2*a)*Ck)*Complex(0,k) - 2.0*Ck);
}

int main(int, char **)
{
  const int n = 101;
  double dk = 2.0 / (n-1);

  for (int i=0; i<n; ++i) {
    Real k = i*dk;
    Complex Ck = theodorsen(k);
    Complex La = pitch(k);
    cout << k << ' ' << Ck.real() << ' ' << Ck.imag()
         << ' ' << La.real() << ' ' << La.imag() << endl;
  }

  return 0;
}
