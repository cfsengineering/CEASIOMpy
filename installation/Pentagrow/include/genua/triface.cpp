
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
 
#include "trimesh.h"
#include "triface.h"
#include "plane.h"

static inline Real lparm(const Vct3 & pt, const Vct3 & p1, const Vct3 & p2) 
{
  Vct3 lnv(p2 - p1), dst(pt - p1);
  return clamp(dot(lnv,dst)/sq(lnv), 0.0, 1.0);
}

bool TriFace::inRange() const
{
  const uint nv = msh->nvertices();
  if (v[0] < nv and v[1] < nv and v[2] < nv)
    return true;
  return false;
}

Vct3 TriFace::eval(Real up, Real vp) const
{
  assert(msh != 0);
  const Vct3 & p1(msh->vertex(v[0]));
  const Vct3 & p2(msh->vertex(v[1]));
  const Vct3 & p3(msh->vertex(v[2]));
  
  Real wp = (1.0 - up - vp);
  return wp * p1 + up * p2 + vp * p3;
}

Vct3 TriFace::center() const 
{
  assert(msh != 0);
  const Vct3 & p1(msh->vertex(v[0]));
  const Vct3 & p2(msh->vertex(v[1]));
  const Vct3 & p3(msh->vertex(v[2]));
  return (p1 + p2 + p3) * (1.0 / 3.0);
}

Vct3 TriFace::normal() const 
{
  assert(msh != 0);
  const Vct3 & p1(msh->vertex(v[0]));
  const Vct3 & p2(msh->vertex(v[1]));
  const Vct3 & p3(msh->vertex(v[2]));
  return cross(p2-p1, p3-p1);
}

Real TriFace::area() const 
{
  assert(msh != 0);
  const Vct3 & p1(msh->vertex(v[0]));
  const Vct3 & p2(msh->vertex(v[1]));
  const Vct3 & p3(msh->vertex(v[2]));
  return 0.5*norm(cross(p2-p1, p3-p1));
}

Real TriFace::normal(Vct3 & nrm) const 
{
  assert(msh != 0);
  const Vct3 & p1(msh->vertex(v[0]));
  const Vct3 & p2(msh->vertex(v[1]));
  const Vct3 & p3(msh->vertex(v[2]));
  nrm = cross(p2-p1, p3-p1);
  return normalize(nrm);
}

Real TriFace::corner(uint gv) const
{
  // compute corner angle
  assert(msh != 0);
  const Vct3 & pt1( msh->vertex(v[0]) );
  const Vct3 & pt2( msh->vertex(v[1]) );
  const Vct3 & pt3( msh->vertex(v[2]) );
  if (gv == v[0]) 
    return arg(pt3-pt1, pt2-pt1);
  else if (gv == v[1]) 
    return arg(pt3-pt2, pt1-pt2);
  else if (gv == v[2]) 
    return arg(pt2-pt3, pt1-pt3);
  else
    throw Error("Face does not contain vertex ",gv);
}

Real TriFace::solidAngle(uint idx) const 
{
  // compute solid angle associated with vertex idx
  assert(msh != 0);
  Vct3 b, c, a( msh->normal(idx) );
  if (idx == v[0]) {
    b = (msh->vertex(v[1]) - msh->vertex(v[0])).normalized();
    c = (msh->vertex(v[2]) - msh->vertex(v[0])).normalized();
  } else if (idx == v[1]) {
    b = (msh->vertex(v[2]) - msh->vertex(v[1])).normalized();
    c = (msh->vertex(v[0]) - msh->vertex(v[1])).normalized();
  } else if (idx == v[2]) {
    b = (msh->vertex(v[0]) - msh->vertex(v[2])).normalized();
    c = (msh->vertex(v[1]) - msh->vertex(v[2])).normalized();
  } else {
    throw Error("This face does not contain vertex ",idx);
  }

  Real alpha, beta, gamma;
  Vct3 sab, sbc, sca, x1, x2;
  sab = cross(a,b);
  sbc = cross(b,c);
  sca = cross(c,a);

  x1 = cross(sab, a);
  x2 = cross(a, sca);
  if (norm(x1)*norm(x2) < gmepsilon)
      return 0;
  alpha = arg(x1, x2);
  
  x1 = cross(sbc, b);
  x2 = cross(b, sab);
  if (norm(x1)*norm(x2) < gmepsilon)
      return 0;
  beta = arg(x1, x2);
  
  x1 = cross(sca, c);
  x2 = cross(c, sbc);
  if (norm(x1)*norm(x2) < gmepsilon)
      return 0;
  gamma = arg(x1, x2);

  Real s = sign(dot(a, normal()));
  return s*(alpha + beta + gamma - PI);
}

Vct3 TriFace::project(const Vct3 & pt) const
{
  // project point onto face plane, return (xi,eta,dist)
  // where dist is positive if point lies in normal direction
  assert(msh != 0);
  const Vct3 & p1( msh->vertex(v[0]) );
  const Vct3 & p2( msh->vertex(v[1]) );
  const Vct3 & p3( msh->vertex(v[2]) );

  Vct3 nrm, va, vb, vXi, vEta;
  va = p2 - p1;
  vb = p3 - p1;
  nrm = cross(va,vb);
  normalize(nrm);
  vXi = va - vb*(dot(va,vb)/dot(vb,vb));
  vEta = vb - va*(dot(va,vb)/dot(va,va));

  Vct3 s;
  s[0] = dot(pt-p1, vXi) / dot(vXi,vXi);
  s[1] = dot(pt-p1, vEta) / dot(vEta,vEta);
  s[2] = dot(pt-p1,nrm);

  return s;
}

Vct3 TriFace::pierce(const Vct3 & a, const Vct3 & b) const
{
  Vct3 q1 = project(a);
  Vct3 q2 = project(b);

  Vct3 uvt;
  if ( fabs(q1[2]-q2[2]) > gmepsilon ) {
    Real t = q1[2]/(q1[2] - q2[2]);
    uvt[0] = q1[0] + t*(q2[0] - q1[0]);
    uvt[1] = q1[1] + t*(q2[1] - q1[1]);
    uvt[2] = t;
  } else {
    uvt[0] = uvt[1] = uvt[2] = huge;
  }
  
  return uvt;
}

Real TriFace::minDistance(const Vct3 & pt, Vct2 & foot) const
{
  // projection of point onto face
  Real up, vp, wp, best(huge);
  Vct3 pj = TriFace::project(pt);
  up = pj[0];
  vp = pj[1];
  wp = 1. - up - vp;

  // projection foot is inside triangle
  if (up >= 0 and vp >= 0 and wp >= 0) {
    foot = vct(up,vp);
    best = pj[2];
  }

  // project on edges of triangle
  else {

    Real lp, dl;
    const Vct3 & pt1(msh->vertex(v[0]));
    const Vct3 & pt2(msh->vertex(v[1]));
    const Vct3 & pt3(msh->vertex(v[2]));
    Vct2 q1( vct(0,0) );
    Vct2 q2( vct(1,0) );
    Vct2 q3( vct(0,1) );

    // project on line pt1 - pt3
    if (up <= 0) {
      lp = lparm(pt, pt1, pt3);
      dl = norm(pt - (1-lp)*pt1 -lp*pt3);
      if (dl < best) {
        foot = (1-lp)*q1 + lp*q3;
        best = dl;
      }
    }

    // project on line pt1 - pt2
    if (vp <= 0) {
      lp = lparm(pt, pt1, pt2);
      dl = norm(pt - (1-lp)*pt1 -lp*pt2);
      if (dl < best) {
        foot = (1-lp)*q1 + lp*q2;
        best = dl;
      }
    }

    // project on line pt2 - pt3
    if (wp <= 0) {
      lp = lparm(pt, pt2, pt3);
      dl = norm(pt - (1-lp)*pt2 -lp*pt3);
      if (dl < best) {
        foot = (1-lp)*q2 + lp*q3;
        best = dl;
      }
    }
    
    // use the same sign convention as project()
    up = foot[0];
    vp = foot[1];
    wp = 1.0 - up - wp;
    Vct3 nrm( cross(pt2-pt1, pt3-pt1) );
    normalize(nrm);
    Vct3 dst( pt - (wp*pt1 + up*pt2 + vp*pt3) );
    best = dot(dst, nrm);
  }
  
  return best;  
}

bool TriFace::intersect(const Plane & pln, Vct3 & src, Vct3 & trg) const
{
  // number of edges intersecting plane
  int nis = 0;

  // iterate over edges, find intersection of edge and plane
  for (int i=0; i<3; ++i) {
    const Vct3 & p1( msh->vertex(v[i]) );         // 0, 1, 2
    const Vct3 & p2( msh->vertex(v[(i+1)%3]) );   // 1, 2, 0
    PlnIts its = pln.pierce(p1, p2);
    Real t = its.parm;
    if (its.pierces and t >= 0.0 and t <= 1.0) {
      if (nis == 0)
        src = its.pt;
      else
        trg = its.pt;
      ++nis;
    }
    if (nis == 2)
      return true;
  }

  return false;
}

Vct3 TriFace::gradient(const Vector & x) const
{
  Vct3 xv;
  xv[0] = x[v[0]];
  xv[1] = x[v[1]];
  xv[2] = x[v[2]];
  
  Mtx33 grad;
  gradient(grad);
  return grad*xv;
}
    
CpxVct3 TriFace::gradient(const CpxVector & x) const
{
  CpxVct3 xv, gx;
  xv[0] = x[v[0]];
  xv[1] = x[v[1]];
  xv[2] = x[v[2]];
  
  Mtx33 gm;
  gradient(gm);    
  
  gx[0] = gm(0,0)*xv[0] + gm(0,1)*xv[1] + gm(0,2)*xv[2];
  gx[1] = gm(1,0)*xv[0] + gm(1,1)*xv[1] + gm(1,2)*xv[2];
  gx[2] = gm(2,0)*xv[0] + gm(2,1)*xv[1] + gm(2,2)*xv[2];
  return gx;
}

void TriFace::gradient(Mtx33 & gm) const
{
  // fetch node coordinates and compute normal
  const Vct3 & pt1(msh->vertex(v[0]));
  const Vct3 & pt2(msh->vertex(v[1]));
  const Vct3 & pt3(msh->vertex(v[2]));
  Vct3 nrm = cross(pt2-pt1, pt3-pt1);
  normalize(nrm);

  // compute gradient matrix
  // this is a 3x3 matrix inversion optimized by
  // common subexpression elimination
  Real t1, t10, t12, t13, t16, t19, t2, t20, t22;
  Real t24, t25, t26, t29, t30, t35, t36, t39;
  Real t4, t41, t44, t46, t47, t48, t5, t52, t55;
  Real t57, t6, t60, t62, t7, t9;
  t1 = nrm[2];
  t2 = pt3[1];
  t4 = pt1[1];
  t5 = t1*t4;
  t6 = nrm[1];
  t7 = pt3[2];
  t9 = pt1[2];
  t10 = t6*t9;
  t12 = pt2[0];
  t13 = t12*t1;
  t16 = t12*t6;
  t19 = pt1[0];
  t20 = t19*t1;
  t22 = t19*t6;
  t24 = pt3[0];
  t25 = t24*t1;
  t26 = pt2[1];
  t29 = t24*t6;
  t30 = pt2[2];
  t35 = nrm[0];
  t36 = t35*t26;
  t39 = t35*t4;
  t41 = t35*t30;
  t44 = t35*t9;
  t46 = -t13*t2+t13*t4+t16*t7-t16*t9+t20*t2-t22*t7+t25*t26-t25*t4-t29*t30+t29
      *t9-t20*t26+t22*t30-t36*t7+t36*t9+t39*t7+t41*t2-t41*t4-t44*t2;
  t47 = 1/t46;
  t48 = (-t1*t2+t5+t7*t6-t10)*t47;
  t52 = (t1*t26-t5-t6*t30+t10)*t47;
  gm(0,0) = -t48-t52;
  gm(0,1) = t48;
  gm(0,2) = t52;
  t55 = (-t25+t20+t35*t7-t44)*t47;
  t57 = (t13-t20-t41+t44)*t47;
  gm(1,0) = t55+t57;
  gm(1,1) = -t55;
  gm(1,2) = -t57;
  t60 = (-t29+t22+t35*t2-t39)*t47;
  t62 = (t16-t22-t36+t39)*t47;
  gm(2,0) = -t60-t62;
  gm(2,1) = t60;
  gm(2,2) = t62;
}

void TriFace::xIntegrate(const Vector & p, const Vct3 & ref, Vct3 & pn, Vct3 & rxpn) const
{
  // values 
  Real f1 = p[v[0]];
  Real f2 = p[v[1]];
  Real f3 = p[v[2]];
  
  // triangle normal 
  const Vct3 & pt1(msh->vertex(v[0]));
  const Vct3 & pt2(msh->vertex(v[1]));
  const Vct3 & pt3(msh->vertex(v[2]));
  Vct3 nrm( cross(pt2-pt1, pt3-pt1) );
  
  // distances 
  Vct3 r1( pt1 - ref );
  Vct3 r2( pt2 - ref );
  Vct3 r3( pt3 - ref );
  
  // integral of pn dA, account for |nrm| = 2*A
  Real fmean = (f1+f2+f3) / 6.0;
  pn[0] += fmean * nrm[0];
  pn[1] += fmean * nrm[1];
  pn[2] += fmean * nrm[2];

  // integral of pr dA 
  Vct3 t;
  for (uint k=0; k<3; ++k)
    t[k] = ( 2.0 * (f1*r1[k] + f2*r2[k] + f3*r3[k])
                 + f1*r2[k] + f1*r3[k] + f2*r1[k] 
                 + f2*r3[k] + f3*r1[k] + f3*r2[k] ) / 24.;
  
  // cross product int(pr dA) x n 
  rxpn += cross(t, nrm);
}

Real TriFace::dotIntegrate(const Vector & p, const PointList<3> & z) const
{
  // values 
  Real f1 = p[v[0]];
  Real f2 = p[v[1]];
  Real f3 = p[v[2]];
  
  // triangle normal 
  const Vct3 & pt1(msh->vertex(v[0]));
  const Vct3 & pt2(msh->vertex(v[1]));
  const Vct3 & pt3(msh->vertex(v[2]));
  Vct3 nrm( cross(pt2-pt1, pt3-pt1) );
  
  // local modeshape
  const Vct3 & r1(z[v[0]]);
  const Vct3 & r2(z[v[1]]);
  const Vct3 & r3(z[v[2]]);
  
  // integrate p*z over triangle
  Vct3 t;
  for (uint k=0; k<3; ++k)
    t[k] = ( 2.0 * (f1*r1[k] + f2*r2[k] + f3*r3[k])
                 + f1*r2[k] + f1*r3[k] + f2*r1[k] 
                 + f2*r3[k] + f3*r1[k] + f3*r2[k] ) / 24.;

  // dot product, account for |nrm| = 2*A 
  return 0.5*dot(t, nrm);
}

void TriFace::edgeLengths(Vct3 & elen) const
{
  const Vct3 & pt1(msh->vertex(v[0]));
  const Vct3 & pt2(msh->vertex(v[1]));
  const Vct3 & pt3(msh->vertex(v[2]));
  
  elen[0] = norm(pt2 - pt1);
  elen[1] = norm(pt3 - pt1);
  elen[2] = norm(pt3 - pt2);
}
