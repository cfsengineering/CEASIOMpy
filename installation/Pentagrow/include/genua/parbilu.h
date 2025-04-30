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

#ifndef GENUA_PARBILU_H
#define GENUA_PARBILU_H

#include "sparseblock.h"
#include "sparseblockmatrix.h"
#include "smallqr.h"

namespace detail {

/// construct CSR pattern for L and CSC pattern for U
void split_sparsity(const ConnectMap &amap,
                    ConnectMap &lmap, ConnectMap &umap);

} // detail

template <typename FloatType, int M>
class ParBILU
{
public:

  typedef SparseBlockMatrix<FloatType,M>    BlockMatrix;
  typedef typename BlockMatrix::Block       Block;
  typedef typename BlockMatrix::BlockArray  BlockArray;
  typedef detail::block_op<FloatType,M>     bop;

  /// fill the values of A which form the standard initial guess
  void initStandard(const BlockMatrix &A) {
    assert(A.nbrows() == A.nbcols());
    extractPattern(A);
    insertValues(A);
  }

  /// copy A into internal storage initialized from A with the same sparsity
  void insertValues(const BlockMatrix &A) {

    // compute row and column scalings
    diagonalScaling(A);

    // copy blocks from A and store diagonal blocks
    const ConnectMap &amap(A.sparsity());
    const size_t nbr = amap.size();
    m_lixdiag.resize(nbr);
    for (size_t i=0; i<nbr; ++i) {
      const uint nj = amap.size(i);
      const uint *pcol = amap.first(i);
      const uint ap = amap.offset(i);
      for (uint k=0; k<nj; ++k) {
        uint j = pcol[k];
        if (j < i) {
          uint tix = m_lower.lindex(i, j);
          m_lower[tix] = A[ap+k];
          scaleBlock(i, j, m_lower[tix]);
        } else {
          uint tix = m_upper.lindex(j, i);
          m_upper[tix] = A[ap+k];
          scaleBlock(i, j, m_upper[tix]);
          if ( hint_unlikely(i == j) ) {
            m_lixdiag[i] = tix;
          }
        }
      }
    }
  }

  /// perform n parallel sweeps to update the factors
  void factorSweep(const BlockMatrix &A, size_t n) {

    // this is the algorithm (2) from
    // FINE-GRAINED PARALLEL INCOMPLETE LU FACTORIZATION
    // EDMOND CHOW AND AFTAB PATEL,
    // SIAM J. SCI. COMPUT 37(2)-C169–C193

    const size_t nbr = m_upper.nbrows();
    m_udinv.resize(nbr);

    const size_t nb = m_index.size();

#pragma omp parallel
    {
      Block aij;
      for (size_t iswp=0; iswp<n; ++iswp) {

#pragma omp for schedule(dynamic, 1024)
        for (size_t ibl=0; ibl<nb; ++ibl) {
          const BlockIndex &bix( m_index[ibl] );
          const uint i = bix.bi;
          const uint j = bix.bj;
          aij = A[bix.alix];
          scaleBlock(i, j, aij);
          if (bix.isUpper()) {
            Block &uij = m_upper[bix.lix];
            uij = aij;
            updateBlock(i, j, i, uij);
          } else {
            Block &lij = m_lower[bix.lix];
            lij = aij;
            updateBlock(i, j, j, lij);
            ujjsolve(j, lij);
          }
        }

      } // end sweep

      // store inverse of U(j,j)
#pragma omp for schedule(static,1024)
      for (size_t i=0; i<nbr; ++i)
        invertBlock( m_upper[m_lixdiag[i]], m_udinv[i] );

    } // end parallel

  }

  /// solve with a single rhs
  void lusolve(const DVector<FloatType> &b, DVector<FloatType> &x) const {

    const ConnectMap &lmap( m_lower.sparsity() );
    const ConnectMap &umap( m_upper.sparsity() );

    // apply row scaling to b, x <- R*b
    const size_t nbr = m_upper.nbrows();
    for (size_t i=0; i<(M*nbr); ++i)
      x[i] = m_scale[i] * b[i];

    // forward substitution; diagonal of L is identity
    // and is not stored; lmap contains only off-diagonal blocks
    for (size_t i=1; i<nbr; ++i) {
      FloatType *xi = &x[M*i];
      const uint nb = lmap.size(i);
      const uint *idx = lmap.first(i);
      const uint p = lmap.offset(i);
      for (uint k=0; k<nb; ++k)
        bop::mvsub(m_lower[p+k], &x[M*idx[k]], xi);
    }

    // backward substitution - solve with diagonal block, which is
    // the last block in each column of U
    for (size_t ti=0; ti<nbr; ++ti) {
      const uint i = nbr-1-ti;
      FloatType *xi = &x[M*i];
      FloatType tmp[M];
      std::fill(tmp, tmp+M, FloatType(0));
      bop::mvadd(m_udinv[i], xi, tmp);
      std::copy(tmp, tmp+M, xi);
      const uint nb = umap.size(i);
      if (nb < 2)
        continue;
      const uint *idx = umap.first(i);
      const uint p = umap.offset(i);
      for (uint k=0; k<nb-1; ++k)
        bop::mvsub(m_upper[p+k], xi, &x[M*idx[k]]);
    }

    // apply column scaling
    for (size_t i=0; i<(M*nbr); ++i)
      x[i] = std::fabs(m_scale[i]) * x[i];
  }

  /// access lower factor stored in row-major order
  const BlockMatrix &lower() const { return m_lower; }

  /// access lower factor stored in row-major order
  const BlockMatrix &upper() const { return m_upper; }

private:

  /// scale block 'a' using stored diagonal scaling matrices
  void scaleBlock(uint i, uint j, Block &a) const {
    bop::scale( &m_scale[M*i], &m_scale[M*j], a );
  }

  /// inner loop of the block update - most work is here
  void updateBlock(uint i, uint j, uint m, Block &lij) const {
    const ConnectMap &amap(m_lower.sparsity());
    const ConnectMap &bmap(m_upper.sparsity());

    const uint na = amap.size(i);
    const uint nb = bmap.size(j);
    const uint *ca = amap.first(i);
    const uint *cb = bmap.first(j);
    const uint pa = amap.offset(i);
    const uint pb = bmap.offset(j);

    // L_{ij} -= \sum_{k=0}^m L_{ik}*U_{kj}
    // looks at row i of L and column j of U

    uint ia(0), ib(0);
    while ((ia < na) and (ib < nb)) {
      uint acol = ca[ia];
      if (acol >= m)
        return;
      uint bcol = cb[ib];
      if (acol < bcol) {
        ++ia;
      } else if (acol > bcol) {
        ++ib;
      } else {
        bop::mmsub(m_lower[pa+ia], m_upper[pb+ib], lij);
        ++ia;
        ++ib;
      }
    }
  }

  /// Lij <- Ujj^-1 * Lij
  void ujjsolve(uint j, Block &lij) const {
    const Block & Ujj( m_upper[m_lixdiag[j]] );
    Block Uinv;
    invertBlock( Ujj, Uinv );
    lij = lij * Uinv;
  }

  /// invert block, perturb diagonal if necessary
  void invertBlock(const Block &a, Block &ai) const {
    Block qrf;
    FloatType tau[M];
    factorBlock(a, qrf, tau);
    ai = Block::identity();
    for (int j=0; j<M; ++j)
      qrsolve<M,M>(qrf.pointer(), tau, ai.colpointer(j));
  }

  /// QR-factor a block; perturb diagonal until successful
  void factorBlock(const Block &a, Block &qrf, FloatType tau[]) const {
    qrf = a;
    FloatType deps = std::sqrt( std::numeric_limits<FloatType>::epsilon() );
    bool ok = qr<M,M>(qrf.pointer(), tau);

    // if not invertible, modify its diagonal
    // with increasingly large perturbations until it is
    while (not ok) {
      qrf = a;
      for (int i=0; i<M; ++i)
        qrf(i,i) += std::copysign(deps, a(i,i));
      ok = qr<M,M>(qrf.pointer(), tau);
      deps *= 4;
    }
  }

  /// find sparsity pattern of L and U
  void extractPattern(const BlockMatrix &A) {

    // TODO
    // - Introduce level k for optional ILU(k) - important!
    ConnectMap lmap, umap;
    detail::split_sparsity(A.sparsity(), lmap, umap);
    m_lower.assign(lmap, A.nbcols());
    m_upper.assign(umap, A.nbcols());

    // generate block index pattern in elimination order
    const ConnectMap &amap(A.sparsity());
    const size_t nbr = A.nbrows();
    m_index.resize(amap.nonzero());
    for (size_t i=0; i<nbr; ++i) {
      const uint nc = amap.size(i);
      const uint *pcol = amap.first(i);
      const uint roff = amap.offset(i);
      for (uint k=0; k<nc; ++k) {
        uint j = pcol[k];
        BlockIndex &bix( m_index[roff+k] );
        bix.bi = i;
        bix.bj = j;
        bix.alix = roff+k;
        bix.lix = bix.isUpper() ? umap.lindex(j,i) : lmap.lindex(i,j);
      }
    }
  }

  /// determine diagonal scalings
  void diagonalScaling(const BlockMatrix &A) {

    // m_scale is the scaling which makes the diagonal of A unity
    // m_iscale is the inverse

    const size_t nbr = A.nbrows();
    m_scale.allocate(nbr*M);

    for (size_t i=0; i<nbr; ++i) {
      const uint lii = A.lindex(i,i);
      FloatType *ps = &m_scale[M*i];
      if (lii != NotFound) {
        const Block & aii = A[lii];
        for (int j=0; j<M; ++j) {
          FloatType d = aii(j,j);
          if (d != 0) {
            FloatType sd = std::sqrt(std::fabs(d));
            ps[j] = copysign(FloatType(1)/sd, d);
          } else {
            ps[j] = FloatType(1);
          }
        }
      } else {
        std::fill(ps, ps+M, FloatType(1));
      }
    }
  }

private:

  /// stores index of a single block
  struct BlockIndex {
    uint bi, bj;
    uint lix;
    uint alix;
    bool isUpper() const {return (bi <= bj);}
  };
  typedef std::vector<BlockIndex> BIndexArray;

  /// lower triangle L stored in row-major, CSR format
  BlockMatrix m_lower;

  /// upper triangle U stored in column-major, CSC format
  BlockMatrix m_upper;

  /// inverse of diagonals of U
  BlockArray m_udinv;

  /// block indices sorted in elimination order
  BIndexArray m_index;

  /// diagonal scaling matrices such that diag(s)*A*diag(abs(s)) has unit diagonal
  DVector<FloatType> m_scale;

  /// linear indices of diagonal blocks of U
  Indices m_lixdiag;
};

#endif // PARBILU_H
