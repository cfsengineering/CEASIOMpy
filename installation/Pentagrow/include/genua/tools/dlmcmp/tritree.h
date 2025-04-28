#ifndef TRITREE_H
#define TRITREE_H

#include "lazytree.h"
#include <genua/kdop.h>
#include <genua/point.h>
#include <genua/xmlelement.h>

class LnTree;
class CgMesh;

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
  TriTree(const PointList<3,float> & vtx,
          const Indices & tri, uint leafCount=8, bool lazySort=false);

  /// copy data, build tree
  TriTree(const CgMesh & cgm, uint leafCount=8, bool lazySort=false);

  /// initialize, swap in data (destructive)
  void init(PointList<3,float> & vtx, Indices & tri, bool lazySort=false);

  /// copy geometry and initialize
  void init(const CgMesh & cgm, bool lazySort=false);

  /// merge in additional surfaces
  void merge(const CgMesh & cgm);

  /// true if no triangles present in tree
  bool empty() const {return m_tri.empty();}

  /// number of triangles
  uint ntriangles() const {return m_tri.size()/3;}

  /// access vertex indices of triangle k
  const uint *vertices(uint k) const {
    assert(3*k+2 < m_tri.size());
    return &m_tri[3*k];
  }

  /// check whether tree uses lazy sorting
  bool isLazy() const {return m_itree.isLazy();}

  /// test whether node is sorted
  bool isSorted(uint k) const {return m_itree.isSorted(k);}

  /// sort a particular node only (*not* recursively)
  void sortNode(uint k);

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
  uint leftChild(uint inode) const { return m_itree.leftChild(inode); }

  /// left child of node inode
  uint rightChild(uint inode) const { return m_itree.rightChild(inode); }

  /// minimum number of elements in node
  uint minElemCount() const {return m_mincount;}

  /// search for intersections
  void intersect(TriTree &other, IndexPairArray & pairs, bool parallel);

  /// search for intersections
  void intersect(LnTree & other, IndexPairArray & pairs, bool parallel);

  /// test triangles in nodes for intersection
  static void testLeaves(const TriTree & a, uint anode,
                         const TriTree & b, uint bnode,
                         IndexPairArray & isec);

  /// test triangles against lines
  static void testLeaves(const TriTree & a, uint anode,
                         const LnTree & b, uint bnode,
                         IndexPairArray & isec);

  /// compute intersection segment for triangle pair
  bool segment(const TriTree & other, const IndexPair & p,
               Vct3f & src, Vct3f & trg) const;

  /// compute intersection point for triangle-line pair, assuming they intersect
  float intersection(const LnTree & other, const IndexPair & p,
                     Vct3f & isp) const;

  /// determine triangle which is nearest to p
  uint nearest(const Vct3f & p) const;

  /// compute projection of pt on triangle tix
  bool project(uint tix, const Vct3f & pt, Vct3f & pj) const;

  /// remove all triangles
  void clear();

  /// create XML representation
  XmlElement toXml(bool share = false) const;

  /// recover from XML representation
  void fromXml(const XmlElement & xe);

private:

  /// allocate and sort tree
  void sort();

  /// compute distance of point from triangle tix
  float elementDistance(const Vct3f & p, uint tix) const;

private:

  /// copy of triangle vertices
  PointList<3,float> m_vtx;

  /// copy of triangles vertex indices
  Indices m_tri;

  /// balanced binary tree
  LazyTree m_itree;

  /// not empty if tree is lazily sorted, otherwise contains flag
  std::vector<bool> m_nodeSorted;

  /// bounding volumes
  std::vector<DopType> m_dop;

  /// minimum number of triangles in node
  uint m_mincount;
};

#endif // TRITREE_H
