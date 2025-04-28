#ifndef LNTREE_H
#define LNTREE_H

#include "lazytree.h"
#include <genua/kdop.h>
#include <genua/point.h>

class TriTree;

class LnTree
{
public:

  typedef Dop3d3<float> DopType;

  /// empty tree
  LnTree() : m_mincount(16) {}

  /// copy data, build tree
  LnTree(const PointList<3,float> & vtx, bool lazy=false);

  /// true if no lines present in tree
  bool empty() const {return m_vtx.empty();}

  /// initialize, swap in data (destructive)
  void init(PointList<3,float> & vtx, bool lazy=false);

  /// number of triangles
  uint nlines() const {return m_vtx.size()/2;}

  /// check whether tree is sorted lazily
  bool isLazy() const {return m_itree.isLazy();}

  /// check whether node k is sorted
  bool isSorted(uint k) const {return m_itree.isSorted(k);}

  /// sort node k only (call to create lazily evaluated tree)
  void sortNode(uint k);

  /// access vertices of line k
  void vertices(uint k, Vct3f & p1, Vct3f & p2) const {
    assert(2*k+1 < m_vtx.size());
    p1 = m_vtx[2*k+0];
    p2 = m_vtx[2*k+1];
  }

  /// source vertex of line k
  const Vct3f & source(uint k) const {return m_vtx[2*k+0];}

  /// target vertex of line k
  const Vct3f & target(uint k) const {return m_vtx[2*k+1];}

  /// number of vertices stored
  uint nvertices() const {return m_vtx.size();}

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

  /// first index of node k
  uint begin(uint k) const {return m_itree.begin(k);}

  /// last+1 index of node k
  uint end(uint k) const {return m_itree.end(k);}

  /// access index offset range for node k
  void offsetRange(uint k, uint & beg, uint & end) const {
    m_itree.offsetRange(k, beg, end);
  }

  /// test whether node inode is a leaf node
  bool leaf(uint inode) const {
    return m_itree.rightChild(inode) >= m_dop.size();
  }

  /// left child of node inode
  uint leftChild(uint inode) const {return m_itree.leftChild(inode);}

  /// left child of node inode
  uint rightChild(uint inode) const {return m_itree.rightChild(inode);}

  /// minimum number of elements in node
  uint minElemCount() const {return m_mincount;}

private:

  /// allocate and sort tree
  void sort();

private:

  /// copy of line vertices
  PointList<3,float> m_vtx;

  /// balanced binary tree
  LazyTree m_itree;

  /// bounding volumes
  std::vector<DopType> m_dop;

  /// minimum number of triangles in node
  uint m_mincount;

};
#endif // LNTREE_H
