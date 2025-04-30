#ifndef UNBALANCEDBVTREE_H
#define UNBALANCEDBVTREE_H

#include <genua/defines.h>
#include <genua/algo.h>
#include <genua/bitfiddle.h>
#include <genua/dvector.h>

#include <genua/kdop.h>
#include <genua/morton.h>
#include <genua/primitives.h>

#include <boost/static_assert.hpp>
#include <boost/dynamic_bitset.hpp>

#ifdef HAVE_TBB
#include <tbb/blocked_range.h>
#include <tbb/parallel_for.h>
#include <tbb/parallel_sort.h>
#endif

#include <deque>
#include <vector>

template <class DopType, typename KeyType = size_t>
class UnbalancedBVTree
{
public:

  struct Node {

    Node() : parent(NotFound), child(NotFound), first(NotFound), last(NotFound) {}

    Node(uint parentIdx, uint beginIdx, uint endIdx)
      : parent(parentIdx), child(NotFound), first(beginIdx), last(endIdx) {}

    uint left() const {return child;}

    uint right() const {return child+1;}

    uint size() const {return last - first;}

    bool leaf() const {
      return (child == NotFound);
    }

    DopType dop;
    uint parent, child;
    uint first, last;
  };

  typedef typename DVector<uint>::const_iterator ItemIterator;

  /// construct empty tree
  UnbalancedBVTree(uint nitems = 0, uint minsize = 8)
  {
    BOOST_STATIC_ASSERT( sizeof(KeyType) == 4 || sizeof(KeyType) == 8 );
    if (nitems > 0)
      allocate(nitems, minsize);
  }

  /// allocate memory for nitems, estimate number of nodes
  void allocate(uint nitems, uint minsize = 8) {
    m_items.resize(nitems);
    m_keys.clear();
    m_keys.resize(nitems);

    m_minsize = (minsize > 1) ? nextpow2(minsize) : 1;
    while (m_minsize > nitems and m_minsize > 1)
      m_minsize /= 2;
    assert(minsize > 0);
    uint m = nextpow2(nitems) / m_minsize;
    m_nodes.clear();
    m_nodes.reserve( ((m > 0) ? (2*nextpow2(m) - 1) : 0) );
  }

  /// build entire tree
  template <class KeyFunctor, class Boxer>
  void build(const KeyFunctor &kf, const Boxer &bf) {
    sortKeys(kf);
    createNodes();
    boundingVolumes(bf);
  }

  /// first stage : compute keys and sort
  template <class KeyFunctor>
  void sortKeys(KeyFunctor &kf) {

    kf.target( m_keys.pointer() );
    const int nitems = m_items.size();
    for (int i=0; i<nitems; ++i) {
      m_items[i] = i;
      kf(i);
    }

    // sort items by keys
    IndirectLess<DVector<KeyType> > cmp(m_keys);
    std::sort(m_items.begin(), m_items.end(), cmp);

    // permute keys accordingly
    DVector<KeyType> tmp( nitems );
    for (int i=0; i<nitems; ++i)
      tmp[i] = m_keys[ m_items[i] ];
    m_keys.swap(tmp);
  }

  /// create nodes iteratively
  void createNodes() {
    m_nodes.clear();

    // create root node
    m_nodes.push_back( Node(NotFound, 0, m_items.size()) );

    // recursion stack
    std::deque<uint> queue;
    // queue.reserve( m_nodes.size() );
    queue.push_back( 0 );
    while (not queue.empty()) {

      uint iparent = queue.front();
      queue.pop_front();

      uint begin = m_nodes[iparent].first;
      uint end = m_nodes[iparent].last;

      // find split index
      uint split = (begin + end)/2;
      KeyType kfirst = m_keys[begin];
      KeyType klast = m_keys[end-1];
      if (kfirst != klast) {
        int prefix = clz( kfirst ^ klast );
        split = begin+1;
        uint step = end - 1 - begin;
        while (step > 1) {
          step = (step + 1) / 2;
          uint newsplit = split + step;
          if ( (newsplit < end-1) and
               (clz(kfirst ^ m_keys[newsplit]) > prefix))
            split = newsplit;
        }
      }

      assert(split > begin);
      assert(split < end);

      uint leftChild = createChildNodes( iparent, begin, split+1, end );
      if (split - begin > m_minsize)
        queue.push_back( leftChild );
      if (end - split > m_minsize)
        queue.push_back( leftChild+1 );
    }

#ifndef NDEBUG
    const uint nn = m_nodes.size();
    for (uint i=0; i<nn; ++i) {
      if (leaf(i)) {
        assert( (left(parent(i)) == i) or (right(parent(i)) == i) );
      } else {
        assert( parent( left(i) ) == i );
        assert( parent( right(i) ) == i );
      }
    }
#endif
  }

  /// determine bounding volumes for nodes, bottom-up
  template <class Boxer>
  void boundingVolumes(const Boxer &f) {

    // brute force
    const int nn = m_nodes.size();
    for (int i=0; i<nn; ++i) {
      Node & inode( m_nodes[i] );
      inode.dop.reset();
      f( begin(i), end(i), inode.dop ) ;
    }

    /*
    const int nn = m_nodes.size();
    std::vector<bool> fitted(nn, false);

    int nfitted = 0;
    for (int i=0; i<nn; ++i) {
      if (leaf(i)) {
        Node & inode( m_nodes[i] );
        inode.dop.reset();
        f( begin(i), end(i), inode.dop ) ;
        fitted[i] = true;
        ++nfitted;
      }
    }

    while (nfitted < nn) {

      for (int i=0; i<nn; ++i) {
        if (fitted[i])
          continue;
        assert(not leaf(i));
        uint cl = left(i);
        uint cr = right(i);
        if (fitted[cl] and fitted[cr]) {
          Node inode( m_nodes[i] );
          inode.dop.reset();
          inode.dop.enclose( m_nodes[cl].dop );
          inode.dop.enclose( m_nodes[cr].dop );
          fitted[i] = true;
          ++nfitted;
        }
      }
    }

    */
  }

  /// access list of items sorted by key
  const DVector<uint> & sortedItems() const {return m_items;}

  /// access parent node of i, returns NotFound for root
  uint parent(uint i) const {
    assert(i < m_nodes.size());
    return m_nodes[i].parent;
  }

  /// test whether node i is a leaf node
  bool leaf(uint i) const {
    assert(i < m_nodes.size());
    return m_nodes[i].leaf();
  }

  /// access index of left child node of node i
  uint left(uint i) const {
    assert(i < m_nodes.size());
    return m_nodes[i].left();
  }

  /// access left child node of node i
  uint right(uint i) const {
    assert(i < m_nodes.size());
    return m_nodes[i].right();
  }

  /// number of items in node i
  uint size(uint i) const {
    assert(i < m_nodes.size());
    return m_nodes[i].size();
  }

  /// iterator pointing to the first item in node i
  ItemIterator begin(uint i) const {
    assert(i < m_nodes.size());
    return m_items.begin() + m_nodes[i].first;
  }

  /// iterator pointing one past the last item in node i
  ItemIterator end(uint i) const {
    assert(i < m_nodes.size());
    return m_items.begin() + m_nodes[i].last;
  }

  /// access bounding box of node i
  const DopType & dop(uint i) const {
    assert(i < m_nodes.size());
    return m_nodes[i].dop;
  }

  /// find iterator to the item nearest by key
  ItemIterator lowerBound(KeyType key) const {
    typename DVector<KeyType>::const_iterator pos;
    pos = std::lower_bound(m_keys.begin(), m_keys.end(), key);
    return m_items.begin() + std::distance(m_keys.begin(), pos);
  }

  /// determine item which is closest to point p
  template <class DistanceFunctor>
  uint nearest(const DistanceFunctor &fdst) const  {

    typedef typename DistanceFunctor::result_type FloatType;
    FloatType ldst, rdst, best;
    uint inear = 0;
    best = fdst(inear);

    uint inode = 0;

    typedef std::pair<uint,FloatType> NodeDst;
    std::vector<NodeDst> opt;

    while (inode != NotFound) {

      if ( leaf(inode) ) {

        // inode is a leaf node, process contained elements
        ItemIterator itr, last = end(inode);
        for (itr = begin(inode); itr != last; ++itr) {
          FloatType dst = fdst(*itr);
          if (dst < best) {
            best = dst;
            inear = *itr;
          }
        }

        // early exit : will never get better than zero...
        if (best == 0.0f)
          return inear;

        inode = NotFound;

      } else { // inode is not a leaf

        uint cleft = left(inode);
        uint cright = right(inode);

        ldst = dop(cleft).pointDistance( fdst.point().pointer() );
        rdst = dop(cright).pointDistance( fdst.point().pointer() );
        assert(isfinite(ldst) or isfinite(rdst));

        inode = NotFound;

        // If p is in left child box (ldst == 0) or at least closer to
        // the box than the smallest point distance computed yet, continue
        // loop with left child. However, if ldst *could* possibly contain
        // a closer match but rdst is smaller, continue with right child but
        // put ldst on the stack.

        if (ldst < best) {
          if (ldst <= rdst)
            inode = cleft;
          else
            opt.push_back( std::make_pair(cleft, ldst) );
        }

        if (rdst < best) {
          if (rdst < ldst)
            inode = cright;
          else
            opt.push_back( std::make_pair(cright, rdst) );
        }
      }

      // pick next candidate c off the stack : discard directly if distance of
      // p from box c is larger than the current best hit, proceed otherwise
      while (inode == NotFound) {
        if (opt.empty())
          break;
        NodeDst c = opt.back();
        opt.pop_back();
        if (c.second < best) {
          inode = c.first;
          break;
        }
      }
    }

    return inear;
  }

protected:

  /// create child nodes
  uint createChildNodes(uint iparent, uint begin, uint split, uint end)
  {
    assert(iparent < m_nodes.size());
    uint idx = m_nodes.size();
    m_nodes.push_back( Node(iparent, begin, split) );
    m_nodes.push_back( Node(iparent, split, end) );
    m_nodes[iparent].child = idx;

    // invariant for leaf nodes
    assert( (left(parent(idx)) == idx) and (right(parent(idx)) == idx+1) );
    return idx;
  }

  /// count leading zeros
  static int clz(KeyType x) {
    if (sizeof(KeyType) == 4)
      return lzcount32(x);
    else
      return lzcount64(x);
  }

protected:

  /// ordered set of items
  DVector<uint> m_items;

  /// set of Morton keys
  DVector<KeyType> m_keys;

  /// nodes
  std::vector<Node> m_nodes;

  /// minimum number of items in each node
  uint m_minsize;
};

template <typename FloatType>
class TriangleKeyFunctor
{
public:

  typedef void result_type;

  /// construct functor
  TriangleKeyFunctor(const PointList<3,FloatType> *pvtx,
                     const uint ptri[]) : m_pvx(pvtx), m_tri(ptri)
  {
    init(21);
  }

  /// assign target array
  void target(uint64_t *pcodes) { m_pkeys = pcodes; }

  /// utility : quantize and compute morton code
  FloatType zcode(const FloatType p[]) const {
    return zcode(p[0], p[1], p[2]);
  }

  /// utility : quantize and compute morton code
  FloatType zcode(FloatType x, FloatType y, FloatType z) const {
    uint64_t ip[3];
    ip[0] = (x - m_offset[0]) * m_scale[0];
    ip[1] = (y - m_offset[1]) * m_scale[1];
    ip[2] = (z - m_offset[2]) * m_scale[2];
    return interleave_bits<uint64_t,21>( ip[0], ip[1], ip[2] );
  }

  /// evaluate key for one triangle
  uint64_t keyOfBbc(uint item) const {
    const uint *vi = &m_tri[3*item];
    FloatType pmin[3], pmax[3];
    for (int k=0; k<3; ++k) {
      pmin[k] = std::numeric_limits<FloatType>::max();
      pmax[k] = -pmin[k];
    }
    const PointList<3,FloatType> & vtx(*m_pvx);
    for (int j=0; j<3; ++j) {
      const SVector<3,FloatType> & p( vtx[vi[j]] );
      for (int k=0; k<3; ++k) {
        pmin[k] = std::min(pmin[k], p[k]);
        pmax[k] = std::max(pmax[k], p[k]);
      }
    }
    return zcode( 0.5*(pmin[0] + pmax[0]),
                  0.5*(pmin[1] + pmax[1]),
                  0.5*(pmin[2] + pmax[2]) );
  }

  /// evaluate key for one triangle
  uint64_t keyOfCtr(uint item) const {
    const uint *vi = &m_tri[3*item];
    SVector<3,FloatType> pctr;
    const PointList<3,FloatType> & vtx(*m_pvx);
    for (int j=0; j<3; ++j) {
      const SVector<3,FloatType> & p( vtx[vi[j]] );
      pctr += p;
    }
    return zcode( pctr.pointer() );
  }

  /// operator form
  void operator() (uint item) {
    m_pkeys[item] = keyOfBbc(item);
  }

#ifdef HAVE_TBB

  /// process a range of triangles
  void operator() (const tbb::blocked_range<uint> &r) {
    for (uint i=r.begin(); i!=r.end(); ++i)
      m_pkeys[i] = key(i);
  }

#endif

private:

  /// determine quantization parameters
  void init(int nbits) {
    FloatType xmin[3], xmax[3];
    for (int k=0; k<3; ++k) {
      xmin[k] =  std::numeric_limits<FloatType>::max();
      xmax[k] = -std::numeric_limits<FloatType>::max();
    }
    const PointList<3,FloatType> & vtx(*m_pvx);
    const int n = m_pvx->size();
    for (int i=0; i<n; ++i) {
      for (int k=0; k<3; ++k) {
        FloatType x = vtx[i][k];
        xmin[k] = std::min( xmin[k], x );
        xmax[k] = std::max( xmax[k], x );
      }
    }
    FloatType maxintval = ((1 << nbits) - 1);
    for (int k=0; k<3; ++k) {
      m_offset[k] = xmin[k] - FloatType(0.01)*(xmax[k] - xmin[k]);
      m_scale[k] = FloatType(0.99) * maxintval / (xmax[k] - xmin[k]);
    }
  }

private:

  /// pointer to vertex list
  const PointList<3,FloatType> *m_pvx;

  /// pointer to triangle indices
  const uint *m_tri;

  /// target
  uint64_t *m_pkeys;

  /// quantization
  FloatType m_offset[3], m_scale[3];
};

template <typename FloatType>
class TriangleBoxFunctor
{
public:

  /// construct functor
  TriangleBoxFunctor(const PointList<3,FloatType> *pvtx,
                     const uint ptri[]) : m_pvx(pvtx), m_tri(ptri) {}

  /// determine bounding box for triangles in range
  template <typename Iterator>
  void operator() (Iterator begin, Iterator end, Dop3d3<FloatType> &dop) const {
    const PointList<3,FloatType> & vtx(*m_pvx);
    for (Iterator itr=begin; itr != end; ++itr) {
      const uint t = *itr;
      const uint *vi = &m_tri[3*t];
      for (int j=0; j<3; ++j)
        dop.adapt( vtx[vi[j]].pointer() );
    }
  }

private:

  /// pointer to vertex list
  const PointList<3,FloatType> *m_pvx;

  /// pointer to triangle indices
  const uint *m_tri;
};

template <typename FloatType>
class TriangleDistanceFunctor
{
public:

  typedef FloatType result_type;
  typedef SVector<3,FloatType> point_type;

  TriangleDistanceFunctor(const PointList<3,FloatType> *pvtx,
                          const uint ptri[]) : m_pvx(pvtx), m_tri(ptri) {}

  void point(const point_type &p) {m_pt = p;}

  const point_type point() const {return m_pt;}

  FloatType operator() (uint itri) const {
    const PointList<3,FloatType> & vtx(*m_pvx);
    point_type tri[3];
    const uint *v = &m_tri[3*itri];
    for (int k=0; k<3; ++k)
      tri[k] = vtx[v[k]];
    return qr_sqdistance(tri, m_pt);
  }

private:

  /// pointer to vertex list
  const PointList<3,FloatType> *m_pvx;

  /// pointer to triangle indices
  const uint *m_tri;

  /// point to which the distance is to be computed
  point_type m_pt;
};

#endif // UNBALANCEDBVTREE_H
