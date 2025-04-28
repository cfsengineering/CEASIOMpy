
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
 
#ifndef SURF_TTINTERSECTOR_H
#define SURF_TTINTERSECTOR_H

#include <boost/shared_ptr.hpp>
#include <genua/sharedvector.h>
#include <genua/bounds.h>
#include <genua/synchron.h>
#include "meshcomponent.h"
#include "ttintersection.h"

class ConnectMap;
class ThreadPool;
class TTIntersector;
class MeshFields;
typedef boost::shared_ptr<TTIntersector> TTIntersectorPtr;

/** Intersect triangle meshes.

    \ingroup meshgen
    \sa TTIntersection
*/
class TTIntersector
{
  public:
    
    /// construct empty intersector
    TTIntersector() {}

    /// add triangle mesh to root node
    void addMesh(const MeshComponent & mp);
    
    /// sort faces to facilitate searching (root node only)
    void sortFaces();

    /// find index for face f (requires sorting)
    uint bsearchFace(const TriFace & f) const;

    /// update root node bounding box when all triangles added
    void updateBox();
    
    /// number of triangles in this node 
    uint nfaces() const {return ifaces.size();}

    /// number of tri-tri intersection segments collected
    uint nisec() const {return allisec.size();}
    
    /// minimum number of triangles in node
    static uint minFaceCount() {return min_node_triangles;}
    
    /// change minimum number of triangles in node
    static void minFaceCount(uint c) {min_node_triangles = c;}
    
    /// global index of local face i 
    uint index(uint i) const {
      assert(i < nfaces());
      return ifaces[i];
    } 
    
    /// access face with global index i 
    const TriFace & face(uint iglob) const {return triangles[iglob];}
    
    /// check if this is a leaf node
    bool isLeaf() const {return ((not mleft) and (not mright));}
    
    /// access the left child node 
    TTIntersector & leftChild() {
      assert(mleft);
      return *mleft;
    }
    
    /// access the right child node 
    TTIntersector & rightChild() {
      assert(mright);
      return *mright;
    }
    
    /// check if this bounding box intersects other's box
    bool bbIntersect(const TTIntersector & other) const {
      return bb.intersects(other.bb);
    }
    
    /// check if this node is exclusively on the same patch as other
    bool samePatch(const TTIntersector & other) const {
      if (patches.size() > 1 or other.patches.size() > 1)
        return false;
      else if (patches[0] == other.patches[0])
        return true;
      else
        return false;
    }

    /// check if this node is on a neighbor patch of other
    bool neighborPatch(const TTIntersector & other) const {
      if (patches.size() > 1 or other.patches.size() > 1)
        return false;
      else if (patches[0]->isNeighbor(other.patches[0]))
        return true;
      else
        return false;
    }
    
    /// split node, create left/right children (not thread-safe)
    void split();
    
    /// test is split is possible, then block and split
    void guardedSplit();
    
    /// compute intersections with another node, face-by-face
    void ttIntersect(const TTIntersector & other);
    
    /// serially compute intersections
    void intersect(TTIntersector & other);
    
    /// compute all intersections in parallel
    void mtIntersect(ThreadPool & pool, TTIntersector & other);
    
    /// enforce a segment manually
    void enforce(uint itri1, uint itri2,
                 const Vct3 & psrc, const Vct3 & ptrg);

    /// generate visualization for debugging
    void addLineViz(MeshFields & mvz) const;
    
    /// visualize leaf boxes for debugging
    void addBoxViz(MeshFields & mvz) const;
    
    /// set identify leafs as components (visu)
    void setComponents(Indices & idx, uint & inext) const;
    
    /// collect child intersections 
    void collect(TTIntersectionArray & isc) const;
    
  private:
    
    /// split constructor
    TTIntersector(const SharedVector<TriFace> & afaces, 
                  const Indices & idx) : triangles(afaces), ifaces(idx) 
    {
      sort(ifaces.begin(), ifaces.end());
      updateBox();              
    }
    
  private:

    /// original triangles
    SharedVector<TriFace> triangles;
    
    /// indices of triangles in this node
    Indices ifaces;
    
    /// patches present in this node
    std::vector<const MeshComponent*> patches;
    
    /// child nodes 
    TTIntersectorPtr mleft, mright;
    
    /// intersections 
    TTIntersectionArray allisec;
    
    /// bounding box of this node
    BndBox bb;
    
    /// lock the current node for write access
    Mutex guard;
    
    /// split limit 
    static uint min_node_triangles;
};

#endif
