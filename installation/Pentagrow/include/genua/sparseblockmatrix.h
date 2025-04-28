
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

#ifndef GENUA_SPARSEBLOCKMATRIX_H
#define GENUA_SPARSEBLOCKMATRIX_H

#include "sparseblock.h"
#include "csrmatrix.h"
#include "smatrix.h"
#include "allocator.h"
#include "dvector.h"
#include "float4.h"

#ifndef NDEBUG
#include <iostream>
using namespace std;
#endif

namespace detail {

void block_sparsity(int M, const ConnectMap &espty, ConnectMap &bmap);

uint nzproduct_pairs(const ConnectMap &a, int arow,
                     const ConnectMap &b, int brow,
                     uint pairs[]);

}

/** Sparse matrix of small blocks.
 *
 *
 *
 *
 * \sa CsrMatrix, float4, float8
 */
template <typename FloatType, int M>
class SparseBlockMatrix
{
public:

  typedef SMatrix<M,M,FloatType> Block;
  typedef std::vector<Block, AlignedAllocator<Block,64> > BlockArray;
  typedef detail::block_op<FloatType,M> bop;

  /** Wrapper around an immutable row of a block matrix.
   *
   */
  class ConstRowVector {
  public:

    /// construct from matrix and row index
    ConstRowVector(const SparseBlockMatrix &m, uint row)
      : m_matrix(m), m_irow(row) {}

    /// number of entries (nonzero blocks)
    uint size() const {return m_matrix.sparsity().size(m_irow);}

    /// access column index
    uint index(uint k) const { return m_matrix.sparsity().index(m_irow, k); }

    /// access block k which is at m_matrix(m_irow, index(k))
    const Block & operator[] (uint k) const {
      uint offset = m_matrix.sparsity().offset(m_irow);
      return m_matrix[offset+k];
    }

  private:

    /// parent matrix
    const SparseBlockMatrix & m_matrix;

    /// row index
    uint m_irow;
  };

  /** Wrapper around a mutable row of a block matrix.
   *
   */
  class RowVector {
  public:

    /// construct from matrix and row index
    RowVector(SparseBlockMatrix &m, uint row)
      : m_matrix(m), m_irow(row) {}

    /// number of entries (nonzero blocks)
    uint size() const {return m_matrix.sparsity().size(m_irow);}

    /// access column index
    uint index(uint k) const { return m_matrix.sparsity().index(m_irow, k); }

    /// access block k which is at m_matrix(m_irow, index(k))
    Block & operator[] (uint k) {
      uint offset = m_matrix.sparsity().offset(m_irow);
      return m_matrix[offset+k];
    }

    /// set the diagonal block to the identity matrix, zero out the rest
    void identity() {
      const uint n = size();
      for (int i=0; i<n; ++i) {
        if (index(i) != m_irow)
          (*this)[i] = FloatType(0);
        else
          (*this)[i] = Block::identity();
      }
    }

  private:

    /// parent matrix
    SparseBlockMatrix & m_matrix;

    /// row index
    uint m_irow;
  };

  /// do nothing
  SparseBlockMatrix() {}

  /// create block matrix which captures the entire element matrix
  template <typename AType>
  explicit SparseBlockMatrix(const CsrMatrix<AType,1> &a) {
    assign(a);
  }

  /// copy block sparsity pattern, allocate block memory
  explicit SparseBlockMatrix(const ConnectMap &map, uint bcols = 0) {
    assign(map, bcols);
  }

  /// change sparsity pattern (zeros out all blocks)
  void assign(const ConnectMap &map, uint bcols = 0) {
    m_spty = map;
    m_blocks.clear();
    m_blocks.resize( m_spty.nonzero() );
    m_nbcol = std::max(bcols, m_spty.maxcolindex());
  }

  /// create block matrix which captures the entire element matrix
  template <typename AType>
  void assign(const CsrMatrix<AType,1> &a, bool permute=false)
  {
    m_perm.clear();
    m_iperm.clear();
    if (permute) {

      ConnectMap tmap;
      detail::block_sparsity( M, a.sparsity(), tmap );

      Indices bperm, ibperm;
      if ( tmap.metisPermutation(bperm, ibperm) ) {
        const size_t nbr = tmap.size();
        m_perm.resize(M*nbr);
        m_iperm.resize(M*nbr);
        for (size_t i=0; i<nbr; ++i) {
          for (int k=0; k<M; ++k)
            m_perm[M*i+k] = M*bperm[i] + k;
        }
        for (size_t i=0; i<M*nbr; ++i)
          m_iperm[m_perm[i]] = i;
        tmap.rowpermute(bperm);
        tmap.colpermute(bperm);
      }

      m_spty = std::move(tmap);

    } else {
      detail::block_sparsity( M, a.sparsity(), m_spty );
    }

    m_blocks.clear();
    m_blocks.resize( m_spty.nonzero() );
    m_nbcol = a.ncols() / M;
    if (m_nbcol*M < a.ncols())
      ++m_nbcol;
    injectValues(a);
  }

  /// block row count
  uint nbrows() const {return m_spty.size();}

  /// block column count
  uint nbcols() const {return m_nbcol;}

  /// number of nonzero values
  uint nonzero() const {return m_spty.nonzero();}

  /// determine linear index
  uint lindex(uint i, uint j) const {return m_spty.lindex(i,j);}

  /// sparsity pattern
  const ConnectMap & sparsity() const {return m_spty;}

  /// access block by linear index
  const Block & operator[] (uint lix) const {
    assert(lix < m_blocks.size());
    return m_blocks[lix];
  }

  /// access block by linear index
  Block & operator[] (uint lix) {
    assert(lix < m_blocks.size());
    return m_blocks[lix];
  }

  /// construct the transpose of this in at
  void transpose(SparseBlockMatrix &at) const {
    // compute sparsity pattern of A^T
    {
      ConnectMap tmap;
      m_spty.transpose( nbcols(), tmap );
      at = SparseBlockMatrix(tmap, nbrows());
    }
    size_t nbr = m_spty.size();
    for (size_t i=0; i<nbr; ++i) {
      const uint nc = m_spty.size(i);
      const uint *col = m_spty.first(i);
      const uint offs = m_spty.offset(i);
      for (uint j=0; j<nc; ++j) {
        uint pos = at.sparsity().lindex(col[j], i);
        assert(pos != NotFound);
        at[pos] = m_blocks[offs+j];
      }
    }
  }

  /// overwrite this with its transpose
  void transpose() {
    SparseBlockMatrix at;
    transpose(at);
    swap(at);
  }

  /// apply stored permutation (if any) to vector x
  DVector<FloatType> permute(const DVector<FloatType> &x) const {
    if (m_perm.empty())
      return x;

    const size_t n = x.size();
    DVector<FloatType> xp(n);
    for (size_t i=0; i<n; ++i)
      xp[i] = x[m_perm[i]];

    return std::move(xp);
  }

  /// apply stored inverse permutation (if any) to vector x
  DVector<FloatType> invpermute(const DVector<FloatType> &x) const {
    if (m_perm.empty())
      return x;

    const size_t n = x.size();
    DVector<FloatType> xp(n);
    for (size_t i=0; i<n; ++i)
      xp[m_perm[i]] = x[i];

    return std::move(xp);
  }

  //  /// apply full permutation
  //  void permute(const Indices &rowperm, const Indices &colperm) {
  //    ConnectMap pmap;
  //    const size_t nr = m_spty.size();
  //    pmap.beginCount(nr);
  //    for (size_t i=0; i<nr; ++i)
  //      pmap.incCount(rowperm[i], m_spty.size(i));
  //    pmap.endCount();
  //    for (size_t i=0; i<nr; ++i) {
  //      const uint pi = rowperm[i];
  //      const uint nc = m_spty.size(i);
  //      const uint *pcol = m_spty.first(i);
  //      for (uint j=0; j<nc; ++j)
  //        pmap.append(pi, colperm[pcol[j]]);
  //    }
  //    pmap.sort();
  //    pmap.close();

  //    BlockArray pblocks(m_blocks.size());
  //    for (size_t i=0; i<nr; ++i) {
  //      const uint pi = rowperm[i];
  //      const uint nc = m_spty.size(i);
  //      const uint *pcol = m_spty.first(i);
  //      const uint voff = m_spty.offset(i);
  //      for (uint j=0; j<nc; ++j) {
  //        uint pj = colperm[pcol[j]];
  //        uint lix = pmap.lindex(pi, pj);
  //        pblocks[lix] = m_blocks[voff+j];
  //      }
  //    }

  //    m_spty.swap(pmap);
  //    m_blocks.swap(pblocks);
  //  }

  /// swap contents with a
  void swap(SparseBlockMatrix &a) {
    m_spty.swap( a.m_spty );
    m_blocks.swap( a.m_blocks );
    std::swap( m_nbcol, a.m_nbcol );
  }

  /// multiply with vector x of possibly another type and add to b
  template <typename XType, typename BType>
  void muladd(const DVector<XType> &x, DVector<BType> &b) const {
    assert(b.size() > M*m_spty.size());
    assert(x.size() > M*m_nbcol);
    pmuladd(x.pointer(), b.pointer());
  }

  /// multiply transposed with vector x of possibly another type and add to b
  template <typename XType, typename BType>
  void transmuladd(const DVector<XType> &x, DVector<BType> &b) const {
    assert(b.size() > M*m_nbcol);
    assert(x.size() > M*m_spty.size());
    ptransmuladd(x.pointer(), b.pointer());
  }

  /// multiply one row with vector x of possibly another type and add to b
  template <typename XType, typename BType>
  void rowmuladd(int i, const DVector<XType> &x, SVector<M,BType> &b) const {
    assert(b.size() > M*m_spty.size());
    assert(x.size() > M*m_nbcol);
    rowmuladd(i, x.pointer(), b.pointer());
  }

  /// x^T multiplied with row i of A added to b
  template <typename XType, typename BType>
  void dotrow(int i, const SVector<M,XType> &x, DVector<BType> &b) const
  {
    assert(b.size() > M*m_spty.size());
    assert(x.size() > M*m_nbcol);
    dotrow(i, x.pointer(), b.pointer());
  }

  /// multiply from left and right, write result to r = r + ZL*A*ZR
  template <class BlockVector>
  void mulmul(const BlockVector &zleft,
              const BlockVector &zright, Block &r) const
  {
    const uint nl = zleft.size();
    const uint nr = zright.size();
    Block rowsum;
    for (uint i=0; i<nl; ++i) {
      const uint row = zleft.index(i);
      const uint nc = m_spty.size(row);
      const uint *col = m_spty.first(row);
      const uint offset = m_spty.offset(row);
      rowsum = FloatType(0);
      uint k(0), j(0), nbm(0);
      while (j < nc and k < nr) {
        const uint jc = col[j];
        const uint kc = zright.index(k);
        if (kc < jc)
          ++k;
        else if (kc > jc)
          ++j;
        else {
          detail::block_mmadd<FloatType,M>(m_blocks[offset+j],
              zright[k], rowsum);
          ++k;
          ++j;
          ++nbm;
        }
      }
      if (nbm > 0)
        detail::block_mmadd<FloatType,M>(zleft[i], rowsum, r);
    }
  }

  /// write to plain text file for debugging
  void writePlain(std::ostream &os) const {
    for (uint i=0; i<m_spty.size(); ++i) {
      const uint rbase = M*i;
      const uint *bcol = m_spty.first(i);
      const uint roffset = m_spty.offset(i);
      for (uint j=0; j<m_spty.size(i); ++j) {
        const uint cbase = M*bcol[j];
        const Block & b(m_blocks[roffset+j]);
        for (int kj=0; kj<M; ++kj)
          for (int ki=0; ki<M; ++ki)
            os << rbase+ki << ' ' << cbase+kj << ' ' << b(ki,kj) << std::endl;
      }
    }
  }

#ifndef NDEBUG

  // write into dense matrix for debugging
  void toDense(DMatrix<FloatType> & a) const {
    a.resize( M*nbrows(), M*nbcols() );
    for (uint i=0; i<m_spty.size(); ++i) {
      const uint rbase = M*i;
      const uint *bcol = m_spty.first(i);
      const uint roffset = m_spty.offset(i);
      for (uint j=0; j<m_spty.size(i); ++j) {
        const uint cbase = M*bcol[j];
        const Block & b(m_blocks[roffset+j]);
        for (int kj=0; kj<M; ++kj)
          for (int ki=0; ki<M; ++ki)
            a(rbase+ki, cbase+kj) = b(ki,kj);
      }
    }
  }

#endif

protected:

  /// transfer nonzero values from scalar sparse matrix
  template <typename AType>
  void injectValues(const CsrMatrix<AType> &a) {
    const uint nsr = a.nrows();
    const ConnectMap &map( a.sparsity() );
    for (uint ki=0; ki<nsr; ++ki) {
      const uint i = m_perm.empty() ? ki : m_perm[ki];
      const uint ibr = i/M;
      const uint blki = i - M*ibr;
      const uint aroff = map.offset(i);
      const uint anc = map.size(i);
      const uint *col = map.first(i);
      for (uint j=0; j<anc; ++j) {
        uint cj = m_perm.empty() ? col[j] : m_perm[col[j]];
        uint jbc = cj / M;
        uint blkj = cj - M*jbc;
        uint bix = lindex(ibr, jbc);
        assert(bix != NotFound);
        m_blocks[bix](blki, blkj) = a[aroff + j];
      }
    }

    // inject ones on the last diagonal (fill-in due to blocking)
    const uint rbase = M*nbrows();
    const uint rfill = rbase - a.nrows();
    Block & lastBlock( m_blocks.back() );
    for (uint k=0; k<rfill; ++k)
      lastBlock(M-1-k,M-1-k) = 1.0;
  }

  /// collapse row i of A with short vector x, add to b
  template <typename XType, typename BType>
  void dotrow(int i, const XType x[], BType b[]) const {
    const int nc = m_spty.size(i);
    const uint *colidx = m_spty.first(i);
    const uint offs = m_spty.offset(i);
    for (int j=0; j<nc; ++j) {
      const Block &blk( m_blocks[offs+j] );
      detail::block_tmuladdv( blk, x, &b[M*colidx[j]]);
    }
  }

  /// multiply row of A with vector x and add to b
  void rowmuladd(int i, const FloatType x[], FloatType b[]) const {
    const int nc = m_spty.size(i);
    const uint *colidx = m_spty.first(i);
    const uint offs = m_spty.offset(i);
    for (int j=0; j<nc; ++j) {
      const Block &blk( m_blocks[offs+j] );
      // detail::block_muladdv( blk, &x[M*colidx[j]], b);
      bop::mvadd(blk, &x[M*colidx[j]], b);
    }
  }

  /// multiply A with vector x of possibly another type and add to b
  template <typename XType, typename BType>
  void pmuladd(const XType x[], BType b[]) const {
    const int nbr = m_spty.size();
#pragma omp parallel for schedule(guided, 64)
    for (int i=0; i<nbr; ++i)
      rowmuladd(i, x, &b[M*i]);
  }

  /// multiply transpose(A) with vector x of possibly another type and add to b
  template <typename XType, typename BType>
  void ptransmuladd(const XType x[], BType b[]) const {
    const int nbr = m_spty.size();
#pragma omp parallel
    {
      // thread-private buffer needed because write acces to b is not
      // disjoint for threads
      SVector<M,BType> tmp;
#pragma omp for
      for (int i=0; i<nbr; ++i) {
        const int nc = m_spty.size(i);
        const uint *colidx = m_spty.first(i);
        const uint offs = m_spty.offset(i);
        for (int j=0; j<nc; ++j) {
          const Block &blk( m_blocks[offs+j] );
          BType *bp = &b[M*colidx[j]];
          memcpy(bp, &tmp[0], M*sizeof(BType));
          detail::block_tmuladdv( blk, &x[M*i], tmp.pointer() );
          for (int k=0; k<M; ++k)
            omp_atomic_add(bp[k], tmp[k]);
        }
      }
    }
  }

protected:

  /// block connectivity
  ConnectMap m_spty;

  /// blocks in aligned storage if block size permits alignment
  BlockArray m_blocks;

  /// symmetric scalar-variable (not block) permutations
  Indices m_perm, m_iperm;

  /// number of (external) block columns
  uint m_nbcol;
};

/// sparse dot product between rows of block matrices, r = a(arow)^T b(brow)
template <typename FloatType, int M>
void spdot(const SparseBlockMatrix<FloatType,M> &a, uint arow,
           const SparseBlockMatrix<FloatType,M> &b, uint brow,
           SMatrix<M,M,FloatType> &r)
{
  const ConnectMap &amap(a.sparsity());
  const ConnectMap &bmap(b.sparsity());

  const uint na = amap.size(arow);
  const uint nb = bmap.size(brow);
  const uint *ca = amap.first(arow);
  const uint *cb = bmap.first(brow);
  const uint pa = amap.offset(arow);
  const uint pb = bmap.offset(brow);

  r = FloatType(0);
  uint ia(0), ib(0);
  while (ia < na and ib < nb) {
    uint acol = ca[ia];
    uint bcol = cb[ib];
    if (acol < bcol) {
      ++ia;
    } else if (acol > bcol) {
      ++ib;
    } else {
      detail::block_mmadd<FloatType,M>(a[pa+ia], b[pb+ib], r);
      ++ia;
      ++ib;
    }
  }
}

#endif // SPARSEBLOCKMATRIX_H
