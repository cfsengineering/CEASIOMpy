
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

#ifndef GENUA_BENZISPAI_H
#define GENUA_BENZISPAI_H

#include "sparseblockmatrix.h"
#include "sparseblock.h"

#ifdef HAVE_TBB
#include <tbb/flow_graph.h>
#endif

//#ifndef NDEBUG
#include <iostream>
using namespace std;
//#endif

/** Approximate sparse inverse for nonsymmetric problems.
 *
 *  Generates a sparse approximate inverse of A according to
 * \f[
 *    W^T A Z = D, \quad A^{-1} = Z D^{-1} W^T = \sum_i \frac{z_i w_i^T}{p_i}
 * \f]
 *
 *
 * M. Benzi, M. Tuma:
 * A Sparse Approximate Inverse Preconditioner for nonsymmetric Linear Systems.
 * SIAM J.Sci.Comput. 19(3):968-994, May 1998
 *
 * M. Bollhöfer, Y. Saad:
 * A Factored Approximate Inverse Preconditioner with Pivoting.
 * SIAM J.Matrix Anal. Appl. 23(3):692–705, January 2002
 *
 * \ingroup numerics
 */
template <typename FloatType, int M>
class BenziSparseInverse
{

public:

  typedef SparseBlockMatrix<FloatType,M>    BlockMatrix;
  typedef typename BlockMatrix::Block       Block;
  typedef typename BlockMatrix::BlockArray  BlockArray;


  /// empty construction
  BenziSparseInverse() {}

  /// access factor Z
  const BlockMatrix & zfactor() const {return m_z;}

  /// access factor W^T, i.e. W stored by columns
  const BlockMatrix & wtfactor() const {return m_wt;}

  /// access inverse diagonal block p_i^{-1}
  const Block & invp(uint k) const {return m_invp[k];}

  /// create approximate factorization for A
  bool staticFactor(const BlockMatrix &A) {
    assert(A.nbrows() == A.nbcols());

    // during factorization, the internal block matrices m_z and m_wt
    // store the columns of Z and W; these are aliases for convenience
    BlockMatrix & Z( m_z );
    BlockMatrix & W( m_wt );

    // Todo: determine good static pattern for Z and W
    zwsparsity(A);
    initIdentity(Z);
    initIdentity(W);

    // transpose of A needed for q_j
    BlockMatrix At;
    A.transpose(At);

    const int nbr = A.nbrows();
    m_invp.resize(nbr);
    for (int i=0; i<nbr; ++i) {

      // compute new diagonal block p_i = q_i
      Block pi;
      spdot(A, i, Z, i, pi);

      // invert new p_i and store
      // this may break down if A does not have an ILU
      bool ok = detail::block_inverse<FloatType,M>(pi, m_invp[i]);
      if (not ok) {
        cout << "Inversion failed, i = " << i << " p_i = " << pi << endl;
        return false;
      }

      // these iterations are independent because each iteration only reads
      // inv(p_i) and columns i and j, but nothing else, that is, each
      // column j is updated from i independently of all other columns
      for (int j=i+1; j<nbr; ++j) {

        // update Z_j from Z_i, reads inv(pi)
        staticUpdate(A, Z, i, j);

        // update W_j from W_i, reads inv(pi)
        staticUpdate(At, W, i, j);
      }
    }

    // make m_z store the rows of Z instead; m_wt stores columns of W
    // so it already is W^T as needed for solve()
    m_z.transpose();
    return true;
  }

  /// compute inverse factorization using dynamic drop-tolerance biconjugation
  bool dynamicFactor(const BlockMatrix &A, double relDropTolerance) {
    assert(A.nbrows() == A.nbcols());
    const size_t nbr = A.nbrows();

    // transpose of A needed for q_j
    BlockMatrix At;
    A.transpose(At);

    typedef AlignedAllocator<WorkColumn,64> ColAllocator;
    typedef std::vector<WorkColumn, ColAllocator> ColumnArray;

    // reserve work space
    ColumnArray Z(nbr), W(nbr);
    for (size_t i=0; i<nbr; ++i) {
      size_t nr = A.sparsity().size(i) + At.sparsity().size(i);
      Z[i].initialize( i, nr );
      W[i].initialize( i, nr );
    }

    // determine absolute drop tolerance
    FloatType maxabs(0);
    const size_t nnz = A.nonzero();
    for (size_t i=0; i<nnz; ++i) {
      FloatType r = detail::block_maxabs<FloatType,M>(A[i]);
      maxabs = std::max(maxabs, r);
    }
    FloatType dropTol = relDropTolerance * maxabs;

    // biconjugation loop
    m_invp.resize(nbr);
    for (size_t i=0; i<nbr; ++i) {

      // diagonal block, p_i = q_i
      Block pi;
      Z[i].spdot(A, i, pi);

      bool ok = detail::block_inverse<FloatType,M>(pi, m_invp[i]);
      if (not ok)
        return false;

      // column updates
      for (size_t j=i+1; j<nbr; ++j) {

        Block pj, pip;
        Z[j].spdot(A, i, pj);
        detail::block_mmadd<FloatType,M>(m_invp[i], pj, pip);
        Z[j].update(pip, Z[i], dropTol);

        Block qj;
        W[j].spdot(At, i, qj);
        pip = FloatType(0);
        detail::block_mmadd<FloatType,M>(m_invp[i], qj, pip);
        W[j].update(pip, W[i], dropTol);
      }
    }

    // compress and transfer
    transfer(nbr, Z, W);

    return true;
  }

  bool saadFactorDynamic(const BlockMatrix &A, double relDropTolerance) {
    assert(A.nbrows() == A.nbcols());
    const size_t nbr = A.nbrows();

    // reserve work space
    ColumnArray Z(nbr), W(nbr);
    for (size_t i=0; i<nbr; ++i) {
      size_t nr = 2*A.sparsity().size(i);
      Z[i].initialize( i, nr );
      W[i].initialize( i, nr );
    }

    // determine absolute drop tolerance
    FloatType maxabs(0);
    const size_t nnz = A.nonzero();
    for (size_t i=0; i<nnz; ++i) {
      FloatType r = detail::block_maxabs<FloatType,M>(A[i]);
      maxabs = std::max(maxabs, r);
    }
    FloatType dropTol = relDropTolerance * maxabs;

    // biconjugation loop
    m_invp.resize(nbr);
    for (size_t i=0; i<nbr; ++i) {

      // diagonal block
      Block dii;
      A.mulmul(W[i], Z[i], dii);

      bool ok = detail::block_inverse<FloatType,M>(dii, m_invp[i]);
      if (not ok)
        return false;

      // column updates
      for (size_t j=i+1; j<nbr; ++j) {

        Block pj, qj, pip;

        // pj = ( W_j * A * Z_i )^T
        A.mulmul(W[j], Z[i], pj);
        detail::block_transpose<FloatType,M>(pj);

        // pip = p_ii^{-1} * pip
        detail::block_mmadd<FloatType,M>(m_invp[i], pj, pip);

        // W_j = W_j - W_i * pip
        W[j].update(pip, W[i], dropTol);

        // qj = W_i * A * Z_j
        A.mulmul(W[i], Z[j], qj);
        pip = FloatType(0);

        // pip = p_ii^{-1} * qj
        detail::block_mmadd<FloatType,M>(m_invp[i], qj, pip);

        // Z_j = Z_j - Z_i * pip
        Z[j].update(pip, Z[i], dropTol);
      }
    }

    // compress and transfer
    transfer(nbr, Z, W);

    return true;
  }

#ifdef HAVE_TBB

  bool parallelFactorDynamic(const BlockMatrix &A, double relDropTolerance)
  {
    assert(A.nbrows() == A.nbcols());
    const size_t nbr = A.nbrows();

    // reserve work space
    ColumnArray Z(nbr), W(nbr);
    for (size_t i=0; i<nbr; ++i) {
      size_t nr = 2*A.sparsity().size(i);
      Z[i].initialize( i, nr );
      W[i].initialize( i, nr );
    }

    // determine absolute drop tolerance
    FloatType maxabs(0);
    const size_t nnz = A.nonzero();
    for (size_t i=0; i<nnz; ++i) {
      FloatType r = detail::block_maxabs<FloatType,M>(A[i]);
      maxabs = std::max(maxabs, r);
    }
    FloatType dropTol = relDropTolerance * maxabs;

    using tbb::flow::continue_msg;

    // setup biconjugation graph
    BiconjugationGraph graph;
    for (size_t i=0; i<nbr; ++i) {
      auto headTask = [this, i, dropTol, &A, &Z, &W] (continue_msg) {
        this->saadHeadUpdate(i, A, Z, W, dropTol); };
      auto tailTask = [this, i, dropTol, &A, &Z, &W] (continue_msg) {
        this->saadTailUpdate(i, A, Z, W, dropTol); };
      graph.append(headTask, tailTask);
    }

    // nudge the first head task to go ahead
    graph.run();
    graph.wait();

    // compress and transfer
    transfer(nbr, Z, W);

    return true;
  }

#endif

  /// solve for single right-hand side
  template <typename BType, typename XType>
  void solve(const DVector<BType> &b, DVector<XType> &x) const {
    x = XType(0.0);
    const int nb = m_wt.nbrows();
    const int nv = b.size();

    //#pragma omp parallel
    {
      // thread-private temporaries
      SVector<M,XType> t1, t2;
      DVector<XType> xp(x.size());

      //#pragma omp for
      for (int i=0; i<nb; ++i) {
        t1 = t2 = XType(0);
        m_wt.rowmuladd(i, b, t1);
        detail::block_muladdv(m_invp[i], t1, t2);
        m_z.dotrow(i, t2, xp);
      }

      //#pragma omp for
      for (int i=0; i<nv; ++i) {
        atomic_add( x[i], xp[i] );
      }
    }
  }

private:

  class WorkColumn {
  public:

    WorkColumn() {}

    /// initialize with one diagonal block, reserve space for n nonzeros
    void initialize(uint ii, uint n) {
      m_irows.reserve(n);
      m_blocks.reserve(n);
      m_irows.push_back(ii);
      m_blocks.push_back( Block::identity() );
      assert( avx_aligned(m_blocks[0].pointer()) );
    }

    /// number of nonzero blocks
    uint size() const {return m_irows.size();}

    /// row index for block k
    uint row(uint k) const {return m_irows[k];}

    /// alias for clarity
    uint index(uint k) const {return row(k);}

    /// pointer to first row index
    const uint *first() const {return &m_irows[0];}

    /// access block
    const Block & operator[] (uint k) const {return m_blocks[k];}

    /// make sure that the pattern of b is contained in *this
    void insertPattern(const WorkColumn &b) {
      const uint nb = b.size();
      for (uint i=0; i<nb; ++i) {
        uint c = b.index(i);
        Indices::iterator pos = std::lower_bound(m_irows.begin(), m_irows.end(), c);
        if (pos == m_irows.end() or *pos != c) {
          uint ipos = std::distance(m_irows.begin(), pos);
          m_irows.insert(pos, c);
          m_blocks.insert( m_blocks.begin()+ipos, Block::identity() );
        }
      }
    }

    /// assign or insert block by row index, return local block index
    uint insert(uint r, const Block &b) {
      Indices::iterator pos;
      pos = std::lower_bound(m_irows.begin(), m_irows.end(), r);
      const uint ip = std::distance(m_irows.begin(), pos);
      if (pos != m_irows.end() and *pos == r) {
        m_blocks[ip] += b;
      } else {
        m_irows.insert(pos, r);
        m_blocks.insert(m_blocks.begin()+ip, b);
      }
    }

    /// sparse dot product
    void spdot(const BlockMatrix &a, uint i, Block &p) const {
      const ConnectMap &amap(a.sparsity());
      const uint na = amap.size(i);
      const uint nb = size();
      const uint *ca = amap.first(i);
      const uint pa = amap.offset(i);

      p = FloatType(0);

      // version for unsorted row indices
      for (uint ib=0; ib<nb; ++ib) {
        const uint r = row(ib);
        const uint *pos = std::lower_bound(ca, ca+na, r);
        if (pos != ca+na and *pos == r) {
          uint ia = std::distance(ca, pos);
          detail::block_mmadd<FloatType,M>(a[pa+ia], m_blocks[ib], p);
        }
      }
    }

    /// assumes and maintains sorted column; extends pattern and updates all
    void updateMerge(const Block &pip, const WorkColumn &Zi)
    {
      insertPattern(Zi);
      const uint na = size();
      const uint nb = Zi.size();
      if (na == 0 or nb == 0)
        return;

      uint ia(0), ib(0);
      while (ia < na and ib < nb) {
        const uint adx = index(ia);
        const uint bdx = Zi.index(ib);
        if (adx < bdx) {
          ++ia;
        } else if (adx > bdx) {
          ++ib;
        } else {
          detail::block_mmsub<FloatType,M>(Zi[ib], pip, m_blocks[ia]);
          ++ia; ++ib;
        }
      }
    }

    /// apply biconjugation update to column
    void update(const Block &pip, const WorkColumn &Zi, float dropTol) {
      sortedUpdate(pip, Zi, dropTol);
    }

    /// apply biconjugation update to column
    void sortedUpdate(const Block &pip, const WorkColumn &Zi, float dropTol)
    {
      const uint nb = Zi.size();
      for (uint ib=0; ib<nb; ++ib) {

        // check whether matching row block exists in this column
        const uint brow = Zi.row(ib);
        Indices::iterator pos;
        pos = std::lower_bound(m_irows.begin(), m_irows.end(), brow);
        uint ip = std::distance(m_irows.begin(), pos);
        if (pos == m_irows.end() or *pos != brow) {

          // not present, i.e. Zj[brow] == 0; compute update -pip*Zi anyway
          Block bnew;
          detail::block_mmsub<FloatType,M>(Zi[ib], pip, bnew);

          // check whether new block is large enough to be inserted
          float bnr = detail::block_maxabs<FloatType,M>(bnew);
          if (bnr >= dropTol) {
            m_irows.insert(pos, brow);
            m_blocks.insert(m_blocks.begin()+ip, bnew);
          }

        } else {
          // block is already present, update.
          detail::block_mmsub<FloatType,M>(Zi[ib], pip, m_blocks[ip]);
        }
      }
    }

    /// apply biconjugation update to column
    void unsortedUpdate(const Block &pip, const WorkColumn &Zi, float dropTol)
    {
      // TODO:
      // - check whether row indices are better kept in sorted order
      //   incurs additional cost (memmove) on insertion, but removes the
      //   need for index searches in spdot()
      // - specify a fixed maximum size via reserve() and avoid allocations
      //   by inserting only up to capacity()

      const uint nb = Zi.size();
      for (uint ib=0; ib<nb; ++ib) {

        // check whether matching row block exists in this column
        const uint brow = Zi.row(ib);
        Indices::iterator pos;
        pos = std::find(m_irows.begin(), m_irows.end(), brow);
        if (pos == m_irows.end()) {

          // not present, i.e. Zj[brow] == 0; compute update -pip*Zi anyway
          Block bnew;
          detail::block_mmsub<FloatType,M>(pip, Zi[ib], bnew);

          // check whether new block is large enough to be inserted
          FloatType bnr = detail::block_maxabs<FloatType,M>(bnew);
          if (bnr >= dropTol) {
            m_irows.push_back(brow);
            m_blocks.push_back(bnew);
          }

        } else {

          // block is already present, update.
          uint ipos = std::distance(m_irows.begin(), pos);
          detail::block_mmsub<FloatType,M>(pip, Zi[ib], m_blocks[ipos]);
        }
      }
    }

    /// drop blocks below tolerance
    void drop(FloatType tol) {
      int n = m_irows.size();
      for (int i=(n-1); i>=0; --i) {
        FloatType r = detail::block_maxabs(m_blocks[i]);
        if ( r < tol ) {
          m_irows.erase( m_irows.begin() + i );
          m_blocks.erase( m_blocks.begin() + i );
        }
      }
    }

    /// inject this column into row i of a
    void inject(BlockMatrix &a, uint i) const {
      const uint n = m_irows.size();
      for (uint j=0; j<n; ++j) {
        uint lix = a.lindex(i, row(j));
        assert(lix != NotFound);
        a[lix] = m_blocks[j];
      }
    }

    /// swap columns (pivoting)
    void swap(WorkColumn &a) {
      m_blocks.swap(a.m_blocks);
      m_irows.swap(a.m_irows);
    }

  private:

    BlockArray m_blocks;
    Indices m_irows;
  };

  typedef AlignedAllocator<WorkColumn,64> ColAllocator;
  typedef std::vector<WorkColumn, ColAllocator> ColumnArray;

#ifdef HAVE_TBB

  typedef tbb::flow::continue_node<tbb::flow::continue_msg> UpdateNode;

  class  BiconjugationGraph
  {
  public:

    // FIXME:
    // This will not work because the tail tasks may not have processed
    // previous sweeps when the next head task accesses a front column.
    // use tbb::parallel_do and column blocks with a predecessor count array

    /// append two tasks for one sweep over columns
    template <class HeadFunctor, class TailFunctor>
    void append(HeadFunctor hf, TailFunctor tf) {
      UpdateNode hnode(m_graph, hf);
      UpdateNode tnode(m_graph, tf);
      if (not m_headNodes.empty())
        tbb::flow::make_edge( m_headNodes.back(), hnode );
      tbb::flow::make_edge(hnode, tnode);
      m_headNodes.push_back(hnode);
      m_tailNodes.push_back(tnode);
    }

    /// start processing
    void run() {
      if (not m_headNodes.empty())
        m_headNodes.front().try_put( tbb::flow::continue_msg() );
    }

    /// wait until last task has finished
    void wait() {
      m_graph.wait_for_all();
    }

  private:

    tbb::flow::graph m_graph;
    std::vector<UpdateNode> m_headNodes;
    std::vector<UpdateNode> m_tailNodes;
  };

#endif

private:

  /// determine static sparsity pattern for Z and W
  void zwsparsity(const BlockMatrix &a) {
    ConnectMap at;
    a.sparsity().transpose(a.nbcols(), at);
    ConnectMap zwmap;
    zwmap.merge( a.sparsity(), at );
    zwmap.lowerTriangle();

    m_z = BlockMatrix(zwmap, a.nbcols());
    m_wt = BlockMatrix(zwmap, a.nbcols());
  }

  /// initialize block matrix z as identity matrix
  void initIdentity(BlockMatrix &z) const {
    const size_t nbr = z.nbrows();
    for (size_t i=0; i<nbr; ++i) {
      uint idg = z.lindex(i,i);
      assert(idg != NotFound);
      z[idg] = Block::identity();
    }
  }

  /** Update a row of z in the inner loop.
   *  p_j = A(i) * Z(j)
   *  z_j -= p_j * p_i^-1 * z_i
   */
  void staticUpdate(const BlockMatrix &A, BlockMatrix &Z, uint i, uint j)
  {
    const ConnectMap &map( Z.sparsity() );
    const uint na = map.size(i);
    const uint nb = map.size(j);
    const uint *ca = map.first(i);
    const uint *cb = map.first(j);
    const uint pa = map.offset(i);
    const uint pb = map.offset(j);

    Block pj, pip;

    // pj = dot(A(i), Z(j)) or qj = dot(A^T(i), W(j))
    spdot<FloatType, M>(A, i, Z, j, pj);

    // pip = p_i^-1 * p_j
    detail::block_mmadd<FloatType, M>( m_invp[i], pj, pip );

    uint ia(0), ib(0);
    while (ia < na and ib < nb) {
      uint acol = ca[ia];
      uint bcol = cb[ib];
      if (acol < bcol) {
        ++ia;
      } else if (acol > bcol) {
        ++ib;
      } else {
        // z_j = z[pb+ib], z_i = z[pa+ia]
        // z_j -= pip * z_i
        detail::block_mmsub<FloatType, M>(pip, Z[pa+ia], Z[pb+ib]);
        ++ia;
        ++ib;
      }
    }
  }

  /// update column i+1 once column i is up-to-date, finally, invert diagonal
  bool saadHeadUpdate(size_t i, const BlockMatrix &A,
                      ColumnArray &Z, ColumnArray &W, double dropTol)
  {
    saadUpdate(i, i+1, A, Z, W, dropTol);

    // diagonal block
    Block dii;
    A.mulmul(W[i], Z[i], dii);
    return mminv(dii, m_invp[i]);
  }

  /// update columns i+2 to end once i is up-to-date
  void saadTailUpdate(size_t i, const BlockMatrix &A,
                      ColumnArray &Z, ColumnArray &W, double dropTol) const
  {
    // column updates
    const size_t nbr = A.nbrows();
    for (size_t j=i+2; j<nbr; ++j)
      saadUpdate(i, j, A, Z, W, dropTol);
  }

  /// Saad/Benzi biconjugation column update
  void saadUpdate(size_t i, size_t j, const BlockMatrix &A,
                  ColumnArray &Z, ColumnArray &W,
                  double dropTol) const
  {
    Block pj, qj, pip;

    // pj = ( W_j * A * Z_i )^T
    A.mulmul(W[j], Z[i], pj);
    mmtranspose(pj);

    // pip = p_ii^{-1} * pip
    mmadd(m_invp[i], pj, pip);

    // W_j = W_j - W_i * pip
    W[j].update(pip, W[i], dropTol);

    // qj = W_i * A * Z_j
    A.mulmul(W[i], Z[j], qj);
    pip = FloatType(0);

    // pip = p_ii^{-1} * qj
    mmadd(m_invp[i], qj, pip);

    // Z_j = Z_j - Z_i * pip
    Z[j].update(pip, Z[i], dropTol);
  }

  /// compress and transfer blocks from work columns
  void transfer(size_t nbr, const ColumnArray &Z, const ColumnArray &W)
  {
    ConnectMap zmap, wmap;
    zmap.beginCount(nbr);
    wmap.beginCount(nbr);
    for (size_t i=0; i<nbr; ++i) {
      zmap.incCount(i, Z[i].size());
      wmap.incCount(i, W[i].size());
    }
    zmap.endCount();
    wmap.endCount();
    for (size_t i=0; i<nbr; ++i) {
      zmap.append(i, Z[i].size(), Z[i].first());
      wmap.append(i, W[i].size(), W[i].first());
    }
    zmap.compress();
    wmap.compress();

    m_z  = BlockMatrix(zmap, nbr);
    m_wt = BlockMatrix(wmap, nbr);
    for (size_t i=0; i<nbr; ++i) {
      Z[i].inject( m_z, i );
      W[i].inject( m_wt, i );
    }

    m_z.transpose();
  }

  /// forwarding of block operation
  static force_inline void mmadd(const Block &a, const Block &b, Block &c)
  attr_always_inline
  {
    detail::block_mmadd<FloatType,M>(a, b, c);
  }

  /// forwarding of block operation
  static force_inline void mmsub(const Block &a, const Block &b, Block &c)
  attr_always_inline
  {
    detail::block_mmsub<FloatType,M>(a, b, c);
  }

  /// forwarding of block operation
  static force_inline bool mminv(const Block &a, Block &ai) attr_always_inline
  {
    return detail::block_inverse<FloatType,M>(a, ai);
  }

  /// forwarding of block operation
  static force_inline void mmtranspose(Block &at) attr_always_inline
  {
    detail::block_transpose<FloatType,M>(at);
  }

private:

  /// left factor W^t
  BlockMatrix m_wt;

  /// right factor, Z
  BlockMatrix m_z;

  /// inverse of the diagonal 1/p_i
  BlockArray m_invp;

};

#endif // BENZISPAI_H
