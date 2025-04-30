
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#include "trafo.h"

using namespace std;

// SSE2 implementation in genua/incubator
// gain is only about 10% -- not worth the hassle 

void vertex_transform_4d(int npt, const double T[], 
                         const double A[], double B[])
{
  double A0, A1, A2, A3;
  int j;
  for (j=0; j<npt; ++j) {
    A0 = A[4*j+0];
    A1 = A[4*j+1];
    A2 = A[4*j+2];
    A3 = A[4*j+3];
    B[4*j+0] = T[0]*A0 + T[4]*A1 + T[ 8]*A2 + T[12]*A3;
    B[4*j+1] = T[1]*A0 + T[5]*A1 + T[ 9]*A2 + T[13]*A3;
    B[4*j+2] = T[2]*A0 + T[6]*A1 + T[10]*A2 + T[14]*A3;
    B[4*j+3] = T[3]*A0 + T[7]*A1 + T[11]*A2 + T[15]*A3;
  }
}
 
void vertex_transform_4f(int npt, const float T[], 
                         const float A[], float B[])
{
  float A0, A1, A2, A3;
  int j;
  for (j=0; j<npt; ++j) {
    A0 = A[4*j+0];
    A1 = A[4*j+1];
    A2 = A[4*j+2];
    A3 = A[4*j+3];
    B[4*j+0] = T[0]*A0 + T[4]*A1 + T[ 8]*A2 + T[12]*A3;
    B[4*j+1] = T[1]*A0 + T[5]*A1 + T[ 9]*A2 + T[13]*A3;
    B[4*j+2] = T[2]*A0 + T[6]*A1 + T[10]*A2 + T[14]*A3;
    B[4*j+3] = T[3]*A0 + T[7]*A1 + T[11]*A2 + T[15]*A3;
  }
}

void vertex_transform_3d(int npt, const double T[], const double A[], double B[])
{
  double A0, A1, A2;
  for (int j=0; j<npt; ++j) {
    A0 = A[3*j+0];
    A1 = A[3*j+1];
    A2 = A[3*j+2];
    B[3*j+0] = T[0]*A0 + T[3]*A1 + T[6]*A2;
    B[3*j+1] = T[1]*A0 + T[4]*A1 + T[7]*A2;
    B[3*j+2] = T[2]*A0 + T[5]*A1 + T[8]*A2;
  }
} 

void vertex_transform_3f(int npt, const float T[], const float A[], float B[])
{
  float A0, A1, A2;
  for (int j=0; j<npt; ++j) {
    A0 = A[3*j+0];
    A1 = A[3*j+1];
    A2 = A[3*j+2];
    B[3*j+0] = T[0]*A0 + T[3]*A1 + T[6]*A2;
    B[3*j+1] = T[1]*A0 + T[4]*A1 + T[7]*A2;
    B[3*j+2] = T[2]*A0 + T[5]*A1 + T[8]*A2;
  }
} 

/* ---------- Rotation ---------------------------------------------------- */

Rotation::Rotation()
{
  mat(0,0) = mat(1,1) = mat(2,2) = 1.0;
}

const Mtx33 & Rotation::rotate(const Vct3 & ax, double beta)
{
  // optimized version
  Mtx33 rv;
  Vct3 a(ax);
  normalize(a);
  
  // temporaries
  double t1, t10, t11, t12, t13, t14, t15, t16, t19;
  double t2, t21, t22, t23, t3, t6, t7, t8, t9;
  {
    t1 = a[0];
    t2 = t1*t1;
    sincosine(beta, t10, t3);
    // t3 = cos(beta);
    rv(0,0) = t2+t3*(1.0-t2);
    t6 = a[1];
    t7 = t1*t6;
    t8 = t3*t1;
    t9 = t8*t6;
    // t10 = sin(beta);
    t11 = a[2];
    t12 = t10*t11;
    rv(0,1) = t7-t9-t12;
    t13 = t1*t11;
    t14 = t8*t11;
    t15 = t10*t6;
    rv(0,2) = t13-t14+t15;
    rv(1,0) = t7-t9+t12;
    t16 = t6*t6;
    rv(1,1) = t16+t3*(1.0-t16);
    t19 = t6*t11;
    t21 = t3*t6*t11;
    t22 = t10*t1;
    rv(1,2) = t19-t21-t22;
    rv(2,0) = t13-t14-t15;
    rv(2,1) = t19-t21+t22;
    t23 = t11*t11;
    rv(2,2) = t23+t3*(1.0-t23);
  }
  mat = rv*mat;
  
  return mat;
}
  
const Mtx33 & Rotation::rotate(Real ax, Real ay, Real az)
{
  Vct3 x,y,z;
  x[0] = y[1] = z[2] = 1.;

  rotate(x,ax);
  rotate(y,ay);
  rotate(z,az);
  
  return mat;
}

void Rotation::forward(SMatrix<4,4> & hm) const
{
  SMatrix<4,4> trf;

  for (uint i=0; i<3; i++)
    for (uint j=0; j<3; j++)
      trf(i,j) = mat(i,j);
  trf(3,3) = 1;

  hm = trf*hm;
}

void Rotation::backward(SMatrix<4,4> & hm) const
{
  SMatrix<4,4> trf;

  for (uint i=0; i<3; i++)
    for (uint j=0; j<3; j++)
      trf(j,i) = mat(i,j);
  trf(3,3) = 1;

  hm = trf*hm;
}

Vct3 Rotation::axis() const
{
  // compute cos(beta)
  Real cb, beta;
  cb = 0.5*(mat(0,0) + mat(1,1) + mat(2,2) - 1);
  if (cb == 1)
    return vct(0,0,0);
  beta = acos(cb);

  // determine normalized axis
  Vct3 v;
  if (mat(0,0) >= cb)
    v[0] = sqrt( (mat(0,0)-cb)/(1-cb) ) * sign(-mat(1,2)/beta);
  if (mat(1,1) >= cb)
    v[1] = sqrt( (mat(1,1)-cb)/(1-cb) ) * sign(mat(0,2)/beta);
  if (mat(2,2) >= cb)
    v[2] = sqrt( (mat(2,2)-cb)/(1-cb) ) * sign(-mat(0,1)/beta);
  normalize(v);
  
  // Now, the above directions will not be correct for approx beta > 15deg
  // because they are based on a small-angle (beta) approximation. Therefore,
  // we need to find the correct signs by a solving three nonlinear equations.
  //  -v[2]*sin(beta) + v[0]*v[1]*(1 - cos(beta)) = mat(0,1)
  //  v[1]*sin(beta) + v[0]*v[2]*(1 - cos(beta)) = mat(0,2)
  //  -v[2]*sin(beta) + v[0]*v[1]*(1 - cos(beta)) = mat(0,1)
  // We don't want to do a Newton-type iteration here, so we approximate.
  // Due to the properties of the equations, only one of the three signs can be
  // wrong, so we identify the one for which the small-beta approximation gives
  // the largest error and correct it assuming that the other two directions 
  // are good.
  Real c1(0), c2(0), c3(0), cmax, sb;
  if (fabs(mat(0,1)) > gmepsilon)
    c1 = fabs(v[0]*v[1]*(1-cb)) / fabs(mat(0,1));
  if (fabs(mat(0,2)) > gmepsilon)
    c2 = fabs(v[0]*v[2]*(1-cb)) / fabs(mat(0,2));
  if (fabs(mat(1,2)) > gmepsilon)
    c3 = fabs(v[1]*v[2]*(1-cb)) / fabs(mat(1,2));
  cmax = max(c1, max(c2,c3));
  assert(std::isfinite(cmax));
  sb = sqrt(1 - sq(cb));
  
  if (c1 == cmax) 
    v[2] = fabs(v[2]) * sign( (-mat(0,1) + v[0]*v[1]*(1-cb))/sb );
  else if (c2 == cmax)
    v[1] = fabs(v[1]) * sign( (mat(0,2) - v[0]*v[2]*(1-cb))/sb );
  else
    v[0] = fabs(v[0]) * sign( (-mat(1,2) + v[1]*v[2]*(1-cb))/sb );
  
  return beta*v;
}

void Rotation::clear()
{
  // reset
  std::fill(mat.begin(), mat.end(), 0.0);
  mat(0,0) = mat(1,1) = mat(2,2) = 1.0;
}

/* ----------- RFrame ----------------------------------------------------- */

RFrame::RFrame()
{
  // Default reference is at (0,0,0) and has global axes.
  mat(0,0) = mat(1,1) = mat(2,2) = mat(3,3) = 1;
}

void RFrame::clear()
{
  mat.clear();
  mat(0,0) = mat(1,1) = mat(2,2) = mat(3,3) = 1;
}

Vct3 RFrame::getOrigin() const
{
  // return position of origin

  Vct3 orig;
  // orig is initialized with zeros == local origin
  orig = forward(orig);
  // now converted to global coords
  return orig;
}

void RFrame::translate(const Vct3 & v)
{
  // moves origin of local coordinate system by v (not _to_ v!)
  SMatrix<4,4> t;
  t(0,0) = t(1,1) = t(2,2) = t(3,3) = 1;
  for (uint i=0; i<3; i++)
    t(i,3) = v[i];
  mat = t* mat;
}

void RFrame::translate(Real dx, Real dy, Real dz)
{
  // moves origin of local coordinate system by (dx,dy,dz)

  SMatrix<4,4> t;
  t(0,0) = t(1,1) = t(2,2) = t(3,3) = 1;
  t(0,3) = dx;
  t(1,3) = dy;
  t(2,3) = dz;
  mat = t* mat;
}

void RFrame::rotate(Real betax, Real betay, Real betaz)
{
  // turn the axes system by specified angles IN RADIAN!
  Rotation rt;
  rt.rotate(betax,betay,betaz);
  rt.forward(mat);
}

void RFrame::rotate(const Vct3 & rotax, Real angle)
{
  Rotation rt;
  rt.rotate(rotax, angle);
  rt.forward(mat);
}

void RFrame::scale(Real xf, Real yf, Real zf)
{
  // scale with three supplied factors

  SMatrix<4,4> t;

  t(0,0) = xf;
  t(1,1) = yf;
  t(2,2) = zf;
  t(3,3) = 1;

  mat = t*mat;
}

void RFrame::mirror(const Vct3 & normal)
{
  // mirror about plane
  SMatrix<3,3> tmi;
  SMatrix<4,4> t;
  tmi(0,0) = tmi(1,1) = tmi(2,2) = 1;
  t(3,3) = 1;
  Vct3 v;
  v = normal.normalized();
  tmi -= 2. * dyadic(v,v);
  for (uint i=0; i<3; i++)
    for (uint j=0; j<3; j++)
      t(i,j) = tmi(i,j);
  mat = t*mat;
}

//Vct3 RFrame::backward(const Vct3 & a) const
//{
//  // transform global vector a into local coordinates
//
//  // convert to 4D
//  Vct4 v4d;
//  for (uint i=0; i<3; i++)
//    v4d(i) = a(i);
//  v4d(3) = 1;
//  v4d = lu_solve_copy(mat, v4d);
//
//  // convert back to 3d
//  Vct3 at;
//  for (uint i=0; i<3; i++)
//    at(i) = v4d(i) / v4d(3);
//
//  return at;
//}

Vct3 RFrame::forward(const Vct3 & a) const
{
  // convert to global coordinates

  // convert to 4D
  Vct4 v4d;
  for (uint i=0; i<3; i++)
    v4d(i) = a(i);
  v4d(3) = 1;
  v4d = mat*v4d;

  // convert back to 3d
  Vct3 at;
  for (uint i=0; i<3; i++)
    at(i) = v4d(i) / v4d(3);

  return at;
}





