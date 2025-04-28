#ifndef BTREEPAIR_H
#define BTREEPAIR_H

#include "btree.h"

/** Encapsulates parallel traversal of a tree pair.

  Encapsulates the traversal of a pair of trees using a visitor function
  object. The Visitor argument to descend() must support the following
  interface
  \code
  class Visitor {
    bool descend(uint anode, uint bnode);
    void process(uint anode, uint bnode);
  };
  \endcode
  where descend(anode, bnode) returns true where the tree traversal should
  continue down to the children of anode and bnode. For pairs of leaf nodes
  reached during traversal, the process() method of the visitor object is
  called.

  Both trees are traversed breadth-first, starting at the root node. The
  next deeper tree level is not touched unless the previous level is fully
  processed.

  */
class BTreePair
{
  public:

    typedef std::pair<uint, uint> NodePair;
    typedef std::vector<NodePair> NodePairStack;

    /// process pair of trees
    template <class Item, class Visitor>
    void descend(const BTree<Item> & a, const BTree<Item> & b, Visitor & v)
    {
      // initialize with root nodes
      stack.clear();
      if (v.descend(0,0))
        stack.push_back( std::make_pair(0,0) );

      // proceed until all node pairs processed
      do {

        // visit each subdivision level in sequence (top-down)
        // process each level in parallel but sync before descending
        const int n = stack.size();

#pragma omp parallel
        {
          // private stack for current thread
          NodePairStack ts;
          ts.reserve(n);

#pragma omp for
          for (int i=0; i<n; ++i) {
            uint anode = stack[i].first;
            uint bnode = stack[i].second;
            bool leaf1 = a.isleaf(anode);
            bool leaf2 = b.isleaf(bnode);
            if (leaf1 and leaf2) {
              v.process(anode, bnode);
            } else if (leaf1) {
              push(anode, 2*bnode+1, v, ts);
              push(anode, 2*bnode+2, v, ts);
            } else if (leaf2) {
              push(2*anode+1, bnode, v, ts);
              push(2*anode+2, bnode, v, ts);
            } else {
              push(2*anode+1, 2*bnode+1, v, ts);
              push(2*anode+1, 2*bnode+2, v, ts);
              push(2*anode+2, 2*bnode+1, v, ts);
              push(2*anode+2, 2*bnode+2, v, ts);
            }
          } // end for

#pragma omp critical
          stack.insert(stack.end(), ts.begin(), ts.end());

        } // end parallel

        // now that another level has been fully processed,
        // remove the processed node indices from the stack
        stack.erase(stack.begin(), stack.begin()+n);

      } while (not stack.empty());
    }

  protected:

    /// push node pair on stack if applicable
    template <class Visitor>
    void push(uint anode, uint bnode, Visitor & v, NodePairStack & ts) const {
      if (v.descend(anode, bnode))
        ts.push_back( std::make_pair(anode, bnode) );
    }

  private:

    /// stack of node pairs to visit
    NodePairStack stack;
};

#endif // BTREEPAIR_H
