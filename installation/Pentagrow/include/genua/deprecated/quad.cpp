
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       quad.cpp
 * begin:      Oct 2004
 * copyright:  (c) 2004 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * simple datastructure quadrilateral mesh element
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */
 
#include "xcept.h"
#include "quad.h"
#include "quadmesh.h"

using namespace std;

Quad::Quad(const QuadMesh *m, uint v1, uint v2, uint v3, uint v4) : srf(m)
{
  assert(m != 0);
  init(v1, v2, v3, v4);
}

Quad::Quad(const QuadMesh *m, uint vi[4]) : srf(m)
{
  assert(m != 0);
  init(vi[0], vi[1], vi[2], vi[3]);    
}

void Quad::init(uint v1, uint v2, uint v3, uint v4)
{
  // make sure that v[0] is the smallest index, but keep ordering
  if (v1 < v2 and v1 < v3 and v1 < v4) {
    v[0] = v1;
    v[1] = v2;
    v[2] = v3;
    v[3] = v4;    
  } else if (v2 < v1 and v2 < v3 and v2 < v4) {
    v[0] = v2;
    v[1] = v3;
    v[2] = v4;
    v[3] = v1;    
  } else if (v3 < v1 and v3 < v2 and v3 < v4) {
    v[0] = v3;
    v[1] = v4;
    v[2] = v1;
    v[3] = v2;    
  } else if (v4 < v1 and v4 < v2 and v4 < v3) {
    v[0] = v4;
    v[1] = v1;
    v[2] = v2;
    v[3] = v3;    
  } else
    throw Error("Quads must have four distinct indices.");  
}

bool Quad::operator< (const Quad & a) const
{
  if (v[0] == a.v[0] and v[1] == a.v[1] and v[2] == a.v[2])
    return (v[3] < a.v[3]);
  else if (v[0] == a.v[0] and v[1] == a.v[1])
    return (v[2] < a.v[2]);
  else if (v[0] == a.v[0])
    return (v[1] < a.v[1]);
  else
    return (v[0] < a.v[0]);
}
    
bool Quad::operator== (const Quad & a) const
{
  if (v[0] != a.v[0])  
    return false;
  else if (v[1] != a.v[1])  
    return false;
  else if (v[2] != a.v[2])  
    return false;
  else if (v[3] != a.v[3])  
    return false;
  else
    return true;
}

void Quad::getVertices(uint vi[4]) const
{
  for (uint i=0; i<4; ++i)
    vi[i] = v[i];
}

Vct3 Quad::center() const
{
  Vct3 ctr;
  for (uint i=0; i<4; ++i)
    ctr += srf->vertex(v[i]);  
  return 0.25*ctr;
}
    
Real Quad::area() const
{
  const Vct3 & p1(srf->vertex(v[0]));
  const Vct3 & p2(srf->vertex(v[1]));
  const Vct3 & p3(srf->vertex(v[2]));
  const Vct3 & p4(srf->vertex(v[3]));  
  
  Real a1 = norm(cross(p2-p1, p4-p1));
  Real a2 = norm(cross(p3-p2, p4-p2));
  return a1+a2;
}
    
Vct3 Quad::normal() const
{
  const Vct3 & p1(srf->vertex(v[0]));
  const Vct3 & p2(srf->vertex(v[1]));
  const Vct3 & p3(srf->vertex(v[2]));
  const Vct3 & p4(srf->vertex(v[3]));  
  
  Vct3 n1 = cross(p2-p1, p4-p1);
  Vct3 n2 = cross(p3-p2, p4-p2);    
  
  return (n1+n2).normalized();
}

void Quad::reverse()
{
  std::swap(v[1], v[3]);  
}

