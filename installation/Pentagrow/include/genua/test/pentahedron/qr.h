#ifndef QR_H
#define QR_H

#include <genua/smallqr.h>
#include <genua/simdsupport.h>

inline float8 qr_alpha(const float8 & xsq, const float8 & x) {
  return copysign(sqrt(xsq), x);
}

template <int M, int N, typename SimdType>
inline SimdType sse_qr(SimdType a[], SimdType tau[])
{
#undef A
#define A(i,j)  a[i + j*M]

  // TODO : eliminate v by writing into a directly
  SimdType t[N], v[M];
  SimdType regular = SimdType::onemask();
  for (int j=0; j<N; ++j) {
    SimdType alpha = detail::generate_reflector<M,N,SimdType>(j, a, v, tau[j]);
    regular &= (alpha != SimdType(0.0f));
    detail::apply_reflector<M,N,SimdType>(j, tau[j], v, a, t);

    // store diagonal value of R and reflector in a
    A(j,j) = alpha;
    for (int i=j+1; i<M; ++i)
      A(i,j) = v[i];
  }

#undef A

  return regular;
}

template <int M, int N, typename SimdType>
inline SimdType sse_qrlls(SimdType a[], SimdType x[])
{
  assert(M >= N);

#undef A
#define A(i,j)  a[i + j*M]

  // factorize a
  SimdType tau[N];
  SimdType qrok = sse_qr<M,N>(a, tau);

  // apply householder transformation to x
  // x <- Q^T x
  SimdType vtx;
  for (int j=0; j<N; ++j) {
    SimdType ajj = A(j,j);
    A(j,j) = SimdType(1.0f);
    vtx = SimdType(0.0f);
    for (int i=j; i<M; ++i)
      vtx += x[i] * A(i,j);
    for (int i=j; i<M; ++i)
      x[i] -= tau[j] * vtx * A(i,j);
    A(j,j) = ajj;
  }

  // solve by backsubstitution with R
  for (int i=N-1; i>=0; --i) {
    for (int j=i+1; j<N; ++j)
      x[i] -= A(i,j)*x[j];
    x[i] /= A(i,i);
  }

  return qrok;

#undef A
}


//// manually unrolled (for AVX2)

///// return 1/y using approximate division operations
//template <typename SimdType>
//SimdType rcpapx(const SimdType &y)
//{
//#if defined(DIV_PREC) && (DIV_PREC == 0)
//  return recip(y);
//#elif defined(DIV_PREC) && (DIV_PREC == 1)
//  SimdType est = recip(y);
//  SimdType diff = SimdType(1.0f) - est*y;
//  return diff*est + est;
//#else
//  return SimdType(1.0f)/y;
//#endif
//}

///// return x/y using approximate division operations
//template <typename SimdType>
//SimdType divapx(const SimdType &x, const SimdType &y)
//{
//#if defined(DIV_PREC) && (DIV_PREC == 0)
//  return x*recip(y);
//#elif defined(DIV_PREC) && (DIV_PREC == 1)
//  SimdType est = recip(y);
//  SimdType diff = SimdType(1.0f) - est*y;
//  SimdType rcpy = diff*est + est;
//  return x*rcpy;
//#else
//  return x/y;
//#endif
//}

//template <typename Float, int k>
//inline Float sse_householder_4x4(const Float a[], Float v[], Float & tau)
//{
//  const int M(4);
//  const int N(4);
//  Float t[4];

//#undef x
//#undef A
//#define x(i)    a[(i) + k*M]
//#define A(i,j)  a[(i) + (j)*M]

//  // generate reflector

//  // xsq is dot(x,x)
//  Float xsq(0.0f);
//  for (int i=k; i<M; ++i)
//    xsq += x(i)*x(i);

//  // alpha is |x| with the opposite sign of x[0]
//  Float alpha = copysign(sqrt(xsq), -x(k));

//  // keep xsq equal to the squared norm of x by
//  // updating the contribution of the first component
//  xsq += xsq - 2.0f*x(k)*alpha;

//  // first value of the reflector is
//  // x(k) - alpha
//  // normalize v such that v[k] == 1.0
//  Float y = x(k) - alpha;
//  tau = divapx(2.0f*y*y, xsq);
//  y = rcpapx(y);
//  v[k] = Float(1.0f);
//  for (int i=k+1; i<M; ++i)
//    v[i] = x(i) * y;

//#undef x

//  // apply reflector

//  // t = tau * v^T * A
//  for (int j=k+1; j<N; ++j) {
//    t[j] = Float(0.0f);
//    for (int i=k; i<M; ++i)
//      t[j] += tau * A(i,j) * v[i];
//  }

//  // A = A - v * t;
//  for (int j=k+1; j<N; ++j) {
//    for (int i=k; i<M; ++i)
//      A(i,j) -= v[i] * t[j];
//  }

//  // return the diagonal value of R
//  return alpha;

//#undef A
//}

//template <typename SimdType>
//inline SimdType sse_qr_4x4(SimdType a[], SimdType tau[])
//{

//#undef A
//#define A(i,j)  a[(i) + (j)*4]

//  // unrolled
//  SimdType v[4], alpha, xsq, y, z;
//  SimdType regular = SimdType::onemask();

//  // k = 0

//#undef x
//#define x(i)    a[(i)]

//  // generate reflector
//  xsq = x(0)*x(0) + x(1)*x(1) + x(2)*x(2) + x(3)*x(3);
//  regular &= (xsq != SimdType(0.0f));
//  alpha = copysign(sqrt(xsq), -x(0));
//  xsq += xsq - 2.0f*x(0)*alpha;

//  y = x(0) - alpha;
//  tau[0] = divapx(2.0f*y*y, xsq);
//  y = rcpapx(y);
//  v[1] = x(1)*y;
//  v[2] = x(2)*y;
//  v[3] = x(3)*y;

//  // apply reflector
//  A(0,0) = alpha;
//  A(1,0) = v[1];
//  A(2,0) = v[2];
//  A(3,0) = v[3];

//  // A = A - v * t
//  z = tau[0]*(A(0,1) + A(1,1)*v[1] + A(2,1)*v[2] + A(3,1)*v[3]);
//  A(0,1) -= z;
//  A(1,1) -= v[1]*z;
//  A(2,1) -= v[2]*z;
//  A(3,1) -= v[3]*z;

//  z = tau[0]*(A(0,2) + A(1,2)*v[1] + A(2,2)*v[2] + A(3,2)*v[3]);
//  A(0,2) -= z;
//  A(1,2) -= v[1]*z;
//  A(2,2) -= v[2]*z;
//  A(3,2) -= v[3]*z;

//  z = tau[0]*(A(0,3) + A(1,3)*v[1] + A(2,3)*v[2] + A(3,3)*v[3]);
//  A(0,3) -= z;
//  A(1,3) -= v[1]*z;
//  A(2,3) -= v[2]*z;
//  A(3,3) -= v[3]*z;

//  // k = 1

//#undef x
//#define x(i)    a[(i) + 1*4]

//  // generate
//  xsq = x(1)*x(1) + x(2)*x(2) + x(3)*x(3);
//  regular &= (xsq != SimdType(0.0f));
//  alpha = copysign(sqrt(xsq), -x(1));
//  xsq += xsq - 2.0f*x(1)*alpha;

//  y = x(1) - alpha;
//  tau[1] = divapx(2.0f*y*y, xsq);
//  y = rcpapx(y);
//  v[2] = x(2)*y;
//  v[3] = x(3)*y;

//  // apply reflector
//  A(1,1) = alpha;
//  A(2,1) = v[2];
//  A(3,1) = v[3];

//  // A = A - v * t
//  z = tau[1]*(A(1,2) + A(2,2)*v[2] + A(3,2)*v[3]);
//  A(1,2) -= z;
//  A(2,2) -= v[2]*z;
//  A(3,2) -= v[3]*z;

//  z = tau[1]*(A(1,3) + A(2,3)*v[2] + A(3,3)*v[3]);
//  A(1,3) -= z;
//  A(2,3) -= v[2]*z;
//  A(3,3) -= v[3]*z;

//  // k = 2

//#undef x
//#define x(i)    a[(i) + 2*4]

//  // generate
//  xsq = x(2)*x(2) + x(3)*x(3);
//  regular &= (xsq != SimdType(0.0f));
//  alpha = copysign(sqrt(xsq), -x(2));
//  xsq += xsq - 2.0f*x(2)*alpha;

//  y = x(2) - alpha;
//  tau[2] = divapx(2.0f*y*y, xsq);
//  y = rcpapx(y);
//  v[3] = x(3)*y;

//  // apply reflector
//  A(2,2) = alpha;
//  A(3,1) = v[3];

//  // A = A - v * t
//  z = tau[2]*(A(2,3) + A(3,3)*v[3]);
//  A(2,3) -= z;
//  A(3,3) -= v[3]*z;

//  // k = 3

//#undef x
//#define x(i)    a[(i) + 3*4]

//  // generate
//  xsq = x(3)*x(3);
//  regular &= (xsq != SimdType(0.0f));
//  alpha = copysign(sqrt(xsq), -x(3));
//  xsq += xsq - 2.0f*x(3)*alpha;

//  y = x(3) - alpha;
//  tau[3] = divapx(2.0f*y*y, xsq);

//#undef x
//#undef A

//  return regular;
//}

//template <typename SimdType>
//inline SimdType sse_qrlls_4x4(SimdType a[], SimdType x[])
//{
//#undef A
//#define A(i,j)  a[i + j*4]

//  // factorize a
//  SimdType tau[4];
//  SimdType qrok = sse_qr_4x4(a, tau);

//  // test explicit unrolling, add FMA later
//  // TODO: check generated asm

////  // apply householder transformation to x
////  // x <- Q^T x
////  SimdType vtx;
////  for (int j=0; j<N; ++j) {
////    SimdType ajj = A(j,j);
////    A(j,j) = SimdType(1.0f);
////    vtx = SimdType(0.0f);
////    for (int i=j; i<M; ++i)
////      vtx += x[i] * A(i,j);
////    for (int i=j; i<M; ++i)
////      x[i] -= tau[j] * vtx * A(i,j);
////    A(j,j) = ajj;
////  }

//  // unrolled, TODO: FMA
//  // j = 0
//  // for (int i=j; i<M; ++i)
//  SimdType vtx;
//  vtx = x[0] + x[1]*A(1,0) + x[2]*A(2,0) + x[3]*A(3,0);
//  // for (int i=j; i<M; ++i)
//  x[0] -= tau[0]*vtx; // i=0
//  x[1] -= tau[1]*vtx*A(1,0); // i=1
//  x[2] -= tau[2]*vtx*A(2,0);
//  x[3] -= tau[3]*vtx*A(3,0);
//  // j = 1
//  // for (int i=j; i<M; ++i)
//  vtx = x[1] + x[2]*A(2,1) + x[3]*A(3,1);
//  // for (int i=j; i<M; ++i)
//  x[1] -= tau[1]; // i=1
//  x[2] -= tau[2]*vtx*A(2,1);
//  x[3] -= tau[3]*vtx*A(3,1);
//  // j = 2
//  // for (int i=j; i<M; ++i)
//  vtx = x[2] + x[3]*A(3,2);
//  // for (int i=j; i<M; ++i)
//  x[2] -= tau[2]*vtx;
//  x[3] -= tau[3]*vtx*A(3,2);
//  // j = 3
//  // vtx = x[3]
//  // for (int i=j; i<M; ++i)
//  x[3] -= tau[3]*x[3];

////  // solve by backsubstitution with R
////  for (int i=N-1; i>=0; --i) {
////    for (int j=i+1; j<N; ++j)
////      x[i] -= A(i,j)*x[j];
////    x[i] /= A(i,i);
////  }

//  // unrolled

//  // i = 3, no j-loop
//  x[3] *= recip(A(3,3));

//  // i = 2, j = 3
//  x[2] -= A(2,3) * x[3];
//  x[2] *= recip(A(2,2));

//  // i = 1, j = 2,3
//  x[1] -= A(1,2)*x[2] + A(1,3)*x[3];
//  x[1] *= recip(A(1,1));

//  // i = 0, j = 1,2,3
//  x[0] -= A(0,1)*x[1] + A(0,2)*x[2] + A(0,3)*x[3];
//  x[0] *= recip(A(0,0));

//  return qrok;

//#undef A
//}


#endif // QR_H
