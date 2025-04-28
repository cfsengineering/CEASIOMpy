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
void serial_traverse_sorted(const ATree & a, const BTree & b, IndexPairArray & pairs)
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

template <class ATree>
inline void enqueue_children(const ATree &atree, uint anode,
                             std::vector<uint> &asl)
{
  uint aleft = atree.leftChild(anode);
  if ( not atree.isSorted(aleft) )
    asl.push_back(aleft);
  uint aright = atree.rightChild(anode);
  if ( not atree.isSorted(aright) )
    asl.push_back(aright);
}

template <class ATree>
inline void sort_children(ATree &atree, uint anode)
{
  uint aleft = atree.leftChild(anode);
  if ( not atree.isSorted(aleft) )
    atree.sortNode(aleft);
  uint aright = atree.rightChild(anode);
  if ( not atree.isSorted(aright) )
    atree.sortNode(aright);
}

template <class ATree, class BTree>
void serial_traverse_lazy(ATree & a, BTree & b, IndexPairArray & pairs)
{
  typedef std::pair<uint,uint> NodePair;
  typedef std::vector<NodePair> NodeStack;

  std::vector<uint> aSortQueue, bSortQueue;

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
          enqueue_children(b, bnode, bSortQueue);
        } else if (b.leaf(bnode)) {
          stack.push_back( std::make_pair(a.leftChild(anode), bnode) );
          stack.push_back( std::make_pair(a.rightChild(anode), bnode) );
          enqueue_children(a, anode, aSortQueue);
        } else {
          stack.push_back( std::make_pair(a.leftChild(anode),
                                     b.leftChild(bnode)) );
          stack.push_back( std::make_pair(a.leftChild(anode),
                                     b.rightChild(bnode)) );
          stack.push_back( std::make_pair(a.rightChild(anode),
                                     b.leftChild(bnode)) );
          stack.push_back( std::make_pair(a.rightChild(anode),
                                     b.rightChild(bnode)) );
          enqueue_children(a, anode, aSortQueue);
          enqueue_children(b, bnode, bSortQueue);
        }
      }
    }

    // remove processed pairs
    stack.erase(stack.begin(), stack.begin()+np);

    // sort nodes in next level
    const int nsa = aSortQueue.size();
    for (int i=0; i<nsa; ++i)
      a.sortNode(aSortQueue[i]);
    const int nsb = bSortQueue.size();
    for (int i=0; i<nsb; ++i)
      b.sortNode(bSortQueue[i]);

    aSortQueue.clear();
    bSortQueue.clear();
  }
}

template <class ATree, class BTree>
void serial_traverse(ATree & a, BTree & b, IndexPairArray & pairs)
{
  if (a.isLazy() or b.isLazy())
    serial_traverse_lazy(a, b, pairs);
  else
    serial_traverse_sorted(a, b, pairs);
}

template <class ATree, class BTree>
void parallel_traverse_sorted(const ATree & a, const BTree & b,
                              IndexPairArray & pairs)
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

template <class ATree, class BTree>
void parallel_traverse_lazy(ATree & a, BTree & b, IndexPairArray & pairs)
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
            sort_children(b, bnode);
          } else if (b.leaf(bnode)) {
            threadStack.push_back( std::make_pair(a.leftChild(anode), bnode) );
            threadStack.push_back( std::make_pair(a.rightChild(anode), bnode) );
            sort_children(a, anode);
          } else {
            threadStack.push_back( std::make_pair(a.leftChild(anode),
                                             b.leftChild(bnode)) );
            threadStack.push_back( std::make_pair(a.leftChild(anode),
                                             b.rightChild(bnode)) );
            threadStack.push_back( std::make_pair(a.rightChild(anode),
                                             b.leftChild(bnode)) );
            threadStack.push_back( std::make_pair(a.rightChild(anode),
                                             b.rightChild(bnode)) );
            sort_children(a, anode);
            sort_children(b, bnode);
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

template <class ATree, class BTree>
void parallel_traverse(ATree & a, BTree & b, IndexPairArray & pairs)
{
  if (a.isLazy() or b.isLazy())
    parallel_traverse_lazy(a, b, pairs);
  else
    parallel_traverse_sorted(a, b, pairs);
}

} // namespace detail

#endif // TREETRAVERSE_H
