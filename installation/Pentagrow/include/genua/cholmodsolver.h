
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

#ifndef GENUA_CHOLMODSOLVER_H
#define GENUA_CHOLMODSOLVER_H

#include "forward.h"
#include "abstractlinearsolver.h"
#include <cholmod.h>

template <typename FloatType>
struct cholmod_xtype_trait {
public:
  static const int xtype = -1;
  static const int dtype = -1;
  static void transfer(size_t n, const FloatType x[], int dtype, void *py) {
    if (dtype == CHOLMOD_DOUBLE) {
      double *y = reinterpret_cast<double *>( py );
      std::copy(x, x+n, y);
    } else {
      float *y = reinterpret_cast<float *>( py );
      std::copy(x, x+n, y);
    }
  }
};

template <>
struct cholmod_xtype_trait<double> {
public:
  static const int xtype = CHOLMOD_REAL;
  static const int dtype = CHOLMOD_DOUBLE;
  static void transfer(size_t n, const double x[], int dtype, void *py) {
    if (dtype == CHOLMOD_DOUBLE) {
      double *y = reinterpret_cast<double *>( py );
      std::copy(x, x+n, y);
    } else {
      float *y = reinterpret_cast<float *>( py );
      std::copy(x, x+n, y);
    }
  }
};

template <>
struct cholmod_xtype_trait<float> {
public:
  static const int xtype = CHOLMOD_REAL;
  static const int dtype = CHOLMOD_SINGLE;
  static void transfer(size_t n, const float x[], int dtype, void *py) {
    if (dtype == CHOLMOD_DOUBLE) {
      double *y = reinterpret_cast<double *>( py );
      std::copy(x, x+n, y);
    } else {
      float *y = reinterpret_cast<float *>( py );
      std::copy(x, x+n, y);
    }
  }
};

template <>
struct cholmod_xtype_trait<std::complex<double> > {
public:
  static const int xtype = CHOLMOD_COMPLEX;
  static const int dtype = CHOLMOD_DOUBLE;
  static void transfer(size_t n, const std::complex<double> x[], int dtype, void *py) {
    if (dtype == CHOLMOD_DOUBLE) {
      std::complex<double> *y = reinterpret_cast<std::complex<double> *>( py );
      std::copy(x, x+n, y);
    } else {
      std::complex<float> *y = reinterpret_cast<std::complex<float> *>( py );
      std::copy(x, x+n, y);
    }
  }
};

template <>
struct cholmod_xtype_trait<std::complex<float> > {
public:
  static const int xtype = CHOLMOD_COMPLEX;
  static const int dtype = CHOLMOD_SINGLE;
  static void transfer(size_t n, const std::complex<float> x[], int dtype, void *py) {
    if (dtype == CHOLMOD_DOUBLE) {
      std::complex<double> *y = reinterpret_cast<std::complex<double> *>( py );
      std::copy(x, x+n, y);
    } else {
      std::complex<float> *y = reinterpret_cast<std::complex<float> *>( py );
      std::copy(x, x+n, y);
    }
  }
};

class CholmodContext
{
public:

  typedef SuiteSparse_long index_t;

  /// initialize solver parameters
  CholmodContext();

  /// finalize and cleanup
  virtual ~CholmodContext();

  /// load configuration settings
  virtual void configure(const ConfigParser &);

  /// convert a CSR-format matrix to SuiteSparse format
  template <typename FloatType>
  cholmod_sparse *assimilate(const CsrMatrix<FloatType> *pa) {
    if (m_psparse != nullptr)
      cholmod_l_free_sparse(&m_psparse, &m_common);

    const CsrMatrix<FloatType> &A(*pa);
    const size_t nrow = A.nrows();
    const size_t ncol = A.ncols();
    const int xtype = cholmod_xtype_trait<FloatType>::xtype;
    m_psparse = cholmod_l_allocate_sparse(nrow, ncol, A.nonzero(), 1, 1, 0,
                                          xtype, &m_common);
    if (m_psparse->dtype != cholmod_xtype_trait<FloatType>::dtype)
      throw Error("CHOLMOD not compiled for this precision.");

    // count number of rows in each column
    std::vector<size_t> rowCount(ncol, 0);
    const ConnectMap &csr( A.sparsity() );
    for (size_t i=0; i<nrow; ++i) {
      const int nc = csr.size(i);
      const uint *col = csr.first(i);
      for (int j=0; j<nc; ++j)
        ++rowCount[col[j]];
    }

    // set values in m_pa
    index_t *colptr = reinterpret_cast<index_t *>( m_psparse->p );
    index_t *rowIdx = reinterpret_cast<index_t *>( m_psparse->i );
    FloatType *val = reinterpret_cast<FloatType *>( m_psparse->x );

    // assign column pointers
    colptr[0] = 0;
    for (size_t i=0; i<ncol; ++i)
      colptr[i+1] = colptr[i] + rowCount[i];
    std::fill(rowCount.begin(), rowCount.end(), 0);

    // assign row indices and values
    for (size_t i=0; i<nrow; ++i) {
      const int nc = csr.size(i);
      const uint *col = csr.first(i);
      const uint offset = csr.offset(i);
      for (int jc=0; jc<nc; ++jc) {
        const index_t j = col[jc];
        rowIdx[colptr[j] + rowCount[j]] = i; // set row index
        val[colptr[j] + rowCount[j]] = A[offset+jc];
        ++rowCount[j];
      }
    }

    return m_psparse;
  }

  /// create a cholmod dense matrix object
  template <typename FloatType>
  cholmod_dense *constructDense(const DVector<FloatType> &x) {
    const int xtype = cholmod_xtype_trait<FloatType>::xtype;
    cholmod_dense *cx = cholmod_l_allocate_dense(x.size(), 1, x.size(),
                                                 xtype, &m_common);
    cholmod_xtype_trait<FloatType>::transfer(x.size(), x.pointer(),
                                             cx->dtype, cx->x);
    return cx;
  }

  /// generate dense matrix object
  template <typename FloatType>
  cholmod_dense *constructDense(const DMatrix<FloatType> &x) {
    cholmod_dense *cx;
    const int xtype = cholmod_xtype_trait<FloatType>::xtype;
    cx = cholmod_l_allocate_dense(x.nrows(), x.ncols(),
                                  x.ldim(), xtype, &m_common);
    cholmod_xtype_trait<FloatType>::transfer(x.size(), x.pointer(),
                                             cx->dtype, cx->x);
    return cx;
  }

  /// access context pointer
  cholmod_common *context() {return &m_common;}

  /// access sparse matrix in cholmod format
  cholmod_sparse *matrix() {return m_psparse;}

  /// message for last recorded status
  virtual const char *lastMessage() const;

  /// release allocated memory
  virtual void release();

  /// perform symbolic factorization using cholesky module
  cholmod_factor *analyze() {
    return cholmod_l_analyze(m_psparse, &m_common);
  }

  /// perform numeric factorization using cholesky module
  void factorize(cholmod_factor *pfactor) {
    cholmod_l_factorize(m_psparse, pfactor, &m_common);
  }

protected:

  /// solver parameters
  cholmod_common m_common;

  /// compressed-sparse-column version of A
  cholmod_sparse *m_psparse = nullptr;
};

template <typename FloatType>
class CholmodSolver : public AbstractLinearSolverTpl<FloatType>
{
public:

  typedef AbstractLinearSolverTpl<FloatType> Base;

  /// create empty solver object
  CholmodSolver(uint typeflag = SpMatrixFlag::RealPositiveDefinite)
    : Base(typeflag)
  {
    assert(SpMatrixFlag::isSymmetric(typeflag));
    Base::m_implName = "SuiteSparse/CHOLMOD";
  }

  /// load configuration settings
  void configure(const ConfigParser &cfg) {
    m_context.configure(cfg);
  }

  /// full factorization (minimum interface)
  bool factor(const CsrMatrix<FloatType,1> *pa) {
    ScopeTimer timer( AbstractLinearSolverTpl<FloatType>::m_factorTime );
    ++Base::m_factorCount;
    m_context.assimilate(pa);
    this->analyze();
    if (context()->status != CHOLMOD_OK)
      return false;
    this->factorize();
    return (context()->status == CHOLMOD_OK);
  }

  /// numerical factorization only (if supported)
  bool refactor(const CsrMatrix<FloatType,1> *pa) {
    assert(m_pfactor != nullptr);
    ScopeTimer timer( AbstractLinearSolverTpl<FloatType>::m_factorTime );
    ++Base::m_factorCount;
    m_context.assimilate(pa);
    this->factorize();
    return (context()->status == CHOLMOD_OK);
  }

  /// solve with multiple rhs
  bool solve(const DMatrix<FloatType> &b, DMatrix<FloatType> &x) {
    ScopeTimer timer( AbstractLinearSolverTpl<FloatType>::m_solveTime );
    ++Base::m_solveCount;

    cholmod_dense *cx(0), *cb = m_context.constructDense(b);
    cx = cholmod_l_solve(CHOLMOD_A, m_pfactor, cb, context()) ;

    x.allocate(cx->nrow, cx->ncol);
    memcpy(x.pointer(), cx->x, x.size() * sizeof(FloatType) );

    cholmod_l_free_dense(&cx, context());
    cholmod_l_free_dense(&cb, context());
    return (context()->status == CHOLMOD_OK);
  }

  /// solve single RHS (by default implemented in terms of the above)
  bool solve(const DVector<FloatType> &b, DVector<FloatType> &x) {
    ScopeTimer timer( AbstractLinearSolverTpl<FloatType>::m_solveTime );
    ++Base::m_solveCount;

    cholmod_dense *cx(0), *cb = m_context.constructDense(b);
    cx = cholmod_l_solve(CHOLMOD_A, m_pfactor, cb, context()) ;

    x.allocate(cx->nrow);
    memcpy(x.pointer(), cx->x, x.size() * sizeof(FloatType) );

    cholmod_l_free_dense(&cx, context());
    cholmod_l_free_dense(&cb, context());
    return (context()->status == CHOLMOD_OK);
  }

  /// return condition number
  double condest() {
    assert(m_pfactor != nullptr);
    return 1.0 / cholmod_l_rcond(m_pfactor, context());
  }

protected:

  /// compute symbolic factorization
  void analyze()
  {
    if (m_pfactor != nullptr)
      cholmod_free_factor(&m_pfactor, context());
    m_pfactor = m_context.analyze();
  }

  /// update numeric factorization
  void factorize()
  {
    assert(m_pfactor != nullptr);
    m_context.factorize(m_pfactor);
  }

  /// access context object
  cholmod_common *context() {return m_context.context();}

protected:

  /// library context
  CholmodContext m_context;

  /// factorization
  cholmod_factor *m_pfactor = nullptr;
};

#endif // CHOLMODSOLVER_H
