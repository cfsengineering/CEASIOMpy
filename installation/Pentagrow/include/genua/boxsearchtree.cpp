
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
 
#include "boxsearchtree.h"

using namespace std;

static const uint min_node_size(8);

class CoordSort 
{
public:
  CoordSort(const Real *p, int kc) : pts(p), ci(kc) {}
  bool operator() (uint a, uint b) const {
    return pts[3*a+ci] < pts[3*b+ci];
  }
private:
  const Real *pts;
  int ci;
};

BSearchTree::BSearchTree(const PointList<3> & pts) : level(0)
{
  // copy master point list
  vtx.resize(pts.size());
  std::copy(pts.begin(), pts.end(), vtx.begin());
  idx.resize(pts.size());
  for (uint i=0; i<idx.size(); ++i)
    idx[i] = i;

  init();
}

void BSearchTree::init()
{
  // sort indices numerically (to make erase() faster)
  // std::sort(idx.begin(), idx.end());
  bSorted = false;
  
  // find bounding box
  Vct3 p1, p2;
  p1 = huge;
  p2 = -huge;
  for (uint i=0; i<idx.size(); ++i) {
    const Vct3 & q(vtx[idx[i]]);
    for (uint k=0; k<3; ++k) {
      p1[k] = min(p1[k], q[k]);
      p2[k] = max(p2[k], q[k]);
    }
  }
  bb = BndBox(p1,p2);
  
  if (idx.size() > min_node_size and bb.diagonal() > gmepsilon) {

    // create siblings 
    Indices ileft, iright;
    partition(ileft, iright);
    if (ileft.empty() or iright.empty()) {
      return;
    } else {
      left = NodePtr(new BSearchTree(vtx, ileft, level+1));
      right = NodePtr(new BSearchTree(vtx, iright, level+1));
    }
  }
  
  // nodes with less than 8 vertices are not split
}

uint BSearchTree::nTreeNodes() const
{
  uint n(1);
  if (left)
    n += left->nTreeNodes();
  if (right)
    n += right->nTreeNodes();
  return n;
}

uint BSearchTree::nearest(const Vct3 & pt) const
{
  // linear search when no siblings present
  if (not left) {
    uint best(0);
    Real dst, mindst(huge);
    const int ni = idx.size();
    for (int i=0; i<ni; ++i) {
      dst = sq(pt - vtx[idx[i]]);
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
  ldst = sq(left->fromBox(pt));
  rdst = sq(right->fromBox(pt));

  // First, find nearest point in closest bounding box.
  // Then, check if the distance found is larger than the distance
  // of the point to the other bounding box. If so, there might be 
  // a better point in the other box (otherwise impossible). Hence,
  // find the best point in the other box and compare the two.
  if (ldst < rdst) {
    lbest = left->nearest(pt);
    dst = sq(pt - vtx[lbest]);
    if (dst > rdst) {
      rbest = right->nearest(pt);
      if (sq(pt - vtx[rbest]) < dst)
        return rbest;
      else
        return lbest;
    } else
      return lbest;
  } else {
    rbest = right->nearest(pt);
    dst = sq(pt - vtx[rbest]);
    if (dst > ldst) {
      lbest = left->nearest(pt);
      if (sq(pt - vtx[lbest]) < dst)
        return lbest;
      else
        return rbest;
    } else
      return rbest;
  }
}

uint BSearchTree::nearestOther(uint ip) const
{
  const Vct3 & pt( vtx[ip] );

  // linear search when no siblings present
  if (not left) {
    uint best = NotFound;
    Real dst, mindst(huge);
    for (uint i=0; i<idx.size(); ++i) {
      if (idx[i] == ip)
        continue;
      dst = sq(pt - vtx[idx[i]]);
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
  ldst = sq(left->fromBox(pt));
  rdst = sq(right->fromBox(pt));

  // First, find nearest point in closest bounding box.
  // Then, check if the distance found is larger than the distance
  // of the point to the other bounding box. If so, there might be
  // a better point in the other box (otherwise impossible). Hence,
  // find the best point in the other box and compare the two.
  if (ldst < rdst) {
    lbest = left->nearestOther(ip);
    dst = sq(pt - vtx[lbest]);
    if (dst > rdst) {
      rbest = right->nearestOther(ip);
      if (sq(pt - vtx[rbest]) < dst)
        return rbest;
      else
        return lbest;
    } else
      return lbest;
  } else {
    rbest = right->nearestOther(ip);
    dst = sq(pt - vtx[rbest]);
    if (dst > ldst) {
      lbest = left->nearestOther(ip);
      if (sq(pt - vtx[lbest]) < dst)
        return lbest;
      else
        return rbest;
    } else
      return rbest;
  }
}

uint BSearchTree::neighborhood(const Vct3 & pt, uint nmin,
                               uint nmax, Indices & nbh) const
{
  // estimate search radius
  uint nmean = (nmin+nmax) / 2;
  Real r = 0.5 * bb.diagonal() * std::pow( Real(nmean)/idx.size(), 1./3. );

  // iterate to improve search radius
  Real f = 2.0;
  Indices fnd;
  for (int i=0; i<16; ++i) {
    fnd.clear();
    find(pt, r, fnd);
    uint n = fnd.size();
    if (n < nmin) {
      r *= f;
    } else if (n > nmax) {
      r /= f;
    } else
      break;

    // decrease factor in each pass
    f = std::pow(f, 0.9);
  }

  fnd.swap(nbh);
  return nbh.size();
}

void BSearchTree::find(const Vct3 & pt, Real r, Indices & fnd) const
{
  // linear search at leaf nodes
  Real sqr = sq(r);
  if (not left) {
    const uint n(idx.size());
    for (uint i=0; i<n; ++i) {
      if (sq(vtx[idx[i]] - pt) < sqr)
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

void BSearchTree::proximityOrdering(Indices & perm) const
{
  if (not left) {
    perm.insert(perm.end(), idx.begin(), idx.end());
  } else {
    left->proximityOrdering(perm);
    right->proximityOrdering(perm);
  }
}

void BSearchTree::partition(Indices & ileft, Indices & iright) const
{
  assert(idx.size() > 1);
  Real ds[3];  
  ds[0] = bb.length();
  ds[1] = bb.width();
  ds[2] = bb.height();

  // decide along which direction to split
  uint c = std::distance(ds, std::max_element(ds, ds+3));
  if (ds[c] < gmepsilon)
    return;

  // partition a copy of idx (need idx kept sorted)
  Indices tmp(idx);
  Indices::iterator imid = tmp.begin() + tmp.size()/2;
  CoordSort pred(vtx[0].pointer(), c);
  
  // postcondition : for all k in (begin, imid[, crd[k] is 
  // smaller than crd[j] for j in (imid, end[, that is,
  // indices in tmp are partitioned along the median of crd 
  std::nth_element(tmp.begin(), imid, tmp.end(), pred);
  
  ileft.clear();
  ileft.insert(ileft.end(), tmp.begin(), imid);
  iright.clear();
  iright.insert(iright.end(), imid, tmp.end());
}

uint BSearchTree::insert(const Vct3 & p)
{
  // top level call to insert vertex
  vtx.push_back(p);
  this->insert(p, vtx.size()-1);
  return vtx.size()-1;
}

void BSearchTree::insert(const Vct3 & p, uint i)
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

void BSearchTree::erase(uint i)
{
  if (not bSorted) {
    std::sort(idx.begin(), idx.end());
    bSorted = true;
  }
  
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

uint BSearchTree::repldup(Real threshold, Indices & repl, Indices & keep) const
{
  const uint nv = vtx.size();

  // find (nearly) identical vertices
  repl.resize(nv);
  keep.clear();
  fill(repl.begin(), repl.end(), NotFound);
  uint count(0);
  Indices idt;
  for (uint i=0; i<nv; ++i) {

    // for each vertex which is not yet marked as duplicate
    if (repl[i] == NotFound) {

      // mark as a vertex to keep
      repl[i] = count;

      // locate vertices within radius of threshold
      idt.clear();
      find(vtx[i], threshold, idt);

      // mark duplicates with indices beyond i
      for (uint j=0; j<idt.size(); ++j) {
        if (idt[j] > i)
          repl[idt[j]] = count;
      }

      // one more vertex kept
      ++count;
      keep.push_back(i);
    }

    // skip vertices marked as duplicates
  }

  return count;
}

