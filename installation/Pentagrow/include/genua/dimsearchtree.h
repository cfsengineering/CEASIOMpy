
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
 
#ifndef GENUA_DTREESEARCH_H
#define GENUA_DTREESEARCH_H

#include <boost/shared_ptr.hpp>
#include "sharedvector.h"
#include "point.h"

/** Dimension search tree.
  
  A three-dimensional geometric tree data structure for efficient point 
  searches. The find() method can be used to collect indices (into the
  point array passed at construction) of points located within some radius
  t from a reference point. The search time is proportional to the logarithm
  of the point array size.

  \b Note: This class is part of an old interface.
  
  \deprecated
  */
class DimSearchTree
{
  public:
    
    typedef SharedVector<SVector<3> > VertexArrayPtr;
    typedef boost::shared_ptr<DimSearchTree> NodePtr;
    
    /// empty construction
    DimSearchTree() : level(0) {}
    
    /// construct from point list, split 
    DimSearchTree(const PointList<3> & pts);
    
    /// find indices of all vertices within a radius t
    void find(const Vct3 & pt, Real t, Indices & fnd) const;
    
  private:
    
    /// recursive sibling construction
    DimSearchTree(VertexArrayPtr vap, Indices & ix, uint lv);
    
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

