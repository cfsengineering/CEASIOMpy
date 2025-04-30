
#include <genua/forward.h>
#include <genua/sdirk.h>
#include <iostream>

using namespace std;

class Springs : public StdSecondOrderSystem
{
public:

  Springs() {

    Real m1 = 1;
    Real m2 = 20;
    Real k1 = 140e6;
    Real k2 = 2e6;

    // f1 = 230 Hz
    // f2 = 1930 Hz

    // point masses
    m_M.resize(3,3);
    m_M(0,0) = m1;
    m_M(1,1) = m2;
    m_M(2,2) = m1;

    m_K.resize(3,3);
    m_K(0,0) = k1;
    m_K(0,1) = m_K(1,0) = -k1;
    m_K(1,1) = k1 + k2;
    m_K(1,2) = m_K(2,1) = -k2;
    m_K(2,2) = k2;

    m_C.resize(3,3);
    //cout << "M = " << endl << m_M << endl;
    //cout << "K = " << endl << m_K << endl;
  }

  void force(Real t, const Vector &u, const Vector &v, Vector &f)
  {
    if (t > 0.008)
      f = 0;
    else if (t > 0.006)
      f[2] = 1e5;
    else if (t > 0.004)
      f[2] = -1e5;
  }

};

int main(int argc, char *argv[])
{
  Springs sys;
  OwrenSimonsen22 itg;

  Real T = 1.0 / 230.3;
  Real h = 0.1*T;

  if (argc > 1)
    h = atof(argv[1])*T;

  Real ee(0), tf = 5.0*T;
  int n = tf/h;
  Vector un(3), vn(3), us(3), vs(3);
  un[1] = 0.1;
  for (int i=0; i<n; ++i) {
    cout << i*h << " " << un << " " << vn << " " << ee << endl;
    ee = itg.step(sys, i*h, h, un, vn, us, vs);
    un = us;
    vn = vs;
  }

  return EXIT_SUCCESS;
}
