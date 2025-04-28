
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
 
#include "dnmesh.h"
#include "dnboxadaptor.h"

using namespace std;

void DnBoxAdaptor::bind(const DnMesh *pm) const
{
  msh = pm;
  crit.bind(pm);
}

void DnBoxAdaptor::addBox(const BndRect & br)
{
  boxes.push_back(br);
  
//  cout << "Added box " << br.lower() << " -- " << br.upper() << endl;
}

void DnBoxAdaptor::addBox(const PointList<2> & pts)
{
  BndRect br;
  br.findBndRect(pts);
  // br.expand(1.2*br.width(), 1.2*br.height());
  boxes.push_back(br);
  
//  cout << "Added box " << br.lower() << " -- " << br.upper() << endl;
}
    
Real DnBoxAdaptor::eval(const uint *vi) const
{
  const uint nb(boxes.size());
  if (nb == 0)
    return 1.0;
  
  // fetch triangle vertices  
  Vct2 p[3];
  for (uint k=0; k<3; ++k)
    p[k] = msh->parpos(vi[k]);
  
  // test if the triangle edges intersect any 
  // of the box edges or if all points are inside
  for (uint i=0; i<nb; ++i) {
    const BndRect & br(boxes[i]);
    for (uint k=0; k<3; ++k) {
      if (br.isInside(p[k]))
        return crit.eval(vi);
      const Vct2 & q1(p[k]);
      const Vct2 & q2(p[(k+1)%3]);
      if (br.intersects(q1,q2))
        return crit.eval(vi);
    }
  }
  
  // not inside box - do not refine 
  return 1.0;
}

DnBoxAdaptor *DnBoxAdaptor::clone() const
{
  DnBoxAdaptor *cpy = new DnBoxAdaptor(crit);
  cpy->boxes = boxes;
  return cpy; 
}
