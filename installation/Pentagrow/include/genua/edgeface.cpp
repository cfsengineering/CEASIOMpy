
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
 
#include "xcept.h"
#include "trigo.h"
#include "lapack.h"
#include "edgeface.h"
#include "triangulation.h"

using namespace std;

// ---------- local helper function ---------------------------------------

static inline Real lparm(const Vct3 & pt, const Vct3 & p1, const Vct3 & p2) 
{
  Line<3> ln(p1, p2);
  Real fp = ln.footPar(pt);
  
  if (fp < 0)
    return 0;
  else if (fp > 1)
    return 1;
  else
    return fp;
}

// ------- Edge -----------------------------------------------------------

Vct3 Edge::direction() const
{
  assert(srf != 0);
  return srf->vertex(trg) - srf->vertex(src);
}

Real Edge::length() const
{
  assert(srf != 0);
  return norm(srf->vertex(trg) - srf->vertex(src));
}

uint Edge::degree() const
{
  // number of faces connected to this edge
  std::map<Edge, std::set<Face> >::const_iterator itm;
  itm = srf->e2f.find(*this);
  if (itm == srf->e2f.end())
    return 0;
  else
    return itm->second.size();
}

FacePair Edge::neighbors() const
{
  // find neighbor faces
  FacePair fp;
  std::map<Edge, std::set<Face> >::const_iterator itm;
  itm = srf->e2f.find(*this);
  if (itm == srf->e2f.end())
    throw Error("No such edge in surface triangulation.");
  else if (itm->second.size() != 2)
    throw Error("Edge is not a surface edge (boundary or triple).");
  std::set<Face>::const_iterator itf;
  itf = itm->second.begin();
  fp.first = *itf;
  itf++;
  fp.second = *itf;
  return fp;
}

Real Edge::maxStretch() const
{
  // find neighbor faces
  std::map<Edge, std::set<Face> >::const_iterator itm;
  itm = srf->e2f.find(*this);
  if (itm == srf->e2f.end())
    throw Error("No such edge in surface triangulation.");

  Real stmax(0), slen, jcb;
  slen = sq(length());
  std::set<Face>::const_iterator itf;
  for (itf = itm->second.begin(); itf != itm->second.end(); ++itf) {
    jcb = norm(itf->normal());
    stmax = max(stmax, jcb/slen);
  }
  return stmax;
}

bool Edge::intersects(const BndBox & bb) const
{
  // check if edge intersects box
  const Vct3 & s(srf->vertex(src));
  const Vct3 & t(srf->vertex(trg));
  const Vct3 & p1(bb.lower());
  const Vct3 & p2(bb.upper());
  if (   ((s[0]<p1[0] and t[0]<p1[0]) or (s[0]>p2[0] and t[0]>p2[0]))
         or ((s[1]<p1[1] and t[1]<p1[1]) or (s[1]>p2[1] and t[1]>p2[1]))
         or ((s[2]<p1[2] and t[2]<p1[2]) or (s[2]>p2[2] and t[2]>p2[2])) )
    return false;
  else
    return true;
}


// ------- Face -----------------------------------------------------------

Face::Face(const Triangulation *parent, uint p1, uint p2, uint p3)
    : srf(parent)
{
  // construction (canonical ordering)
  v[0] = p1;
  v[1] = p2;
  v[2] = p3;
  orderCanonical();
}

Face::Face(const Triangulation *parent,
           const Edge & e1, const Edge & e2, const Edge &) : srf(parent)
{
  // construction according to GTS direction rules
  assert(srf != 0);
  v[0] = e1.source();
  if (e1.source() == e2.source()) {
    v[1] = e2.target();
    v[2] = e1.target();
  } else if (e1.target() == e2.target()) {
    v[1] = e1.target();
    v[2] = e2.source();
  } else if (e1.source() == e2.target()) {
    v[1] = e2.source();
    v[2] = e1.target();
  } else {
    v[1] = e1.target();
    v[2] = e2.target();
  }
}

void Face::getEdges(Edge e[3]) const
{
  // copy edges into edg
  if (v[1] > v[2]) {
    e[0] = Edge(srf, v[0], v[1]);
    e[1] = Edge(srf, v[2], v[1]);              // pattern (ii)
    e[2] = Edge(srf, v[0], v[2]);
  } else {
    e[0] = Edge(srf, v[0], v[1]);
    e[1] = Edge(srf, v[1], v[2]);              // pattern (iv)
    e[2] = Edge(srf, v[0], v[2]);
  }
}

uint Face::neighbors(Face f[3]) const
{
  assert(srf != 0);
  Edge e[3];
  getEdges(e);
  uint k(0);
  CrossMap::const_iterator itm;
  for (uint i=0; i<3; ++i) {
    itm = srf->e2f.find(e[i]);
    if (itm != srf->e2f.end() and itm->second.size() == 2) {
      std::set<Face>::const_iterator itf;
      itf = itm->second.begin();
      if (*itf == *this) {
        ++itf;
        f[i] = *itf;
        ++k;
      } else {
        f[i] = *itf;
        ++k;
      }
    }
  }       
  return k;
}

Vct3 Face::eval(Real xi, Real eta) const
{
  assert(srf != 0);
  Vct3 p1 = srf->vertex(v[0]);
  Vct3 p2 = srf->vertex(v[1]);
  Vct3 p3 = srf->vertex(v[2]);
  return p1 + xi*(p2-p1) + eta*(p3-p1);
}

bool Face::operator== (const Face & a) const
{
  // equality
  if (a.v[0] == v[0] and a.v[1] == v[1] and a.v[2] == v[2])
    return true;
  else if (a.v[0] == v[2] and a.v[1] == v[0] and a.v[2] == v[1])
    return true;
  else if (a.v[0] == v[1] and a.v[1] == v[2] and a.v[2] == v[0])
    return true;
  else
    return false;
}

Edge Face::edge(uint i) const
{
  // find edge i
  assert(i > 0 and i < 4);
  Edge ev[3];
  getEdges(ev);
  return ev[i-1];
}

bool Face::hasEdge(const Edge & e) const
{
  uint s = e.source();
  uint t = e.target();
  if ( (s == v[0] or s == v[1] or s == v[2])
     and (t == v[0] or t == v[1] or t == v[2]) )
    return true;
  else
    return false;
}

Vct3 Face::center() const
{
  assert(srf != 0);
  return (srf->vertex(v[0])+srf->vertex(v[1])+srf->vertex(v[2]))/3.0;
}

Vct3 Face::normal() const
{
  Vct3 pt1, pt2, pt3;
  assert(srf != 0);
  pt1 = srf->vertex(v[0]);
  pt2 = srf->vertex(v[1]);
  pt3 = srf->vertex(v[2]);
  return cross(pt2-pt1,pt3-pt1);
}

void Face::reverse()
{
  // reverse normal direction
  uint tmp(v[2]);
  v[2] = v[1];
  v[1] = tmp;
}

void Face::orderCanonical()
{
  // make sure v[0] is minimum
  if ((v[0] > v[1] and v[1] > v[2]) or (v[0] > v[2] and v[1] > v[2])) {
    uint tmp = v[2];
    v[2] = v[1];
    v[1] = v[0];
    v[0] = tmp;
  } else if ((v[0] > v[1] and v[2] > v[1]) or (v[0] > v[2] and v[2] > v[1])) {
    uint tmp = v[0];
    v[0] = v[1];
    v[1] = v[2];
    v[2] = tmp;
  }
}

Real Face::solidAngle(uint idx) const
{
  // compute solid angle associated with vertex idx
  assert(srf != 0);
  Vct3 b, c, a( srf->normal(idx) );
  if (idx == v[0]) {
    b = (srf->vertex(v[1]) - srf->vertex(v[0])).normalized();
    c = (srf->vertex(v[2]) - srf->vertex(v[0])).normalized();
  } else if (idx == v[1]) {
    b = (srf->vertex(v[2]) - srf->vertex(v[1])).normalized();
    c = (srf->vertex(v[0]) - srf->vertex(v[1])).normalized();
  } else if (idx == v[2]) {
    b = (srf->vertex(v[0]) - srf->vertex(v[2])).normalized();
    c = (srf->vertex(v[1]) - srf->vertex(v[2])).normalized();
  } else
    throw Error("This face does not contain vertex index ",idx);

  Real alpha, beta, gamma;
  Vct3 sab, sbc, sca, x1, x2;
  sab = cross(a,b);
  sbc = cross(b,c);
  sca = cross(c,a);

  x1 = cross(sab, a);
  x2 = cross(a, sca);
  if (norm(x1)*norm(x2) < gmepsilon)
    return 0;
  alpha = acos( dot(x1,x2) / (norm(x1)*norm(x2)) );
  x1 = cross(sbc, b);
  x2 = cross(b, sab);
  if (norm(x1)*norm(x2) < gmepsilon)
    return 0;
  beta = acos( dot(x1,x2) / (norm(x1)*norm(x2)) );
  x1 = cross(sca, c);
  x2 = cross(c, sbc);
  if (norm(x1)*norm(x2) < gmepsilon)
    return 0;
  gamma = acos( dot(x1,x2) / (norm(x1)*norm(x2)) );

  Real s = sign(dot(a,normal()));
  return s*(alpha+beta+gamma-PI);
}

Real Face::solidAngle(uint idx, const Vct3 & a) const
{
  // compute solid angle associated with vertex idx
  assert(srf != 0);
  Vct3 b, c;
  if (idx == v[0]) {
    b = (srf->vertex(v[1]) - srf->vertex(v[0])).normalized();
    c = (srf->vertex(v[2]) - srf->vertex(v[0])).normalized();
  } else if (idx == v[1]) {
    b = (srf->vertex(v[2]) - srf->vertex(v[1])).normalized();
    c = (srf->vertex(v[0]) - srf->vertex(v[1])).normalized();
  } else if (idx == v[2]) {
    b = (srf->vertex(v[0]) - srf->vertex(v[2])).normalized();
    c = (srf->vertex(v[1]) - srf->vertex(v[2])).normalized();
  } else
    throw Error("This face does not contain vertex index ",idx);

  Real alpha, beta, gamma;
  Vct3 sab, sbc, sca, x1, x2;
  sab = cross(a,b);
  sbc = cross(b,c);
  sca = cross(c,a);

  x1 = cross(sab, a);
  x2 = cross(a, sca);
  if (norm(x1)*norm(x2) < gmepsilon)
    return 0;
  alpha = acos( dot(x1,x2) / (norm(x1)*norm(x2)) );
  x1 = cross(sbc, b);
  x2 = cross(b, sab);
  if (norm(x1)*norm(x2) < gmepsilon)
    return 0;
  beta = acos( dot(x1,x2) / (norm(x1)*norm(x2)) );
  x1 = cross(sca, c);
  x2 = cross(c, sbc);
  if (norm(x1)*norm(x2) < gmepsilon)
    return 0;
  gamma = acos( dot(x1,x2) / (norm(x1)*norm(x2)) );

  Real s = sign(dot(a,normal()));
  return s*(alpha+beta+gamma-PI);
}

uint Face::opposed(const Edge & e) const
{
  // find vertex opposed to edge e

  Edge ev[3];
  getEdges(ev);

  if (e != ev[0] and e != ev[1] and e != ev[2])
    throw Error("Face does not own this edge.");

  if (v[0] != e.source() and v[0] != e.target())
    return v[0];
  else if (v[1] != e.source() and v[1] != e.target())
    return v[1];
  else
    return v[2];
}

Edge Face::opposed(uint i) const
{
  // find vertex opposed to edge e
  Edge ev[3];
  getEdges(ev);

  if (ev[0].source() != i and ev[0].target() != i)
    return ev[0];
  else if (ev[1].source() != i and ev[1].target() != i)
    return ev[1];
  else if (ev[2].source() != i and ev[2].target() != i)
    return ev[2];
  else
    throw Error("No opposed edge for "+str(i));
}

Vct3 Face::project(const Vct3 & pt) const
{
  // project point onto face plane, return (xi,eta,dist)
  // where dist is positive if point lies in normal direction
  assert(srf != 0);
  Vct3 p1, p2, p3;
  p1 = srf->vertex(v[0]);
  p2 = srf->vertex(v[1]);
  p3 = srf->vertex(v[2]);

  Vct3 nrm, va, vb, vXi, vEta;
  va = p2 - p1;
  vb = p3 - p1;
  nrm = cross(va,vb).normalized();
  vXi = va - vb*(dot(va,vb)/dot(vb,vb));
  vEta = vb - va*(dot(va,vb)/dot(va,va));

  Vct3 s;
  s[0] = dot(pt-p1, vXi) / dot(vXi,vXi);
  s[1] = dot(pt-p1, vEta) / dot(vEta,vEta);
  s[2] = dot(pt-p1,nrm);

  return s;
}

Vct3 Face::pierce(const Edge & e) const
{
  // find the projected point where e pierces the face
  const Triangulation *es = e.surface();
  Vct3 q1 = project(es->vertex(e.source()));
  Vct3 q2 = project(es->vertex(e.target()));

  Vct3 uvt;
  if ( fabs(q1[2]-q2[2]) > gmepsilon ) {
    Real t = q1[2]/(q1[2] - q2[2]);
    uvt[0] = q1[0] + t*(q2[0] - q1[0]);
    uvt[1] = q1[1] + t*(q2[1] - q1[1]);
    uvt[2] = t;
  } else
    uvt[0] = uvt[1] = uvt[2] = huge;

  return uvt;
}

SMatrix<3,3> Face::trafo() const
{
  // transformation matrix for local coordinate system
  // returns m so that m*(xi,eta,h) + p1 = (x,y,z)
  assert(srf != 0);
  Vct3 p1, p2, p3;
  p1 = srf->vertex(v[0]);
  p2 = srf->vertex(v[1]);
  p3 = srf->vertex(v[2]);

  Vct3 nm, va, vb;
  va = p2 - p1;
  vb = p3 - p1;
  nm = cross(va,vb).normalized();

  SMatrix<3,3> m;
  for (uint i=0; i<3; ++i) {
    m(i,0) = va[i];
    m(i,1) = vb[i];
    m(i,2) = nm[i];
  }

  //  std::copy(va.begin(), va.end(), m.column_begin(0));
  //  std::copy(vb.begin(), vb.end(), m.column_begin(1));
  //  std::copy(nm.begin(), nm.end(), m.column_begin(2));

  return m;
}

Real Face::corner(uint gv) const
{
  // compute corner angle
  assert(srf != 0);
  if (gv == v[0]) {
    Vct3 pt1 = srf->vertex(v[0]);
    Vct3 pt2 = srf->vertex(v[1]);
    Vct3 pt3 = srf->vertex(v[2]);
    return arg(pt3-pt1, pt2-pt1);
  } else if (gv == v[1]) {
    Vct3 pt1 = srf->vertex(v[0]);
    Vct3 pt2 = srf->vertex(v[1]);
    Vct3 pt3 = srf->vertex(v[2]);
    return arg(pt3-pt2, pt1-pt2);
  } else if (gv == v[2]) {
    Vct3 pt1 = srf->vertex(v[0]);
    Vct3 pt2 = srf->vertex(v[1]);
    Vct3 pt3 = srf->vertex(v[2]);
    return arg(pt2-pt3, pt1-pt3);
  } else
    throw Error("Face does not contain vertex ",gv);
}

Real Face::quality() const
{
  // triangle quality
  Vct3 pt[3];
  for (uint i=0; i<3; i++)
    pt[i] = srf->vertex(v[i]);

  Real a,b,c;
  a = norm(pt[1]-pt[0]);
  b = norm(pt[2]-pt[0]);
  c = norm(pt[1]-pt[2]);

  return min(a,min(b,c)) / max(a,max(b,c));
}

void Face::replace(uint vold, uint vnew)
{
  // replace index
  for (uint i=0; i<3; i++) {
    if (v[i] == vold)
      v[i] = vnew;
  }
}

Vct3 Face::gradient(const Vector & x) const
{
  Mtx33 gm;
  gradient(gm);
  Vct3 xe;
  xe[0] = x[v[0]];
  xe[1] = x[v[1]];
  xe[2] = x[v[2]];
  return gm*xe;
}

CpxVct3 Face::gradient(const CpxVector & x) const
{
  Mtx33 gm;
  gradient(gm);
  CpxVct3 xv, gx;
  xv[0] = x[v[0]];
  xv[1] = x[v[1]];
  xv[2] = x[v[2]];

  gx[0] = gm(0,0)*xv[0] + gm(0,1)*xv[1] + gm(0,2)*xv[2];
  gx[1] = gm(1,0)*xv[0] + gm(1,1)*xv[1] + gm(1,2)*xv[2];
  gx[2] = gm(2,0)*xv[0] + gm(2,1)*xv[1] + gm(2,2)*xv[2];
  
  return gx;
}

uint Face::inside(const BndBox & bb) const
{
  uint c(0);
  for (uint k=0; k<3; ++k) {
    const Vct3 & p(srf->vertex(v[k]));
    if (bb.isInside(p))
      ++c;
  }    
  return c;
}

void Face::gradient(Mtx33 & gm) const
{

  // fetch node coordinates and compute normal
  const Vct3 & pt1(srf->vertex(v[0]));
  const Vct3 & pt2(srf->vertex(v[1]));
  const Vct3 & pt3(srf->vertex(v[2]));
  Vct3 nrm = cross(pt2-pt1, pt3-pt1).normalized();

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

Real Face::minDistance(const Vct3 & pt, Vct2 & foot) const
{
  // projection of point onto face
  Real u, v, w, best(huge);
  Vct3 pj = Face::project(pt);
  u = pj[0];
  v = pj[1];
  w = 1. - u - v;

  // projection foot is inside triangle
  if (u >= 0 and v >= 0 and w >= 0) {
    foot = vct(u,v);
    best = pj[2];
  }

  // project on edges of triangle
  else {

    Real lp, dl;
    uint vi[3];
    getVertices(vi);
    const Vct3 & pt1(srf->vertex(vi[0]));
    const Vct3 & pt2(srf->vertex(vi[1]));
    const Vct3 & pt3(srf->vertex(vi[2]));
    Vct2 q1 = vct(0,0);
    Vct2 q2 = vct(1,0);
    Vct2 q3 = vct(0,1);

    // project on line pt1 - pt3
    if (u < 0) {
      lp = lparm(pt, pt1, pt3);
      dl = norm(pt - (1-lp)*pt1 -lp*pt3);
      if (dl < best) {
        foot = (1-lp)*q1 + lp*q3;
        best = dl;
      }
    }

    // project on line pt1 - pt2
    if (v < 0) {
      lp = lparm(pt, pt1, pt2);
      dl = norm(pt - (1-lp)*pt1 -lp*pt2);
      if (dl < best) {
        foot = (1-lp)*q1 + lp*q2;
        best = dl;
      }
    }

    // project on line pt2 - pt3
    if (w < 0) {
      lp = lparm(pt, pt2, pt3);
      dl = norm(pt - (1-lp)*pt2 -lp*pt3);
      if (dl < best) {
        foot = (1-lp)*q2 + lp*q3;
        best = dl;
      }
    }
    
    // use the same sign convention as project()
    u = foot[0];
    v = foot[1];
    w = 1.0 - u - w;
    Vct3 nrm( cross(pt2-pt1, pt3-pt1) );
    normalize(nrm);
    Vct3 dst( pt -  w*pt1 + u*pt2 + v*pt3 );
    best = dot(dst, nrm);
  }
  
  return best;  
}

