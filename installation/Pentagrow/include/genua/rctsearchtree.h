
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       rctsearchtree.h
 * begin:      Oct 2004
 * copyright:  (c) 2004 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * 2D geometric trees for point searches
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */
 
#ifndef GENUA_RCTSEARCHTREE_H
#define GENUA_RCTSEARCHTREE_H

#include <boost/shared_ptr.hpp>
#include "bounds.h"
#include "sharedvector.h"
#include "point.h"

/** Dimension search tree.
  
  A two-dimensional geometric tree data structure for efficient point 
  searches. The find() method can be used to collect indices (into the
  point array passed at construction) of points located within some radius
  t from a reference point. The search time is proportional to the logarithm
  of the point array size.
  
  */
class RctSearchTree
{
  public:
    
    typedef SharedVector<SVector<2> > VertexArrayPtr;
    typedef boost::shared_ptr<RctSearchTree> NodePtr;
    
    /// empty construction
    RctSearchTree() : level(0) {}
    
    /// construct from point list, split 
    RctSearchTree(const PointList<2> & pts);
    
    /// find indices of all vertices within a radius t
    void find(const Vct2 & pt, Real t, Indices & fnd) const;
    
  private:
    
    /// recursive sibling construction
    RctSearchTree(VertexArrayPtr vap, Indices & ix, uint lv);
    
    /// initialize and construct recursively
    void init();
    
    /// create left and right index sets
    void partition(Indices & ileft, Indices & iright);
    
  private:
    
    /// siblings
    NodePtr left, right;
    
    /// subdivision level
    uint level;
    
    /// indices of vertices in this node
    Indices idx;
    
    /// pointer to vertex array
    VertexArrayPtr vtx;
    
    /// median and distances for this division
    Real median, lmin, rmin;
};

#endif
