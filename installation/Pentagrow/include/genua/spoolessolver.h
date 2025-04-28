
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
 
#ifndef SPOOLESSOLVER_H
#define SPOOLESSOLVER_H

#include "forward.h"
#include "abstractlinearsolver.h"

extern "C" {

#include <spooles/InpMtx.h>
#include <spooles/LinSol/BridgeMT.h>
#include <spooles/DenseMtx.h>

}

/** Base class for wrapper around SPOOLES.
 *
 *
 * \internal
 */
class SpoolesBase
{
public:

  enum ElementType { IndexOnly = INPMTX_INDICES_ONLY,
                     Real = INPMTX_REAL_ENTRIES,
                     Complex = INPMTX_COMPLEX_ENTRIES};

  enum Symmetry { Symmetric = SPOOLES_SYMMETRIC,
                  Hermitian = SPOOLES_HERMITIAN,
                  Unsymmetric = SPOOLES_NONSYMMETRIC };

  /// helper class used to map types
  template <typename FloatType>
  struct TypeMap {
    static const ElementType value = IndexOnly;
    static const bool convert = false;
  };

  /// construct and initialize solver objects
  SpoolesBase(Symmetry symflag = SpoolesBase::Unsymmetric,
              ElementType etype = SpoolesBase::Real);

  /// free memory
  ~SpoolesBase();

  /// configure parameter of the underlying solver
  void configure(const ConfigParser &cfg);

  /// translate matrix type
  static SpoolesBase::ElementType mapElementType(uint typeflag);

  /// translate matrix type
  static SpoolesBase::Symmetry mapSymmetry(uint typeflag);

  /// copy values to solver representation of matrix
  void assemble(const ConnectMap &spty, const double *val);

  /// copy and convert when necessary
  void assemble(const CsrMatrix<double> &a);

  /// copy and convert when necessary
  void assemble(const CsrMatrix<float> &a);

  /// copy and convert when necessary
  void assemble(const CsrMatrix<std::complex<double> > &a);

  /// copy and convert when necessary
  void assemble(const CsrMatrix<std::complex<float> > &a);

  /// numerical factorization setup
  void symbolicFactorization(int nrows);

  /// actual numerical factorization
  void numericalFactorization();

  /// access pointer to right-hand side object
  DenseMtx *rightSide() {return m_mb;}

  /// solve step only, uses internal matrix objects
  DenseMtx *bridgeSolve(int nrows, int ncols);

  /// transfer to spooles dense matrix object
  void transfer(int nrows, int ncols, const double *p, DenseMtx *pm) const;

  /// transfer to spooles dense matrix object
  void transfer(int nrows, int ncols, const std::complex<double> *p,
                DenseMtx *pm) const
  {
    assert(m_etype == SpoolesBase::Complex);
    transfer(nrows, ncols, reinterpret_cast<const double*>(p), pm);
  }

  /// transfer to spooles dense matrix object
  void transfer(int nrows, int ncols, const float *p, DenseMtx *pm) const;

  /// transfer to spooles dense matrix object
  void transfer(int nrows, int ncols, const std::complex<float> *p,
                DenseMtx *pm) const
  {
    assert(m_etype == SpoolesBase::Complex);
    transfer(nrows, ncols, reinterpret_cast<const float*>(p), pm);
  }

  /// transfer from spooles dense matrix object
  void transfer(DenseMtx *pm, int nrows, int ncols, double *p) const;

  /// transfer from spooles dense matrix object
  void transfer(DenseMtx *pm, int nrows, int ncols,
                std::complex<double> *p) const
  {
    assert(m_etype == SpoolesBase::Complex);
    transfer(pm, nrows, ncols, reinterpret_cast<double*>(p));
  }

  /// transfer to spooles dense matrix object
  void transfer(DenseMtx *pm, int nrows, int ncols, float *p) const;

  /// transfer from spooles dense matrix object
  void transfer(DenseMtx *pm, int nrows, int ncols,
                std::complex<float> *p) const
  {
    assert(m_etype == SpoolesBase::Complex);
    transfer(pm, nrows, ncols, reinterpret_cast<float*>(p));
  }

protected:

  /// input object used to pass system matrix to library
  InpMtx *m_inp = nullptr;

  /// helper object for the factor stage
  BridgeMT *m_bridge = nullptr;

  /// dense matrices x and b
  DenseMtx *m_mx = nullptr, *m_mb = nullptr;

  /// entry type of the current matrix
  int m_etype, m_symflag;

  /// level of verbosity
  int m_msglevel;

  /// number of threads to use
  uint m_nthread;

  /// lookahead parameter for parallel factorizations
  uint m_lookahead;

  /// build an approximate or exact factorization?
  bool m_exactFactor;

  /// pivoting or not?
  bool m_pivoting;

  /// pivoting value
  double m_taupivot;

  /// drop tolerance for approximate factorization
  double m_droptol;

  /// whether the matrix is already permuted
  bool m_permuted;
};

template <>
struct SpoolesBase::TypeMap<float> {
  static const SpoolesBase::ElementType value = SpoolesBase::Real;
  static const bool convert = true;
};

template <>
struct SpoolesBase::TypeMap<double> {
  static const SpoolesBase::ElementType value = SpoolesBase::Real;
  static const bool convert = false;
};

template <>
struct SpoolesBase::TypeMap<std::complex<float> > {
  static const SpoolesBase::ElementType value = SpoolesBase::Complex;
  static const bool convert = true;
};

template <>
struct SpoolesBase::TypeMap<std::complex<double> > {
  static const SpoolesBase::ElementType value = SpoolesBase::Complex;
  static const bool convert = false;
};

/** Interface for SPOOLES sparse solver.
 *
 *  This wrapper provides an interface for the public-domain SPOOLES solver for
 *  sparse, symmetric or unsymmetric, real- or complex-valued linear systems.
 *
 *  http://www.netlib.org/linalg/spooles/spooles.2.2.html
 *
 * \ingroup numerics
 * \sa AbstractLinearSolverTpl
 */
template <typename FloatType>
class SpoolesSolver : public AbstractLinearSolverTpl<FloatType>
{
public:

  typedef AbstractLinearSolverTpl<FloatType> Base;

  /// construct solver object
  SpoolesSolver(uint typeflag) : Base(typeflag),
    m_context(SpoolesBase::mapSymmetry(typeflag),
    SpoolesBase::mapElementType(typeflag))
  {
    Base::m_implName = "spooles";
  }

  /// configure context
  void configure(const ConfigParser &cfg) {
    m_context.configure(cfg);
  }

  /// perform full factorization
  bool factor(const CsrMatrix<FloatType> *pa) {
    ScopeTimer timer( Base::m_factorTime );
    m_pa = pa;
    m_context.assemble(*m_pa);
    m_context.symbolicFactorization(m_pa->nrows());
    m_context.numericalFactorization();
    ++Base::m_factorCount;
    return true;
  }

  /// perform numerical factorization of a new matrix with the same pattern
  bool refactor(const CsrMatrix<FloatType> *pa) {
    ScopeTimer timer( Base::m_factorTime );
    m_pa = pa;
    m_context.assemble(*m_pa);
    m_context.numericalFactorization();
    ++Base::m_factorCount;
    return true;
  }

  /// solve system once a factorization is available
  bool solve(const DMatrix<FloatType> &b, DMatrix<FloatType> &x) {
    ScopeTimer timer( Base::m_solveTime );
    m_context.transfer(b.nrows(), b.ncols(), b.pointer(),
                       m_context.rightSide());
    DenseMtx *pmx = m_context.bridgeSolve(b.nrows(), b.ncols());
    x.allocate(b.nrows(), b.ncols());
    m_context.transfer(pmx, b.nrows(), b.ncols(), x.pointer());
    ++Base::m_solveCount;
    return true;
  }

  /// solve system once a factorization is available
  bool solve(const DVector<FloatType> &b, DVector<FloatType> &x) {
    ScopeTimer timer( AbstractLinearSolverTpl<FloatType>::m_solveTime );
    m_context.transfer(b.size(), 1, b.pointer(), m_context.rightSide());
    DenseMtx *pmx = m_context.bridgeSolve(b.size(), 1);
    x.allocate(b.size());
    m_context.transfer(pmx, b.size(), 1, x.pointer());
    ++Base::m_solveCount;
    return true;
  }

protected:

  /// the matrix currently factored
  const CsrMatrix<FloatType> *m_pa;

  /// wrapper around the spooles solver
  SpoolesBase m_context;
};

#endif // SPOOLESSOLVER_H
