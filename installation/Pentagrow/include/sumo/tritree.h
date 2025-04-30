
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
 
#ifndef TRITREE_H
#define TRITREE_H

#include <genua/implicittree.h>
#include <genua/kdop.h>
#include <genua/point.h>
#include <genua/smatrix.h>

class CgMesh;

/** Bounding volume hierarchy for triangles.

  TriTree is a balanced binary tree implementing a bounding volume hierarchy
  for triangles. It supports parallel construction and intersection testing
  where OpenMP is supported.

  Bounding volumes are plain axis-aligned boxes in the present implementation,
  but can be changed to any three-dimensional k-DOP implemented by libgenua
  (see genua/kdop.h). DopType in LnTree must be changed accordingly to retain
  compatibility.

  Tree construction is relatively simple and fairly fast. Should the current
  implementation show insufficient intersection testing performance, more
  advanced tree construction method may be preferable.

  Axis-aligned boxes split by their longest axis can be inefficient
  bounding volumes when many triangles are very strongly stretched. The optimal
  solution to this problem would be to test different split directions for their
  efficiency before selection, possibly in combination with more DOP axes.
  Furthermore, sorting triangles into child nodes by comparing their center
  coordinate need not be optimal either.

  Since an exhaustive search for the optimal split direction of each node is
  rather expensive, the current implementation decides on the split direction
  by looking at the bounding box of triangle centers. This occurs some
  additional computational effort, but improves tge tree quality in terms of
  child node sepration substantially for low-quality tesselation containing
  triangles with extremely high aspect ratio.
*/
class TriTree
{
public:

  typedef Dop3d3<float> DopType;
  typedef std::pair<uint,uint> IndexPair;
  typedef std::vector<IndexPair> IndexPairArray;

  /// Use with std::sort to sort index pairs by first index
  struct CompareFirst {
    bool operator() (const IndexPair & a, const IndexPair & b) const {
      return a.first < b.first;
    }
  };

  /// Use with std::sort to sort index pairs by second index
  struct CompareSecond {
    bool operator() (const IndexPair & a, const IndexPair & b) const {
      return a.second < b.second;
    }
  };

  /// empty tree
  TriTree() : m_mincount(16) {}

  /// copy data, build tree
  TriTree(const PointList<3,float> & vtx, const Indices & tri);

  /// copy data, build tree
  TriTree(const CgMesh & cgm);

  /// initialize, swap in data (destructive)
  void init(PointList<3,float> & vtx, Indices & tri);

  /// merge in additional surfaces
  void merge(const CgMesh & cgm);

  /// merge in additional surfaces
  void merge(const CgMesh & cgm, const Mtx44f & tfm);

  /// true if no triangles present in tree
  bool empty() const {return m_tri.empty();}

  /// number of triangles
  uint ntriangles() const {return m_tri.size()/3;}

  /// access vertex indices of triangle k
  const uint *vertices(uint k) const {
    assert(3*k+2 < m_tri.size());
    return &m_tri[3*k];
  }

  /// number of vertices stored
  uint nvertices() const {return m_vtx.size();}

  /// access vertex k
  const Vct3f & vertex(uint k) const {return m_vtx[k];}

  /// access bounding volume for a single node
  DopType & dop(uint k) {
    assert(k < m_dop.size());
    return m_dop[k];
  }

  /// access bounding volume for a single node
  const DopType & dop(uint k) const {
    assert(k < m_dop.size());
    return m_dop[k];
  }

  /// element index from node position
  uint elementIndex(uint k) const {return m_itree.index(k);}

  /// access index offset range for node k
  void offsetRange(uint k, uint & beg, uint & end) const {
    m_itree.offsetRange(k, beg, end);
  }

  /// test whether node inode is a leaf node
  bool leaf(uint inode) const {
    return m_itree.rightChild(inode) >= m_dop.size();
  }

  /// left child of node inode
  uint leftChild(uint inode) const { return m_itree.leftChild(inode); }

  /// left child of node inode
  uint rightChild(uint inode) const { return m_itree.rightChild(inode); }

  /// minimum number of elements in node
  uint minElemCount() const {return m_mincount;}

  /// search for intersections
  void intersect(const TriTree & other, IndexPairArray & pairs,
                 bool parallel) const;

  /// test triangles in nodes for intersection
  static void testLeaves(const TriTree & a, uint anode,
                         const TriTree & b, uint bnode,
                         IndexPairArray & isec);

  /// compute intersection segment for triangle pair
  bool segment(const TriTree & other, const IndexPair & p,
               Vct3f & src, Vct3f & trg) const;

  /// compute all intersection segments
  bool segments(const TriTree & other, const IndexPairArray & p,
                PointList<3,float> & segs) const;

  /// remove all triangles
  void clear();

private:

  /// allocate and sort tree
  void sort();

private:

  /// copy of triangle vertices
  PointList<3,float> m_vtx;

  /// copy of triangles vertex indices
  Indices m_tri;

  /// balanced binary tree
  ImplicitTree m_itree;

  /// bounding volumes
  std::vector<DopType> m_dop;

  /// minimum number of triangles in node
  uint m_mincount;
};

#endif // TRITREE_H
