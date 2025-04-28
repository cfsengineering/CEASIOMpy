
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
 
#ifndef GENUA_PARDISOSOLVER_H
#define GENUA_PARDISOSOLVER_H

#include "forward.h"
#include "abstractlinearsolver.h"
#include "csrmatrix.h"
#include "typecode.h"

/** Internal wrapper object for MKL PARDISO.
 *
 *  This is a type-independent class which serves as a parent for the template
 *  classes for different floating-point types (float/double/scomplex/dcomplex).
 *
 * \internal
 */
class PardisoBase
{
public:

  /// supported matrix types
  enum MatrixType { ComplexHermitianIndefinite = -4,
                    RealSymmetricIndefinite = -2,
                    UnknownMatrixType = 0,
                    RealStructurallySymmetric = 1,
                    RealPositiveDefinite = 2,
                    ComplexStructurallySymmetric = 3,
                    ComplexPositiveDefinite = 4,
                    ComplexSymmetric = 6,
                    RealUnsymmetric = 11,
                    ComplexUnsymmetric = 13 };

  /// factorization precision
  enum PrecisionType { DoublePrecision = 0,
                       SinglePrecision = 1 };

  /// solve transposed system A^T x = b ?
  enum Transposition { NoTransposition = 0,
                       Hermitian = 1,
                       Transposed = 2 };

  /// initialize library and configuration
  PardisoBase();

  /// initialize library and configuration
  PardisoBase(MatrixType t);

  /// release memory
  virtual ~PardisoBase();

  /// configure solver settings
  void configureBase(const ConfigParser &cfg);

  /// set default values
  void setDefaults(MatrixType t);

  /// set PARDISO input option, uses 1-based indexing
  void setOption(int iopt, int val) {
    assert(iopt > 0 and iopt <= 64);
    m_iparm[iopt-1] = val;
  }

  /// get PARDISO output option, uses 1-based indexing
  int getOption(int iopt) const {
    assert(iopt > 0 and iopt <= 64);
    return m_iparm[iopt-1];
  }

  /// solve a transposed problem A^T x = b using an factorization of A
  void solveTransposed(Transposition t) {
    setOption(11, int(t));
  }

protected:

  /// map matrix type flag conversion
  static MatrixType pardisoMatrixType(uint flags);

  /// initialize internal data structures
  void init();

  /// release memory
  void release();

  /// compute memory highwater mark
  float highwaterMemory() const;

  /// determine whether a matrix type counts as symmetric
  static bool isSymmetric(MatrixType t);

  /// set single/double precision option
  template <typename FloatType>
  void setFloatType() {
    TypeCode tc = create_typecode<FloatType>();
    if (tc.value() == TypeCode::Float32
        or tc.value() == TypeCode::Complex64)
      setOption(28, (int) PardisoBase::SinglePrecision);
    else if (tc.value() == TypeCode::Float64
             or tc.value() == TypeCode::Complex128)
      setOption(28, (int) PardisoBase::DoublePrecision);
    else
      throw Error("PardisoSolver: Precision not supported.");
  }

  /// type-neutral call into MKL library
  void backend(int phs, int nrows, const int *rowPtr, const int *colIdx,
               const void *nzValues, void *bptr, void *xptr);

  /// type-neutral call to retrieve diagonal
  void getDiagonal(void *padia, void *pfdia);

  /// template interface for the above
  template <typename FloatType>
  void backend(int phs, const CsrMatrix<FloatType> &a)
  {
    setFloatType<FloatType>();
    const ConnectMap & spty( a.sparsity() );
    this->backend( phs, a.nrows(),
                   (const int *) spty.rowPointer(),
                   (const int *) spty.colIndex(),
                   (const void *) a.pointer(),
                   (void *) 0, (void *) 0 );
  }

  /// template interface for the above
  template <typename FloatType>
  void backend(int phs, const CsrMatrix<FloatType> &a,
               const DVector<FloatType> &b, DVector<FloatType> &x)
  {
    m_nrhs = 1;
    setFloatType<FloatType>();
    const ConnectMap & spty( a.sparsity() );
    this->backend( phs, a.nrows(),
                   (const int *) spty.rowPointer(),
                   (const int *) spty.colIndex(),
                   (const void *) a.pointer(),
                   (void *) b.pointer(), (void *) x.pointer() );
  }

  /// template interface for the above
  template <typename FloatType>
  void backend(int phs, const CsrMatrix<FloatType> &a,
               const DMatrix<FloatType> &b, DMatrix<FloatType> &x)
  {
    m_nrhs = b.ncols();
    setFloatType<FloatType>();
    const ConnectMap & spty( a.sparsity() );
    this->backend( phs, a.nrows(),
                   (const int *) spty.rowPointer(),
                   (const int *) spty.colIndex(),
                   (const void *) a.pointer(),
                   (void *) b.pointer(), (void *) x.pointer() );
  }

  /// access diagonal of original and factored matrix
  template <typename FloatType>
  void getDiagonal(DVector<FloatType> &adia, DVector<FloatType> &fdia) {
    this->getDiagonal((void *) adia.pointer(), (void *) fdia.pointer());
  }

  /// handle error
  void bailout(int error) const;

protected:

  /// pardiso's internal data structure
  size_t m_pt[64];

  /// options
  int m_iparm[64];

  /// permutation computed by pardiso
  DVector<int> m_perm;

  /// type of matrix currently processed
  int m_mtyp;

  /// vebosity
  int m_msglevel;

  /// number of right-hand sides to process
  int m_nrhs;
};

/** Interface to PARDISO solver from MKL.
 *
 * This class adapts the sparse direct solver PARDISO from the Intel MKL
 * library to the interface fixed by the AbstractLinearSolverTpl template.
 *
 * Pardiso supports symmetric (definite and indefinite) linear systems in
 * single and double precsion as well as complex-valued problems.
 *
 * The configuration interface supports the following options (defaults shown)
 * \verbatim
 * PardisoParallelMetis = true
 * PardisoVerbose = false
 * PardisoCheckMatrix = false
 * PardisoTwoLevel = true
 * \endverbatim
 *
 * \ingroup numerics
 * \sa PardisoBase, AbstractLinearSolverTpl
 */
template <typename FloatType>
class PardisoSolver : public PardisoBase,
                      public AbstractLinearSolverTpl<FloatType>
{
public:

  typedef AbstractLinearSolverTpl<FloatType> SolverBase;

  /// initialize
  PardisoSolver() : PardisoBase(), SolverBase() {}

  /// initialize
  PardisoSolver(uint typeflag) : PardisoBase( PardisoBase::pardisoMatrixType(typeflag) ),
                                 SolverBase(typeflag)
                                  {this->m_implName = "mkl/pardiso";}

  /// configure Pardiso
  virtual void configure(const ConfigParser &cfg) {
    PardisoBase::configureBase(cfg);
  }

  /// full factorization
  virtual bool factor(const CsrMatrix<FloatType,1> *pa) {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_factorTime);
    m_pa = pa;
    PardisoBase::backend(12, *m_pa);
    SolverBase::m_maxMemory = highwaterMemory();
    ++SolverBase::m_factorCount;
    return true;
  }

  /// numerical factorization only, same sparsity pattern
  virtual bool refactor(const CsrMatrix<FloatType,1> *pa) {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_factorTime);
    m_pa = pa;
    PardisoBase::backend(22, *m_pa);
    SolverBase::m_maxMemory = highwaterMemory();
    ++SolverBase::m_factorCount;
    return true;
  }

  /// solve with multiple rhs
  virtual bool solve(const DMatrix<FloatType> &b, DMatrix<FloatType> &x) {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_solveTime);
    assert(m_pa != 0);
    PardisoBase::solveTransposed( SolverBase::m_solveTransposed ?
                                    PardisoBase::Transposed :
                                    PardisoBase::NoTransposition );
    PardisoBase::backend(33, *m_pa, b, x);
    ++SolverBase::m_solveCount;
    return true;
  }

  /// solve single RHS (by default implemented in terms of the above)
  virtual bool solve(const DVector<FloatType> &b, DVector<FloatType> &x) {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_solveTime);
    assert(m_pa != 0);
    PardisoBase::solveTransposed( SolverBase::m_solveTransposed ?
                                    PardisoBase::Transposed :
                                    PardisoBase::NoTransposition );
    PardisoBase::backend(33, *m_pa, b, x);
    ++SolverBase::m_solveCount;
    return true;
  }

  /// solve with multiple rhs
  virtual bool solve(const CsrMatrix<FloatType,1> *pa,
                     const DMatrix<FloatType> &b, DMatrix<FloatType> &x)
  {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_solveTime);
    m_pa = pa;
    PardisoBase::solveTransposed( SolverBase::m_solveTransposed ?
                                    PardisoBase::Transposed :
                                    PardisoBase::NoTransposition );
    PardisoBase::backend(13, *m_pa, b, x);
    ++SolverBase::m_solveCount;
    return true;
  }

  /// solve single RHS (by default implemented in terms of the above)
  virtual bool solve(const CsrMatrix<FloatType,1> *pa,
                     const DVector<FloatType> &b, DVector<FloatType> &x)
  {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_solveTime);
    m_pa = pa;
    PardisoBase::solveTransposed( SolverBase::m_solveTransposed ?
                                    PardisoBase::Transposed :
                                    PardisoBase::NoTransposition );
    PardisoBase::backend(13, *m_pa, b, x);
    ++SolverBase::m_solveCount;
    return true;
  }

  /// solve with multiple rhs
  virtual bool resolve(const CsrMatrix<FloatType,1> *pa,
                       const DMatrix<FloatType> &b, DMatrix<FloatType> &x)
  {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_solveTime);
    m_pa = pa;
    PardisoBase::solveTransposed( SolverBase::m_solveTransposed ?
                                    PardisoBase::Transposed :
                                    PardisoBase::NoTransposition );
    PardisoBase::backend(23, *m_pa, b, x);
    ++SolverBase::m_solveCount;
    return true;
  }

  /// solve single RHS (by default implemented in terms of the above)
  virtual bool resolve(const CsrMatrix<FloatType,1> *pa,
                       const DVector<FloatType> &b, DVector<FloatType> &x)
  {
    ScopeTimer timer(AbstractLinearSolverTpl<FloatType>::m_solveTime);
    m_pa = pa;
    PardisoBase::solveTransposed( SolverBase::m_solveTransposed ?
                                    PardisoBase::Transposed :
                                    PardisoBase::NoTransposition );
    PardisoBase::backend(23, *m_pa, b, x);
    ++SolverBase::m_solveCount;
    return true;
  }

  /// estimate condition number (only available after factorization)
  virtual double condest() {
    assert(m_pa != nullptr);
    const size_t n = m_pa->nrows();
    DVector<FloatType> adia(n, 1), fdia(n, 1);
    PardisoBase::getDiagonal(adia, fdia);
    double dmin = std::numeric_limits<double>::max();
    double dmax = 0;
    for (size_t i=0; i<n; ++i) {
      double v = std::abs( fdia[i] );
      dmin = std::fmin(dmin, v);
      dmax = std::fmax(dmax, v);
    }
    return dmax/dmin;
  }

private:

  /// pointer to matrix currently factored
  const CsrMatrix<FloatType,1> *m_pa;
};

#endif // PARDISOSOLVER_H
