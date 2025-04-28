#ifndef LAZYTREE_H
#define LAZYTREE_H

#include <genua/implicittree.h>
#include <genua/xmlelement.h>

/** A wrapper for ImplicitTree to simplify lazy sorting.
 *
 *
 * \sa ImplicitTree
 */
class LazyTree
{
public:

  /// create initial tree for n items
  LazyTree(uint n = 0, uint mincount=1) : m_nnodes(0), m_nsorted(0) {
    init(n, mincount);
  }

  /// initialize tree for n items
  void init(uint n, uint mincount=1) {
    m_itree.init(n, mincount);
    m_nnodes = m_itree.nnodes();
  }

  /// number of valid item indices
  uint size() const {return m_itree.size();}

  /// first index of node k
  uint begin(uint k) const {return m_itree.begin(k);}

  /// last+1 index of node k
  uint end(uint k) const {return m_itree.end(k);}

  /// number of nodes in this tree
  uint nnodes() const {return m_nnodes;}

  /// minimum number of items in node
  uint minSize() const {return m_itree.minSize();}

  /// compute parent index
  uint parent(uint k) const {return m_itree.parent(k);}

  /// left child node index
  uint leftChild(uint k) const {return m_itree.leftChild(k);}

  /// left child node index
  uint rightChild(uint k) const {return m_itree.rightChild(k);}

  /// compute depth level of node k
  uint level(uint k) const {return m_itree.level(k);}

  /// access index
  uint index(uint k) const {return m_itree.index(k);}

  /// extract range of valid indices, relies on NotFound sorted back
  bool offsetRange(uint k, uint & ibegin, uint & iend) const {
    // return m_itree.offsetRange(k, ibegin, iend);
    ibegin = m_itree.begin(k);
    iend = m_itree.end(k);
    return ibegin != iend;
  }

  /// check whether lazy sorting is used
  bool isLazy() const {return (m_nsorted < m_nnodes);}

  /// check if node k is sorted
  bool isSorted(uint k) const {
    return (m_sortedflag.empty() or m_sortedflag[k]);
  }

  /// sort a single node
  template <class Comparison>
  void sortNode(Comparison & cmp, uint k) {
    if (k == 0)
      m_sortedflag = std::vector<bool>( m_itree.nnodes(), false );
    assert((k == 0) or isSorted(parent(k)));
    m_itree.sortNode(cmp, k);
    m_sortedflag[k] = true;
#pragma omp atomic
    ++m_nsorted;
  }

  /// sort entire tree, mark all nodes sorted
  template <class Comparison>
  void sort(Comparison cmp) {
    m_itree.sort(cmp);
    m_sortedflag.clear();
    m_nsorted = m_nnodes;
  }

protected:

  /// balanced binary tree, stored contiguously
  ImplicitTree m_itree;

  /// flag indicating whether a node is sorted or not
  std::vector<bool> m_sortedflag;

  /// (cached) number of nodes
  uint m_nnodes;

  /// number of sorted nodes
  uint m_nsorted;
};

#endif // LAZYTREE_H
