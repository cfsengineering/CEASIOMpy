
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       rctsearchtree.cpp
 * begin:      Oct 2004
 * copyright:  (c) 2004 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * 2D geometric trees for point searches
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */
 
#include "rctsearchtree.h"

using namespace std;

RctSearchTree::RctSearchTree(const PointList<2> & pts) : level(0)
{
  // copy master point list
  vtx.resize(pts.size());
  std::copy(pts.begin(), pts.end(), vtx.begin());
  idx.resize(pts.size());
  for (uint i=0; i<idx.size(); ++i)  
    idx[i] = i;
  
  init();
}

RctSearchTree::RctSearchTree(VertexArrayPtr vap, Indices & ix, uint lv) 
          : level(lv), idx(ix), vtx(vap)
{
  init();
}
 
void RctSearchTree::init()
{
  if (idx.size() > 8) {
    Indices ileft, iright;
    partition(ileft, iright);
    if ( (not ileft.empty()) and (not iright.empty())) {
      left = NodePtr(new RctSearchTree(vtx, ileft, level+1));
      right = NodePtr(new RctSearchTree(vtx, iright, level+1));
    }
  }    
}
   
void RctSearchTree::find(const Vct2 & pt, Real t, Indices & fnd) const
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
  uint c = level % 2;
  Real dst = pt[c] - median;
  if (dst < 0 or dst-t < -lmin) 
    left->find(pt, t, fnd);
  if (dst >= 0 or dst+t > rmin)
    right->find(pt, t, fnd);    
}

void RctSearchTree::partition(Indices & ileft, Indices & iright)
{
  assert(idx.size() > 1);
  uint c = level % 2;
  
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
    if (pos < median) {
      lmin = min(lmin, median-pos);
      ileft.push_back(idx[i]);
    }
    else {
      rmin = min(rmin, pos-median);
      iright.push_back(idx[i]);
    }
  }
}
