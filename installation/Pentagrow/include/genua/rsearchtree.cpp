
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
 
#include "rsearchtree.h"

using namespace std;

static const uint min_node_size(8);

RSearchTree::RSearchTree(const PointList<2> & pts) : level(0)
{
  // copy master point list
  vtx.resize(pts.size());
  std::copy(pts.begin(), pts.end(), vtx.begin());
  idx.resize(pts.size());
  for (uint i=0; i<idx.size(); ++i)
    idx[i] = i;

  init();
}

RSearchTree::RSearchTree(VertexArrayPtr vap, Indices & ix, uint lv)
  : level(lv), idx(ix), vtx(vap)
{
  assert(ix.size() > 0);
  assert(lv < 8192);
  init(); 
}

void RSearchTree::init()
{
  // sort indices numerically (to make erase() faster)
  std::sort(idx.begin(), idx.end());
  
  // find bounding box
  Vct2 p1, p2;
  p1 = huge;
  p2 = -huge;
  for (uint i=0; i<idx.size(); ++i) {
    const Vct2 & q(vtx[idx[i]]);
    for (uint k=0; k<2; ++k) {
      p1[k] = min(p1[k], q[k]);
      p2[k] = max(p2[k], q[k]);
    }
  }
  bb = BndRect(p1,p2);
  
  if (idx.size() > min_node_size and bb.diagonal() > gmepsilon) {

    // create siblings 
    Indices ileft, iright;
    partition(ileft, iright);
    if (ileft.empty() or iright.empty()) {
      return;
    } else {
      left = NodePtr(new RSearchTree(vtx, ileft, level+1));
      right = NodePtr(new RSearchTree(vtx, iright, level+1));
    }
  }
  
  // nodes with less than 8 vertices are not split
}

uint RSearchTree::nearest(const Vct2 & pt) const
{
  // linear search when no siblings present
  if (not left) {
    uint best(0);
    Real dst, mindst(huge);
    for (uint i=0; i<idx.size(); ++i) {
      dst = norm(pt - vtx[idx[i]]);
      if (dst < mindst) {
        best = idx[i];
        mindst = dst;
      }
    }
    return best;
  }

  // search subtrees
  uint lbest, rbest;
  Real ldst, rdst, dst;
  ldst = left->fromBox(pt);
  rdst = right->fromBox(pt);

  // First, find nearest point in closest bounding box.
  // Then, check if the distance found is larger than the distance
  // of the point to the other bounding box. If so, there might be 
  // a better point in the other box (otherwise impossible). Hence,
  // find the best point in the other box and compare the two.
  if (ldst < rdst) {
    lbest = left->nearest(pt);
    dst = norm(pt - vtx[lbest]);
    if (dst > rdst) {
      rbest = right->nearest(pt);
      if (norm(pt - vtx[rbest]) < dst)
        return rbest;
      else
        return lbest;
    } else
      return lbest;

  } else {
    rbest = right->nearest(pt);
    dst = norm(pt - vtx[rbest]);
    if (dst > ldst) {
      lbest = left->nearest(pt);
      if (norm(pt - vtx[lbest]) < dst)
        return lbest;
      else
        return rbest;
    } else
      return rbest;
  }
}

void RSearchTree::find(const Vct2 & pt, Real r, Indices & fnd) const
{
  // linear search at leaf nodes
  if (not left) {
    const uint n(idx.size());
    for (uint i=0; i<n; ++i) {
      if (norm(vtx[idx[i]] - pt) < r)
        fnd.push_back(idx[i]);
    }
    return;
  } 
  
  // call siblings if a sphere with radius r around pt intersects
  // their respective bounding boxes
  if (left->fromBox(pt) < r)
    left->find(pt, r, fnd);
  if (right->fromBox(pt) < r)
    right->find(pt, r, fnd);
}

void RSearchTree::proximityOrdering(Indices & perm) const
{
  if (not left) {
    perm.insert(perm.end(), idx.begin(), idx.end());
  } else {
    left->proximityOrdering(perm);
    right->proximityOrdering(perm);
  }
}

void RSearchTree::partition(Indices & ileft, Indices & iright) const
{
  assert(idx.size() > 1);
  Real ds[2];  
  ds[0] = bb.width();
  ds[1] = bb.height();

  // decide along which direction to split
  uint c = std::distance(ds, std::max_element(ds, ds+2));
  if (ds[c] < gmepsilon)
    return;

  // find median
  Vector crd(idx.size());
  for (uint i=0; i<idx.size(); ++i) {
    crd[i] = vtx[idx[i]][c];
  }
  std::sort(crd.begin(), crd.end());
  Real median = crd[crd.size() / 2];

  // create partition
  ileft.clear();
  iright.clear();
  for (uint i=0; i<idx.size(); ++i) {
    Real pos = vtx[idx[i]][c];
    if (pos <= median)
      ileft.push_back(idx[i]);
    else
      iright.push_back(idx[i]);
  }
}

uint RSearchTree::insert(const Vct2 & p)
{
  // top level call to insert vertex
  vtx.push_back(p);
  this->insert(p, vtx.size()-1);
  return vtx.size()-1;
}

void RSearchTree::insert(const Vct2 & p, uint i)
{
  idx.push_back(i);
  bb.enclose(p);

  if (left) {
    
    // recurse into child nodes
    Real ldst = left->fromBox(p);
    Real rdst = right->fromBox(p);
        
    if (ldst < rdst)
      left->insert(p, i);
    else 
      right->insert(p, i);
    
  } else {
    
    // trigger top level split if necessary
    init();
  }
}

void RSearchTree::erase(uint i)
{
  // relies on idx being sorted numerically
  Indices::iterator pos;
  pos = std::lower_bound(idx.begin(), idx.end(), i);
  if (pos != idx.end() and *pos == i) {
    idx.erase(pos);
    if (left) {
      if (idx.size() > min_node_size) {
        left->erase(i);
        right->erase(i);
      } else {
        left.reset();
        right.reset();
      }
    }

    // we do not recompute the bounding box (it therefore remains too large)
    // since that would incur an additional cost which does not appear acceptable
  }    
}

