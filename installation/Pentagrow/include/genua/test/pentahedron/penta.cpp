
#include "penta.h"
#include "qr.h"

template <typename FloatType>
static inline int is_inside(const FloatType x[])
{
  FloatType zero(0.0), one(1.0);
  FloatType u = x[0];
  FloatType v = x[1];
  int mask(1);
  mask &= (u >= zero) & (u <= one);
  mask &= (v >= zero) & (v <= one);
  FloatType w = one - u - v;
  mask &= (w >= zero) & (w <= one);
  return mask;
}

template <typename FloatType>
static inline int tt4d_intersect(const FloatType ta[], const FloatType tb[])
{
  const FloatType *pa1 = &ta[0];
  const FloatType *pa2 = &ta[4];
  const FloatType *pa3 = &ta[8];
  const FloatType *pb1 = &tb[0];
  const FloatType *pb2 = &tb[4];
  const FloatType *pb3 = &tb[8];

  FloatType am[4*4], x[4];
#undef A
#define A(i,j) am[4*(j)+(i)]
  for (int k=0; k<4; ++k) {
    A(k,0) = ( pa2[k] - pa1[k] );
    A(k,1) = ( pa3[k] - pa1[k] );
    A(k,2) = - ( pb2[k] - pb1[k] );
    A(k,3) = - ( pb3[k] - pb1[k] );
    x[k] = pb1[k] - pa1[k];
  }
#undef A

  int mask = qrlls<4,4>(am, x);
  mask &= is_inside( &x[0] );
  mask &= is_inside( &x[2] );

  return mask;
}

int scalar_intersection( const Penta &pa, const Penta &pb )
{
  const int m[8*3] = {  0,1,2,
                        3,4,5,
                        0,1,4,
                        0,4,3,
                        1,2,5,
                        1,5,4,
                        0,3,5,
                        0,5,2 };

  int mask(0);
  Vct4f ta[3], tb[3];
  for (int i=0; i<8; ++i) {
    const int *vi = &m[3*i];
    for (int k=0; k<3; ++k)
      ta[k] = pa.pts[vi[k]];
    for (int j=0; j<8; ++j) {
      const int *vj = &m[3*j];
      for (int k=0; k<3; ++k)
        tb[k] = pb.pts[vj[k]];
      mask |= tt4d_intersect( ta[0].pointer(), tb[0].pointer() );
    }
  }

  return mask;
}

template <typename SimdType>
static inline SimdType sse_is_inside(const SimdType x[])
{
  SimdType zero(0.0f), one(1.0f);
  SimdType u = x[0];
  SimdType v = x[1];
  SimdType mask = SimdType::onemask();
  mask &= (u >= zero) & (u <= one);
  mask &= (v >= zero) & (v <= one);
  SimdType w = one - u - v;
  mask &= (w >= zero) & (w <= one);
  return mask;
}

template <typename SimdType>
static inline SimdType sse_tt4d_intersect(const SimdType ta[], const SimdType tb[])
{
  const SimdType *pa1 = &ta[0];
  const SimdType *pa2 = &ta[4];
  const SimdType *pa3 = &ta[8];
  const SimdType *pb1 = &tb[0];
  const SimdType *pb2 = &tb[4];
  const SimdType *pb3 = &tb[8];

  SimdType am[4*4], x[4];
#undef A
#define A(i,j) am[4*(j)+(i)]
  for (int k=0; k<4; ++k) {
    A(k,0) = ( pa2[k] - pa1[k] );
    A(k,1) = ( pa3[k] - pa1[k] );
    A(k,2) = - ( pb2[k] - pb1[k] );
    A(k,3) = - ( pb3[k] - pb1[k] );
    x[k] = pb1[k] - pa1[k];
  }
#undef A

  SimdType mask = sse_qrlls<4,4>(am, x);
  mask &= sse_is_inside( &x[0] );
  mask &= sse_is_inside( &x[2] );

  return mask;
}

static inline float4 sse_gather_coordinate(const Penta &pa,
                                           int offset, int ip, int jc)
{
  float c[4] ALIGNED_SSE;
  for (int k=0; k<4; ++k) {
    int v = Penta::index(offset+k, ip);
    c[k] = pa.pts[v][jc];
  }
  return float4(c);
}

static inline float8 avx_gather_coordinate(const Penta &pa, int ip, int jc)
{
  float c[8] ALIGNED_AVX;
  for (int k=0; k<8; ++k) {
    int v = Penta::index(k, ip);
    c[k] = pa.pts[v][jc];
  }
  return float8(c);
}

int sse_intersection( const Penta &pa, const Penta &pb )
{
  const int m[8*3] = {  0,1,2,
                        3,4,5,
                        0,1,4,
                        0,4,3,
                        1,2,5,
                        1,5,4,
                        0,3,5,
                        0,5,2 };

  float4 ta[12], tb[12];
  float4 mask = float4::zeromask();
  for (int i=0; i<8; ++i) {

    // broadcast triangle i into ta
    const int *vi = &m[3*i];
    const float *tip0 = pa.pts[vi[0]].pointer();
    const float *tip1 = pa.pts[vi[1]].pointer();
    const float *tip2 = pa.pts[vi[2]].pointer();

    for (int k=0; k<4; ++k) {
      ta[0+k] = float4( tip0[k] );
      ta[4+k] = float4( tip1[k] );
      ta[8+k] = float4( tip2[k] );
    }

    // fetch four triangles into tb, where the simd lanes correspond to
    // different triangles (leads to shuffle instructions)
    for (int k=0; k<3; ++k)
      for (int l=0; l<4; ++l)
        tb[4*k+l] = sse_gather_coordinate(pb, 0, k, l);
    mask |= sse_tt4d_intersect( ta, tb );

    for (int k=0; k<3; ++k)
      for (int l=0; l<4; ++l)
        tb[4*k+l] = sse_gather_coordinate(pb, 4, k, l);
    mask |= sse_tt4d_intersect( ta, tb );
  }

  return mask.signbits() != 0;
}

int avx_intersection( const Penta &pa, const Penta &pb )
{
  const int m[8*3] = {  0,1,2,
                        3,4,5,
                        0,1,4,
                        0,4,3,
                        1,2,5,
                        1,5,4,
                        0,3,5,
                        0,5,2 };

  float8 ta[12], tb[12];
  float8 mask = float8::zeromask();
  for (int i=0; i<8; ++i) {

    // broadcast triangle i into ta
    const int *vi = &m[3*i];
    const float *tip0 = pa.pts[vi[0]].pointer();
    const float *tip1 = pa.pts[vi[1]].pointer();
    const float *tip2 = pa.pts[vi[2]].pointer();

    for (int k=0; k<4; ++k) {
      ta[0+k] = float8( tip0[k] );
      ta[4+k] = float8( tip1[k] );
      ta[8+k] = float8( tip2[k] );
    }

    // fetch eight triangles into tb, where the simd lanes correspond to
    // different triangles (leads to shuffle instructions)
    for (int k=0; k<3; ++k)
      for (int l=0; l<4; ++l)
        tb[4*k+l] = avx_gather_coordinate(pb, k, l);
    mask |= sse_tt4d_intersect( ta, tb );
  }

  return mask.signbits() != 0;
}

/*

static inline float8 unrolled_tt4d_intersect(const float8 ta[], const float8 tb[])
{
  const float8 *pa1 = &ta[0];
  const float8 *pa2 = &ta[4];
  const float8 *pa3 = &ta[8];
  const float8 *pb1 = &tb[0];
  const float8 *pb2 = &tb[4];
  const float8 *pb3 = &tb[8];

  float8 am[4*4], x[4];
#undef A
#define A(i,j) am[4*(j)+(i)]
  for (int k=0; k<4; ++k) {
    A(k,0) = ( pa2[k] - pa1[k] );
    A(k,1) = ( pa3[k] - pa1[k] );
    A(k,2) = - ( pb2[k] - pb1[k] );
    A(k,3) = - ( pb3[k] - pb1[k] );
    x[k] = pb1[k] - pa1[k];
  }
#undef A

  float8 mask = sse_qrlls_4x4(am, x);
  mask &= sse_is_inside( &x[0] );
  mask &= sse_is_inside( &x[2] );

  return mask;
}

// icpc -axCORE-AVX2   : for AVX-FMA
// -inline-factor=900  : to inline QR factorization, otherwise cpuid check in inner loop
// -unroll-aggressive

int unrolled_intersection( const Penta &pa, const Penta &pb )
{
  const int m[8*3] = {  0,1,2,
                        3,4,5,
                        0,1,4,
                        0,4,3,
                        1,2,5,
                        1,5,4,
                        0,3,5,
                        0,5,2 };

  float8 ta[12], tb[12];
  float8 mask = float8::zeromask();
  for (int i=0; i<8; ++i) {

    // broadcast triangle i into ta
    const int *vi = &m[3*i];
    const float *tip0 = pa.pts[vi[0]].pointer();
    const float *tip1 = pa.pts[vi[1]].pointer();
    const float *tip2 = pa.pts[vi[2]].pointer();

    for (int k=0; k<4; ++k) {
      ta[0+k] = float8( tip0[k] );
      ta[4+k] = float8( tip1[k] );
      ta[8+k] = float8( tip2[k] );
    }

    // fetch eight triangles into tb, where the simd lanes correspond to
    // different triangles (leads to shuffle instructions)
    for (int k=0; k<3; ++k)
      for (int l=0; l<4; ++l)
        tb[4*k+l] = avx_gather_coordinate(pb, k, l);
    mask |= unrolled_tt4d_intersect( ta, tb );
  }

  return mask.signbits() != 0;
}

*/
