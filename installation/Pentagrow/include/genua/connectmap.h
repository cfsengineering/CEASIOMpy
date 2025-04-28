
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

#ifndef GENUA_CONNECTMAP_H
#define GENUA_CONNECTMAP_H

#include "atomicop.h"
#include "forward.h"
#include "xmlelement.h"
#include "sparsitycounter.h"
#include "algo.h"
#include <cstring>
#include <algorithm>

/** Container for connectivity data.

  ConnectMap stores index-based connectivity data in a format similar
  to the compressed-row scheme for sparse matrices. Since insert
  operations are expensive, it is required to use two passes. In the
  first pass, the number of elements (columns) connected to entry
  (row) ir are counted. After completion, connected values are set
  using append() or set(). To minimize memory consumption, call close()
  when the append operation is completed.

  \ingroup numerics
  \sa CsrMatrix
  */
class ConnectMap
{
public:

  enum Symmetry { Unsymmetric, LowerTriangular, UpperTriangular };

  /// iterator over connection array
  typedef Indices::const_iterator const_iterator;
  typedef std::vector<uint64_t> PairArray;

  /// construct empty map
  ConnectMap() {}

  /// construct map from CSR representation
  template <class Iterator>
  ConnectMap(Iterator colindBegin, Iterator colindEnd,
             Iterator rowptrBegin, Iterator rowptrEnd) :
    icol(colindBegin, colindEnd), irow(rowptrBegin, rowptrEnd) {}

  /// helper for packed construction
  static uint64_t packpair(uint32_t r, uint32_t c) {
    uint64_t wr(r), wc(c);
    return (wr << 32) | wc;
  }

  /// helper for packed construction
  static void unpackpair(uint64_t p, uint32_t &r, uint32_t &c) {
    uint64_t wr = (p >> 32);
    uint64_t wc = (p & uint64_t(0xffffffff));
    r = (uint32_t) wr;
    c = (uint32_t) wc;
  }

  /// helper function for removal of invalid pairs
  static size_t dropInvalidPairs(Symmetry sym, size_t n, uint64_t sp[]);

  /// generate packed index pairs for this map
  void generatePairs(const Indices &rowMap, const Indices &colMap,
                     uint rowOffset, uint colOffset, PairArray &pairs) const;

  /// generate packed index pairs for this map
  void generatePairs(uint rowOffset, uint colOffset, PairArray &pairs) const;

  /// construct from unique, sorted packed pairs
  void assign(uint nrows, size_t npairs, const uint64_t sp[]);

  /// copy from vector-of-vector data structure
  void assign(const std::vector<Indices> & m);

  /// copy data from interleaved linear storage (ir,k,ir,k,...)
  void assign(uint nr, const Indices & lmap);

  /// copy data from sparsity counter
  void assign(uint nr, const SparsityCounter & sc);

  /// construct from unique, sorted triplets
  template <class TripletIterator>
  void assign(uint nrows, TripletIterator first, TripletIterator last) {
    irow.resize(nrows+1);
    irow[0] = 0;
    icol.resize( std::distance(first, last) );
    uint i(0), k(0);
    TripletIterator itr;
    for (itr = first; itr != last; ++itr, ++i) {
      icol[i] = itr->col();
      uint r = itr->row();
      if (r != k) {
        assert(r >= k);
        while (r > k) {
          ++k;
          irow[k] = i;
        }
      }
    }
    irow[nrows] = icol.size();
  }

  /// copy data from bucket map
  template <int lg2n>
  void assign(uint nr, const BucketMap<lg2n> & bm) {
    beginCount(nr);
    const int nb = bm.nbuckets();
    for (int i=0; i<nb; ++i) {
      typename BucketMap<lg2n>::const_iterator itr, last;
      last = bm.end(i);
      for (itr = bm.begin(i); itr != last; ++itr)
        incCount( itr->row );
    }
    endCount();
    for (int i=0; i<nb; ++i) {
      typename BucketMap<lg2n>::const_iterator itr, last;
      last = bm.end(i);
      for (itr = bm.begin(i); itr != last; ++itr)
        append( itr->row, itr->col );
    }
  }

  /// assemble connectivity by rows : append row
  template <class Iterator>
  void appendRow(Iterator ifirst, Iterator ilast) {
    if (irow.empty()) {
      irow.resize(1);
      irow[0] = 0;
    }
    icol.insert(icol.end(), ifirst, ilast);
    irow.push_back(icol.size());
  }

  /// start counting phase with nr rows
  void beginCount(uint nr) {
    icount.resize(nr);
    std::fill(icount.begin(), icount.end(), 0);
  }

  /// access current row count during the counting phase
  uint currentCount(uint row) const {
    assert(row < icount.size());
    return icount[row];
  }

  /// setup phase - increment value count for row i
  force_inline void incCount(uint i, uint k = 1) {
    assert(i < icount.size());
    icount[i] += k;
  }

  /// as incCount above, but for multiple DOFs per node
  template <int NDOF>
  void ndIncrement(uint i, uint k=1) {
    assert(i < icount.size());
    for (int idof=0; idof<NDOF; ++idof)
      icount[i+idof] += k*NDOF;
  }

  /// setup phase - increment value count for row i
  void atomicIncCount(uint i, uint k = 1) {
    assert(i < icount.size());
    atomic_add(icount[i], k);
  }

  /// merge another pattern, optionally with row offset
  void incCount(const ConnectMap & map, int rowOffset=0);

  /// merge another pattern with row and column renaming
  void incCount(const ConnectMap & spty, const Indices & rcmap);

  /// setup phase - increment count for an element
  template <int M>
  void incCountElement(const Indices &rmap, const uint *vi) {
    for (int i=0; i<M; ++i) {
      assert(vi[i] < rmap.size());
      const uint row = rmap[vi[i]];
      if (row != NotFound)
        incCount(row, M);
    }
  }

  /// allocate after counting is completed
  void endCount();

  /// allocate storage for a fixed number nc of connections per entry
  void allocate(uint nr, uint nc);

  /// append value k to row ir, without checking for sufficient space
  force_inline void append(uint ir, uint k) {
    assert(ir < icount.size());
    assert(icount[ir] < size(ir));
    assert(irow[ir] + icount[ir] < icol.size());
    icol[irow[ir] + icount[ir]] = k;
    ++icount[ir];
  }

  /// as append above, but for multiple DOFs per node
  template <int NDOF>
  void ndAppend(uint ir, uint k) {
    for (int idof=0; idof<NDOF; ++idof)
      for (int jdof=0; jdof<NDOF; ++jdof)
        append(ir+idof, k+jdof);
  }

  /// append n values in kv to row ir, without checking for sufficient space
  void append(uint ir, uint n, const uint kv[]) {
    assert(ir < icount.size());
    assert(icount[ir]+n <= size(ir));
    assert(irow[ir] + icount[ir] + n <= icol.size());
    uint *dst = &icol[irow[ir]+icount[ir]];
    memcpy(dst, kv, n*sizeof(uint));
    icount[ir] += n;
  }

  /// append another map with row and column offsets
  void append(const ConnectMap & map, int rowOffset=0, int colOffset=0);

  /// append another map with row and columen renaming
  void append(const ConnectMap & spty, const Indices & rcmap);

  /// append element using row and column maps
  template <int M, Symmetry symFlag>
  void appendElement(const Indices &rmap, const Indices &cmap,
                     const uint *vi)
  {
    uint row[M], col[M];
    for (int i=0; i<M; ++i) {
      assert(vi[i] < rmap.size());
      assert(vi[i] < cmap.size());
      row[i] = rmap[vi[i]];
      col[i] = cmap[vi[i]];
    }
    for (int i=0; i<M; ++i) {
      if (row[i] != NotFound) {
        for (int j=0; j<M; ++j) {
          if (col[j] != NotFound and inrange<symFlag>(row[i], col[j]))
            append(row[i], col[j]);
        }
      }
    }
  }

  /// set elements connected to ir
  void set(uint ir, uint n, const uint kv[]) {
    assert(ir < icount.size());
    assert(n == irow[ir+1]-irow[ir]);
    memcpy(&icol[irow[ir]], kv, n*sizeof(uint));
  }

  /// finished appending
  void close() {
    icount = Indices();
  }

  /// compactify only, use only if sorting is guaranteed
  void compactify();

  /// sort, compactify and close : expensive!
  void compress();

  /// sort column indices of each row
  void sort();

  /// determine whether rows ri and rj have the same pattern
  bool equalPattern(uint ri, uint rj) const;

  /// number of rows
  uint size() const {return irow.empty() ? 0 : (irow.size()-1);}

  /// number of connected values
  uint size(uint ir) const {
    assert(ir < irow.size()-1);
    assert(irow[ir+1] >= irow[ir]);
    return irow[ir+1] - irow[ir];
  }

  /// number of column indices
  uint nonzero() const {return icol.size();}

  /// find the largest column index present
  uint maxcolindex() const;

  /// pointer to first index
  const uint *first(uint ir) const {
    assert(ir < irow.size());
    return &icol[irow[ir]];
  }

  /// column value k < size(ir) of row ir
  uint index(uint ir, uint k) const {
    assert(k < size(ir));
    return icol[irow[ir] + k];
  }

  /// column index of value offs
  uint colindex(uint offs) const {
    assert(offs < icol.size());
    return icol[offs];
  }

  /// row pointer offset
  uint offset(uint ir) const {
    assert(ir < irow.size());
    return irow[ir];
  }

  /// iterator access
  const_iterator begin(uint ir) const {
    assert(ir+1 < irow.size());
    return icol.begin()+irow[ir];
  }

  /// iterator access
  const_iterator end(uint ir) const {
    assert(ir+1 < irow.size());
    return icol.begin()+irow[ir+1];
  }

  /// if sorted, find linear index of (i,j) or return NotFound
  uint lindex(uint i, uint j) const {
    if ( hint_unlikely(i == NotFound or j == NotFound) )
      return NotFound;
    const_iterator beg, lst, pos;
    beg = begin(i);
    lst = end(i);
    pos = std::lower_bound(beg, lst, j);
    if ( hint_unlikely(pos == lst or *pos != j) )
      return NotFound;
    else
      return std::distance(icol.begin(), pos);
  }

  /// utility : find linear index of symmetric matrix (upper triangle)
  uint uptrilix(uint i, uint j) const {
    uint a = (i < j) ? i : j;
    uint b = (i < j) ? j : i;
    return lindex(a,b);
    // return (i <= j) ? lindex(i,j) : lindex(j,i);
  }

  /// utility : find linear index of symmetric matrix (lower triangle)
  uint lotrilix(uint i, uint j) const {
    uint a = (i < j) ? i : j;
    uint b = (i < j) ? j : i;
    return lindex(b,a);
    // return (i >= j) ? lindex(i,j) : lindex(j,i);
  }

  /// determine if row i has neighbor j (sorted only)
  bool search(uint i, uint j) const {
    return std::binary_search(begin(i), end(i), j);
  }

  /// return the number of column indices shared between rows i and j
  uint sharedColumns(uint i, uint j) const;

  /// compute a row permutation to improve blocking
  void rowBlockPermutation(uint blockSize, Indices &perm) const;

  /// permute using METIS, when available
  bool metisPermutation(Indices &perm, Indices &iperm) const;

  /// apply a replacement table to rows
  void rowpermute(const Indices &rep);

  /// apply a column permutation
  void colpermute(const Indices &rep);

  /// apply full permutation to both rows and columns
  void permute(const Indices &perm) {
    rowpermute(perm);
    colpermute(perm);
  }

  /// determine one-level factorrization fill-in
  static void fillIn(const ConnectMap &amap, const ConnectMap &tmap,
                     std::vector<uint64_t> &f);

  /// make this the merge of a and b
  void merge(const ConnectMap & a, const ConnectMap & b);

  /// make this the column-wise (horizontal) concatenation of a and b
  void catColumns(const ConnectMap &a, const ConnectMap &b, uint acol);

  /// make this the row-wise (vertical) concatenation of a and b
  void catRows(const ConnectMap &a, const ConnectMap &b);

  /// construct the transpose of *this in mt
  void transpose(uint ncol, ConnectMap &mt) const;

  /// make this the transpose of itself
  void transpose(uint ncol);

  /** Drop entries below the main diagonal.
     \param utlix is set to the linear indices of the upper triangular values */
  void dropLowerTriangle(Indices & upperlix);

  /// compute pattern for the upper triangular part
  void upperTriangle(ConnectMap &uptri) const;

  /// compute pattern for the upper triangular part
  void upperTriangle() {
    ConnectMap tmp;
    upperTriangle(tmp);
    swap(tmp);
  }

  /// compute pattern for the lower triangular part
  void lowerTriangle(ConnectMap &lotri) const;

  /// compute pattern for the lower triangular part
  void lowerTriangle() {
    ConnectMap tmp;
    lowerTriangle(tmp);
    swap(tmp);
  }

  /// straightforward multicoloring
  uint coloring(Indices &clr) const;

  /// release all storage
  void clear() {
    icol.clear();
    irow.clear();
    icount.clear();
  }

  /// swap contents with other map
  void swap(ConnectMap & a) {
    icol.swap(a.icol);
    irow.swap(a.irow);
    icount.swap(a.icount);
  }

  /// diagnose out-of-bounds problems
  bool checkPattern(uint nr, uint nc) const;

  /// compute memory requirements
  float megabytes() const;

  /// return column index pointer
  const uint *colIndex() const {return &icol[0];}

  /// return pointer to row offsets in colIndex
  const uint *rowPointer() const {return &irow[0];}

  /// remove loops (diagonals), make symmetric
  void scotchify(ConnectMap & map) const;

  /** Copy into CSR data structure. colindex must point into storage for at least
      nonzero() entries, and rowstart must have space for size()+1 values or be an
      back insertion iterator. */
  template <typename Iterator>
  void tocsr(Iterator colix, Iterator rowstart) const {
    std::copy(icol.begin(), icol.end(), colix);
    std::copy(irow.begin(), irow.end(), rowstart);
  }

  /// create xml representation
  XmlElement toXml(bool shared=false) const;

  /// generate from xml representation
  void fromXml(const XmlElement & xe);

  /// create 1-based FFA format node (copies)
  FFANodePtr toFFA() const;

  /// fetch data from FFA format file node
  bool fromFFA(const FFANodePtr &root);

  // debugging
  bool equal(const ConnectMap & a) const;

  // debugging
  void print(std::ostream &os);

private:

  /// test if index is permissible
  template <Symmetry flag>
  force_inline static bool inrange(uint row, uint col) {
    if (flag == Unsymmetric)
      return true;
    else if (flag == LowerTriangular)
      return col <= row;
    else
      return col >= row;
  }

private:

  /// connectivity data (column indices)
  Indices icol;

  /// indexes of icol indicating where the rows begin
  Indices irow, icount;
};

inline void swap(ConnectMap & a, ConnectMap & b)
{
  a.swap(b);
}

#endif

