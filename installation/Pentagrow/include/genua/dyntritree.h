
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
 
#ifndef GENUA_DYNTRITREE_H
#define GENUA_DYNTRITREE_H

#include "defines.h"
#include "point.h"
#include "kdop.h"
#include <boost/pool/pool.hpp>

/** Dynamic tree for 2D triangles.
  */
class DynTriTree
{
public:

  /// construct empty tree
  DynTriTree() : pvx(0), pix(0), nodePool(sizeof(DynTriTree::Node)), root(0) {}

  /// construct tree
  DynTriTree(const PointList<2> *vtx, const Indices *idx);

  /// assign vertex list and triangle indices
  void assign(const PointList<2> *vtx, const Indices *idx);

  /// rebuild tree explicitly
  void build();

  /// insert triangle k
  void insert(uint k);

  /// find triangle nearest to p
  uint nearest(const Vct2 & p) const;

  /// access vertex
  const Vct2 & vertex(uint k) const {
    assert(pvx != 0);
    assert(k < pvx->size());
    return (*pvx)[k];
  }

  /// access triangle indices
  const uint *triangle(uint k) const {
    assert(pix != 0);
    assert(3*k+2 < pix->size());
    return &((*pix)[3*k]);
  }

  /// number of triangles present
  uint ntriangles() const {
    return (pix == 0) ? 0 : pix->size()/3;
  }

  // debug
  void dbPrintTree() const {
    assert(root != 0);
    root->dbprint(0);
  }

  /// simple quality measure
  Real leafSqArea() const;

  /// release allocated memory
  void clear();

private:

  enum {maxCount = 4};

  typedef Indices::iterator idx_iterator;

  class BbcCompare {
  public:
    BbcCompare(const DynTriTree & t, uint ax) : tree(t), iax(ax) {}

    bool operator() (uint a, uint b) const {
      const uint *va = tree.triangle(a);
      const uint *vb = tree.triangle(b);
      Real amin, amax, bmin, bmax;
      amin = bmin = std::numeric_limits<Real>::max();
      amax = bmax = -amin;
      for (int i=0; i<3; ++i) {
        const Vct2 & pa( tree.vertex(va[i]) );
        const Vct2 & pb( tree.vertex(vb[i]) );
        for (int k=0; k<2; ++k) {
          amin = std::min(amin, pa[iax]);
          amax = std::max(amax, pa[iax]);
          bmin = std::min(bmin, pb[iax]);
          bmax = std::max(bmax, pb[iax]);
        }
      }
      return (amin+amax) < (bmin+bmax);
    }

    Real centerValue(uint a) const {
      const uint *va = tree.triangle(a);
      Real amin, amax;
      amin = std::numeric_limits<Real>::max();
      amax = -amin;
      for (int i=0; i<3; ++i) {
        const Vct2 & pa( tree.vertex(va[i]) );
        for (int k=0; k<2; ++k) {
          amin = std::min(amin, pa[iax]);
          amax = std::max(amax, pa[iax]);
        }
      }
      return 0.5*(amin+amax);
    }

  private:
    const DynTriTree & tree;
    uint iax;
  };

  class Node
  {
  public:

    /// default : create leaf node
    Node() : left(0), right(0), nelm(0), iax(0) {}

    /// access left child node
    Node *leftChild() const {return left;}

    /// access left child node
    Node *rightChild() const {return right;}

    /// separating axis
    uint axis() const {return iax;}

    /// test whether node is a leaf
    bool leaf() const {
      return (left == 0);
    }

    /// number of elements directly in this node
    uint size() const {return nelm;}

    /// collect element indices
    void collectElements(Indices & elix) const {
      if (left != 0) {
        left->collectElements(elix);
        right->collectElements(elix);
      } else {
        elix.insert(elix.end(), idx, idx+nelm);
      }
    }

    /// add another element, return false if split necessary
    bool append(uint k) {
      assert(leaf());
      if (nelm < DynTriTree::maxCount) {
        idx[nelm] = k;
        ++nelm;
        return true;
      } else {
        return false;
      }
    }

    /// split and insert
    void splitInsert(DynTriTree & tree, uint k);

    /// insert range and split
    template <class Iterator>
    void insert(DynTriTree & tree, Iterator begin, Iterator end)
    {
      nelm = 0;
      const int ne = std::distance(begin, end);
      if (ne > DynTriTree::maxCount) {
        Iterator mid = begin + ne/2;
        DynTriTree::BbcCompare cmp(tree, iax);
        std::nth_element(begin, mid, end, cmp);
        median = cmp.centerValue(*mid);
        if (left == 0)
          split(tree);
        left->insert(tree, begin, mid);
        right->insert(tree, mid, end);
      } else {
        left = right = 0; // drops child nodes off
        for (Iterator itr=begin; itr != end; ++itr)
          append(*itr);
      }
      updateBounds(tree);
    }

    /// where to insert triangle with bb center bb
    bool leftTriangle(const Vct2 & bb) const {
      // return 2*bb[iax] < (bvol.minCoef(iax) + bvol.maxCoef(iax));
      return bb[iax] < median;
    }

    /// just create child nodes, do nothing more
    void split(DynTriTree & tree) {
      uint ax = (iax + 1) % 2;
      left = tree.constructNode();
      left->iax = ax;
      right = tree.constructNode();
      right->iax = ax;
    }

    /// ratio of larger to smaller child bounding valumes
    Real unbalance() const {
      if (left == 0) {
        return 1.0;
      } else {
        Real sleft = left->bvol.sqsize();
        Real sright = right->bvol.sqsize();
        return std::max(sleft,sright) / std::min(sleft,sright);
      }
    }

    /// size of leaf nodes divided by node size
    Real growth() const {
      if (left == 0) {
        return 0.0;
      } else {
        return (left->bvol.sqsize() + right->bvol.sqsize()) / bvol.sqsize();
      }
    }

    /// redistribute subtree
    void rebalance(DynTriTree & tree);

    /// compute bounding volume
    bool updateBounds(const DynTriTree & tree);

    /// compute bounding DOP for element range
    template <class Iterator>
    void boundingDop(const DynTriTree & tree,
                     Iterator itbegin, Iterator itend,
                     Dop2d2<Real> & dop) const
    {
      Vct2 pmin, pmax;
      pmin = std::numeric_limits<Real>::max();
      pmax = -pmin;
      for (Iterator itr = itbegin; itr != itend; ++itr) {
        const uint *v = tree.triangle(*itr);
        for (int k=0; k<3; ++k)
          dop.fit(tree.vertex(v[k]).pointer(), pmin.pointer(), pmax.pointer());
      }
      dop.setCoef(pmin.pointer(), pmax.pointer());
    }

    /// nearest triangle search
    void nearestTriangle(const DynTriTree &tree,
                         const Vct2 &p, uint & best, Real &dmin) const;

    /// simple quality measure : sum of leaf sizes
    Real leafSqArea() const;

    // debug : print text representation, recursively
    void dbprint(uint k) const;

  private:

    /// bounding volume
    Dop2d2<Real> bvol;

    /// element indices in this node, nonempty for leaf nodes only
    uint idx[DynTriTree::maxCount];

    /// left child
    Node *left;

    /// right child
    Node *right;

    /// median value used for left/right decision
    Real median;

    /// number of elements in this node
    uint nelm;

    /// dividing direction
    uint iax;
  };

  typedef std::vector<Node*> NodeStack;

  /// allocate a leaf node
  Node *constructNode() {
    Node *pn = (Node *) nodePool.malloc();
    return (new(pn) Node());
  }

  /// compute center of the triangle bounding box
  Vct2 bbCenter(uint kt) const {
    const uint *v = triangle(kt);
    Vct2 xmin, xmax;
    xmin= std::numeric_limits<Real>::max();
    xmax = -xmin;
    for (int i=0; i<3; ++i) {
      const Vct2 & px = vertex(v[i]);
      for (int k=0; k<2; ++k) {
        xmin = std::min(xmin[k], px[k]);
        xmax = std::max(xmax[k], px[k]);
      }
    }
    return 0.5*(xmin + xmax);
  }

  /// make node pn hold all triangles in idx
  void insert(Node *pn, idx_iterator begin, idx_iterator end);

  /// compute distance of p from triangle t
  Real pdistance(const Vct2 & p, uint t) const;

private:

  /// triangle vertices
  const PointList<2> *pvx;

  /// triangle vertex indices
  const Indices *pix;

  /// allocator for nodes
  boost::pool<> nodePool;

  /// root node
  Node *root;

  /// number of triangles in tree
  uint nintree;

  /// number of triangles when tree was rebuild last
  uint nrebuild;

  friend class Node;
};

#endif // DYNTRITREE_H
