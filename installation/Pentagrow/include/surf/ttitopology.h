
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
 
#ifndef SURF_TTITOPOLOGY_H
#define SURF_TTITOPOLOGY_H

#include <genua/connectmap.h>
#include "spotrefine.h"
#include "ttintersector.h"
#include "ttinode.h"
#include "ttintersection.h"

class MeshFields;

/** Intersection topology.

  This is the top-level object for the intersection processing algorithm in 
  libsurf. It uses an intersector object, which computes the discrete triangle
  intersections, and processes the intersection segments found. 

  \ingroup meshgen
  \sa TTIntersection, TTIntersector
*/
class TTiTopology
{
  public:
    
    /// empty topology object
    TTiTopology() {}
 
    /// construct intersection topology 
    TTiTopology(const TTIntersectorPtr & tti);
    
    /// visualization (lines only)
    void addLineViz(MeshFields & mvz) const;
    
    /// search for singly-connected intersection lines
    uint findLines();
        
    /// refine intersection points iteratively 
    void refine();
    
    /// number of intersection lines identifies
    uint nlines() const {return lines.size();}
    
    /// filter identified intersection lines to improve mesh quality
    void filter(uint jline); 
    
    /// construct projection of intersection line k on component c
    bool projection(uint k, const MeshComponent *c, 
                    PointList<2> & ppt, PointList<3> & vtx) const;
    
    /// determine local refinement pattern near intersections
    void spotRefinement(const MeshComponent *c, Real smax, RSpotArray & sra) const;
    
    /// determine vertices affected by intersections
    void affectedVertices(const MeshComponent *c, Indices & vlist) const;
    
  private:
    
    /// merge intersection nodes
    void mergeNodes(Real mthreshold);
    
    /// helper for mergeNodes, does not work otherwise
    Real uvDistance(const std::vector<bool> & onb, uint i, uint j) const;
    
    /// find three-surface intersections
    void findTriples();
    
    /// construct node-segment connectivity data
    void fixate();
    
    /// compute minimum local triangle dimension around node k
    Real localLength(uint k) const;
    
  private:
    
    /// pointer to intersector object
    TTIntersectorPtr tip;
    
    /// connectivity from nodes to segments
    ConnectMap n2smap;
    
    /// points shared by intersection segments
    TTiNodeArray nodes;
    
    /// edges / segments
    TTIntersectionArray segments;
    
    /// segment indices which make up singly-connected strings
    std::vector<std::deque<uint> > lines;
    
    /// parameter limit for tolerant boundaries
    static Real tolBound;
};

#endif
