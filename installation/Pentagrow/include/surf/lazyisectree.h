
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
 
#ifndef SURF_LAZYISECTREE_H
#define SURF_LAZYISECTREE_H

#include "forward.h"
#include <genua/point.h>
#include <genua/kdop.h>
#include <genua/synchron.h>
#include <genua/implicittree.h>
#include <genua/trimesh.h>

/** Lazily constructed triangle tree.
 *
 * This binary tree for triangles is a bounding volume hierarchy which is
 * constructed during the top-down traversal performed for intersection
 * checking.
 *
 * \ingroup geometry
 * \sa ImplicitTree, Dop3d3
 */
class LazyIsecTree
{
public:

  typedef Dop3d3<Real> DopType;

  /// empty tree
  LazyIsecTree() : m_pmsh(0), m_mincount(8) {}

  /// copy data, build tree
  LazyIsecTree(const TriMesh *msh);

  /// true if no triangles present in tree
  bool empty() const {return (m_pmsh == 0) or (m_pmsh->nfaces() == 0);}

  /// number of triangles
  uint ntriangles() const {return m_pmsh != 0 ? m_pmsh->nfaces() : 0;}

  /// access vertex indices of triangle k
  const uint *vertices(uint k) const {
    assert(m_pmsh != 0 and k < m_pmsh->nfaces());
    return m_pmsh->face(k).vertices();
  }

  /// number of vertices stored
  uint nvertices() const {
    return (m_pmsh != 0) ? m_pmsh->nvertices() : 0;
  }

  /// access vertex k
  const Vct3 & vertex(uint k) const {
    assert(m_pmsh != 0);
    return m_pmsh->vertex(k);
  }

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

  /// check whether node k is already sorted
  bool isSorted(uint k) const {
    assert(k < m_nodeSorted.size());
    return m_nodeSorted[k];
  }

  /// sort just one node
  void sortNode(uint k);

  /// search for intersections
  void intersect(LazyIsecTree &other, IndexPairArray & pairs, bool parallel);

  /// test triangles in nodes for intersection
  static void testLeaves(const LazyIsecTree & a, uint anode,
                         const LazyIsecTree & b, uint bnode,
                         IndexPairArray & isec);

  /// compute intersection segment for triangle pair
  bool segment(const LazyIsecTree & other, const IndexPair & p,
               Vct3 & src, Vct3 & trg) const;

  /// compute all intersection segments
  bool segments(const LazyIsecTree & other,
                const IndexPairArray & p,
                PointList<3> & segs) const;

  /// remove all triangles
  void clear();

private:

  /// allocate space for nodes
  void allocate();

  /// allocate and sort entire tree
  void sort();

private:

  /// mesh to which this tree is attached
  const TriMesh *m_pmsh;

  /// balanced binary tree
  ImplicitTree m_itree;

  /// bounding volumes
  std::vector<DopType> m_dop;

  /// flag which indicates whether a node is already sorted or not
  std::vector<bool> m_nodeSorted;

  /// minimum number of triangles in node
  uint m_mincount;
};

#endif // LAZYISECTREE_H
