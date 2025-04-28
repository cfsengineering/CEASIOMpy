
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
 
#ifndef GENUA_SPARSEQR_H
#define GENUA_SPARSEQR_H

#include "csrmatrix.h"
#include "dmatrix.h"
#include "abstractlinearsolver.h"
#include "configparser.h"
#include "cholmodsolver.h"
#include "propmacro.h"
#include <SuiteSparseQR.hpp>

class SpqrContext : public CholmodContext
{
public:

  /// set defaults
  SpqrContext();

  /// configure settings
  virtual void configure(const ConfigParser &cfg);

  GENUA_PROP(int, ordering)
  GENUA_PROP(double, columnTolerance)
};

/** Interface for SPQR from Davis' SuiteSparse package.
 *
 * http://www.cise.ufl.edu/research/sparse/SPQR/
 *
 *
 *
 */
template <typename FloatType>
class SparseQR : public AbstractLinearSolverTpl<FloatType>
{
public:

  typedef CholmodContext::index_t index_t;
  typedef AbstractLinearSolverTpl<FloatType> Base;

  /// initialize context, ignore matrix type flag - rectangular solver.
  SparseQR(uint ignoredTypeFlag = SpMatrixFlag::Unsymmetric)
    : Base(ignoredTypeFlag)
  {
    Base::m_implName = "SuiteSparse/SPQR";
  }

  /// disable copy construction
  SparseQR(const SparseQR &) = delete;

  /// release all allocated memory
  ~SparseQR() { release(); }

  /// configure settings
  void configure(const ConfigParser &cfg) {
    m_context.configure(cfg);
  }

  /// perform factorization only
  bool factor(const CsrMatrix<FloatType> *pa) {
    ScopeTimer timer( AbstractLinearSolverTpl<FloatType>::m_factorTime );
    cholmod_sparse *ps = m_context.assimilate(pa);
    m_qrf = SuiteSparseQR_factorize<FloatType>( m_context.ordering(),
                                                m_context.columnTolerance(),
                                                ps, context());
    ++Base::m_factorCount;
    return true;
  }

  /// perform solution step only
  bool solve(const DVector<FloatType> &b, DVector<FloatType> &x) {
    assert(m_qrf != nullptr);
    ScopeTimer timer( AbstractLinearSolverTpl<FloatType>::m_solveTime );
    cholmod_dense *cx(0), *cy(0), *cb;
    cb = m_context.constructDense(b);

    // solve Q*R*x = b
    cy = SuiteSparseQR_qmult<FloatType>(SPQR_QTX, m_qrf, cb, context());
    cx = SuiteSparseQR_solve<FloatType>(SPQR_RETX_EQUALS_B,
                                        m_qrf, cy, context());

    x.resize( cx->nrow );
    memcpy(x.pointer(), cx->x, x.size() * sizeof(FloatType) );

    cholmod_l_free_dense(&cx, context());
    cholmod_l_free_dense(&cy, context());
    cholmod_l_free_dense(&cb, context());
    ++Base::m_solveCount;
    return true;
  }

  /// perform solution step only
  bool solve(const DMatrix<FloatType> &b, DMatrix<FloatType> &x) {
    assert(m_qrf != nullptr);
    ScopeTimer timer( AbstractLinearSolverTpl<FloatType>::m_solveTime );
    cholmod_dense *cx(0), *cy(0), *cb;
    cb = m_context.constructDense(b);

    // solve Q*R*x = b
    cy = SuiteSparseQR_qmult<FloatType>(SPQR_QTX, m_qrf, cb, context());
    cx = SuiteSparseQR_solve<FloatType>(SPQR_RETX_EQUALS_B,
                                        m_qrf, cy, context());

    x.resize( cx->nrow, cx->ncol );
    memcpy(x.pointer(), cx->x, x.size() * sizeof(FloatType) );

    cholmod_l_free_dense(&cx, context());
    cholmod_l_free_dense(&cy, context());
    cholmod_l_free_dense(&cb, context());
    ++Base::m_solveCount;
    return true;
  }

  /// factor and solve in one call (more efficient according to Davis)
  bool solve(const CsrMatrix<FloatType> *pa, const DVector<FloatType> &b,
             DVector<FloatType> &x)
  {
    ScopeTimer timer( AbstractLinearSolverTpl<FloatType>::m_factorTime );
    cholmod_sparse *ps = m_context.assimilate(pa);
    cholmod_dense *cx(0), *cb;
    cb = m_context.constructDense(b);
    if (pa->nrows() >= pa->ncols())
      cx = SuiteSparseQR<FloatType>(ps, cb, context());
    else
      cx = SuiteSparseQR_min2norm<FloatType>(m_context.ordering(),
                                             m_context.columnTolerance(),
                                             ps, cb, context());
    cholmod_l_free_dense(&cb, context());
    x.allocate( cx->nrow );
    memcpy(x.pointer(), cx->x, x.size() * sizeof(FloatType) );
    cholmod_l_free_dense(&cx, context());
    ++Base::m_solveCount;
    return true;
  }

  /// deallocate internal storage
  void release() {
    if (m_qrf != nullptr)
      SuiteSparseQR_free(&m_qrf, context());
    m_qrf = nullptr;
    m_context.release();
  }

private:

  /// access context
  cholmod_common *context() {return m_context.context();}

private:

  /// library context
  SpqrContext m_context;

  /// factorization
  SuiteSparseQR_factorization<FloatType> *m_qrf = nullptr;
};

#endif // SPARSEQR_H
