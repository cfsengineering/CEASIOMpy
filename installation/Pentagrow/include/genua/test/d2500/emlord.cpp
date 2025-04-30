
#include <genua/dvector.h>

using namespace std;

extern "C"
{

// F77 routine converetd by f2c
double emlord_mod(const double *ell, const double *sn, const double *sb,
                  const int *nn, const double *xx, const double *ss);


}

double emlord(const double & ell, const double & sn, const double & sb,
              const Vector & xx, const Vector & ss)
{
  assert(xx.size() == ss.size());
  assert(xx.size() <= 400);
  int n(xx.size());
  return emlord_mod(&ell, &sn, &sb, &n, xx.pointer(), ss.pointer());
}

#include <fstream>

int main(int argc, char *argv[])
{
  if (argc != 2) {
    cerr << "Usage: " << argv[0] << " area.txt" << endl;
    return -1;
  }

  Vector xx, ss;
  Real x, s;
  ifstream in(argv[1]);
  while (in >> x >> s) {
    if (xx.empty() or s > 0) {
      xx.push_back(x);
      ss.push_back(s);
    } else {
      xx.back() = x;
      ss.back() = s;
    }
  }

  Real ell = xx.back() - xx.front();
  xx -= xx.front();
  xx /= ell;

  Real D = emlord(ell, 0.0, 0.0, xx, ss);
  cout << "Length: " << ell << endl;
  cout << "C Wave drag/q = " << D << endl;

  return 0;
}
