
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
 
#include "lazyisectree.h"
#include "guige.h"

using namespace std;

// ------------------- local scope --------------------------------------

namespace detail {

class LazyIsecTreeDivider
{
public:

  LazyIsecTreeDivider(LazyIsecTree & t) : tree(t), iax(0) {}

  // node division criterion
  template <class Iterator>
  bool divide(uint inode, Iterator nbegin, Iterator nend) {
    return divideLongest(inode, nbegin, nend);
  }

  // sorting criterion : compare elements bounding box center
  bool operator() (uint a, uint b) const {
    return cmpElementCenter(a,b);
  }

private:

  // node division criterion
  template <class Iterator>
  bool divideLongest(uint inode, Iterator nbegin, Iterator nend) {
    if (nend <= nbegin)
      return false;

    // first, collect all element vertex indices
    const int nel = std::distance(nbegin, nend);
    Indices vix( 3*nel );
    uint ipos = 0;
    for (Iterator itr = nbegin; itr != nend; ++itr) {
      const uint *vi = tree.vertices(*itr);
      vix[ipos+0] = vi[0];
      vix[ipos+1] = vi[1];
      vix[ipos+2] = vi[2];
      ipos += 3;
    }
    std::sort(vix.begin(), vix.end());
    vix.erase( std::unique(vix.begin(), vix.end()), vix.end() );

    // low/high BV limits
    Vct3 p1, p2;
    p1 =   std::numeric_limits<float>::max();
    p2 = - std::numeric_limits<float>::max();

    // now, process all element vertices
    const int nvix = vix.size();
    for (int i=0; i<nvix; ++i) {
      LazyIsecTree::DopType::fit( tree.vertex(vix[i]).pointer(),
                                  p1.pointer(), p2.pointer() );
    }

    LazyIsecTree::DopType & dop( tree.dop(inode) );
    dop.setCoef(p1.pointer(), p2.pointer());
    iax = dop.longestAxis();

    // leaf nodes must be processed to generate the bounding box,
    // but they do not need to be sorted
    return ( uint(nel) > tree.minElemCount());
  }

  // compare elements by center coordinate
  bool cmpElementCenter(uint a, uint b) const {
    float ca(0.0f), cb(0.0f);
    const uint *v = tree.vertices(a);
    for (int k=0; k<3; ++k)
      ca += tree.vertex(v[k])[iax];
    v = tree.vertices(b);
    for (int k=0; k<3; ++k)
      cb += tree.vertex(v[k])[iax];
    return ca < cb;
  }

private:

  /// reference to point tree
  LazyIsecTree & tree;

  /// separating axis
  int iax;
};

// tree traversal

static void lazy_traverse(LazyIsecTree & a, LazyIsecTree & b,
                          IndexPairArray & pairs)
{
  typedef std::pair<uint,uint> NodePair;
  typedef std::vector<NodePair> NodeStack;

  if (a.empty() or b.empty())
    return;

  NodeStack stack;
  stack.push_back( make_pair(0u, 0u) );

  while (not stack.empty()) {

    const int np = stack.size();
    for (int i=0; i<np; ++i) {
      const uint anode = stack[i].first;
      if (not a.isSorted(anode))
        a.sortNode(anode);
      const uint bnode = stack[i].second;
      if (not b.isSorted(bnode))
        b.sortNode(bnode);
      if ( a.dop(anode).intersects( b.dop(bnode) ) ) {
        if ( a.leaf(anode) and b.leaf(bnode) ) {
          LazyIsecTree::testLeaves(a, anode, b, bnode, pairs);
        } else if (a.leaf(anode)) {
          stack.push_back( make_pair(anode, b.leftChild(bnode)) );
          stack.push_back( make_pair(anode, b.rightChild(bnode)) );
        } else if (b.leaf(bnode)) {
          stack.push_back( make_pair(a.leftChild(anode), bnode) );
          stack.push_back( make_pair(a.rightChild(anode), bnode) );
        } else {
          stack.push_back( make_pair(a.leftChild(anode),
                                     b.leftChild(bnode)) );
          stack.push_back( make_pair(a.leftChild(anode),
                                     b.rightChild(bnode)) );
          stack.push_back( make_pair(a.rightChild(anode),
                                     b.leftChild(bnode)) );
          stack.push_back( make_pair(a.rightChild(anode),
                                     b.rightChild(bnode)) );
        }
      }
    }

    // remove processed pairs
    stack.erase(stack.begin(), stack.begin()+np);
  }
}

static void lazy_traverse_omp(LazyIsecTree & a, LazyIsecTree & b,
                              IndexPairArray & pairs)
{
  typedef std::pair<uint,uint> NodePair;
  typedef std::vector<NodePair> NodeStack;
  typedef std::vector<uint> SortSet;

  NodeStack stack;
  SortSet asort, bsort;
  stack.push_back( make_pair(0u, 0u) );


  while (not stack.empty()) {

    // collect indices of candidate nodes which may need sorting
    const int np = stack.size();
    asort.resize(np);
    bsort.resize(np);
    for (int i=0; i<np; ++i) {
      asort[i] = stack[i].first;
      bsort[i] = stack[i].second;
    }

    // handle the special, but common, case of a == b
    if (&a == &b) {
      asort.insert(asort.end(), bsort.begin(), bsort.end());
      bsort.clear();
    }

    std::sort(asort.begin(), asort.end());
    asort.erase(  std::unique(asort.begin(), asort.end()), asort.end() );

    std::sort(bsort.begin(), bsort.end());
    bsort.erase(  std::unique(bsort.begin(), bsort.end()), bsort.end() );

    const int nsa = asort.size();
    const int nsb = bsort.size();

#pragma omp parallel
    {
      NodeStack threadStack;  // thread-private stack
      IndexPairArray threadPairs;  // thread-private intersecting pairs

      // sort candidate nodes in parallel
#pragma omp for schedule(dynamic) // nowait
      for (int i=0; i<nsa; ++i) {
        if (not a.isSorted( asort[i] ))
          a.sortNode( asort[i] );
      }

#pragma omp for schedule(dynamic)
      for (int i=0; i<nsb; ++i) {
        if (not b.isSorted(bsort[i]))
          b.sortNode( bsort[i] );
      }

#pragma omp for schedule(dynamic)
      for (int i=0; i<np; ++i) {
        const uint anode = stack[i].first;
        const uint bnode = stack[i].second;
        if ( a.dop(anode).intersects( b.dop(bnode) ) ) {
          if ( a.leaf(anode) and b.leaf(bnode) ) {
            LazyIsecTree::testLeaves(a, anode, b, bnode, threadPairs);
          } else if (a.leaf(anode)) {
            threadStack.push_back( make_pair(anode, b.leftChild(bnode)) );
            threadStack.push_back( make_pair(anode, b.rightChild(bnode)) );
          } else if (b.leaf(bnode)) {
            threadStack.push_back( make_pair(a.leftChild(anode), bnode) );
            threadStack.push_back( make_pair(a.rightChild(anode), bnode) );
          } else {
            threadStack.push_back( make_pair(a.leftChild(anode),
                                             b.leftChild(bnode)) );
            threadStack.push_back( make_pair(a.leftChild(anode),
                                             b.rightChild(bnode)) );
            threadStack.push_back( make_pair(a.rightChild(anode),
                                             b.leftChild(bnode)) );
            threadStack.push_back( make_pair(a.rightChild(anode),
                                             b.rightChild(bnode)) );
          }
        }
      } // omp for
#pragma omp critical
      {
        stack.insert(stack.end(), threadStack.begin(), threadStack.end());
        pairs.insert(pairs.end(), threadPairs.begin(), threadPairs.end());
      }
    } // omp parallel

    // remove processed pairs
    stack.erase(stack.begin(), stack.begin()+np);

  } // while
}

} //  namespace detail

// ------------------- LazyIsecTree ------------------------------------------

LazyIsecTree::LazyIsecTree(const TriMesh *msh) : m_pmsh(msh), m_mincount(8)
{
  allocate();
}

void LazyIsecTree::allocate()
{
  if (m_pmsh == 0)
    return;

  // allocate space
  const int ntri = m_pmsh->nfaces();
  if (ntri == 0)
    return;

  m_itree.init( ntri, m_mincount );
  const int nnd = m_itree.nnodes();
  m_dop.resize(nnd);
  m_nodeSorted.clear();
  m_nodeSorted.resize(nnd, false);

  // process root node
  sortNode(0);
}

void LazyIsecTree::sort()
{
  // sort and create bounding volumes
  detail::LazyIsecTreeDivider axd(*this);
  m_itree.sort(axd);
  std::fill(m_nodeSorted.begin(), m_nodeSorted.end(), true);
}

void LazyIsecTree::sortNode(uint k)
{
  detail::LazyIsecTreeDivider axd(*this);
  m_itree.sortNode(axd, k);
  m_nodeSorted[k] = true;
}

void LazyIsecTree::clear()
{
  m_itree = ImplicitTree();
  m_dop.clear();
  m_nodeSorted.clear();
}

void LazyIsecTree::intersect(LazyIsecTree &other, IndexPairArray &pairs,
                             bool parallel)
{
  if (parallel)
    detail::lazy_traverse_omp(*this, other, pairs);
  else
    detail::lazy_traverse(*this, other, pairs);
}

void LazyIsecTree::testLeaves(const LazyIsecTree & a, uint anode,
                              const LazyIsecTree & b, uint bnode,
                              IndexPairArray & isec)
{
  uint aBegin, aEnd, bBegin, bEnd;
  a.offsetRange(anode, aBegin, aEnd);
  b.offsetRange(bnode, bBegin, bEnd);

  for (uint ati=aBegin; ati != aEnd; ++ati) {
    Vct3 ap[3];
    uint ida = a.elementIndex(ati);
    const uint *va = a.vertices( ida );
    for (int k=0; k<3; ++k)
      ap[k] = Vct3( a.vertex(va[k]) );
    for (uint bti=bBegin; bti != bEnd; ++bti) {
      Vct3 bp[3];
      uint idb = b.elementIndex(bti);
      const uint *vb = b.vertices( idb );
      for (int k=0; k<3; ++k)
        bp[k] = Vct3( b.vertex(vb[k]) );
      if (moeller_intersect(ap, bp))
        isec.push_back( make_pair(ida,idb) );
    }
  }
}

bool LazyIsecTree::segment(const LazyIsecTree & other, const IndexPair & p,
                           Vct3 & src, Vct3 & trg) const
{
  Vct3 ap[3], bp[3];
  const uint *va = vertices( p.first );
  for (int k=0; k<3; ++k)
    ap[k] = Vct3( vertex(va[k]) );

  const uint *vb = other.vertices( p.second );
  for (int k=0; k<3; ++k)
    bp[k] = Vct3( other.vertex(vb[k]) );

  int r(0), coplanar(0);
  r = tri_tri_intersect_with_isectline(ap[0].pointer(), ap[1].pointer(),
                                       ap[2].pointer(), bp[0].pointer(),
                                       bp[1].pointer(), bp[2].pointer(),
                                       &coplanar, src.pointer(), trg.pointer());

  return (r != 0 and coplanar != 1);
}

bool LazyIsecTree::segments(const LazyIsecTree & other,
                            const IndexPairArray & p,
                            PointList<3> & segs) const
{
  const int np = p.size();
  segs.resize(2*np);

  //#pragma omp parallel for
  for (int i=0; i<np; ++i)
    segment(other, p[i], segs[2*i+0], segs[2*i+1]);

  return (not segs.empty());
}



