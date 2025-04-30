
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       rsearchtree.h
 * begin:      Oct 2004
 * copyright:  (c) 2004 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * bounding-box search tree in two dimensions
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#ifndef GENUA_RSEARCHTREE_H
#define GENUA_RSEARCHTREE_H

#include <boost/shared_ptr.hpp>
#include "sharedvector.h"
#include "point.h"
#include "bounds.h"

/** Bounding-rectangle search tree.

  A geometric binary tree data structure for efficient nearest neighbor
  queries. The constructor builds a bounding box tree data structure which
  can be efficiently queried for neighbor searches using nearest(), which
  returns the index of the point in the original point set (passed at
  construction time) closest to the argument of nearest().
  
  This is the two-dimensional equivalent of BSearchTree.

  \deprecated
  \ingroup meshgen
  \sa DnMesh
  
 */
class RSearchTree
{
public:

  typedef SharedVector<SVector<2> > VertexArrayPtr;
  typedef boost::shared_ptr<RSearchTree> NodePtr;

  /// empty construction
  RSearchTree() : level(0) {}

  /// construct from point list, split
  RSearchTree(const PointList<2> & pts);

  /// insert point into tree
  uint insert(const Vct2 & p);

  /// erase a point from tree
  void erase(uint i);

  /// find nearest point
  uint nearest(const Vct2 & pt) const;

  /// find all points within a radius r of pt
  void find(const Vct2 & pt, Real r, Indices & fnd) const;

  /// number of points in this node
  uint size() const {return idx.size();}

  /// compute a geometric node ordering
  void proximityOrdering(Indices & perm) const;

private:

  /// initialize and create siblings
  void init();

  /// recursive sibling construction
  RSearchTree(VertexArrayPtr vap, Indices & ix, uint lv);

  /// create left and right index sets
  void partition(Indices & ileft, Indices & iright) const;

  /// distance from bounding box
  Real fromBox(const Vct2 & pt) const {
    if (bb.isInside(pt))
      return 0.0;
    else
      return norm(bb.distance(pt));
  }

  /// insert point into this node
  void insert(const Vct2 & p, uint i);

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
  BndRect bb;
};

#endif
