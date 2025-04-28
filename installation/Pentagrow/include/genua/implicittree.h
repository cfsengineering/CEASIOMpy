
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

#ifndef GENUA_IMPLICITTREE_H
#define GENUA_IMPLICITTREE_H

#include "forward.h"
#include "bitfiddle.h"
#include "xmlelement.h"
#include <limits>
#include <cassert>
#include <vector>
#include <algorithm>
// #include <parallel/algorithm> // gcc > 4.3 only

#ifdef HAVE_TBB
#include <boost/config.hpp>
#include <tbb/parallel_invoke.h>
#endif

/** Balanced binary tree using implicit references to content.

ImplicitTree is a fully balanced binary tree which does not store nor define
tree nodes. It is therefore suitable for very deep trees since the memory
requirements increase only with the number of items to be represented, and
not with the depth of the tree. Only a single memory allocation is performed
in init().

The tree object does not store copies or references to the items contained in
it, but only an array of item indices. It does not support insertion or removal
of items. Items are accessed using the comparison object passed to sort().

The tree is partitioned using std::nth_element() using a user-supplied comparison
functor, which implements a call operator taking unsigned integer values. As
the comparison functor needs to be copied for each call of nth_element,
it should not be too large. Before sorting, the method
\verbatim
  bool divide(begin, end);
\endverbatim
of the comparison object is called in order to
- establish whether the range (begin, end) should be sorted at all;
- let the functor compute a partitioning/sorting criterion.

In parallel mode, (TBB or OpenMP), each thread will use a private copy of the
comparison object, which means that it cannot contain data which needs to be
shared between calls on different nodes.

\b Note: The comparison object must handle the case where the item index passed
to divide() or operator() evaluates to the constant NotFound, since that value
might be present in nodes which are not fully populated.

\ingroup geometry
\sa NDPointTree, MxElementTree
  */
class ImplicitTree
{
public:

  typedef std::vector<uint>     ItemArray;
  typedef ItemArray::const_iterator  ConstIterator;
  typedef ItemArray::iterator        Iterator;

  /// create initial tree for n items
  ImplicitTree(uint n = 0, uint mincount=1) : parthreshold(4096) {
    init(n, mincount);
  }

  /// initialize tree for n items
  void init(uint n, uint mincount=1) {
    minsize = (mincount > 1) ? nextpow2(mincount) : 1;
    while (minsize > n and minsize > 1)
      minsize /= 2;
    assert(minsize > 0);
    nitem = n;
    ntop = nextpow2(n);
    items.resize(n);
    for (uint i=0; i<n; ++i)
      items[i] = i;
    nnds = (ntop > 0) ? (2*nextpow2(ntop / minsize) - 1) : 0;

    irange = Indices(2*nnds, NotFound);
  }

  /// change threshold node size for switching down to serial sort
  void parallelThreshold(uint n) {
    parthreshold = std::max( n, 2*minsize );
  }

  /// number of valid item indices
  uint size() const {return items.size();}

  /// number of nodes in this tree
  uint nnodes() const {return nnds;}

  /// minimum number of items in node
  uint minSize() const {return minsize;}

  /// compute parent index
  uint parent(uint k) const {
    return (k != 0) ? ((k - 1) >> 1) : 0;
  }

  /// left child node index
  uint leftChild(uint k) const {return (k << 1) + 1;}

  /// left child node index
  uint rightChild(uint k) const {return (k << 1) + 2;}

  /// compute depth level of node k
  uint level(uint k) const {
    return floorlog2(k + 1);
  }

  /// access index
  uint index(uint k) const {
    assert(k < items.size());
    return items[k];
  }

  /// first index of node k
  uint begin(uint k) const {return irange[2*k+0];}

  /// last+1 index of node k
  uint end(uint k) const {return irange[2*k+1];}

  /// access ranges
  const Indices &indexRanges() const {return irange;}

  /// return node size
  uint size(uint k) const {return (end(k) - begin(k));}

  // deprecated, recursive version of offsetRange, relies on NotFound sorted back
  bool roffsetRange(uint k, uint & ibegin, uint & iend) const {
    if (k == 0) {
      ibegin = 0;
      iend = nitem;
      return true;
    }

    uint t1, t2;
    offsetRange(parent(k), t1, t2);
    uint imid = (t1 + t2) / 2;

    if (k & 0x1) {
      ibegin = t1;
      iend = imid;
    } else {
      ibegin = imid;
      iend = t2;
    }

    if (ibegin > iend)
      iend = ibegin;

    return (ibegin != iend);
  }

  /// extract range of valid indices, relies on NotFound sorted back
  bool offsetRange(uint k, uint & ibegin, uint & iend) const {

    uint64_t oddbits = (k & 0x1);
    uint j(k), depth(0);
    while (j > 0) {
      uint parent = ((j != 0) ? ((j - 1) >> 1) : 0);
      oddbits = ((oddbits << 1) | (parent & 0x1));
      j = parent;
      ++depth;
    }

    uint tbeg(0), tend(nitem);
    for (uint i=0; i<depth; ++i) {
      uint tmid = (tbeg + tend) / 2;
      oddbits >>= 1;
      if ( oddbits & 0x1 )
        tend = tmid;
      else
        tbeg = tmid;
    }
    ibegin = tbeg;
    iend = tend;

    // below : will not distribute remainder, results in large block

    // compute depth
    // uint depth = floorlog2( k + 1 );

    //          0              : 0              n  : d = 0
    //     1          2        : 0     n/2      n  : d = 1
    //   3   4     5     6     : 0 n/4 n/2 3n/4 n  : d = 2
    //  7 8 9 10 11 12 13 14   : ... n/8           : d = 3
    //
    // first index at depth d is (1 << d) - 1
    // bucket width at d is n/(1 << d) == n >> d

    //    uint first = (1 << depth) - 1;
    //    uint idx = k - first;
    //    uint wid = (nitem >> depth);
    //    ibegin = idx * wid;
    //    iend = (k < 2*first) ? (ibegin + wid) : nitem;

    return (ibegin != iend);
  }

  /// sort entire tree
  template <class Comparison>
  void sort(Comparison cmp, bool inparallel=true) {
    if (items.empty())
      return;
    if (inparallel) {
#ifdef HAVE_TBB
      tbb::task_group_context ctx;
      tbbsort(cmp, 0, ctx);
#elif !defined(HAVE_NO_OPENMP)
      ompsort(cmp);
#else
      itersort(cmp, 0);
#endif
    } else {
      itersort(cmp, 0);
    }
  }

  /// create XML representation
  XmlElement toXml(bool share = false) const;

  /// retrieve from XML representation
  void fromXml(const XmlElement & xe);

  /// sort node with index k
  template <class Comparison>
  void sortNode(Comparison &cmp, uint k)
  {
    // determine node size
    uint ibegin(0), iend(nitem);
    if (k > 0) {
      uint ipre = this->parent(k);
      uint pbegin = this->begin(ipre);
      uint pend = this->end(ipre);
      if (k & 0x1) {
        ibegin = pbegin;
        iend = (pbegin + pend) / 2;
      } else {
        ibegin = (pbegin + pend) / 2;
        iend = pend;
      }
    }
    irange[2*k+0] = ibegin;
    irange[2*k+1] = iend;

    // no need to partition nodes with less than 2 items
    if ((iend - ibegin) < 2)
      return;

    ItemArray::iterator nbegin = items.begin() + ibegin;
    ItemArray::iterator nend = items.begin() + iend;
    if ( cmp.divide(k, nbegin, nend) ) {
      ItemArray::iterator nmid = items.begin() + (ibegin+iend)/2;
      std::nth_element( nbegin, nmid, nend, cmp );
    }
  }

  /// determine memory footprint
  float megabyte() const;

protected:

  /// serial stack-based sort
  template <class Comparison>
  void itersort(Comparison cmp, uint inode) {
    std::vector<uint> cstack;
    uint inisize = std::max(8u, (nnds + 1) / (inode+1));
    cstack.reserve( inisize );
    cstack.push_back(inode);
    while (not cstack.empty()) {
      uint jnode = cstack.back();
      cstack.pop_back();
      sortNode(cmp, jnode);
      if ( leftChild(jnode) < nnodes() ) {
        cstack.push_back( leftChild(jnode) );
        cstack.push_back( rightChild(jnode) );
      }
    }
  }

#ifdef HAVE_TBB

  template <class Comparison>
  void tbbsort(Comparison cmp, uint inode, tbb::task_group_context &ctx) {
    if (inode < nnodes()) {
      sortNode(cmp, inode);
      const uint leftNode = leftChild(inode);
      const uint rightNode = rightChild(inode);
      if (this->size(inode) > parthreshold) {
        auto leftTask = [&]() {
          Comparison cpriv(cmp);
          this->tbbsort(cpriv, leftNode, ctx);
        };
        auto rightTask = [&]() {
          Comparison cpriv(cmp);
          this->tbbsort(cpriv, rightNode, ctx);
        };
        tbb::parallel_invoke(leftTask, rightTask, ctx);
      } else {
        if (leftNode < nnodes())
          itersort(cmp, leftNode);
        if (rightNode < nnodes())
          itersort(cmp, rightNode);
      }
    }
  }

#endif // HAVE_TBB

#if !defined(HAVE_NO_OPENMP)

  /// sort entire tree
  template <class Comparison>
  void ompsort(Comparison cmp) {
    if (items.empty())
      return;

    // process root node
    ItemArray::iterator begin = items.begin();
    ItemArray::iterator end = items.begin() + nitem;
    ItemArray::iterator mid = items.begin() + (nitem/2);
    cmp.divide(0, begin, end);  // TODO : parallelize
    std::nth_element(begin, mid, end, cmp);
    //__gnu_parallel::nth_element(begin, mid, end, cmp);

    // root node dimension
    irange[0] = 0;
    irange[1] = nitem;

    int npass = ceillog2(nnodes());
#pragma omp parallel
    {
      // thread-private copy of the comparison object
      Comparison tcp(cmp);

      for (int i=1; i<npass; ++i) {
        int nbegin = (1 << i) - 1;
        int nend = 2*nbegin + 1;
#pragma omp for schedule(dynamic)
        for (int j=nbegin; j<nend; ++j) {
          sortNode(tcp, j);
        }
      }
    }
  }

#endif


protected:

  /// sorted index set
  ItemArray items;

  /// begin and end indices for each node
  Indices irange;

  /// number of items stored
  uint nitem, ntop, nnds;

  /// minimum number of items in node
  uint minsize;

  /// parallelization threshold
  uint parthreshold;
};

#endif // IMPLICITTREE_H
