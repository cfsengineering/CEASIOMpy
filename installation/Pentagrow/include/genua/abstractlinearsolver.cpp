
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

#include "abstractlinearsolver.h"

#ifdef HAVE_MKL_PARDISO
#include "pardisosolver.h"
#endif

#ifdef HAVE_SPOOLES
#include "spoolessolver.h"
#endif

#ifdef HAVE_SPQR
#include "sparseqr.h"
#include "cholmod.h"
#include "umfpacksolver.h"
#endif

#ifdef HAVE_EIGEN
#include <genua/eigensparsesolver.h>
#endif

template <typename FloatType>
static boost::shared_ptr<AbstractLinearSolverTpl<FloatType> >
new_preferred_dp_solver(uint typeflag)
{
  typedef AbstractLinearSolverTpl<FloatType> LocalSolver_t;
  typedef boost::shared_ptr<LocalSolver_t> LocalSolverPtr;

#if defined(HAVE_MKL_PARDISO)
  return LocalSolverPtr(new PardisoSolver<FloatType>(typeflag));
#elif defined(HAVE_SPQR)
  if (SpMatrixFlag::isSymmetric(typeflag) and SpMatrixFlag::isDefinite(typeflag))
    return LocalSolverPtr(new CholmodSolver<FloatType>(typeflag));
  else if (SpMatrixFlag::isSquare(typeflag))
    return LocalSolverPtr(new UmfpackSolver<FloatType>(typeflag));
  else
    return LocalSolverPtr(new SparseQR<FloatType>(typeflag));
#elif defined(HAVE_SPOOLES)
  return LocalSolverPtr(new SpoolesSolver<FloatType>(typeflag));
#elif defined(HAVE_EIGEN)
  if ( SpMatrixFlag::isSymmetric(typeflag) )
    return LocalSolverPtr(new EigenSparseChol<FloatType>(typeflag));
  else
    return LocalSolverPtr(new EigenSparseLU<FloatType>(typeflag));
#else
  throw Error("No sparse direct solver support in libgenua.");
#endif
}

// SuiteSparse SPQR does not support single precision without conversion

template <typename FloatType>
static boost::shared_ptr<AbstractLinearSolverTpl<FloatType> >
new_preferred_sp_solver(uint typeflag)
{
  typedef AbstractLinearSolverTpl<FloatType> LocalSolver_t;
  typedef boost::shared_ptr<LocalSolver_t> LocalSolverPtr;

#if defined(HAVE_MKL_PARDISO)
  return LocalSolverPtr(new PardisoSolver<FloatType>(typeflag));
#elif defined(HAVE_SPOOLES)
  return LocalSolverPtr(new SpoolesSolver<FloatType>(typeflag));
#elif defined(HAVE_EIGEN)
  if ( SpMatrixFlag::isSymmetric(typeflag) )
    return LocalSolverPtr(new EigenSparseChol<FloatType>(typeflag));
  else
    return LocalSolverPtr(new EigenSparseLU<FloatType>(typeflag));
#else
  throw Error("No single-precision sparse direct solver support in libgenua.");
#endif
}

// partial specializations

template<>
SSparseSolverPtr AbstractLinearSolverTpl<float>::create(uint typeflag)
{
  return new_preferred_sp_solver<float>(typeflag);
}

template<>
DSparseSolverPtr AbstractLinearSolverTpl<double>::create(uint typeflag)
{
  return new_preferred_dp_solver<double>(typeflag);
}

template<>
CSparseSolverPtr
AbstractLinearSolverTpl<std::complex<float> >::create(uint typeflag)
{
  return new_preferred_sp_solver<std::complex<float> >(typeflag);
}

template<>
ZSparseSolverPtr
AbstractLinearSolverTpl<std::complex<double> >::create(uint typeflag)
{
  return new_preferred_dp_solver<std::complex<double> >(typeflag);
}


// ---------------------------

//AbstractLinearSolver::AbstractLinearSolver()
//  : m_psa(0), m_pda(0), m_pca(0), m_pza(0),
//    m_pvalues(0), m_prowptr(0), m_pcolidx(0), m_nrows(0), m_ncols(0), m_nnz(0)
//{
//  m_valueType = detail::Unknown;
//  m_indexType = detail::Unknown;
//}

//void AbstractLinearSolver::configure(const ConfigParser &)
//{}

//void AbstractLinearSolver::initialize()
//{}

//void AbstractLinearSolver::assign(const CsrMatrix<float,1> *pa)
//{
//  m_psa = pa;
//  if (pa != 0) {
//    const ConnectMap &spty( pa->sparsity() );
//    this->assign( pa->nrows(), pa->ncols(), spty.nonzero(), spty.rowPointer(),
//                  spty.colIndex(), pa->pointer() );
//  }
//}

//void AbstractLinearSolver::assign(const CsrMatrix<double,1> *pa)
//{
//  m_pda = pa;
//  if (pa != 0) {
//    const ConnectMap &spty( pa->sparsity() );
//    this->assign( pa->nrows(), pa->ncols(), spty.nonzero(), spty.rowPointer(),
//                  spty.colIndex(), pa->pointer() );
//  }
//}

//void AbstractLinearSolver::assign(const CsrMatrix<std::complex<float>,1> *pa)
//{
//  m_pca = pa;
//  if (pa != 0) {
//    const ConnectMap &spty( pa->sparsity() );
//    this->assign( pa->nrows(), pa->ncols(), spty.nonzero(), spty.rowPointer(),
//                  spty.colIndex(), pa->pointer() );
//  }
//}

//void AbstractLinearSolver::assign(const CsrMatrix<std::complex<double>,1> *pa)
//{
//  m_pza = pa;
//  if (pa != 0) {
//    const ConnectMap &spty( pa->sparsity() );
//    this->assign( pa->nrows(), pa->ncols(), spty.nonzero(), spty.rowPointer(),
//                  spty.colIndex(), pa->pointer() );
//  }
//}

//bool AbstractLinearSolver::solve(const DMatrix<float> &b, DMatrix<float> &x)
//{
//  assert(b.nrows() == m_nrows);
//  assert(x.nrows() == m_ncols);
//  assert(b.ncols() == x.ncols());
//  assert( m_valueType == detail::Float32 );
//  return this->solve(b.ncols(), b.pointer(), x.pointer());
//}

//bool AbstractLinearSolver::solve(const DMatrix<double> &b, DMatrix<double> &x)
//{
//  assert(b.nrows() == m_nrows);
//  assert(x.nrows() == m_ncols);
//  assert(b.ncols() == x.ncols());
//  assert( m_valueType == detail::Float64 );
//  return this->solve(b.ncols(), b.pointer(), x.pointer());
//}

//bool AbstractLinearSolver::solve(const DMatrix<std::complex<float> > &b,
//                                 DMatrix<std::complex<float> > &x)
//{
//  assert(b.nrows() == m_nrows);
//  assert(x.nrows() == m_ncols);
//  assert(b.ncols() == x.ncols());
//  assert( m_valueType == detail::Complex64 );
//  return this->solve(b.ncols(), b.pointer(), x.pointer());
//}

//bool AbstractLinearSolver::solve(const DMatrix<std::complex<double> > &b,
//                                 DMatrix<std::complex<double> > &x)
//{
//  assert(b.nrows() == m_nrows);
//  assert(x.nrows() == m_ncols);
//  assert(b.ncols() == x.ncols());
//  assert( m_valueType == detail::Complex128 );
//  return this->solve(b.ncols(), b.pointer(), x.pointer());
//}

//bool AbstractLinearSolver::solve(const DVector<float> &b, DVector<float> &x)
//{
//  assert(b.size() == m_nrows);
//  assert(x.size() == m_ncols);
//  assert( m_valueType == detail::Float32 );
//  return this->solve(1, b.pointer(), x.pointer());
//}

//bool AbstractLinearSolver::solve(const DVector<double> &b, DVector<double> &x)
//{
//  assert(b.size() == m_nrows);
//  assert(x.size() == m_ncols);
//  assert( m_valueType == detail::Float64 );
//  return this->solve(1, b.pointer(), x.pointer());
//}

//bool AbstractLinearSolver::solve(const DVector<std::complex<float> > &b,
//                                 DVector<std::complex<float> > &x)
//{
//  assert(b.size() == m_nrows);
//  assert(x.size() == m_ncols);
//  assert( m_valueType == detail::Complex64 );
//  return this->solve(1, b.pointer(), x.pointer());
//}

//bool AbstractLinearSolver::solve(const DVector<std::complex<double> > &b,
//                                 DVector<std::complex<double> > &x)
//{
//  assert(b.size() == m_nrows);
//  assert(x.size() == m_ncols);
//  assert( m_valueType == detail::Complex128 );
//  return this->solve(1, b.pointer(), x.pointer());
//}

//void AbstractLinearSolver::release()
//{
//  m_psa = 0;
//  m_pda = 0;
//  m_pca = 0;
//  m_pza = 0;

//  m_pvalues = 0;
//  m_pcolidx = 0;
//  m_prowptr = 0;
//  m_nrows = 0;
//  m_ncols = 0;
//  m_nnz = 0;

//  m_valueType = detail::Unknown;
//  m_indexType = detail::Unknown;
//}




