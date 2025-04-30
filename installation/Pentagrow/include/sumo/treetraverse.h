
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
 
#ifndef TREETRAVERSE_H
#define TREETRAVERSE_H

#include <genua/defines.h>
#include <vector>
#include <utility>

// Internally used template function which generalizes parallel traversal of
// a pair of binary trees. This is a typical operation in intersection
// computations and collision detection.

namespace detail {

typedef std::pair<uint,uint> IndexPair;
typedef std::vector<IndexPair> IndexPairArray;

template <class ATree, class BTree>
void serial_traverse(const ATree & a, const BTree & b, IndexPairArray & pairs)
{
  typedef std::pair<uint,uint> NodePair;
  typedef std::vector<NodePair> NodeStack;

  NodeStack stack;
  stack.push_back( std::make_pair(0u, 0u) );

  while (not stack.empty()) {

    const int np = stack.size();
    for (int i=0; i<np; ++i) {
      const uint anode = stack[i].first;
      const uint bnode = stack[i].second;
      if ( a.dop(anode).intersects( b.dop(bnode) ) ) {
        if ( a.leaf(anode) and b.leaf(bnode) ) {
          ATree::testLeaves(a, anode, b, bnode, pairs);
        } else if (a.leaf(anode)) {
          stack.push_back( std::make_pair(anode, b.leftChild(bnode)) );
          stack.push_back( std::make_pair(anode, b.rightChild(bnode)) );
        } else if (b.leaf(bnode)) {
          stack.push_back( std::make_pair(a.leftChild(anode), bnode) );
          stack.push_back( std::make_pair(a.rightChild(anode), bnode) );
        } else {
          stack.push_back( std::make_pair(a.leftChild(anode),
                                     b.leftChild(bnode)) );
          stack.push_back( std::make_pair(a.leftChild(anode),
                                     b.rightChild(bnode)) );
          stack.push_back( std::make_pair(a.rightChild(anode),
                                     b.leftChild(bnode)) );
          stack.push_back( std::make_pair(a.rightChild(anode),
                                     b.rightChild(bnode)) );
        }
      }
    }

    // remove processed pairs
    stack.erase(stack.begin(), stack.begin()+np);
  }
}

template <class ATree, class BTree>
void parallel_traverse(const ATree & a, const BTree & b, IndexPairArray & pairs)
{
  typedef std::pair<uint,uint> NodePair;
  typedef std::vector<NodePair> NodeStack;

  NodeStack stack;
  stack.push_back( std::make_pair(0u, 0u) );

  // This profits substantially from using far more threads
  // than cores, set thread count explicitly

  while (not stack.empty()) {

    const int np = stack.size();

#pragma omp parallel
    {
      NodeStack threadStack;  // thread-private stack
      IndexPairArray threadPairs;  // thread-private intersecting pairs

#pragma omp for schedule(dynamic)
      for (int i=0; i<np; ++i) {
        const uint anode = stack[i].first;
        const uint bnode = stack[i].second;
        if ( a.dop(anode).intersects( b.dop(bnode) ) ) {
          if ( a.leaf(anode) and b.leaf(bnode) ) {
            ATree::testLeaves(a, anode, b, bnode, threadPairs);
          } else if (a.leaf(anode)) {
            threadStack.push_back( std::make_pair(anode, b.leftChild(bnode)) );
            threadStack.push_back( std::make_pair(anode, b.rightChild(bnode)) );
          } else if (b.leaf(bnode)) {
            threadStack.push_back( std::make_pair(a.leftChild(anode), bnode) );
            threadStack.push_back( std::make_pair(a.rightChild(anode), bnode) );
          } else {
            threadStack.push_back( std::make_pair(a.leftChild(anode),
                                             b.leftChild(bnode)) );
            threadStack.push_back( std::make_pair(a.leftChild(anode),
                                             b.rightChild(bnode)) );
            threadStack.push_back( std::make_pair(a.rightChild(anode),
                                             b.leftChild(bnode)) );
            threadStack.push_back( std::make_pair(a.rightChild(anode),
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

} // namespace detail

#endif // TREETRAVERSE_H
