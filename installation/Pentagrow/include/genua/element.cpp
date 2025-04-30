
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
 
#include "meshfields.h"
#include "element.h"

using namespace std;

// --------------------- Element -------------------------------------

uint Element::edges(uint *) const 
{
  return 0;
}

uint Element::faces(uint *) const 
{
  return 0;
}

uint Element::idtype() const 
{
  return 0;
}

// --------------------- PointElement -------------------------------------

uint PointElement::add2viz(MeshFields & m) const
{
  const uint *v(vertices());
  return m.addMarker(v[0]);
}

uint PointElement::idtype() const 
{
  return 1;
}

// --------------------- Line2Element -------------------------------------

uint Line2Element::edges(uint ep[]) const 
{
  const uint *v( vertices() );
  ep[0] = v[0];
  ep[1] = v[1];
  return 1;
}

uint Line2Element::idtype() const 
{
  return 2;
}

uint Line2Element::add2viz(MeshFields & m) const
{
  const uint *v(vertices());
  return m.addLine2(v[0], v[1]);
}

// --------------------- Line3Element -------------------------------------

uint Line3Element::edges(uint ep[]) const 
{
  const uint *v( vertices() );
  ep[0] = v[0];
  ep[1] = v[2];
  ep[2] = v[2];
  ep[3] = v[1];
  return 2;
}

uint Line3Element::idtype() const 
{
  return 3;
}

uint Line3Element::add2viz(MeshFields & m) const
{
  const uint *v(vertices());
  m.addLine2(v[0], v[2]);
  return m.addLine2(v[2], v[1]);
}

// --------------------- Tri3Element -------------------------------------

uint Tri3Element::edges(uint ep[]) const 
{
  const uint *v( vertices() );
  ep[0] = v[0];
  ep[1] = v[1];
  ep[2] = v[1];
  ep[3] = v[2];
  ep[4] = v[2];
  ep[5] = v[0];
  return 3;
}

uint Tri3Element::idtype() const 
{
  return 4;
}

uint Tri3Element::add2viz(MeshFields & m) const
{
  return m.addTri3(vertices());
}

// --------------------- Tri6Element -------------------------------------

uint Tri6Element::edges(uint ep[]) const 
{
  const uint *v( vertices() );
  ep[0] = v[0];
  ep[1] = v[3];
  ep[2] = v[3];
  ep[3] = v[1];
  ep[4] = v[1];
  ep[5] = v[4];
  ep[6] = v[4];
  ep[7] = v[2];
  ep[8] = v[2];
  ep[9] = v[5];
  ep[10] = v[5];
  ep[11] = v[0];
  return 6;
}

uint Tri6Element::idtype() const 
{
  return 5;
}

uint Tri6Element::add2viz(MeshFields & m) const
{
  const uint *v(vertices());
  m.addTri3(v[0], v[3], v[5]);
  m.addTri3(v[1], v[4], v[3]);
  m.addTri3(v[2], v[5], v[4]);
  return m.addTri3(v[3], v[4], v[5]);
}

// --------------------- Quad4Element -------------------------------------

uint Quad4Element::edges(uint ep[]) const 
{
  const uint *v( vertices() );
  ep[0] = v[0];
  ep[1] = v[1];
  ep[2] = v[1];
  ep[3] = v[2];
  ep[4] = v[2];
  ep[5] = v[3];
  ep[6] = v[3];
  ep[7] = v[0];
  return 4;
}

uint Quad4Element::idtype() const 
{
  return 6;
}

uint Quad4Element::add2viz(MeshFields & m) const
{
  return m.addQuad4(vertices());
}

// --------------------- Quad8Element -------------------------------------

uint Quad8Element::edges(uint ep[]) const 
{
  const uint *v(vertices());
  ep[0] = v[0];
  ep[1] = v[4];
  ep[2] = v[4];
  ep[3] = v[1];
  ep[4] = v[1];
  ep[5] = v[5];
  ep[6] = v[5];
  ep[7] = v[2];
  ep[8] = v[2];
  ep[9] = v[6];
  ep[10] = v[6];
  ep[11] = v[3];
  ep[12] = v[3];
  ep[13] = v[7];
  ep[14] = v[7];
  ep[15] = v[0];
  return 8;
}

uint Quad8Element::idtype() const 
{
  return 7;
}

uint Quad8Element::add2viz(MeshFields & m) const
{
  const uint *v(vertices());
  return m.addQuad4(v);
}

// --------------------- Quad9Element -------------------------------------

uint Quad9Element::edges(uint ep[]) const 
{
  const uint *v(vertices());
  ep[0] = v[0];
  ep[1] = v[4];
  ep[2] = v[4];
  ep[3] = v[1];
  ep[4] = v[1];
  ep[5] = v[5];
  ep[6] = v[5];
  ep[7] = v[2];
  ep[8] = v[2];
  ep[9] = v[6];
  ep[10] = v[6];
  ep[11] = v[3];
  ep[12] = v[3];
  ep[13] = v[7];
  ep[14] = v[7];
  ep[15] = v[0];
  return 8;
}

uint Quad9Element::idtype() const 
{
  return 8;
}

uint Quad9Element::add2viz(MeshFields & m) const
{
  const uint *v(vertices());
  m.addQuad4(v[0], v[4], v[8], v[7]);
  m.addQuad4(v[4], v[1], v[5], v[8]);
  m.addQuad4(v[5], v[2], v[6], v[8]);
  return m.addQuad4(v[3], v[7], v[8], v[6]);
}

// --------------------- HexElement -------------------------------------

uint HexElement::edges(uint ep[]) const 
{
  const uint *v(vertices());
  if (nvertices() == 20) {
    
    const int e1[] = {1,9,2,10,3,11,4,12,1};
    const int e2[] = {5,17,6,18,7,19,8,20,5};
    for (int k=0; k<8; ++k) {
      ep[2*k] = v[e1[k]-1];
      ep[2*k+1] = v[e1[k+1]-1];
    }
    for (int k=0; k<8; ++k) {
      ep[16+2*k] = v[e2[k]-1];
      ep[16+2*k+1] = v[e2[k+1]-1];
    }
    
    int m = 16;
    const int e3[] = {1,13,5,2,14,6,3,15,7,4,16,8};
    for (int i=0; i<4; ++i) {
      const int *e = &e3[3*i];
      for (int k=0; k<4; ++k) {
        ep[m+2*k] = v[e[k]-1];
        ep[m+2*k+1] = v[e[k+1]-1];
      }
      m += 8; 
    }
    return 24;
    
  } else {
  
    const int e1[] = {1,2,3,4,1};
    for (int k=0; k<4; ++k) {
      ep[2*k] = v[e1[k]-1];
      ep[2*k+1] = v[e1[k+1]-1];
    }
    for (int k=0; k<4; ++k) {
      ep[8+2*k] = v[e1[k]+3];
      ep[8+2*k+1] = v[e1[k+1]+3];
    }
    
    ep[16] = v[0]; ep[17] = v[4];
    ep[18] = v[1]; ep[19] = v[5];
    ep[20] = v[2]; ep[21] = v[6];
    ep[22] = v[3]; ep[23] = v[7];
    
    return 12;
  }
}

uint HexElement::idtype() const 
{
  return 9;
}

uint HexElement::add2viz(MeshFields & m) const
{
  const uint *v(vertices());
  m.addQuad4(v[0], v[1], v[5], v[4]);
  m.addQuad4(v[1], v[2], v[6], v[5]);
  m.addQuad4(v[2], v[6], v[7], v[3]);
  m.addQuad4(v[0], v[4], v[7], v[3]);
  m.addQuad4(v[4], v[5], v[6], v[7]);
  return m.addQuad4(v[0], v[3], v[2], v[1]);
}

// --------------------- TetraElement -------------------------------------

uint TetraElement::edges(uint ep[]) const
{
  const uint *v(vertices());
  if (nvertices() == 4) {

    const int e1[] = { 1, 2, 3, 1, 2, 3 };
    const int e2[] = { 2, 3, 1, 4, 4, 4 };
    for (int k=0; k<6; ++k) {
      ep[2*k+0] = v[e1[k]-1];
      ep[2*k+1] = v[e2[k]-1];
    }

    return 6;

  } else {

    const int e1[] = { 1, 5, 2, 6, 3, 7, 1, 2, 3, 8, 9, 10 };
    const int e2[] = { 5, 2, 6, 3, 7, 1, 8, 9, 10, 4, 4, 4 };
    for (int k=0; k<12; ++k) {
      ep[2*k+0] = v[e1[k]-1];
      ep[2*k+1] = v[e2[k]-1];
    }

    return 12;
  }
}

uint TetraElement::idtype() const
{
  return 10;
}

uint TetraElement::add2viz(MeshFields &) const
{
  assert(!"Not implemented.");
  return NotFound;
}


