/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       btreenode.h
 * copyright:  (c) 2009 by david.eller@gmx.net
 * ------------------------------------------------------------------------
 * Node in balanced binary tree
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#ifndef GENUA_BTREENODE_H
#define GENUA_BTREENODE_H

#include <algorithm>

// use parallel libstdc++ if available, but not with icc
// #if !__ICC && (__GNUC__ >= 4 && __GNUC_MINOR__ >= 3 && _OPENMP)
//   #include <parallel/algorithm>
//   #define parallel_nth_element    __gnu_parallel::nth_element
// #else
//   #define parallel_nth_element    std::nth_element
// #endif

#define parallel_nth_element    std::nth_element

/** Node of a balanced binary tree.
  
  Intended to be used for trees where the nodes do not perform
  their own memory management, but share data located in contiguous storage
  within the root object.

  The size of a single node is 2*sizeof(Item *). 

 */
template <class Item>
class BTreeNode
{
  public:
    
    typedef Item * iterator;

    /// create an uninitialized node
    BTreeNode() : ibegin(0), iend(0) {}
    
    /// assign item range
    void range(iterator pbegin, iterator pend) {
      ibegin = pbegin;
      iend = pend;
    }
    
    /// is this a valid node?
    bool valid() const {return ibegin != 0;}
    
    /// number of items in this node
    size_t size() const {return iend-ibegin;}

    /// empty node?
    bool empty() const {
      return (iend == ibegin);
    }
    
    /// start of range
    iterator begin() const {return ibegin;}
    
    /// end of range
    iterator end() const {return iend;}
    
    /// access median iterator
    iterator median() const {return ibegin + std::distance(ibegin, iend)/2;}
    
    /// sort range such that median is correct (uses std::nth_element)
    template <class Ordering> 
    iterator sort(Ordering p, bool parsort = false) {
      iterator med = median();
      if (not parsort)
        std::nth_element(ibegin, med, iend, p);
      else
        parallel_nth_element(ibegin, med, iend, p);
      return med;
    }
    
  private:
    
    /// range of items belonging to this node
    iterator ibegin, iend;
};

#endif
