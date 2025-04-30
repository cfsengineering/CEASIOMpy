
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
 
#ifndef GENUA_BBTREE_H
#define GENUA_BBTREE_H

#include <boost/shared_ptr.hpp>
#include "sharedvector.h"
#include "point.h"
#include "bounds.h"

/** Bounding-box search tree.

  A geometric binary tree data structure for efficient nearest neighbor 
  queries. The constructor builds a bounding box tree data structure which
  can be efficiently queried for neighbor searches using nearest(), which
  returns the index of the point in the original point set (passed at 
  construction time) closest to the argument of nearest().
  
  */
class BSearchTree
{
  public:
    
    typedef SharedVector<SVector<3> > VertexArrayPtr;
    typedef boost::shared_ptr<BSearchTree> NodePtr;
    
    /// empty construction
    BSearchTree() : level(0) {}
    
    /// construct from point list, split 
    BSearchTree(const PointList<3> & pts);

    /// access vertex k
    const Vct3 & vertex(uint k) const {return vtx[k];}

    /// insert point into tree
    uint insert(const Vct3 & p);
    
    /// erase a point from tree 
    void erase(uint i);
    
    /// find nearest point
    uint nearest(const Vct3 & pt) const;

    /// find nearest point not identical to itself
    uint nearestOther(uint ip) const;

    /// locate n nearest points
    uint neighborhood(const Vct3 & p, uint nmin,
                      uint nmax, Indices & nbh) const;
    
    /// find all points within a radius r of pt
    void find(const Vct3 & pt, Real r, Indices & fnd) const;

    /// number of points in this node
    uint size() const {return idx.size();}
    
    /// diagonal of the bounding box
    Real diagonal() const {return bb.diagonal();}

    /// compute a geometric node ordering
    void proximityOrdering(Indices & perm) const;

    /// identify duplicate vertices and assemble replacement map
    uint repldup(Real threshold, Indices & repl, Indices & keep) const;
    
    /// count number of tree nodes
    uint nTreeNodes() const;

  private:
    
    /// initialize and create siblings
    void init();
    
    /// recursive sibling construction
    BSearchTree(VertexArrayPtr vap, Indices & ix, uint lv)
      : level(lv), idx(ix), vtx(vap)
    {
      assert(ix.size() > 0);
      assert(lv < 8192);
      init();
    }
    
    /// create left and right index sets
    void partition(Indices & ileft, Indices & iright) const;
    
    /// distance from bounding box
    Real fromBox(const Vct3 & pt) const {
      if (bb.isInside(pt))
        return 0.0;
      else
        return norm(bb.distance(pt));
    }

    /// insert point into this node
    void insert(const Vct3 & p, uint i);

  private:
    
    /// siblings
    NodePtr left, right;
    
    /// subdivision level
    uint level;
    
    /// indices of vertices in this node
    Indices idx;
    
    /// pointer to vertex array
    VertexArrayPtr vtx;
    
    /// bounding box
    BndBox bb;
    
    /// flag indicating whether idx is sorted
    bool bSorted;
};

#endif
