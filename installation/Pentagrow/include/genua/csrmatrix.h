
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

#ifndef GENUA_CSRMATRIX_H
#define GENUA_CSRMATRIX_H

#include "forward.h"
#include "connectmap.h"
#include "dvector.h"
#include "dmatrix.h"
#include "xmlelement.h"
#include "svector.h"
#include "algo.h"
#include "ffanode.h"
#include "sparsebuilder.h"
#include "atomicop.h"
#include "typecode.h"
#ifdef HAVE_EIGEN
#include <eeigen/SparseCore>
#endif
#include <boost/static_assert.hpp>
#include <fstream>

namespace detail
{

  template <typename FloatType>
  inline int32_t float_type_marker()
  {
    return sizeof(FloatType);
  }

  template <>
  inline int32_t float_type_marker<std::complex<float>>()
  {
    return -8;
  }

  template <>
  inline int32_t float_type_marker<std::complex<double>>()
  {
    return -16;
  }
}

/** Compressed-row sparse matrix.

  Generic CSR matrix with N components per row. N equal one yields
  a standard CSR matrix; larger N are used to represent a sparse
  matrix where N consecutive rows have the same sparsity pattern.

  N != 1 can be used to represent sparse block matrices or gradient
  stencils, but note that some member functions do not make sense for
  N != 1, as they only are defined for plain element matrices.


  \ingroup numerics
  \sa ConnectMap
  */
template <class Type, int N = 1>
class CsrMatrix
{
public:
  /// empty matrix
  CsrMatrix(uint nr = 0, uint nc = 0) : nrow(nr), ncol(nc) {}

  /// construct matrix from sparsity
  CsrMatrix(const ConnectMap &s, uint nc = 0) : spty(s)
  {
    nrow = s.size();
    ncol = std::max(nc, s.maxcolindex() + 1);
    val.resize(N * spty.nonzero());
  }

  /// construct matrix from sparsity
  CsrMatrix(ConnectMap &&s, uint nc = 0) : spty(s)
  {
    nrow = s.size();
    ncol = std::max(nc, s.maxcolindex() + 1);
    val.resize(N * spty.nonzero());
  }

  /// construct from sparsity and value vector
  CsrMatrix(const ConnectMap &s, const DVector<Type> &v, uint nc = 0)
      : spty(s), val(v)
  {
    nrow = s.size();
    ncol = std::max(nc, s.maxcolindex() + 1);
    assert(val.size() == N * spty.nonzero());
  }

  /// construct from sparsity and value vector
  CsrMatrix(ConnectMap &&s, DVector<Type> &&v, uint nc = 0) : spty(s), val(v)
  {
    nrow = s.size();
    ncol = std::max(nc, s.maxcolindex() + 1);
    assert(val.size() == N * spty.nonzero());
  }

  /// construct from sparse builder
  CsrMatrix(uint nr, uint nc, const SparseBuilder<Type> &builder)
  {
    assign(nr, nc, builder);
  }

  /// assign values from sorted builder
  void assign(uint nr, uint nc, const SparseBuilder<Type> &builder)
  {
    BOOST_STATIC_ASSERT(N == 1);
    nrow = nr;
    ncol = nc;
    spty.assign(nr, builder.begin(), builder.end());
    const size_t n = builder.size();
    val.resize(n);
    for (size_t i = 0; i < n; ++i)
      val[i] = builder[i].value();
  }

  /// incremental assembly: append a row with column indices and values
  void appendRow(uint n, const uint colind[], const Type v[])
  {
    // colind MUST be sorted!
    spty.appendRow(colind, colind + n);
    val.insert(val.end(), v, v + (n * N));
  }

  /// number of sparse rows
  uint nrows() const { return spty.size(); }

  /// number of sparse columns
  uint ncols() const { return ncol; }

  /// number of nonzero values (vectors)
  uint nonzero() const { return spty.nonzero(); }

  /// number of nonzero values in row kr
  uint ncols(uint kr) const { return spty.size(kr); }

  /// linear index offset for row kr
  uint offset(uint kr) const { return spty.offset(kr); }

  /// find linear index for (i,j)
  uint lindex(uint i, uint j) const { return spty.lindex(i, j); }

  /// find linear index for (i,j) if upper triangular symmetric part is stored
  uint uptrilix(uint i, uint j) const { return spty.uptrilix(i, j); }

  /// find linear index for (i,j) if lower triangular symmetric part is stored
  uint lotrilix(uint i, uint j) const { return spty.lotrilix(i, j); }

  /// access sparsity pattern directly
  const ConnectMap &sparsity() const { return spty; }

  /// access value pointer directly
  const Type *pointer() const { return val.pointer(); }

  /// access value pointer directly
  Type *pointer() { return val.pointer(); }

  /// access array of nonzero values
  const DVector<Type> &nzarray() const { return val; }

  /// set all values to t
  CsrMatrix<Type, N> &operator=(const Type &t)
  {
    val = t;
    return *this;
  }

  /// access value by linear index (N == 1)
  const Type &operator[](uint lix) const
  {
    BOOST_STATIC_ASSERT(N == 1);
    return val[lix];
  }

  /// access value by linear index (N == 1)
  Type &operator[](uint lix)
  {
    BOOST_STATIC_ASSERT(N == 1);
    return val[lix];
  }

  /// access nonzero value by row/column
  const Type &operator()(uint ki, uint kj) const
  {
    BOOST_STATIC_ASSERT(N == 1);
    uint lix = lindex(ki, kj);
    assert(lix < val.size());
    return val[lix];
  }

  /// access nonzero value by row/column
  Type &operator()(uint ki, uint kj)
  {
    BOOST_STATIC_ASSERT(N == 1);
    uint lix = lindex(ki, kj);
    assert(lix < val.size());
    return val[lix];
  }

  /// access component k of value by linear index
  const Type &value(uint lix, uint k) const
  {
    assert(k < N);
    return val[N * lix + k];
  }

  /// access component k of value by linear index
  Type &value(uint lix, uint k)
  {
    assert(k < N);
    return val[N * lix + k];
  }

  /// fill dg with the diagonal elements of *this
  void diagonal(DVector<Type> &dg) const
  {
    BOOST_STATIC_ASSERT(N == 1);
    const size_t n = nrows();
    dg.allocate(nrows());
    for (size_t i = 0; i < n; ++i)
    {
      const uint lix = lindex(i, i);
      dg[i] = (lix != NotFound) ? val[lix] : Type(0);
    }
  }

  /// return the trace, optionally of the absolute values
  Type trace(bool absValue = false) const
  {
    BOOST_STATIC_ASSERT(N == 1);
    const size_t n = nrows();
    Type t(0);
    if (not absValue)
    {
      for (size_t i = 0; i < n; ++i)
      {
        const uint lix = lindex(i, i);
        t += (lix != NotFound) ? val[lix] : Type(0);
      }
    }
    else
    {
      for (size_t i = 0; i < n; ++i)
      {
        const uint lix = lindex(i, i);
        t += (lix != NotFound) ? std::abs(val[lix]) : Type(0);
      }
    }
    return t;
  }

  /// compute row sum
  Type rowSum(uint k) const
  {
    const uint nnz = sparsity().size(k);
    const Type *prow = &val[sparsity().offset(k)];
    Type rsum(0);
    for (uint j = 0; j < nnz; ++j)
      rsum += prow[j];
    return rsum;
  }

  /// atomically add to value (lix,k)
  void atomicAdd(uint lix, uint k, Type t)
  {
    assert(k < N);
    omp_atomic_add(val[N * lix + k], t);
  }

  /// atomically add to value lix, for the case N == 1
  void atomicAdd(uint lix, Type t)
  {
    BOOST_STATIC_ASSERT(N == 1);
    omp_atomic_add(val[lix], t);
  }

  /// add element matrix using row- and column index mapping
  template <int M>
  void assemble(const Indices &rmap, const Indices &cmap, const uint *vi,
                const SMatrix<M, M, Type> &Me)
  {
    uint row[M], col[M];
    for (int i = 0; i < M; ++i)
    {
      row[i] = rmap[vi[i]];
      col[i] = cmap[vi[i]];
    }
    for (int i = 0; i < M; ++i)
    {
      if (row[i] != NotFound)
      {
        for (int j = 0; j < M; ++j)
        {
          const uint lix = lindex(row[i], col[j]);
          if (lix != NotFound)
            atomicAdd(lix, Me(i, j));
        }
      }
    }
  }

  /// b <- A*x + beta*b : multiply with x, add result to b, low level form
  template <class AType>
  void muladd(const AType a[], AType b[], AType beta = AType(1)) const
  {
    const int nr = spty.size();
#pragma omp parallel for
    for (int i = 0; i < nr; ++i)
    {
      CPHINT_SIMD_LOOP
      for (int k = 0; k < N; ++k)
        b[i * N + k] *= beta;
      const int ncol = spty.size(i);
      if (ncol == 0)
        continue;
      const uint *col = spty.first(i);
      const Type *row = &val[N * spty.offset(i)];
      for (int j = 0; j < ncol; ++j)
      {
        AType aj = a[col[j]];
        CPHINT_SIMD_LOOP
        for (int k = 0; k < N; ++k)
          b[i * N + k] += row[j * N + k] * aj;
      }
    }
  }

  /// multiply with a, add result to b, low level form
  template <class AType>
  void muladd(size_t acols, size_t lda, const AType a[], size_t ldb,
              AType b[]) const
  {
    const int nr = spty.size();
#pragma omp parallel for schedule(static, 128)
    for (int i = 0; i < nr; ++i)
    {
      const int nzcol = spty.size(i);
      if (nzcol == 0)
        continue;
      const uint *col = spty.first(i);
      const Type *row = &val[N * spty.offset(i)];
      for (int j = 0; j < nzcol; ++j)
      {
        for (size_t jc = 0; jc < acols; ++jc)
        {
          AType aj = a[jc * lda + col[j]];
          CPHINT_SIMD_LOOP
          for (int k = 0; k < N; ++k)
            b[jc * ldb + i * N + k] += row[j * N + k] * aj;
        }
      }
    }
  }

  /// multiply row i with a, set b, low level form
  template <class AType>
  void muladdRow(uint i, const AType a[], AType b[]) const
  {
    const int ncol = spty.size(i);
    const uint *col = spty.first(i);
    const Type *row = &val[N * spty.offset(i)];
    for (int j = 0; j < ncol; ++j)
    {
      AType aj = a[col[j]];
      CPHINT_SIMD_LOOP
      for (int k = 0; k < N; ++k)
        b[k] += row[j * N + k] * aj;
    }
  }

  /// multiply row i with a, set b, high level form
  template <class AType>
  void muladdRow(uint i, const DVector<AType> &a, SVector<N, AType> &b) const
  {
    muladdRow(i, a.pointer(), b.pointer());
  }

  /// multiply with x, set b, low level form
  template <class AType>
  void multiply(const AType a[], AType b[]) const
  {
    const int nr = spty.size();
#pragma omp parallel for schedule(static, 128)
    for (int i = 0; i < nr; ++i)
    {
      CPHINT_SIMD_LOOP
      for (int k = 0; k < N; ++k) // zero out before accumulation
        b[i * N + k] = AType(0);
      const int ncol = spty.size(i);
      if (ncol == 0)
        continue;
      const uint *col = spty.first(i);
      const Type *row = &val[N * spty.offset(i)];
      for (int j = 0; j < ncol; ++j)
      {
        AType aj = a[col[j]];
        CPHINT_SIMD_LOOP
        for (int k = 0; k < N; ++k)
          b[i * N + k] += row[j * N + k] * aj;
      }
    }
  }

  /// multiply with a, general low level form
  template <class AType>
  void multiply(size_t acols, size_t lda, const AType a[], size_t ldb,
                AType b[]) const
  {
    const int nr = spty.size();
#pragma omp parallel for schedule(static, 128)
    for (int i = 0; i < nr; ++i)
    {
      // zero out b before accumulation
      for (size_t jc = 0; jc < acols; ++jc)
      {
        CPHINT_SIMD_LOOP
        for (int k = 0; k < N; ++k)
          b[(jc * ldb + i) * N + k] = AType(0);
      }
      const int nzcol = spty.size(i);
      if (nzcol == 0)
        continue;
      const uint *col = spty.first(i);
      const Type *row = &val[N * spty.offset(i)];
      for (int j = 0; j < nzcol; ++j)
      {
        for (size_t jc = 0; jc < acols; ++jc)
        {
          AType aj = a[jc * lda + col[j]];
          CPHINT_SIMD_LOOP
          for (int k = 0; k < N; ++k)
            b[(jc * ldb + i) * N + k] += row[j * N + k] * aj;
        }
      }
    }
  }

  /// multiply with x, add result to b, high level form
  template <class AType>
  void muladd(const DVector<AType> &a,
              DVector<AType> &b, AType beta = AType(1)) const
  {
    assert(b.size() >= N * nrows());
    this->muladd(a.pointer(), b.pointer(), beta);
  }

  /// multiply with x, add result to b, high level form
  template <class AType>
  void muladd(const DMatrix<AType> &a, DMatrix<AType> &b) const
  {
    assert(a.ncols() == b.ncols());
    assert(b.nrows() >= N * nrows());
    this->muladd(a.ncols(), a.nrows(), a.pointer(), b.nrows(), b.pointer());
  }

  /// multiply with x, set b, high level form
  template <class AType>
  void multiply(const DVector<AType> &a, DVector<AType> &b) const
  {
    assert(b.size() >= N * nrows());
    this->multiply(a.pointer(), b.pointer());
  }

  /// multiply with x, set b, high level form
  template <class AType>
  void multiply(const DMatrix<AType> &a, DMatrix<AType> &b) const
  {
    assert(b.size() >= N * nrows());
    this->multiply(a.ncols(), a.ldim(), a.pointer(), b.ldim(), b.pointer());
  }

  /// b += a^T * this = this^T * a, multiply transpose with a, add to b, low
  /// level form
  template <class AType>
  void muladdTransposed(const AType a[], AType b[]) const
  {
    this->muladdTransposed(AType(1), a, b);
  }

  template <class AType>
  void muladdTransposed(AType alpha, const AType a[], AType b[]) const
  {
    const int nr = nrows();
#pragma omp parallel for schedule(static, 256)
    for (int i = 0; i < nr; ++i)
    {
      const int ncol = spty.size(i);
      const uint *col = spty.first(i);
      const Type *row = &val[N * spty.offset(i)];
      const AType ai = alpha * a[i];
      for (int j = 0; j < ncol; ++j)
      {
        AType *bj = &b[N * col[j]];
        for (int k = 0; k < N; ++k)
          omp_atomic_add(bj[k], ai * row[j * N + k]);
      }
    }
  }

  /// b += alpha * a^T * this = alpha * this^T * a, multiply transpose with a, add to b
  template <class AType>
  void muladdTransposed(AType alpha, const DVector<AType> &a, DVector<AType> &b) const
  {
    assert(a.size() >= nrows());
    assert(b.size() >= N * ncols());
    muladdTransposed(alpha, a.pointer(), b.pointer());
  }

  /// b += a^T * this = this^T * a, multiply transpose with a, add to b
  template <class AType>
  void muladdTransposed(const DVector<AType> &a, DVector<AType> &b) const
  {
    assert(a.size() >= nrows());
    assert(b.size() >= N * ncols());
    muladdTransposed(a.pointer(), b.pointer());
  }

  /// b = a^T * this = this^T * a, multiply transpose with a, set b, low level
  /// form
  template <class AType>
  void multiplyTransposed(const AType a[], AType b[]) const
  {
    // zero out b first because we will use b[i] += ...
    const int nc = ncols();
    std::fill(b, b + nc * N, AType(0));
    muladdTransposed(a, b);
  }

  /// b = a^T * this = this^T * a, multiply transpose with a, set b
  template <class AType>
  void multiplyTransposed(const DVector<AType> &a, DVector<AType> &b) const
  {
    assert(a.size() >= nrows());
    assert(b.size() >= N * ncols());
    multiplyTransposed(a.pointer(), b.pointer());
  }

  /// scale matrix rows
  void scale(const DVector<Type> &a)
  {
    assert(a.size() >= nrows());
    const int nr = nrows();
#pragma omp parallel for
    for (int i = 0; i < nr; ++i)
    {
      const int ncol = spty.size(i);
      const int offs = spty.offset(i);
      for (int j = 0; j < ncol; ++j)
      {
        CPHINT_SIMD_LOOP
        for (int k = 0; k < N; ++k)
          val[(offs + j) * N + k] *= a[i];
      }
    }
  }

  /// set complete row to t
  void setRow(uint kr, Type t)
  {
    const int nj = spty.size(kr);
    const int offs = spty.offset(kr);
    for (int i = 0; i < nj; ++i)
      CPHINT_SIMD_LOOP
    for (int k = 0; k < N; ++k)
      val[(offs + i) * N + k] = t;
  }

  /// scale a row with factor f
  void scaleRow(uint kr, Type f)
  {
    const int nj = spty.size(kr);
    const int offs = spty.offset(kr);
    for (int i = 0; i < nj; ++i)
      CPHINT_SIMD_LOOP
    for (int k = 0; k < N; ++k)
      val[(offs + i) * N + k] *= f;
  }

  /// scale a column with factor f
  void scaleColumn(uint kc, Type f)
  {
    uint nr = nrows();
    for (uint ii = 0; ii < nr; ++ii)
    {
      uint lix = lindex(ii, kc);
      if (lix != NotFound)
      {
        CPHINT_SIMD_LOOP
        for (int k = 0; k < N; ++k)
          val[lix * N + k] *= f;
      }
    }
  }

  /// add row b to row a, assuming compatibility
  void addRow(uint b, uint a, Type f = Type(1.0))
  {
    assert(b != a);
    const int ncol = spty.size(b);
    const int boff = spty.offset(b);
    const uint *jc = spty.first(b);
    for (int i = 0; i < ncol; ++i)
    {
      uint blix = boff + i;
      uint alix = lindex(a, jc[i]);
      assert(alix != NotFound);
      CPHINT_SIMD_LOOP
      for (int k = 0; k < N; ++k)
        value(alix, k) += f * value(blix, k);
    }
  }

  /// modify by adding lambda to diagonal
  void addDiagonal(Type lambda)
  {
    BOOST_STATIC_ASSERT(N == 1);
    const int n = spty.size();
    for (int i = 0; i < n; ++i)
    {
      uint lix = lindex(i, i);
      if (lix != NotFound)
        val[lix] += lambda;
    }
  }

  /// modify by increasing magnitude of diagonal element
  void signaddDiagonalRel(Type lambda, uint offs)
  {
    BOOST_STATIC_ASSERT(N == 1);
    const int n = spty.size();
    Type dmax(0.0);
    for (int j = offs; j < n; ++j)
    {
      uint lix = lindex(j, j);
      if (lix != NotFound)
      {
        if (fabs(val[lix]) > dmax)
          dmax = fabs(val[lix]);
      }
    }

    for (int i = offs; i < n; ++i)
    {
      uint lix = lindex(i, i);
      if (lix != NotFound)
      {
        Type curval = val[lix];
        val[lix] += sign(curval) * lambda * dmax;
      }
    }
  }

  /// modify by increasing magnitude of diagonal element
  void signaddDiagonal(Type lambda, uint offs)
  {
    BOOST_STATIC_ASSERT(N == 1);
    const int n = spty.size();
    for (int i = offs; i < n; ++i)
    {
      uint lix = lindex(i, i);
      if (lix != NotFound)
      {
        Type curval = val[lix];
        val[lix] += sign(curval) * lambda;
      }
    }
  }

  /// modify by increasing magnitude of diagonal element
  void multDiagonal(Type lambda, uint offs)
  {
    BOOST_STATIC_ASSERT(N == 1);
    const int n = spty.size();
    for (int i = offs; i < n; ++i)
    {
      uint lix = lindex(i, i);
      if (lix != NotFound)
      {
        val[lix] *= lambda;
      }
    }
  }

  /// modify Jacobian by making diagonal terms more dominant
  void domDiagonal(Type k, uint noff)
  {
    BOOST_STATIC_ASSERT(N == 1);
    const int n = spty.size();
    uint nf(0), nnf(0);
    for (int i = noff; i < n; ++i)
    {
      Type jii(0.0);
      uint lix = lindex(i, i);
      if (lix != NotFound)
      {
        jii = val[lix];
        ++nf;
      }
      scaleRow(i, k);
      scaleColumn(i, k);
      if (lix == NotFound)
      {
        ++nnf;
      }
      if (lix != NotFound)
      {
        val[lix] = jii;
      }
    }
    std::cout << "nfound = " << nf << " nnotfound = " << nnf << std::endl;
  }

  /// modify Jacobian by making three-diagonal terms more dominant
  void dom3Diagonal(Type k)
  {
    BOOST_STATIC_ASSERT(N == 1);
    const int n = spty.size();
    for (int i = 0; i < n; ++i)
    {
      Type jii0(0.0), jii1(0.0), jii2(0.0);
      uint lix0 = lindex(i, i - 1);
      uint lix1 = lindex(i, i);
      uint lix2 = lindex(i, i + 1);
      if (lix0 != NotFound)
      {
        jii0 = val[lix0];
      }
      if (lix1 != NotFound)
      {
        jii1 = val[lix1];
      }
      if (lix2 != NotFound)
      {
        jii2 = val[lix2];
      }

      scaleRow(i, k);

      if (lix0 != NotFound)
      {
        val[lix0] = jii0;
      }
      if (lix1 != NotFound)
      {
        val[lix1] = jii1;
      }
      if (lix2 != NotFound)
      {
        val[lix2] = jii2;
      }
    }
  }

  /// modify by increasing magnitude of diagonal element
  void signadd3Diagonal(Type lambda, uint offs)
  {
    BOOST_STATIC_ASSERT(N == 1);
    const int n = spty.size();
    for (int i = 0; i < n; ++i)
    {
      uint lix = lindex(i, i);
      if (lix != NotFound)
      {
        Type curval = val[lix];
        val[lix] += sign(curval) * lambda;
      }
    }

    for (int i = offs; i < n - 1; ++i)
    {
      uint lixu = lindex(i, i + 1);
      uint lixl = lindex(i + 1, i);
      if (lixu != NotFound)
      {
        Type curval = val[lixu];
        val[lixu] += sign(curval) * lambda;
      }

      if (lixl != NotFound)
      {
        Type curval = val[lixl];
        val[lixl] += sign(curval) * lambda;
      }
    }
  }

  /// give uniform magnitude of diagonal elements
  void signuniDiagonal(Type lambda)
  {
    BOOST_STATIC_ASSERT(N == 1);
    const int n = spty.size();
    for (int i = 0; i < n; ++i)
    {
      uint lix = lindex(i, i);
      if (lix != NotFound)
      {
        Type curval = val[lix];
        Type addval = sign(curval) * lambda - curval;
        val[lix] += addval;
      }
    }
  }

  /// find largest magnitude of diagonal element
  Type maxmagDiagonal() const
  {
    BOOST_STATIC_ASSERT(N == 1);
    Type dmax = 0.0;
    const int n = spty.size();
    for (int i = 0; i < n; ++i)
    {
      uint lix = lindex(i, i);
      if (lix != NotFound)
        dmax = std::max(dmax, std::fabs(val[lix]));
    }
    return dmax;
  }

  /// compute trace of matrix
  void trace(Type &lambda, uint offs)
  {
    Type t(0.0);
    const int n = spty.size();
    for (int i = offs; i < n; ++i)
    {
      uint lix = lindex(i, i);
      if (lix != NotFound)
      {
        t += val[lix];
      }
    }
    lambda = t;
  }

  /// compute "trace" of absolute values of diagonal elements of matrix
  void abstrace(Type &lambda, uint offs)
  {
    Type t(0.0);
    const int n = spty.size();
    for (int i = offs; i < n; ++i)
    {
      uint lix = lindex(i, i);
      if (lix != NotFound)
      {
        t += fabs(val[lix]);
      }
    }
    lambda = t;
  }

  /// compute "trace" of absolute values of diagonal elements of matrix
  void diagfrac(Type &dqmin, Type &rvmin, uint offs)
  {
    Type tmin(10.0), rmin(0.0); // any number larger than 1
    const int n = spty.size();
    for (int i = offs; i < n; ++i)
    {
      Type d(0.0);
      uint lix = lindex(i, i);
      if (lix != NotFound)
      {
        uint roff = spty.offset(i);
        uint nc = spty.size(i);
        d = fabs(val[lix]);
        Type rs(0.0);
        for (uint j = 0; j < nc; ++j)
        {
          rs += fabs(val[roff + j]);
        }
        Type dq = d / rs;

        if (dq < tmin)
        {
          tmin = dq;
          rmin = rs;
        }
      }
    }
    dqmin = tmin;
    rvmin = rmin;
  }

  /// compute "trace" of absolute values of diagonal elements of matrix
  void absrowmin(Type &rvmin, uint offs)
  {
    Type rmin(1e9); // set to large number
    const int n = spty.size();
    for (int i = offs; i < n; ++i)
    {
      uint roff = spty.offset(i);
      uint nc = spty.size(i);
      Type rs(0.0);
      for (uint j = 0; j < nc; ++j)
      {
        rs += fabs(val[roff + j]);
      }

      if (rs < rmin)
        rmin = rs;
    }
    rvmin = rmin;
  }

  /// compute "trace" of absolute values of diagonal elements of matrix
  void rowmax(Type &rvmax, uint offs)
  {
    Type rmax(0.0); // set to large number
    const int n = spty.size();
    for (int i = offs; i < n; ++i)
    {
      uint roff = spty.offset(i);
      uint nc = spty.size(i);
      Type rs(0.0);
      for (uint j = 0; j < nc; ++j)
      {
        rs += val[roff + j];
      }

      if (fabs(rs) > rmax)
        rmax = rs;
    }
    rvmax = rmax;
  }
  void diagminmax(Type &dvmin, Type &dvmax, uint offs)
  {
    Type dmin(1e9), dmax(-1e9); // set to large and small number
    const int n = spty.size();
    for (int i = offs; i < n; ++i)
    {
      uint lix = lindex(i, i);

      if (lix != NotFound)
      {
        Type d = val[lix];
        if (d > dmax)
          dmax = d;
        if (d < dmin)
          dmin = d;
      }
      else
      {
        dmin = 0.0;
      }
    }
    dvmin = dmin;
    dvmax = dmax;
  }

  /// perform an incomplete rank-1 update with u*v^T
  template <typename AType>
  void rank1update(const DVector<AType> &u, DVector<AType> &v)
  {
    BOOST_STATIC_ASSERT(N == 1);
    const int nr = spty.size();
#pragma omp parallel for
    for (int i = 0; i < nr; ++i)
    {
      const uint roff = spty.offset(i);
      const int nc = spty.size(i);
      const uint *col = spty.first(i);
      for (int j = 0; j < nc; ++j)
      {
        const uint jc = col[j];
        val[roff + j] += u[i] * v[jc];
      }
    }
  }

  /// perform an incomplete Broyden update of a Jacobian matrix
  template <typename AType>
  void broydenUpdate(const DVector<AType> &df, DVector<AType> &dx)
  {
    assert(df.size() == nrows());
    DVector<AType> u(df.size());
    muladd(dx, u);
    u = (df - u) / dot(dx, dx);
    rank1update(u, dx);
  }

  /// restrict to upper triangular part (including diagonal)
  void upperTriangular(CsrMatrix<Type> &uptri) const
  {
    Indices colIndex, rowPointer(1);
    DVector<Type> vtmp;
    rowPointer[0] = 0;
    Indices::const_iterator dpos;
    typename DVector<Type>::const_iterator itv;
    const int nr = spty.size();
    for (int i = 0; i < nr; ++i)
    {
      dpos = std::lower_bound(spty.begin(i), spty.end(i), i);
      assert(dpos != spty.end(i) and *dpos == i);
      colIndex.insert(colIndex.end(), dpos, spty.end(i));
      uint offset = std::distance(spty.begin(0), dpos);
      itv = val.begin() + offset;
      vtmp.insert(vtmp.end(), itv, itv + std::distance(dpos, spty.end(i)));
      rowPointer.push_back(colIndex.size());
    }
    assert(rowPointer.size() == nr + 1);
    assert(vtmp.size() == colIndex.size());

    ConnectMap map(colIndex.begin(), colIndex.end(), rowPointer.begin(),
                   rowPointer.end());
    uptri.swap(map);
    assert(uptri.nonzero() == vtmp.size());
    std::copy(vtmp.begin(), vtmp.end(), uptri.pointer());
  }

  /// drop values with magnitude less than threshold
  void dropTiny(Type threshold = std::numeric_limits<Type>::epsilon())
  {
    BOOST_STATIC_ASSERT(N == 1);
    ConnectMap pmap;
    DVector<Type> pval;
    pval.reserve(val.size());
    const size_t nr = nrows();
    pmap.beginCount(nr);
    for (size_t i = 0; i < nr; ++i)
      pmap.incCount(i, spty.size(i));
    pmap.endCount();
    uint pos = 0;
    for (size_t i = 0; i < nr; ++i)
    {
      const uint nc = sparsity().size(i);
      const uint *col = sparsity().first(i);
      for (uint j = 0; j < nc; ++j)
      {
        if (std::fabs(val[pos]) > threshold)
        {
          pmap.append(i, col[j]);
          pval.push_back(val[pos]);
        }
        ++pos;
      }
    }
    pmap.compactify();

    spty = std::move(pmap);
    val = DVector<Type>(pval.begin(), pval.end());
  }

  /** \brief Compute row permutation.
   * Without changing the matrix itself, determine a row permutation which
   * would move large (absolute) elements into the diagonal entries.
   */
  void rowPermutation(Indices &perm) const
  {
    BOOST_STATIC_ASSERT(N == 1);
    const size_t n = nrows();
    perm.resize(n);
    std::vector<bool> consumed(n, false);
    for (size_t i = 0; i < n; ++i)
    {

      // pick row j which has the largest absolute value in (j,i)
      Type maxabs(0);
      size_t jbest = n;
      for (size_t j = 0; j < n; ++j)
      {
        if (consumed[j])
          continue;
        uint lix = lindex(j, i);
        if (lix == NotFound)
          continue;
        Type vj = std::fabs(value(lix, 0));
        if (vj > maxabs)
        {
          jbest = j;
          maxabs = vj;
        }
      }

      // if there is no row left with (j,i) != 0, pick the first one unassigned
      if (jbest == n)
      {
        for (size_t j = 0; j < n; ++j)
        {
          if (not consumed[j])
          {
            jbest = j;
            break;
          }
        }
      }
      perm[i] = jbest;
      consumed[jbest] = true;
    }
  }

  /// permute by calling METIS, if available, pass row/column permutation vector
  bool permuteByMetis(Indices &perm, Indices &iperm)
  {
    bool stat = spty.metisPermutation(perm, iperm);
    if (not stat)
      return false;
    permute(iperm, iperm);
    return true;
  }

  /// apply an arbitrary row/column permutation
  void permute(const Indices &irowperm, const Indices &icolperm)
  {
    ConnectMap pmap;
    const size_t nr = spty.size();
    pmap.beginCount(nr);
    for (size_t i = 0; i < nr; ++i)
      pmap.incCount(irowperm[i], spty.size(i));
    pmap.endCount();
    for (size_t i = 0; i < nr; ++i)
    {
      const uint pi = irowperm[i];
      const uint nc = spty.size(i);
      const uint *pcol = spty.first(i);
      for (uint j = 0; j < nc; ++j)
        pmap.append(pi, icolperm[pcol[j]]);
    }
    pmap.sort();
    pmap.close();

    DVector<Type> pval(val.size());
    for (size_t i = 0; i < nrow; ++i)
    {
      const uint pi = irowperm[i];
      const uint nc = spty.size(i);
      const uint *pcol = spty.first(i);
      const uint voff = spty.offset(i);
      for (uint j = 0; j < nc; ++j)
      {
        assert(icolperm.size() > pcol[j]);
        uint pj = icolperm[pcol[j]];
        uint lix = pmap.lindex(pi, pj);
        assert(lix != NotFound);
        memcpy(&pval[N * lix], &val[N * (voff + j)], N * sizeof(Type));
      }
    }

    spty.swap(pmap);
    val.swap(pval);
  }

  /// swap sparsity, reallocate storage
  void swap(ConnectMap &s, uint nc = 0)
  {
    nrow = s.size();
    ncol = std::max(nc, s.maxcolindex() + 1);
    spty.swap(s);
    val.resize(N * spty.nonzero());
  }

  /// swap contents with another matrix
  void swap(CsrMatrix<Type, N> &a)
  {
    spty.swap(a.spty);
    val.swap(a.val);
    std::swap(nrow, a.nrow);
    std::swap(ncol, a.ncol);
  }

  /// convert to xml representation
  XmlElement toXml(bool share = false) const
  {
    XmlElement xe("CsrMatrix");
    xe["rows"] = str(nrows());
    xe["cols"] = str(ncols());
    xe["nnz"] = str(val.size());
    xe["dimension"] = str(N);
    xe.append(spty.toXml(share));
    XmlElement xv("Values");
    xv.asBinary(val.size(), val.pointer(), share);
    xe.append(std::move(xv));
    return xe;
  }

  /// read from xml representation
  void fromXml(const XmlElement &xe)
  {
    if (xe.attr2int("dimension", 1) != N)
      throw Error("CsrMatrix: Incompatible dimension in XML representation.");
    uint nnz = Int(xe.attribute("nnz"));
    val.resize(nnz);
    XmlElement::const_iterator itr = xe.findChild("ConnectMap");
    if (itr != xe.end())
      spty.fromXml(*itr);
    else
      throw Error(
          "CsrMatrix: Sparsity pattern not found in XML representation.");
    itr = xe.findChild("Values");
    if (itr != xe.end())
      itr->fetch(val.size(), val.pointer());
    else
      throw Error("CsrMatrix: No values found in XML representation.");
    if (val.size() != spty.nonzero())
      throw Error(
          "CsrMatrix: Sparsity pattern does not match nonzero value count.");
    ncol = std::max(uint(xe.attr2int("cols", 0)), spty.maxcolindex() + 1);
  }

  /// performance statistics
  float megabytes() const
  {
    float mb = 1e-6f * sizeof(CsrMatrix<Type, N>);
    mb += spty.megabytes();
    mb += 1e-6f * val.capacity() * sizeof(Type);
    return mb;
  }

  /// plain text output for matlab etc
  void writePlain(std::ostream &os) const
  {
    const int n = spty.size();
    for (int i = 0; i < n; ++i)
    {
      const uint offs = spty.offset(i);
      const int ncol = spty.size(i);
      const uint *jc = spty.first(i);
      for (int j = 0; j < ncol; ++j)
      {
        os << i << ' ' << jc[j];
        for (int k = 0; k < N; ++k)
          os << ' ' << val[(offs + j) * N + k];
        os << std::endl;
      }
    }
  }

  /// plain text input from text file for matlab and debugging
  void readPlain(std::istream &is)
  {
    BOOST_STATIC_ASSERT(N == 1);
    SparseBuilder<Type> builder;
    uint row, col, maxrow(0), maxcol(0);
    Type val;
    while (is >> row >> col >> val)
    {
      maxrow = std::max(row, maxrow);
      maxcol = std::max(col, maxcol);
      builder.append(row, col, val);
    }
    builder.sort(builder.size() > 1024);
    assign(maxrow + 1, maxcol + 1, builder);
  }

  /// write matrix market coordinate format (1-based, only scalar-valued
  /// matrices)
  void writeMarket(std::ostream &os, bool writeZeros = true) const
  {
    BOOST_STATIC_ASSERT(N == 1);
    size_t n;
    if (writeZeros)
      n = spty.nonzero();
    else
      n = std::count_if(val.begin(), val.end(), [=](Type x)
                        { return x != 0; });
    os << "%%MatrixMarket matrix coordinate real general" << std::endl;
    os << nrows() << ' ' << ncols() << ' ' << n << std::endl;
    if (writeZeros)
    {
      for (size_t i = 0; i < nrows(); ++i)
      {
        const uint offs = spty.offset(i);
        const int ncol = spty.size(i);
        const uint *jc = spty.first(i);
        for (int j = 0; j < ncol; ++j)
          os << i + 1 << ' ' << jc[j] + 1 << ' ' << val[offs + j] << std::endl;
      }
    }
    else
    {
      for (size_t i = 0; i < nrows(); ++i)
      {
        const uint offs = spty.offset(i);
        const int ncol = spty.size(i);
        const uint *jc = spty.first(i);
        for (int j = 0; j < ncol; ++j)
          if (val[offs + j] != 0)
            os << i + 1 << ' ' << jc[j] + 1 << ' '
               << val[offs + j] << std::endl;
      }
    }
  }

  /// simple binary output
  void writeBin(std::ostream &os) const
  {
    uint32_t nnz = spty.nonzero();
    std::vector<uint32_t> irow(nnz), icol(nnz);
    uint k(0);
    const int nrow = spty.size();
    for (int i = 0; i < nrow; ++i)
    {
      const int nc = spty.size(i);
      for (int j = 0; j < nc; ++j)
      {
        irow[k] = i;
        icol[k] = spty.index(i, j);
        ++k;
      }
    }
    assert(k == nnz);

    int32_t tcode = detail::float_type_marker<Type>();
    os.write((const char *)&tcode, 4);
    os.write((const char *)&nnz, 4);
    os.write((const char *)&irow[0], nnz * 4);
    os.write((const char *)&icol[0], nnz * 4);
    os.write((const char *)&val[0], nnz * sizeof(Type));
  }

  /// simple binary input
  void readBin(std::istream &is)
  {
    int32_t tcode;
    uint32_t nnz;
    is.read((char *)&tcode, 4);
    is.read((char *)&nnz, 4);
    if (tcode != detail::float_type_marker<Type>())
      throw Error("Attempting to read CsrMatrix of incompatible element type.");

    if (nnz == 0)
      return;
    val.allocate(nnz);
    std::vector<uint32_t> irow(nnz), icol(nnz), rowptr(1);
    is.read((char *)&irow[0], nnz * 4);
    is.read((char *)&icol[0], nnz * 4);
    is.read((char *)&val[0], nnz * sizeof(Type));

    rowptr.reserve(irow.back() + 1);
    rowptr[0] = 0;
    uint32_t lastrow(0);
    for (uint i = 0; i < nnz; ++i)
    {
      if (irow[i] > lastrow)
      {
        lastrow = irow[i];
        rowptr.push_back(i);
      }
    }
    rowptr.push_back(nnz);

    spty = ConnectMap(icol.begin(), icol.end(), rowptr.begin(), rowptr.end());
    ncol = spty.maxcolindex() + 1;
    nrow = spty.size();
  }

  /// export to FFA format
  FFANodePtr toFFA() const
  {
    FFANodePtr proot = boost::make_shared<FFANode>("csr_matrix");
    proot->append("external_rows", (int)nrow);
    proot->append("external_cols", (int)ncol);
    proot->append(spty.toFFA());
    FFANodePtr pval = boost::make_shared<FFANode>("values");
    int nnz = (val.size() / N);
    pval->copy(ffa_type_trait<Type>::value, N, nnz, val.pointer());
    proot->append(pval);
    return proot;
  }

  /// import from FFA format
  bool fromFFA(const FFANodePtr &root)
  {
    assert(root->name() == "csr_matrix");

    bool ok = true;
    int xr, xc;
    ok &= root->retrieve("external_rows", xr);
    ok &= root->retrieve("external_cols", xc);
    if (not ok)
      return false;
    nrow = xr;
    ncol = xc;

    uint ip = root->findChild("values");
    if (ip == NotFound)
      return false;
    FFANodePtr pval = root->child(ip);
    if (pval->nrows() != N)
      return false;
    if (pval->contentType() != ffa_type_trait<Type>::value)
      return false;
    val.allocate(pval->numel());
    pval->retrieve(val.pointer());

    ip = root->findChild("sparsity");
    if (ip == NotFound)
      return false;
    return spty.fromFFA(root->child(ip));
  }

#ifdef HAVE_EIGEN

  /// convert to a sparse matrix from the eeigen library
  template <class EigenSpMatrix>
  void copy(EigenSpMatrix &m) const
  {
    BOOST_STATIC_ASSERT(N == 1);

    // clear out
    m = EigenSpMatrix(nrows(), ncols());

    // generate triplets
    typedef eeigen::Triplet<Type, int> Trip;
    std::vector<Trip> trips(nonzero());
    const int nr = nrows();
    size_t lix = 0;
    for (int i = 0; i < nr; ++i)
    {
      const int n = spty.size(i);
      const uint *jc = spty.first(i);
      for (int k = 0; k < n; ++k)
      {
        trips[lix] = Trip(i, jc[k], val[lix]);
        ++lix;
      }
    }

    m.setFromTriplets(trips.begin(), trips.end());
    m.makeCompressed();
  }

#endif

  /// concatenate columns of a and b to yield matrix ab
  static void catColumns(const CsrMatrix<Type> &a, const CsrMatrix<Type> &b,
                         CsrMatrix<Type> &ab)
  {
    const uint anr = a.nrows();
    assert(b.nrows() = anr);

    // merge connectivity pattern first
    {
      ConnectMap abm;
      abm.catColumns(a.sparsity(), b.sparsity(), a.ncols());
      ab.swap(abm);
    }

    // copy numerical values
    Type *dst = ab.pointer();
    const Type *asrc = a.pointer();
    const Type *bsrc = b.pointer();
    for (uint i = 0; i < anr; ++i)
    {
      const size_t na = a.size(i);
      memcpy(dst, asrc, na * sizeof(Type));
      dst += na;
      asrc += na;
      const size_t nb = b.size(i);
      memcpy(dst, bsrc, nb * sizeof(Type));
      dst += nb;
      bsrc += nb;
    }
  }

  /// concatenate rows of a and b to yield matrix ab
  static void catRows(const CsrMatrix<Type> &a, const CsrMatrix<Type> &b,
                      CsrMatrix<Type> &ab)
  {
    assert(a.ncols() == b.ncols());

    // merge connectivity pattern first
    {
      ConnectMap abm;
      abm.catRows(a.sparsity(), b.sparsity());
      ab.swap(abm);
    }

    // copy numerical values
    Type *dst = ab.pointer();
    memcpy(dst, a.pointer(), a.nonzero() * sizeof(Type));
    dst += a.nonzero();
    memcpy(dst, b.pointer(), b.nonzero() * sizeof(Type));
  }

  /// assemble from four blocks
  static void assemble(const CsrMatrix<Type> &a11, const CsrMatrix<Type> &a12,
                       const CsrMatrix<Type> &a21, const CsrMatrix<Type> &a22,
                       CsrMatrix<Type> &b)
  {
    CsrMatrix<Type> b1, b2;
    catColumns(a11, a12, b1);
    catColumns(a21, a22, b2);
    catRows(b1, b2, b);
  }

private:
  /// connectivity data
  ConnectMap spty;

  /// nonzero values
  DVector<Type> val;

  /// external dimensions for reference
  uint nrow, ncol;
};

#endif
