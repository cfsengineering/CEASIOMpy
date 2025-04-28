
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
 
#include "dimsearchtree.h"

using namespace std;

DimSearchTree::DimSearchTree(const PointList<3> & pts) : level(0)
{
  // copy master point list
  vtx.resize(pts.size());
  std::copy(pts.begin(), pts.end(), vtx.begin());
  idx.resize(pts.size());
  for (uint i=0; i<idx.size(); ++i)  
    idx[i] = i;
  
  init();
}

DimSearchTree::DimSearchTree(VertexArrayPtr vap, Indices & ix, uint lv) 
          : level(lv), idx(ix), vtx(vap)
{
  init();
}
 
void DimSearchTree::init()
{
  if (idx.size() > 8) {
    Indices ileft, iright;
    partition(ileft, iright);
    if ( (not ileft.empty()) and (not iright.empty())) {
      left = NodePtr(new DimSearchTree(vtx, ileft, level+1));
      right = NodePtr(new DimSearchTree(vtx, iright, level+1));
    }
  }    
}
   
void DimSearchTree::find(const Vct3 & pt, Real t, Indices & fnd) const
{
  // search vertices if no siblings present
  if (not left) {
    for (uint i=0; i<idx.size(); ++i) {
      if (norm(vtx[idx[i]] - pt) < t)
        fnd.push_back(idx[i]);
    }
    return;
  }
  
  // else, search subtrees
  uint c = level % 3;
  Real dst = pt[c] - median;
  if (dst < 0 or dst-t < -lmin) 
    left->find(pt, t, fnd);
  if (dst >= 0 or dst+t > rmin)
    right->find(pt, t, fnd);    
}

void DimSearchTree::partition(Indices & ileft, Indices & iright)
{
  assert(idx.size() > 1);
  uint c = level % 3;
  
  // find median
  Vector crd(idx.size());
  for (uint i=0; i<idx.size(); ++i) {
    crd[i] = vtx[idx[i]][c];
  } 
  std::sort(crd.begin(), crd.end());
  median = crd[crd.size() / 2];
  
  // create partition 
  ileft.clear();
  iright.clear();
  lmin = rmin = huge;
  for (uint i=0; i<idx.size(); ++i) {
    Real pos = vtx[idx[i]][c];
    if (pos <= median) {
      lmin = min(lmin, median-pos);
      ileft.push_back(idx[i]);
    }
    else {
      rmin = min(rmin, pos-median);
      iright.push_back(idx[i]);
    }
  }
}
