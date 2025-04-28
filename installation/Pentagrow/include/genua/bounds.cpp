
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
#include "bounds.h"

using namespace std;

/* --------------- BndRect ----------------------------------------------- */

BndRect::BndRect(const Vct2 & a, const Vct2 & b)
{
  p1[0] = min(a[0], b[0]);
  p1[1] = min(a[1], b[1]);
  p2[0] = max(a[0], b[0]);
  p2[1] = max(a[1], b[1]);
}

BndRect::BndRect(Real p1x, Real p1y, Real p2x, Real p2y)
{
  p1[0] = min(p1x, p2x);
  p1[1] = min(p1y, p2y);
  p2[0] = max(p1x, p2x);
  p2[1] = max(p1y, p2y);
}

void BndRect::setCorners(Real lox, Real loy, Real hix, Real hiy)
{
  p1[0] = lox;
  p1[1] = loy;
  p2[0] = hix;
  p2[1] = hiy;
}

void BndRect::findBndRect(const PointList<2> & pg)
{
  Vct2 pt;
  p1 = p2 = pg[0];
  PointList<2>::const_iterator itr;
  for (itr = pg.begin(); itr != pg.end(); itr++)
    {
      pt = *itr;
      p1[0] = min( p1[0], pt[0] );
      p1[1] = min( p1[1], pt[1] );
      p2[0] = max( p2[0], pt[0] );
      p2[1] = max( p2[1], pt[1] );
    }
}

bool BndRect::isInside(const BndRect & rct) const
{
  // check if rectangle is completely inside
  if (isInside(rct.p1) and isInside(rct.p2))
    return true;
  else
    return false;
}

bool BndRect::intersects(const BndRect & other) const
{
  // check if rectangles do not intersect, return negated result

  if ( other.p1[0] > p2[0] or other.p2[0] < p1[0])
    return false;
  else if (other.p1[1] > p2[1] or other.p2[1] < p1[1])
    return false;
  else
    return true;
}

BndRect BndRect::intersection(const BndRect & other) const
{
  if ( !intersects(other) )
    return BndRect();

  Vct2 lo, hi;
  lo[0] = max( p1[0], other.p1[0] );
  lo[1] = max( p1[1], other.p1[1] );
  hi[0] = min( p2[0], other.p2[0] );
  hi[1] = min( p2[1], other.p2[1] );

  return BndRect(lo,hi);
}

bool BndRect::touches(const BndRect & other) const
{
  // test for touching regions (fuzzy)
  if ( p1[0] - other.p2[0] > gmepsilon )
    return false;
  if ( other.p1[0] - p2[0] > gmepsilon )
    return false;
  if ( p1[1] - other.p2[1] > gmepsilon )
    return false;
  if ( other.p1[1] - p2[1] > gmepsilon )
    return false;

  return true;
}

void BndRect::expand(Real w, Real h)
{
  // change size
  Vct2 ctr = center();
  p1[0] = ctr[0] - 0.5*w;
  p1[1] = ctr[1] - 0.5*h;
  p2[0] = ctr[0] + 0.5*w;
  p2[1] = ctr[1] + 0.5*h;
}

/* --------------- BndBox ------------------------------------------------ */

BndBox::BndBox(const Vct3 & a, const Vct3 & b)
{
  for (int i = 0; i<3; i++)
    {
      p1[i] = min(a[i], b[i]);
      p2[i] = max(a[i], b[i]);
    }
}

bool BndBox::intersects(const BndBox & other) const
{
  // test if *this _does not_ intersect other
  // if any pair of extreme coordinates of one box is completely
  // outside the range of the other box, no intersection is possible

  if (p1[0] > other.p2[0] or p2[0] < other.p1[0])
    return false;
  else if (p1[1] > other.p2[1] or p2[1] < other.p1[1])
    return false;
  else if (p1[2] > other.p2[2] or p2[2] < other.p1[2])
    return false;
  else
    return true;
}

BndBox BndBox::intersection(const BndBox & other) const
{
  // return intersection box
  if ( !intersects(other) )
    return BndBox();

  Vct3 lo,hi;
  for (uint i=0; i<3; i++)
    {
      lo[i] = max( p1[i], other.p1[i] );
      hi[i] = min( p2[i], other.p2[i] );
    }

  return BndBox(lo,hi);
}

void BndBox::writeQuads(ostream & os) const
{
  // write four vertices per row to os
  Vct3 c[8];
  c[0] = p1;
  c[1] = vct(p2[0], p1[1], p1[2]);
  c[2] = vct(p2[0], p2[1], p1[2]);
  c[3] = vct(p1[0], p2[1], p1[2]);
  c[4] = vct(p1[0], p1[1], p2[2]);
  c[5] = vct(p2[0], p1[1], p2[2]);
  c[6] = vct(p2[0], p2[1], p2[2]);
  c[7] = vct(p1[0], p2[1], p2[2]);
  
  os << c[0][0] << "  " << c[0][1] << "  " << c[0][2] << "  ";
  os << c[1][0] << "  " << c[1][1] << "  " << c[1][2] << "  ";
  os << c[5][0] << "  " << c[5][1] << "  " << c[5][2] << "  ";
  os << c[4][0] << "  " << c[4][1] << "  " << c[4][2] << endl;

  os << c[4][0] << "  " << c[4][1] << "  " << c[4][2] << "  ";
  os << c[5][0] << "  " << c[5][1] << "  " << c[5][2] << "  ";
  os << c[6][0] << "  " << c[6][1] << "  " << c[6][2] << "  ";
  os << c[7][0] << "  " << c[7][1] << "  " << c[7][2] << endl;

  os << c[2][0] << "  " << c[2][1] << "  " << c[2][2] << "  ";
  os << c[3][0] << "  " << c[3][1] << "  " << c[3][2] << "  ";
  os << c[7][0] << "  " << c[7][1] << "  " << c[7][2] << "  ";
  os << c[6][0] << "  " << c[6][1] << "  " << c[6][2] << endl;

  os << c[0][0] << "  " << c[0][1] << "  " << c[0][2] << "  ";
  os << c[3][0] << "  " << c[3][1] << "  " << c[3][2] << "  ";
  os << c[2][0] << "  " << c[2][1] << "  " << c[2][2] << "  ";
  os << c[1][0] << "  " << c[1][1] << "  " << c[1][2] << endl;

  os << c[0][0] << "  " << c[0][1] << "  " << c[0][2] << "  ";
  os << c[4][0] << "  " << c[4][1] << "  " << c[4][2] << "  ";
  os << c[7][0] << "  " << c[7][1] << "  " << c[7][2] << "  ";
  os << c[3][0] << "  " << c[3][1] << "  " << c[3][2] << endl;

  os << c[1][0] << "  " << c[1][1] << "  " << c[1][2] << "  ";
  os << c[2][0] << "  " << c[2][1] << "  " << c[2][2] << "  ";
  os << c[6][0] << "  " << c[6][1] << "  " << c[6][2] << "  ";
  os << c[5][0] << "  " << c[5][1] << "  " << c[5][2] << endl;  
}

void BndBox::addQuads(MeshFields & mvz) const
{
  Vct3 c[8];
  c[0] = p1;
  c[1] = vct(p2[0], p1[1], p1[2]);
  c[2] = vct(p2[0], p2[1], p1[2]);
  c[3] = vct(p1[0], p2[1], p1[2]);
  c[4] = vct(p1[0], p1[1], p2[2]);
  c[5] = vct(p2[0], p1[1], p2[2]);
  c[6] = vct(p2[0], p2[1], p2[2]);
  c[7] = vct(p1[0], p2[1], p2[2]);
  
  uint v[8];
  for (int k=0; k<8; ++k)
    v[k] = mvz.addVertex(c[k]);
  
  mvz.addQuad4(v[0], v[1], v[5], v[4]);
  mvz.addQuad4(v[4], v[5], v[6], v[7]);
  mvz.addQuad4(v[2], v[3], v[7], v[6]);
  mvz.addQuad4(v[0], v[3], v[2], v[1]);
  mvz.addQuad4(v[0], v[4], v[7], v[3]);
  mvz.addQuad4(v[1], v[2], v[6], v[5]);
}

string str(const BndBox & bb) {
  string s("BndBox ");
  s += str(bb.lower()) + "\n";
  s += str(bb.upper()) + "\n";
  return s;
}



