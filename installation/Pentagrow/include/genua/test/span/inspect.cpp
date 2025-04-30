
// example to inspect compiler-generated asm 

#include "../../span.h"

template <size_t N>
void process_span( Span<float,N> s, float a )
{
  const size_t m = s.size();
  for (size_t i=0; i<m; ++i)
    s[i] += 3.0f * float(i)/a;
}

void example1(float p[], float a)
{
  Span<float, 8> s(p);
  process_span(s, a);
}

void example2(float p[], size_t n, float a)
{
  Span<float> s(p, n);
  process_span(s, a);
}