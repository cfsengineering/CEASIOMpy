
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

#ifndef GENUA_EIGENSPARSESOLVER_H
#define GENUA_EIGENSPARSESOLVER_H

#include "abstractlinearsolver.h"
#include <eeigen/SparseLU>
#include <eeigen/SparseCholesky>
// #include <eeigen/SparseQR>
#include <eeigen/Core>

/** Interface to sparse LU-decomposition.
 *
 * This is an interface to the SparseLU solver from the eeigen library.
 * It is available whenever the eeigen
 * header library has been found by the qmake run.
 *
 * On failure, a detailed error message can be retrieved by calling the
 * message() function.
 *
 * \ingroup numerics
 * \sa AbstractLinearSolverTpl
 */
template <typename FloatType>
class EigenSparseLU : public AbstractLinearSolverTpl<FloatType>
{
private:
  typedef AbstractLinearSolverTpl<FloatType> Base;
  typedef eeigen::SparseMatrix<FloatType, eeigen::ColMajor> SpMatrixType;
  typedef eeigen::Matrix<FloatType, eeigen::Dynamic, eeigen::Dynamic> DenseType;
  typedef eeigen::Map<const DenseType, eeigen::Aligned> DenseMap;

public:
  /// construct, do nothing more
  EigenSparseLU(uint ignored = 0) : AbstractLinearSolverTpl<FloatType>(ignored)
  {
    this->m_implName = "eeigen/SparseLU";
  }

  /// symbolic and numerical factorization
  bool factor(const CsrMatrix<FloatType> *pa)
  {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_factorTime);
    assert(pa->nrows() == pa->ncols());
    pa->copy(m_alu);
    m_solver.analyzePattern(m_alu);
    m_solver.factorize(m_alu);
    ++Base::m_factorCount;
    return (m_solver.info() == eeigen::Success);
  }

  /// factorize again, reusing the symbolic factorization
  bool refactor(const CsrMatrix<FloatType> *pa)
  {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_factorTime);
    pa->copy(m_alu);
    m_solver.factorize(m_alu);
    ++Base::m_factorCount;
    return (m_solver.info() == eeigen::Success);
  }

  /// solve system
  bool solve(const DMatrix<FloatType> &b, DMatrix<FloatType> &x)
  {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_solveTime);
    if (m_solver.info() != eeigen::Success)
      throw Error("Factorization failed, cannot solve: " + m_solver.lastErrorMessage());
    DenseMap bmap(b.pointer(), b.nrows(), b.ncols());
    DenseType xe;
    if (not Base::m_solveTransposed)
      xe = m_solver.solve(bmap);
    else
      this->tsolve(bmap, xe);
    const FloatType *px = xe.data();
    assert(x.size() >= b.size());
    std::copy(px, px + b.size(), x.begin());
    ++Base::m_solveCount;
    return (m_solver.info() == eeigen::Success);
  }

  /// solve system
  bool solve(const DVector<FloatType> &b, DVector<FloatType> &x)
  {
    if (m_solver.info() != eeigen::Success)
      throw Error("Factorization failed, cannot solve: " + m_solver.lastErrorMessage());
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_solveTime);
    DenseMap bmap(b.pointer(), b.size(), 1);
    DenseType xe;
    if (not Base::m_solveTransposed)
      xe = m_solver.solve(bmap);
    else
      this->tsolve(bmap, xe);
    const FloatType *px = xe.data();
    assert(x.size() >= b.size());
    std::copy(px, px + b.size(), x.begin());
    ++Base::m_solveCount;
    return (m_solver.info() == eeigen::Success);
  }

  /// access error message on failure
  std::string message() const { return m_solver.lastErrorMessage(); }

private:
  /// solve the transposed problem A^T X = B (not correct -> perm)
  bool tsolve(const DenseMap &B, DenseType &X_base) const
  {
    typedef typename DenseType::Index Index;
    DenseType &X(X_base.derived());
    X.resize(B.rows(), B.cols());
    for (Index j = 0; j < B.cols(); ++j)
      X.col(j) = m_solver.colsPermutation() * B.const_cast_derived().col(j);
    m_solver.matrixU().solveInPlace(X);
    m_solver.matrixL().solveInPlace(X);
    for (Index j = 0; j < B.cols(); ++j)
      X.col(j) = m_solver.rowsPermutation().inverse() * X.col(j);
    return true;
  }

private:
  /// local copy of coefficient matrix
  SpMatrixType m_alu;

  /// actual solver
  eeigen::SparseLU<SpMatrixType> m_solver;
};

/** Interface to sparse Cholesky solver.
 *
 * This is an interface to the SimplicialLDLT solver from the eeigen library.
 * It can only solve symmetrix problems and is available whenever the eeigen
 * header library has been found by the qmake run.
 *
 * \ingroup numerics
 * \sa AbstractLinearSolverTpl
 */
template <typename FloatType>
class EigenSparseChol : public AbstractLinearSolverTpl<FloatType>
{
private:
  typedef AbstractLinearSolverTpl<FloatType> Base;
  typedef eeigen::SparseMatrix<FloatType, eeigen::ColMajor> SpMatrixType;
  typedef eeigen::Matrix<FloatType, eeigen::Dynamic, eeigen::Dynamic> DenseType;
  typedef eeigen::Map<const DenseType, eeigen::Aligned> DenseMap;

public:
  /// construct, do nothing more
  EigenSparseChol(uint ignored = 0) : AbstractLinearSolverTpl<FloatType>(ignored)
  {
    this->m_implName = "eeigen/SimplicialLDLT";
  }

  /// symbolic and numerical factorization
  bool factor(const CsrMatrix<FloatType> *pa)
  {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_factorTime);
    assert(pa->nrows() == pa->ncols());
    pa->copy(m_alu);
    m_solver.analyzePattern(m_alu);
    m_solver.factorize(m_alu);
    ++Base::m_factorCount;
    return (m_solver.info() == eeigen::Success);
  }

  /// factorize again, reusing the symbolic factorization
  bool refactor(const CsrMatrix<FloatType> *pa)
  {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_factorTime);
    pa->copy(m_alu);
    m_solver.factorize(m_alu);
    ++Base::m_factorCount;
    return (m_solver.info() == eeigen::Success);
  }

  /// solve system
  bool solve(const DMatrix<FloatType> &b, DMatrix<FloatType> &x)
  {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_solveTime);
    DenseMap bmap(b.pointer(), b.nrows(), b.ncols());
    DenseType xe = m_solver.solve(bmap);
    const FloatType *px = xe.data();
    // x.allocate(m_pa->ncols(), b.ncols());
    std::copy(px, px + b.size(), x.begin());
    ++Base::m_solveCount;
    return (m_solver.info() == eeigen::Success);
  }

  /// solve system
  bool solve(const DVector<FloatType> &b, DVector<FloatType> &x)
  {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_solveTime);
    DenseMap bmap(b.pointer(), b.size(), 1);
    DenseType xe = m_solver.solve(bmap);
    const FloatType *px = xe.data();
    // x.allocate(m_pa->ncols(), b.ncols());
    std::copy(px, px + b.size(), x.begin());
    ++Base::m_solveCount;
    return (m_solver.info() == eeigen::Success);
  }

private:
  /// local copy of coefficient matrix
  SpMatrixType m_alu;

  /// actual solver
  eeigen::SimplicialLDLT<SpMatrixType> m_solver;
};

#endif // EIGENSPARSESOLVER_H
