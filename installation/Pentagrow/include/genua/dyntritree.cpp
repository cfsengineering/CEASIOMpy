
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
 
#include "dyntritree.h"
#include <iostream>

using namespace std;

// ------------------- DynTriTree --------------------------------------

DynTriTree::DynTriTree(const PointList<2> *vtx, const Indices *idx)
  : nodePool(sizeof(DynTriTree::Node))
{
  assign(vtx, idx);
  build();
}

void DynTriTree::assign(const PointList<2> *vtx, const Indices *idx)
{
  nintree = nrebuild = 0;
  root = constructNode();
  assert(root != 0);
  pvx = vtx;
  pix = idx;
}

void DynTriTree::build()
{
  nintree = nrebuild = 0;
  assert(pix != 0);
  clear();
  root = constructNode();
  const int ne = ntriangles();
  Indices idx( ne );
  for (int i=0; i<ne; ++i)
    idx[i] = i;
  root->insert(*this, idx.begin(), idx.end());
  nintree = ne;
  nrebuild = ne;
}

void DynTriTree::clear()
{
  nintree = 0;
  nodePool.purge_memory();
  root = 0;
}

void DynTriTree::insert(uint k)
{
  NodeStack parents;

  // walk down the tree, locate leaf triangle into
  // which to insert triangle k, keep track of parents
  Node *pn = root;
  Vct2 trc = bbCenter(k);
  while (not pn->leaf()) {
    parents.push_back(pn);
    if ( pn->leftTriangle(trc) )
      pn = pn->leftChild();
    else
      pn = pn->rightChild();
  }

  // insert into leaf pn, split if necessary
  if (pn->append(k)) {
    pn->updateBounds(*this);
  } else {
    pn->splitInsert(*this, k);
  }

  // walk down the stack and adapt bounding volumes
  bool changed(true);
  //  Node *ubn = 0;
  const int np = parents.size();
  for (int i=0; i<np; ++i) {
    Node *pn = parents[np-i-1];
    //    Real unb = pn->unbalance();
    //    if (unb > 4.0)
    //      ubn = pn;
    changed = pn->updateBounds(*this);
    if (not changed)
      break;
  }

  //  cout << "in tree " << nintree << " rebalanced: " << nrebuild << endl;

  //  if (ubn != 0 and (nintree > 2*nrebuild or nintree > nrebuild + 64)) {
  //    // ubn->rebalance(*this);
  //    root->rebalance(*this);
  //    nrebuild = nintree;
  //  }

  nintree++;
}

Real DynTriTree::leafSqArea() const
{
  return (root == 0) ? 0.0 : root->leafSqArea();
}

uint DynTriTree::nearest(const Vct2 &p) const
{
  assert(root != 0);
  uint best = NotFound;
  Real dmin = std::numeric_limits<Real>::max();
  root->nearestTriangle(*this, p, best, dmin);
  return best;
}

Real DynTriTree::pdistance(const Vct2 &p, uint t) const
{
  const uint *v = triangle(t);
  Real dl[3];
  int scase = 0;
  for (int k=0; k<3; ++k) {
    const Vct2 & a = vertex( v[k] );
    const Vct2 & b = vertex( v[(k+1)%3] );
    Vct2 re(b - a), rp(p - a);
    Real z = re[0]*rp[1] - re[1]*rp[0];
    scase |= (z < 0.0) << k;
    dl[k] = 0.5*fabs(z) / norm(re);
  }

  switch (scase) {
  case 0:
    return 0.0;
  case 1:
    return dl[0];
  case 2:
    return dl[1];
  case 3:
    return norm(p - vertex(v[1]));
  case 4:
    return dl[2];
  case 5:
    return norm(p - vertex(v[0]));
  case 6:
    return norm(p - vertex(v[2]));
  };

  assert(!"Should never be here.");
  return norm(p - vertex(v[0]));
}

// ----------------- DynTriTree::Node ------------------------------------

void DynTriTree::Node::splitInsert(DynTriTree &tree, uint kt)
{
  if ( leaf() )
    split(tree);

  const uint ne = DynTriTree::maxCount+1;
  uint elx[ne];
  std::copy(idx, idx+maxCount, elx);
  elx[DynTriTree::maxCount] = kt;
  insert(tree, elx, elx+ne);
}

void DynTriTree::Node::rebalance(DynTriTree &tree)
{
  if (leaf())
    return;

  cout << "Rebalancing..." << endl;

  // special case of one-above-leaf
  if (left->leaf() and right->leaf()) {
    uint elx[2*DynTriTree::maxCount];
    std::copy(left->idx, left->idx+left->nelm, elx);
    std::copy(right->idx, right->idx+right->nelm, elx+left->nelm);
    uint ne = left->nelm + right->nelm;
    insert(tree, elx, elx+ne);
  } else {
    Indices elx;
    collectElements(elx);
    insert(tree, elx.begin(), elx.end());
  }
}

bool DynTriTree::Node::updateBounds(const DynTriTree &tree)
{
  Dop2d2<Real> dop;
  if (leaf()) {
    boundingDop(tree, idx, idx+nelm, dop);
  } else {
    dop.enclose( left->bvol );
    dop.enclose( right->bvol );
  }

  bool changed = !(dop == bvol);
  bvol = dop;
  return changed;
}

void DynTriTree::Node::nearestTriangle(const DynTriTree &tree,
                                       const Vct2 &p, uint & best, Real &dmin) const
{
  if ( leaf() ) {
    for (uint i=0; i<nelm; ++i) {
      Real d = tree.pdistance(p, idx[i]);
      if (d < dmin) {
        dmin = d;
        best = idx[i];
      }
      if (d == 0.0)
        return;
    }
  } else {
    Real dleft = left->bvol.eclDistance(p.pointer());
    if (dleft <= dmin)
      left->nearestTriangle(tree, p, best, dmin);
    if (dmin == 0.0)
      return;
    Real dright = left->bvol.eclDistance(p.pointer());
    if (dright <= dmin)
      right->nearestTriangle(tree, p, best, dmin);
    if (dmin == 0.0)
      return;
  }
}

Real DynTriTree::Node::leafSqArea() const
{
  Real sum = 0;
  if (leaf()) {
    sum += bvol.sqsize();
  } else {
    sum += left->leafSqArea();
    sum += right->leafSqArea();
  }
  return sum;
}

void DynTriTree::Node::dbprint(uint k) const
{
  cout << "Node " << k << " split: " << iax << endl;
  cout << "x: " << bvol.minCoef(0) << " | " << bvol.maxCoef(0) << endl;
  cout << "y: " << bvol.minCoef(1) << " | " << bvol.maxCoef(1) << endl;
  if (leaf()) {
    cout << "leaf " << nelm << " : ";
    for (uint i=0; i<nelm; ++i)
      cout << idx[i] << ", ";
    cout << endl;
  } else {
    cout << "Unbalance: " << unbalance() << " Growth: "<< growth() << endl;
    left->dbprint(2*k+1);
    right->dbprint(2*k+2);
  }
}
