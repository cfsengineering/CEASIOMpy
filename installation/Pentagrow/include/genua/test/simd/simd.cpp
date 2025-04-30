
#include <genua/defines.h>
#include <genua/simdsupport.h>
#include <genua/cbvops.h>
#include <genua/dvector.h>
#include <iostream>
#include <cstdlib>

using namespace std;

template <typename FloatType>
void rnd(int n, FloatType a[])
{
  for (int i=0; i<n; ++i)
    a[i] = 2*FloatType(rand()) / RAND_MAX - 1;
}

template <class SomeType>
inline SomeType expr(const SomeType &a, const SomeType &b, const SomeType &c)
{
  SomeType c1(PI);
  SomeType t1 = a*b / (-c) + sqrt(fabs(c)) - a;
  SomeType t2 = (b - a + c1) / fabs(c - a);
  return select(t1, t2, (a < b));
}

template <class SimdType>
bool test_ops()
{
  typedef typename SimdType::Scalar FloatT;
  const int N( SimdType::width() );
  FloatT a[N], b[N], c[N], d[N];
  rnd(N, a);
  rnd(N, b);
  rnd(N, c);

  for (int i=0; i<N; ++i)
    d[i] = expr(a[i], b[i], c[i]);

  SimdType va(a), vb(b), vc(c);
  SimdType vd = expr(va, vb, vc);

  FloatT sd[N];
  vd.store(sd);
  bool match = true;
  for (int i=0; i <N; ++i) {
    match &= (sd[i] == d[i]);
    cout << i << " : " << sd[i]-d[i] << endl;
  }
  return match;
}

// for asm inspection
float4 foo_f4(const float4 &a, const float4 &b, const float4 &c)
{
  return expr(a, b, c);
}

// for asm inspection
float8 foo_f8(const float8 &a, const float8 &b, const float8 &c)
{
  return expr(a, b, c);
}

// for asm inspection
float foo_maxval(DVector<float> &v)
{
  return internal::maxval(v.size(), v.pointer());
}

// for asm inspection
double foo_norm2f(DVector<double> &v)
{
  return std::sqrt(internal::sqsum(v.size(), v.pointer()));
}

// for asm inspection
void foo_axpyf(float a, const DVector<float> &x, float b, DVector<float> &y)
{
  internal::axpy(x.size(), a, x.pointer(), b, y.pointer());
}

// for asm inspection
void foo_axpyd(double a, const DVector<double> &x, double b, DVector<double> &y)
{
  internal::axpy(x.size(), a, x.pointer(), b, y.pointer());
}

int main(int, char **)
{
  bool ok = true;
  cout << "float4:" << endl;
  ok &= test_ops<float4>();
  cout << "float8:" << endl;
  ok &= test_ops<float8>();
  cout << "float16:" << endl;
  ok &= test_ops<float16>();
  cout << "double2:" << endl;
  ok &= test_ops<double2>();
  cout << "double4:" << endl;
  ok &= test_ops<double4>();
  cout << "double8:" << endl;
  ok &= test_ops<double8>();
  cout << "double16:" << endl;
  ok &= test_ops<double16>();
  cout << (ok ? "PASSED" : "FAILED") << endl;
}
