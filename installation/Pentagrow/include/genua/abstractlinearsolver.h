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

#ifndef ABSTRACTLINEARSOLVER_H
#define ABSTRACTLINEARSOLVER_H

#include "forward.h"
#include "defines.h"
#include "csrmatrix.h"
#include "typecode.h"
#include "dmatrix.h"
#include "timing.h"
#include <boost/shared_array.hpp>

namespace detail {

enum TypeTag { Unknown, Int32, Int64, Float32, Float64, Complex64, Complex128 };

template <typename SolverType>
inline int create_solver_typetag() {
  return Unknown;
}

template <>
inline int create_solver_typetag<float>() {return Float32;}

template <>
inline int create_solver_typetag<double>() {return Float64;}

template <>
inline int create_solver_typetag<std::complex<float> >() {return Complex64;}

template <>
inline int create_solver_typetag<std::complex<double> >() {return Complex128;}

template <>
inline int create_solver_typetag<int>() {return Int32;}

template <>
inline int create_solver_typetag<unsigned int>() {return Int32;}

template <>
inline int create_solver_typetag<int64_t>() {return Int64;}

template <>
inline int create_solver_typetag<uint64_t>() {return Int64;}

}

/** Utility to differentiate sparse matrix types.
 *
 *  The wrapper classes for the linear solvers used below depend on a way
 *  to identify which type of matrix is to be factored. This simple container
 *  for a few constants is used to pass information about matrix properties to
 *  the solver constructor.
 *
 * \ingroup numerics
 * \sa AbstractLinearSolverTpl
 */
class SpMatrixFlag
{
public:

  enum Symmetry { Unsymmetric = 1, Symmetric,
                  Hermitian, StructurallySymmetric };
  enum Value { IndexOnly = 1, RealValued, ComplexValued };
  enum Definity { PositiveDefinite = 1, Indefinite };
  enum Squarity { Square = 0, Rectangular };

  /// matrix type, uses 4 bits for each field
  enum Type { RealUnsymmetric = Unsymmetric | (RealValued << 4),
              ComplexUnsymmetric = Unsymmetric | (ComplexValued << 4),

              RealStructuralSym = StructurallySymmetric | (RealValued << 4),
              ComplexStructuralSym = StructurallySymmetric | (ComplexValued << 4),

              RealPositiveDefinite = Symmetric | (RealValued << 4)
              | (PositiveDefinite << 8),
              ComplexPositiveDefinite = Symmetric | (ComplexValued << 4)
              | (PositiveDefinite << 8),

              RealSymIndefinite = Symmetric | (RealValued << 4)
              | (Indefinite << 8),
              ComplexHermIndefinite = Hermitian | (ComplexValued << 4)
              | (Indefinite << 8),
              ComplexSymmetric = Symmetric | (ComplexValued << 4),
              RealRectangular = RealValued | (Rectangular << 12),
              ComplexRectangular = ComplexValued | (Rectangular << 12)};

  /// extract component
  static uint symmetryFlag(uint t) { return (t & 15); }

  /// extract component
  static uint valueFlag(uint t) { return ( (t >> 4) & 15); }

  /// extract component
  static uint definiteFlag(uint t) { return ( (t >> 8) & 15); }

  /// extract component
  static uint rectangularFlag(uint t) { return ( (t >> 12) & 15); }

  /// matrix property tests
  static bool isSymmetric(uint t) { return symmetryFlag(t) == Symmetric; }

  /// matrix property tests
  static bool isReal(uint t) { return valueFlag(t) == RealValued; }

  /// matrix property tests
  static bool isComplex(uint t) { return valueFlag(t) == ComplexValued; }

  /// matrix property tests
  static bool isDefinite(uint t) {
    return (definiteFlag(t) == PositiveDefinite);
  }

  /// matrix property tests
  static bool isSquare(uint t) { return rectangularFlag(t) == Square; }
};

/** Templated interface for linear solver.
 *
 * This template class defines the common interface for all of the wrappers
 * around linear solvers. This is useful to allow switching between different
 * solvers at runtime.
 *
 * Note that not all backend solvers actually support
 * all matrix types and all precisions.
 *
 * \ingroup numerics
 * \sa SpoolesSolver, PardisoSolver, SparseQR, EigenSparseLU, EigenSparseChol
 */
template <class FloatType>
class AbstractLinearSolverTpl
{
public:

  typedef AbstractLinearSolverTpl<FloatType> SolverType;
  typedef boost::shared_ptr<SolverType> SolverPtr;

  /// default construction for undefined matrix type
  AbstractLinearSolverTpl()
    : m_mtxflags(0), m_factorTime(0), m_solveTime(0), m_maxMemory(0),
      m_factorCount(0), m_solveCount(0) {}

  /// construction for defined matrix type
  AbstractLinearSolverTpl(uint typeflag)
    : m_mtxflags(typeflag), m_factorTime(0), m_solveTime(0), m_maxMemory(0),
      m_factorCount(0), m_solveCount(0) {}

  /// virtual destructor
  virtual ~AbstractLinearSolverTpl() {}

  /// the matrix type for which this solver has been instantiated
  uint matrixType() const {return m_mtxflags;}

  /// solver name (libary/implementation)
  const std::string & name() const {return m_implName;}

  /// load configuration settings
  virtual void configure(const ConfigParser &) {}

  /// full factorization (minimum interface)
  virtual bool factor(const CsrMatrix<FloatType,1> *pa) = 0;

  /// numerical factorization only (if supported)
  virtual bool refactor(const CsrMatrix<FloatType,1> *pa) { return factor(pa); }

  /// request to solve the transposed problem (not always supported)
  void transposed(bool flag) { m_solveTransposed = flag; }

  /// solve with multiple rhs
  virtual bool solve(const DMatrix<FloatType> &b, DMatrix<FloatType> &x) = 0;

  /// solve single RHS (by default implemented in terms of the above)
  virtual bool solve(const DVector<FloatType> &b, DVector<FloatType> &x) {
    size_t n = b.size();
    DMatrix<FloatType> bm(n,1), xm(n,1);
    memcpy(bm.pointer(), b.pointer(), n*sizeof(FloatType));
    bool stat = solve(bm, xm);
    memcpy(x.pointer(), xm.pointer(), n*sizeof(FloatType));
    return stat;
  }

  /// single-shot solve (may be more efficient for some solvers)
  virtual bool solve(const CsrMatrix<FloatType,1> *pa,
                     const DMatrix<FloatType> &b, DMatrix<FloatType> &x)
  {
    bool stat(true);
    stat &= factor(pa);
    if (stat)
      stat &= solve(b,x);
    return stat;
  }

  /// single-shot solve (may be more efficient for some solvers)
  virtual bool solve(const CsrMatrix<FloatType,1> *pa,
                     const DVector<FloatType> &b, DVector<FloatType> &x)
  {
    bool stat(true);
    stat &= factor(pa);
    if (stat)
      stat &= solve(b,x);
    return stat;
  }

  /// solution with new values in A, but the same non-zero pattern
  virtual bool resolve(const CsrMatrix<FloatType,1> *pa,
                       const DMatrix<FloatType> &b, DMatrix<FloatType> &x)
  {
    bool stat(true);
    stat &= refactor(pa);
    if (stat)
      stat &= solve(b,x);
    return stat;
  }

  /// solution with new values in A, but the same non-zero pattern
  virtual bool resolve(const CsrMatrix<FloatType,1> *pa,
                       const DVector<FloatType> &b, DVector<FloatType> &x)
  {
    bool stat(true);
    stat &= refactor(pa);
    if (stat)
      stat &= solve(b,x);
    return stat;
  }

  /// number of (re-) factorizations
  size_t factorizations() const {return m_factorCount;}

  /// number of (re-) factorizations
  size_t solves() const {return m_solveCount;}

  /// access timing data (if supported by implementation)
  virtual float factorTime() const {return m_factorTime;}

  /// access timing data (if supported by implementation)
  virtual float solveTime() const {return m_solveTime;}

  /// memory, in Megabyte, as reported by solver (if possible)
  virtual float maxMemory() const {return m_maxMemory;}

  /// release internal storage
  virtual void release() {}

  /// return estimated condition number after factorization (if supported)
  virtual double condest() {return 0.0;}

  /// enable diagnostid printing
  void verbose(bool flag) { m_verbose = flag ? 1 : 0;}

  /** Create a new instance of any solver which is supported by the library.
   *  Use this interface only when there really is no preferred choice of the
   *  solver implementation. The current interface will return an MKL PARDISO
   *  interface, a SPOOLES interface, or a SparseQR interface when one of those
   *  is supported by the compiled library.
   */
  static SolverPtr create(uint /* typeflag */) {
    return nullptr;
  }

protected:

  /// matrix property tests
  bool isSymmetric() { return SpMatrixFlag::isSymmetric(m_mtxflags); }

  /// matrix property tests
  bool isReal() { return SpMatrixFlag::isReal(m_mtxflags); }

  /// matrix property tests
  bool isComplex() { return SpMatrixFlag::isComplex(m_mtxflags); }

protected:

  /// matrix type flag
  uint m_mtxflags;

  /// implementation/solver/library name for logging
  std::string m_implName;

  /// timing data; only useful if child classes set these values
  mutable float m_factorTime, m_solveTime, m_maxMemory;

  /// call statistics; only useful if child classes set these values
  mutable size_t m_factorCount, m_solveCount;

  /// whether to solve the transposed problem A^T x = b
  bool m_solveTransposed = false;

  /// print diagnostic info?
  int m_verbose = 0;
};

template <>
SSparseSolverPtr AbstractLinearSolverTpl<float>::create(uint typeflag);

template <>
DSparseSolverPtr AbstractLinearSolverTpl<double>::create(uint typeflag);

template <>
CSparseSolverPtr
AbstractLinearSolverTpl<std::complex<float> >::create(uint typeflag);

template <>
ZSparseSolverPtr
AbstractLinearSolverTpl<std::complex<double> >::create(uint typeflag);

#endif // ABSTRACTLINEARSOLVER_H
