
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
 
#ifndef GENUA_CONVERTINGSOLVER_H
#define GENUA_CONVERTINGSOLVER_H

#include "abstractlinearsolver.h"

/** Solve in another precision.
 *
 *  This wrapper solves a linear problem in another precision than the one
 *  presented by the interface. Quite often, it is sufficient to solve a linear
 *  problem in single precision even though other parts of the same program may
 *  require double-precision computations. Many solvers are quite exactly twice
 *  as fast in single precision, in which case this class can be used to convert
 *  between the two. The overhead of this wrapper is an extra copy of the matrix
 *  and right-hand side.
 *
 * \ingroup numerics
 * \sa AbstractLinearSolverTpl
 */
template <typename InterfaceFloat, typename SolverFloat>
class ConvertingSolver : public AbstractLinearSolverTpl<InterfaceFloat>
{
public:

  typedef AbstractLinearSolverTpl<InterfaceFloat> Base;
  typedef AbstractLinearSolverTpl<SolverFloat> InnerSolver;
  typedef boost::shared_ptr<InnerSolver> InnerSolverPtr;

  /// construct with actual solver
  ConvertingSolver(InnerSolverPtr psolver)
    : Base( psolver->matrixType() ),
      m_isolver(psolver) { Base::m_implName = psolver->name() + "/converting"; }

  /// load configuration settings
  virtual void configure(const ConfigParser &cfg) { m_isolver->configure(cfg); }

  /// full factorization (minimum interface)
  virtual bool factor(const CsrMatrix<InterfaceFloat,1> *pa) {
    ++Base::m_factorCount;
    gobbleup(*pa);
    return m_isolver->factor( &m_acopy );
  }

  /// numerical factorization only (if supported)
  virtual bool refactor(const CsrMatrix<InterfaceFloat,1> *pa) {
    ++Base::m_factorCount;
    gobbleup(*pa);
    return m_isolver->refactor( &m_acopy );
  }

  /// solve with multiple rhs
  virtual bool solve(const DMatrix<InterfaceFloat> &b,
                     DMatrix<InterfaceFloat> &x)
  {
    assert(x.size() == b.size());
    DMatrix<SolverFloat> cb( b );
    DMatrix<SolverFloat> cx( x );
    bool stat = m_isolver->solve(cb, cx);
    std::copy(cx.begin(), cx.end(), x.begin());
    Base::m_factorCount = m_isolver->factorizations();
    Base::m_solveCount = m_isolver->solves();
    return stat;
  }

  /// solve single RHS (by default implemented in terms of the above)
  virtual bool solve(const DVector<InterfaceFloat> &b,
                     DVector<InterfaceFloat> &x)
  {
    assert(x.size() == b.size());
    DVector<SolverFloat> cb( b );
    DVector<SolverFloat> cx( x );
    bool stat = m_isolver->solve(cb, cx);
    std::copy(cx.begin(), cx.end(), x.begin());
    Base::m_factorCount = m_isolver->factorizations();
    Base::m_solveCount = m_isolver->solves();
    return stat;
  }

  /// single-shot solve (may be more efficient for some solvers)
  virtual bool solve(const CsrMatrix<InterfaceFloat,1> *pa,
                     const DMatrix<InterfaceFloat> &b,
                     DMatrix<InterfaceFloat> &x)
  {
    gobbleup(*pa);
    DMatrix<SolverFloat> cb( b );
    DMatrix<SolverFloat> cx( x );
    bool stat = m_isolver->solve(&m_acopy, cb, cx);
    std::copy(cx.begin(), cx.end(), x.begin());
    Base::m_factorCount = m_isolver->factorizations();
    Base::m_solveCount = m_isolver->solves();
    return stat;
  }

  /// single-shot solve (may be more efficient for some solvers)
  virtual bool solve(const CsrMatrix<InterfaceFloat,1> *pa,
                     const DVector<InterfaceFloat> &b,
                     DVector<InterfaceFloat> &x)
  {
    gobbleup(*pa);
    DVector<SolverFloat> cb( b );
    DVector<SolverFloat> cx( x );
    bool stat = m_isolver->solve(&m_acopy, cb, cx);
    std::copy(cx.begin(), cx.end(), x.begin());
    Base::m_factorCount = m_isolver->factorizations();
    Base::m_solveCount = m_isolver->solves();
    return stat;
  }

  /// solution with new values in A, but the same non-zero pattern
  virtual bool resolve(const CsrMatrix<InterfaceFloat,1> *pa,
                       const DMatrix<InterfaceFloat> &b,
                       DMatrix<InterfaceFloat> &x)
  {
    gobbleup(*pa);
    DMatrix<SolverFloat> cb( b );
    DMatrix<SolverFloat> cx( x );
    bool stat = m_isolver->resolve(&m_acopy, cb, cx);
    std::copy(cx.begin(), cx.end(), x.begin());
    Base::m_factorCount = m_isolver->factorizations();
    Base::m_solveCount = m_isolver->solves();
    return stat;
  }

  /// solution with new values in A, but the same non-zero pattern
  virtual bool resolve(const CsrMatrix<InterfaceFloat,1> *pa,
                       const DVector<InterfaceFloat> &b,
                       DVector<InterfaceFloat> &x)
  {
    gobbleup(*pa);
    DVector<SolverFloat> cb( b );
    DVector<SolverFloat> cx( x );
    bool stat = m_isolver->resolve(&m_acopy, cb, cx);
    std::copy(cx.begin(), cx.end(), x.begin());
    Base::m_factorCount = m_isolver->factorizations();
    Base::m_solveCount = m_isolver->solves();
    return stat;
  }

  /// access timing data (if supported by implementation)
  float factorTime() const {return m_isolver->factorTime();}

  /// access timing data (if supported by implementation)
  float solveTime() const {return m_isolver->solveTime();}

  /// memory, in Megabyte, as reported by solver (if possible)
  float maxMemory() const {return m_isolver->maxMemory();}

  /// release internal storage
  virtual void release() { m_isolver->release(); }

  /// condition number estimate
  virtual double condest() { return m_isolver->condest(); }

private:

  /// copy matrix to internal format
  void gobbleup(const CsrMatrix<InterfaceFloat> &a) {
    const size_t nnz = a.nonzero();
    DVector<SolverFloat> sval;
    sval.allocate(nnz);
    std::copy(a.nzarray().begin(), a.nzarray().end(), sval.begin());
    m_acopy = CsrMatrix<SolverFloat>(a.sparsity(), sval, a.ncols());
  }

private:

  /// converted matrix
  CsrMatrix<SolverFloat> m_acopy;

  /// actual solver
  InnerSolverPtr m_isolver;
};

#endif // CONVERTINGSOLVER_H

