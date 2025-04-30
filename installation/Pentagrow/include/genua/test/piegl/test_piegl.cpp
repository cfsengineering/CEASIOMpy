
#include <iostream>

using namespace std;

template <int degr, class FloatType>
int find_span(const FloatType knot[], int nkts, FloatType u)
{
  int bot, top, mid, n = nkts - degr - 2;
  if (u == knot[n+1])
    return n;
  else if (u == knot[0])
    return degr;

  bot = degr;
  top = n+1;
  mid = (bot+top) / 2;
  while (u < knot[mid] or u >= knot[mid+1]) {
    if (u < knot[mid])
      top = mid;
    else
      bot = mid;
    if (top-bot < 2)
      return bot;
    mid = (bot+top) / 2;
  }
  return mid;
}

template <int degr, int n, class FloatType>
void derive_basis(FloatType u, int span, const FloatType knot[], FloatType ders[])
{
  const int K = degr+1;
  FloatType ndu_[K*K];
  FloatType tleft[K], tright[K];
  std::fill(std::begin(ndu_), std::end(ndu_), FloatType(0));
  std::fill(std::begin(tleft), std::end(tleft), FloatType(0));
  std::fill(std::begin(tright), std::end(tright), FloatType(0));

#undef ndu
#define ndu(ki, kj)   ndu_[K*((kj)) + ((ki))]

  ndu(0,0) = 1.0;
  FloatType saved(0), temp(0);

#pragma clang loop vectorize(enable)
  for (int j=1; j <= degr; ++j) {
    tleft[j] = u - knot[span+1-j];
    tright[j] = knot[span+j] - u;
    saved = 0.0;
    for (int r=0; r<j; ++r) {
      ndu(j,r) = tright[r+1] + tleft[j-r];
      temp = ndu(r,j-1) / ndu(j,r);
      ndu(r,j) = saved + tright[r+1] * temp;
      saved = tleft[j-r] * temp;
    }
    ndu(j,j) = saved;
  }

  for (int j=0; j<=degr; ++j)
    ders[j*K] = ndu(j,degr);

  FloatType a_[K*K];
  std::fill(std::begin(a_), std::end(a_), FloatType(0));

#undef a
#define a(ki, kj)  a_[K*((kj)) + ((ki))]

#pragma clang loop vectorize(enable)
  for (int r=0; r<=degr; ++r) {

    int s1(0), s2(1);
    a(0,0) = 1.0;
    for (int k=1; k<=n; k++) {
      FloatType d(0.0);
      int rk, pk, j1, j2;
      rk = r-k;
      pk = degr-k;
      if ( r >= k ) {
        a(s2,0) = a(s1,0) / ndu(pk+1,rk);
        d = a(s2,0) * ndu(rk,pk);
      }

      j1 = (rk >= -1) ? 1 : -rk;
      j2 = (r-1 <= pk) ? (k-1) : (degr-r);

      for (int j=j1; j<=j2; j++) {
        a(s2,j) = (a(s1,j) - a(s1,j-1)) / ndu(pk+1,rk+j);
        d += a(s2,j) * ndu(rk+j,pk);
      }
      if ( r <= pk ) {
        a(s2,k) = -a(s1,k-1) / ndu(pk+1,r);
        d += a(s2,k) * ndu(r,pk);
      }
      ders[r*K + k] = d;
      std::swap(s1,s2);
    }
  }

  int r(degr);

  for (int k=1; k<=n; k++) {
    for (int j=0; j<=degr; j++)
      ders[j*K + k] *= r;
    r *= degr-k;
  }

#undef a
#undef ndu
}

int main(int argc, char **argv)
{
  const int p = 3+1;
  float knots[2*p+1];
  std::fill(knots, knots+p, 0.0);
  std::fill(knots+p+1, std::end(knots), 1.0);
  knots[p] = 0.5;

  for (int i=0; i<2*p+1; ++i)
    cout << knots[i] << ", ";
  cout << endl;

  float ders[3*p];
  std::fill(std::begin(ders), std::end(ders), 0.0);

  float t = 0.52;
  int nkts = std::end(knots) - std::begin(knots);
  int span = find_span<p-1>(knots, nkts, t);
  derive_basis<p-1,2>(t, span, knots, ders);

  cout << "ders = " << endl;
  for (int i=0; i<3; ++i) {
    for (int j=0; j<p; ++j)
      cout << ders[3*j + i] << ", ";
    cout << endl;
  }

}
