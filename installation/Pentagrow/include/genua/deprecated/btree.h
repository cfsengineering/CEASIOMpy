
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       btree.h
 * copyright:  (c) 2009 by david.eller@gmx.net
 * ------------------------------------------------------------------------
 * Balanced binary tree
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#ifndef GENUA_BTREE_H
#define GENUA_BTREE_H

#include <vector>
#include <boost/shared_array.hpp>

#include "defines.h"
#include "btreenode.h"

/** Balanced binary tree.

  \deprecated

  */
template <class Item>
class BTree
{
  public:
    
    // typedef BTreeNode<Item> Node;
  
    /// empty tree
    BTree() {}
    
    /// allocate storage for an index tree containing n items
    BTree(uint n, uint mincount=4) { 
      init(n, mincount);
    }
    
    /// allocate storage for an index tree containing n items
    BTree(uint n, Item *pit, uint mincount) : nitem(n), minitemcount(mincount) {
      init(n, pit, mincount);
    }
    
    /// initialization 
    void init(int n, uint mincount=4) {
      nitem = n;
      minitemcount = mincount;
      items.reset(new Item[n]);
      for (int i=0; i<int(n); ++i)
        items[i] = i; 
      allocate();
    }
    
    /// initialization 
    void init(int n, Item *pit, uint mincount) {
      assert(pit != 0);
      nitem = n;
      minitemcount = mincount;
      items = ItemArray(pit, null_deleter());
      allocate();
    }
    
    /// determine whether node k is a leaf or not
    bool isleaf(uint k) const {return leaftag[k];}
    
    /// determine whether node k is a leaf or not
    bool noleaf(uint k) const {return (not leaftag[k]);}
    
    /// plain recursive sort with single predicate evaluation
    template <class Ordering>
    void rsplit(uint k, Ordering p) { 
      nodes[k].sort(p);
      if (noleaf(k)) {
        rsplit(2*k+1, p);
        rsplit(2*k+2, p);
      }
    }
    
    /// parallel split using OpenMP
    template <class Ordering>
    void psplit(Ordering p) {
      
      // root node is processed using parallel nth_element
      nodes[0].sort(p, true);
      
      // TODO : when omp_num_threads > 2, sort the following
      // few levels in parallel as well before parallelizing 
      // over nodes as below
      
      // parallel recursion until last-but one depth level
      const int nlevel = depth() - 1;
      int nfirst(1), nlast(3);
      for (int j=1; j<nlevel; ++j) {
        
//#pragma omp parallel for schedule(static)
        for (int i=nfirst; i<nlast; ++i) {
          if (noleaf(i)) {
            nodes[i].sort(p);
          }
        }
        
        nfirst = 2*nfirst + 1;
        nlast = 2*nlast + 1;
      }
    }
    
    /// number of items in tree
    uint size() const {return nitem;}
    
    /// number of nodes allocated
    uint nnodes() const {return nodes.size();}
    
    /// minimum number of items in node
    uint minItemCount() const {return minitemcount;}
    
    /// tree depth
    uint depth() const {
      uint dep(0), ndep(minitemcount);
      while (ndep < nitem) {
        ++dep;
        ndep *= 2;
      }
      return dep;
    }
    
    /// number of empty nodes
    uint nempty() const {
      const int n = nnodes();
      int ne(0);
      for (int i=0; i<n; ++i)
        if (node(i).size() == 0)
          ++ne;
      return ne;
    }
    
    /// access node by index
    const BTreeNode<Item> & node(uint k) const {
      assert(k < nodes.size()); 
      return nodes[k];
    }
    
    /// access node by index
    BTreeNode<Item> & node(uint k) {
      assert(k < nodes.size()); 
      return nodes[k];
    }
    
    /// access left child node of node k
    const BTreeNode<Item> & leftChildOf(uint k) const {
      return node(2*k + 1);
    }
    
    /// access right child node of node k
    const BTreeNode<Item> & rightChildOf(uint k) const {
      return node(2*k + 2);
    }
    
    /// access left child node of node k
    BTreeNode<Item> & leftChildOf(uint k) {
      return node(2*k + 1);
    }
    
    /// access right child node of node k
    BTreeNode<Item> & rightChildOf(uint k) {
      return node(2*k + 2);
    }

    /// reset storage to empty tree
    void clear() {
      items.reset();
      nitem = 0;
      nodes = std::vector<BTreeNode<Item> >();
      leaftag = std::vector<bool>();
    }
    
    /// swap contents with a
    void swap(BTree<Item> & a) {
      items.swap(a.items);
      nodes.swap(a.nodes);
      leaftag.swap(a.leaftag);
      std::swap(nitem, a.nitem);
      std::swap(minitemcount, a.minitemcount);
    }
    
  protected:
    
    /// initialize once index and pitems is set
    void allocate() {
      int nnds = 2*( (nitem/minitemcount)+1 ) - 1;
      nodes.resize(nnds);
      leaftag.resize(nnds);
      nodes[0].range(items.get(), items.get() + nitem);
      for (int i=0; i<nnds; ++i) {
        int ileft = 2*i + 1;
        int iright = 2*i + 2;
        uint nni = nodes[i].size();
        if (iright < nnds and nni >= 2*minitemcount) {
          leaftag[i] = false;
          typename BTreeNode<Item>::iterator med = nodes[i].median();
          nodes[ileft].range(nodes[i].begin(), med);
          nodes[iright].range(med, nodes[i].end());
        } else {
          leaftag[i] = true;
        }
      }
    }
    
  private:
    
    typedef boost::shared_array<Item> ItemArray;  
    
    /// top-level item array
    ItemArray items;
    
    /// storage for fully populated tree
    std::vector<BTreeNode<Item> > nodes;
    
    /// marks whether node is a leaf or not
    std::vector<bool> leaftag;
    
    /// least number of items per leaf node
    uint nitem, minitemcount;
};

typedef BTree<uint> BIndexTree;

#endif
