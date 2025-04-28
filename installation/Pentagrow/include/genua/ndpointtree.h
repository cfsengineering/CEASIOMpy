
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
 
#ifndef GENUA_NDPOINTTREE_H
#define GENUA_NDPOINTTREE_H

#include "defines.h"
#include "point.h"
#include "implicittree.h"
#include "kdop.h"
#include <boost/shared_array.hpp>

/** Balanced binary tree for N-dimensional points.

  NDPointTree is a generalization of BSearchTree which makes use of an
  implicitely represented balanced binary tree to eliminate a large number
  of small memory allocations. Furthermore, the comparatively costly tree
  construction operation is parallelized in ImplicitTree::sort().

  Algorithmically, NDPointTree is a bounding-volume hierarchy (BVH) using
  simple axis-aligned bounding boxes as bounding volumes. Nodes are split
  along the median using the longest axis of a bounding box.

  \ingroup geometry
  \sa ImplicitTree, DopBase
  */
template <int ND, class FloatType>
class NDPointTree
{
public:

  typedef SVector<ND,FloatType> NDPoint;
  typedef boost::shared_array<NDPoint> NDPointArray;
  typedef DopBase<FloatType,ND> DopType;

  /** Division and comparison along coordinate axes.

    This is an internal helper class used to define the algorithm used to
    construct bounding volumes and define an ordering based on the longest
    dimension of the bounding volume.

  */
  class Divider {
  public:

    /// construct divider
    Divider(NDPointTree & ptree) : tree(ptree), iax(0) {}

    /// node division criterion
    template <class Iterator>
    bool divide(uint inode, Iterator nbegin, Iterator nend) {
      if (nend <= nbegin)
        return false;
      NDPoint p1, p2;
      p1 = std::numeric_limits<FloatType>::max();
      p2 = - std::numeric_limits<FloatType>::max();
      for (Iterator itr = nbegin; itr != nend; ++itr) {
        const NDPoint & q( tree.point(*itr) );
        DopType::fit(q.pointer(), p1.pointer(), p2.pointer());
      }
      DopType & dop( tree.dop(inode) );
      dop.setCoef(p1.pointer(), p2.pointer());
      iax = dop.longestAxis();

      // leaf nodes must be processed to generate the bounding box,
      // but they do not need to be sorted
      return (uint(std::distance(nbegin, nend)) > tree.minPointCount());
    }

    /// sorting criterion
    bool operator() (uint a, uint b) const {
      const NDPoint & pa( tree.point(a) );
      const NDPoint & pb( tree.point(b) );
      return pa[iax] < pb[iax];
    }

  private:

    /// reference to point tree
    NDPointTree & tree;

    /// separating axis
    int iax;
  };

public:

  /// construct empty tree
  NDPointTree() {}

  /// allocate storage
  uint allocate(uint np, const NDPoint *pts, bool share, uint mincount=4) {
    if (share) {
      // const can be cast away since points are accessed read-only
      points = NDPointArray( (NDPoint *) pts, null_deleter() );
      assert(&points[0] == pts);
    } else {
      points = NDPointArray( new NDPoint[np] );
      std::copy(pts, pts+np, points.get());
    }
    itree.init(np, mincount);
    bvol.resize(itree.nnodes());
    return itree.nnodes();
  }

  /// convenience interface
  uint allocate(const PointList<ND,FloatType> & pts,
                bool share, uint mincount = 8)
  {
    clear();
    if (pts.size() > 0)
      return allocate(pts.size(), &pts[0], share, mincount);
    else
      return 0;
  }

  /// clear storage
  void clear() {
    bvol.clear();
    points.reset();
    itree = ImplicitTree();
  }

  /// sort entire tree
  void sort() {
    Divider cmp(*this);
    itree.sort(cmp);
  }

  /// number of indexed points
  uint npoints() const {
    return itree.size();
  }

  /// access minimum number of points in node
  uint minPointCount() const {return itree.minSize();}

  /// access point
  const NDPoint & point(uint k) const {
    assert(k < itree.size());
    return points[k];
  }

  /// access bounding volume for node k
  DopType & dop(uint k) {
    assert(k < bvol.size());
    return bvol[k];
  }

  /// access bounding volume for node k
  const DopType & dop(uint k) const {
    assert(k < bvol.size());
    return bvol[k];
  }

  /// find point nearest to p using iterative procedure
  uint nearest(const NDPoint & p) const {
    return nearestIterative(p);
  }

  /// find point indices within radius of pt
  bool find(const NDPoint & pt, FloatType r, Indices & fnd) const {
    FloatType ldst, rdst, sqr = sq(r);
    uint inode(0), nnodes(bvol.size());
    std::vector<uint> opt;

    while (inode != NotFound) {

      uint left = itree.leftChild(inode);
      uint right = itree.rightChild(inode);

      if (left >= nnodes) {

        // inode is a leaf node, process contained points
        uint ibegin, iend;
        itree.offsetRange(inode, ibegin, iend);
        for (uint i=ibegin; i<iend; ++i) {
          uint idx = itree.index(i);
          FloatType dst = sq(pt - point(idx));
          if (dst < sqr)
            fnd.push_back( idx );
        }

        inode = NotFound;

      } else {

        ldst = rdst = std::numeric_limits<FloatType>::max();
        if (left < nnodes)
          ldst = bvol[left].eclDistance(pt.pointer());
        if (right < nnodes)
          rdst = bvol[right].eclDistance(pt.pointer());
        assert(std::isfinite(ldst) or std::isfinite(rdst));

        inode = NotFound;

        if (ldst < sqr)
          inode = left;
        if (rdst < sqr) {
          if (inode == NotFound)
            inode = right;
          else
            opt.push_back(right);
        }


      }  // process child nodes

      // pick next candidate node off the stack
      if (inode == NotFound and (not opt.empty())) {
        inode = opt.back();
        opt.pop_back();
      }
    }

    return (not fnd.empty());
  }

  /// compute replacement map for de-duplication
  uint repldup(FloatType threshold, Indices & repl, Indices & keep) const
  {
    const int nv = npoints();

    // find (nearly) identical vertices
    keep.clear();
    keep.reserve(nv);
    repl.resize(nv);
    fill(repl.begin(), repl.end(), NotFound);
    uint count(0);
    Indices idt;
    idt.reserve(64);

    for (int i=0; i<nv; ++i) {

      // for each vertex which is not yet marked as duplicate
      if (repl[i] == NotFound) {

        // mark as a vertex to keep
        repl[i] = count;

        // locate vertices within radius of threshold
        idt.clear();
        this->find(point(i), threshold, idt);

        // mark duplicates with indices beyond i
        const int ni = idt.size();
        for (int j=0; j<ni; ++j) {
          if (idt[j] > uint(i)) {
            assert(idt[j] < repl.size());
            repl[idt[j]] = count;
          }
        }

        // one more vertex kept
        ++count;
        keep.push_back(i);
      }

      // skip vertices marked as duplicates
    }

    return count;
  }

  /// determine memory footprint
  float megabyte(bool shared) const {
    float b(sizeof(NDPointTree<ND,FloatType>));
    b += bvol.capacity() * sizeof(DopType);
    if (not shared)
      b += npoints() * sizeof(NDPoint);
    return 1e-6f*b + itree.megabyte();
  }

private:

  /// find point nearest to p in node inode, recursively
  void nearestRecursive(const NDPoint & p, uint inode,
                        uint & inear, FloatType & mindst) const
  {
    // this is much slower than the iterative version below
    // but strangely also much slower than BSearchTree::nearest.

    const uint nnodes = bvol.size();
    const uint left = itree.leftChild(inode);
    const uint right = itree.rightChild(inode);
    if (left < nnodes) {

      FloatType ldst = bvol[left].eclDistance(p.pointer());
      FloatType rdst = bvol[right].eclDistance(p.pointer());
      assert(std::isfinite(ldst) or std::isfinite(rdst));

      if (ldst < mindst)
        nearestRecursive(p, left, inear, mindst);

      if (rdst < mindst)
        nearestRecursive(p, right, inear, mindst);

    } else {

      // process leaf node
      uint ibegin, iend;
      itree.offsetRange(inode, ibegin, iend);
      for (uint i=ibegin; i<iend; ++i) {
        uint idx = itree.index(i);
        FloatType dst = sq(p - point(idx));
        if (dst < mindst) {
          mindst = dst;
          inear = idx;
        }
      }
    }
  }

  /// find point nearest to p using iterative procedure
  uint nearestIterative(const NDPoint & p) const
  {
    uint inear = 0;
    uint inode = 0;
    uint nnodes = bvol.size();

    FloatType ldst, rdst, best;
    best = sq(p - point(inear));

    typedef std::pair<uint,FloatType> NodeDst;
    std::vector<NodeDst> opt;

    while (inode != NotFound) {

      uint left = itree.leftChild(inode);
      uint right = itree.rightChild(inode);

      if (left >= nnodes) {

        // inode is a leaf node, process contained points
        uint ibegin, iend;
        itree.offsetRange(inode, ibegin, iend);
        for (uint i=ibegin; i<iend; ++i) {
          uint idx = itree.index(i);
          FloatType dst = sq(p - point(idx));
          if (dst < best) {
            best = dst;
            inear = idx;
          }
        }

        // early exit : will never get better than zero...
        if (best == 0)
          return inear;

        inode = NotFound;

      } else {

        ldst = rdst = std::numeric_limits<FloatType>::max();
        if (left < nnodes)
          ldst = bvol[left].eclDistance(p.pointer());
        if (right < nnodes)
          rdst = bvol[right].eclDistance(p.pointer());
        assert(std::isfinite(ldst) or std::isfinite(rdst));

        inode = NotFound;

        // If p is in left child box (ldst == 0) or at least closer to
        // the box than the smallest point distance computed yet, continue
        // loop with left child. However, if ldst *could* possibly contain
        // a closer match but rdst is smaller, continue with right child but
        // put ldst on the stack.

        if (ldst < best) {
          if (ldst <= rdst)
            inode = left;
          else
            opt.push_back( std::make_pair(left, ldst) );
        }

        if (rdst < best) {
          if (rdst < ldst)
            inode = right;
          else
            opt.push_back( std::make_pair(right, rdst) );
        }

      }  // process child nodes

      // pick next candidate c off the stack : discard directly if distance of
      // p from box c is larger than the current best hit, proceed otherwise
      while (inode == NotFound) {
        if (opt.empty())
          break;
        NodeDst c = opt.back();
        opt.pop_back();
        if (c.second < best) {
          inode = c.first;
          break;
        }
      }
    }

    return inear;
  }

  /// find point nearest to p using iterative procedure
  uint findIterative(const NDPoint & p) const
  {
    uint inear = 0;
    uint inode = 0;
    uint nnodes = bvol.size();

    FloatType ldst, rdst, best;
    best = sq(p - point(inear));

    typedef std::pair<uint,FloatType> NodeDst;
    std::vector<NodeDst> opt;

    while (inode != NotFound) {

      uint left = itree.leftChild(inode);
      uint right = itree.rightChild(inode);

      if (left >= nnodes) {

        // inode is a leaf node, process contained points
        uint ibegin, iend;
        itree.offsetRange(inode, ibegin, iend);
        for (uint i=ibegin; i<iend; ++i) {
          uint idx = itree.index(i);
          FloatType dst = sq(p - point(idx));
          if (dst < best) {
            best = dst;
            inear = idx;
          }
        }

        // early exit : will never get better than zero...
        if (best == 0)
          return inear;

        inode = NotFound;

      } else {

        ldst = rdst = std::numeric_limits<FloatType>::max();
        if (left < nnodes)
          ldst = bvol[left].eclDistance(p.pointer());
        if (right < nnodes)
          rdst = bvol[right].eclDistance(p.pointer());
        assert(std::isfinite(ldst) or std::isfinite(rdst));

        inode = NotFound;

        // If p is in left child box (ldst == 0) or at least closer to
        // the box than the smallest point distance computed yet, continue
        // loop with left child. However, if ldst *could* possibly contain
        // a closer match but rdst is smaller, continue with right child but
        // put ldst on the stack.

        if (ldst < best) {
          if (ldst <= rdst)
            inode = left;
          else
            opt.push_back( std::make_pair(left, ldst) );
        }

        if (rdst < best) {
          if (rdst < ldst)
            inode = right;
          else
            opt.push_back( std::make_pair(right, rdst) );
        }

      }  // process child nodes

      // pick next candidate c off the stack : discard directly if distance of
      // p from box c is larger than the current best hit, proceed otherwise
      while (inode == NotFound) {
        if (opt.empty())
          break;
        NodeDst c = opt.back();
        opt.pop_back();
        if (c.second < best) {
          inode = c.first;
          break;
        }
      }
    }

    return inear;
  }


private:

  /// optionally shared point list
  NDPointArray points;

  /// binary tree
  ImplicitTree itree;

  /// bounding volumes
  std::vector<DopType> bvol;
};

#endif // NDPOINTTREE_H
