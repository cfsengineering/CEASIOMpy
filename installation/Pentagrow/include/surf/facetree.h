
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
 
#ifndef SURF_FACETREE_H
#define SURF_FACETREE_H

#include <genua/sharedvector.h>
#include <genua/trimesh.h>
#include <genua/bounds.h>
#include <genua/plane.h>
#include "edgefaceisec.h"


/** Binary tree for triangles.

  A search data structure used to efficiently locate intersecting pairs of
  triangles. The bounding volume used is an axis-aligned bounding box, and
  the tree split operator divides the set of triangles along the estimated
  principal axis of the contained set of vertices. This is a relatively simple
  implementation which yields fairly well-balanced trees for reasonably shaped
  triangles. The split operator will fail to produce well-separated child
  trees for very strongly stretched triangles.

  \ingroup geometry
  \sa Intersector
  */
class FaceTree
{
public:

  /// Intersection between triangle and plane
  class Segment {
  public:

    /// return whether face intersects plane
    bool intersects(const TriFace & f, const Plane & pln) {
      return f.intersect(pln, src, trg);
    }

    /// compute projection of point on segment
    Vct3 projection(const Vct3 & pt) const {
      Vct3 d(trg - src);
      Real t = dot( pt-src, d ) / dot(d, d);
      if (t <= 0.0)
        return src;
      else if (t >= 1.0)
        return trg;
      else
        return (src + t*d);
    }

  public:

    /// intersection points
    Vct3 src, trg;

    /// tag associated with the face
    int iface;
  };

public:

  typedef SharedVector<TriFace> FaceArray;
  typedef boost::shared_ptr<FaceTree> FaceTreePtr;
  typedef std::vector<FaceTree::Segment> SegmentArray;

  /// empty constructor
  FaceTree() : srf(0), level(0) {}

  /// root node constructor
  FaceTree(const TriMesh & t);

  /// check if this is a leaf node
  bool isLeaf() const {return (lft == 0) and (rgt == 0);}

  /// access left sibling
  const FaceTree & left() const {return *lft;}

  /// access right sibling
  const FaceTree & right() const {return *rgt;}

  /// count faces belonging to this tree
  uint nfaces() const {return idx.size();}

  /// access face
  const TriFace & face(uint i) const {
    assert(i < idx.size());
    return faces[idx[i]];
  }

  /// access edge
  const TriEdge & edge(uint i) const {return srf->edge(i);}

  /// split recursively
  void split(uint depth, uint npmin);

  /// check bounding box intersection
  bool bbintersects(const FaceTree & other) const {
    return bb.intersects(other.bb);
  }

  /// determine face-edge intersections
  uint intersect(const FaceTree & other, FaceIsecMap & m) const;

  /// determine the number of self-intersections
  uint selfIntersect(FaceIsecMap & m) const;

  /// collect edge indices
  void collectEdges(Indices & eix) const;

  /// collect faces intersected by plane pln
  void intersectPlane(const Plane & pln, Indices & ifaces) const;

  /// collect intersection segments with plane pln
  void intersectPlane(const Plane & pln, SegmentArray & segments) const;

private:

  /// childnode constructor
  FaceTree(const FaceArray & fcs, const Indices & ix, uint lv);

  /// initialize geometric properties
  void init();

  /// create child nodes
  void fork();

  /// check if face belongs to the left child node
  bool isLeft(const TriFace & f) const;

private:

  /// children
  FaceTreePtr lft, rgt;

  /// shared array of faces, data stored in/owned by root node
  FaceArray faces;

  /// indices for this node
  Indices idx;

  /// associated mesh
  const TriMesh *srf;

  /// center and principal direction
  Vct3 ctr, pcp;

  /// bounding box
  BndBox bb;

  /// tree depth
  uint level;
};

#endif

