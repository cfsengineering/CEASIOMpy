
#include <genua/defines.h>
#include <genua/blob.h>
#include <genua/typecode.h>
#include <iostream>
#include <fstream>

using namespace std;

template <typename POD>
void dump_float(const std::vector<POD> & v)
{
  Blob b;
  b.allocate( create_typecode<float>(), v.size() );
  b.inject( &v[0] );

  ofstream os("dumpfile");
  b.write(os);
}

template <typename POD>
void fetch(std::vector<POD> & v)
{
  Blob b;
  ifstream in("dumpfile");
  b.read( create_typecode<float>(), v.size(), in );
  b.extract( &v[0] );
}

int main(int, char **)
{
  size_t n(20);
  std::vector<double> x(n), y(n);
  for (size_t i=0; i<n; ++i) {
    x[i] = (i + 1) / 3.0;
    y[i] = 0.0;
  }

  dump_float(x);
  fetch(y);

  cout.precision(15);
  for (size_t i=0; i<n; ++i) {
    cout << x[i] << " : " << y[i] << endl;
  }

  return 0;
}
