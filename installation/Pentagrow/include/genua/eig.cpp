
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

#include "eig.h"
#include "lapack_interface.h"
#include "xcept.h"

using namespace std;

// ------------------- Symmetric Standard ------------------------------------

template <class MatrixType, class VectorType>
static inline int sym_eig_tpl(const MatrixType &a, VectorType &eval)
{
  assert(a.nrows() == a.ncols());
  assert(eval.size() == a.nrows());

#ifndef HAVE_NO_LAPACK

  typedef typename MatrixType::value_type value_type;
  // typedef typename detail::real_version<value_type> real_type;
  typedef DVector<value_type> WorkArray;
  lapack::lpint status, n(a.nrows());
  WorkArray work;
  DVector<int> iwork;

  // workspace query
  MatrixType acopy(a);
  lapack::syevd('V', 'U', n, acopy.pointer(), n, eval.pointer(),
                &(work[0]), -1, &(iwork[0]), -1, status);

  if (status != 0)
    return status;

  work.resize((size_t)std::real(work[0]));
  iwork.resize((size_t)iwork[0]);

  // decomposition
  lapack::syevd('V', 'U', n, acopy.pointer(), n, eval.pointer(),
                &(work[0]), work.size(),
                &(iwork[0]), iwork.size(), status);

  return status;

#else

  typedef typename MatrixType::EigenMatrix EigenMatrix;
  const int option = eeigen::EigenvaluesOnly;
  eeigen::SelfAdjointEigenSolver<EigenMatrix> solver(a.cmap(), option);
  eval.mmap() = solver.eigenvalues();
  return (solver.info() == eeigen::Success) ? 0 : -1;

#endif
}

template <class MatrixType, class VectorType>
static inline void sym_eig_tpl(const MatrixType &a, VectorType &eval,
                               MatrixType &z)
{
  assert(a.nrows() == a.ncols());

#ifndef HAVE_NO_LAPACK

  typedef std::vector<typename MatrixType::value_type> WorkArray;
  lapack::lpint status, n(a.nrows());
  WorkArray work(1 + 6 * n + 2 * n * n);
  std::vector<int> iwork(3 + 5 * n);

  // workspace query
  eval.resize(n);
  z = a;
  lapack::syevd('V', 'U', n, z.pointer(), n, eval.pointer(),
                &(work[0]), -1, &(iwork[0]), -1, status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (*syevd).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }

  work.resize((size_t)std::real(work[0]));
  iwork.resize((size_t)iwork[0]);

  // decomposition
  lapack::syevd('V', 'U', n, z.pointer(), n, eval.pointer(),
                &(work[0]), work.size(),
                &(iwork[0]), iwork.size(), status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (*syevd).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }

#else

  eval.allocate(a.nrows());
  z.allocate(a.nrows(), a.ncols());

  typedef typename MatrixType::EigenMatrix EigenMatrix;
  const int option = eeigen::ComputeEigenvectors;
  eeigen::SelfAdjointEigenSolver<EigenMatrix> solver(a.cmap(), option);
  if (solver.info() != eeigen::Success)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in eeigen::SelfAdjointEigenSolver.\n";
    ss << "info = " << int(solver.info());
    throw Error(ss.str());
  }

  eval.mmap() = solver.eigenvalues();
  z.mmap() = solver.eigenvectors();

#endif
}

// instantiate obverloads

int sym_eig(const DMatrix<float> &a, DVector<float> &lambda)
{
  return sym_eig_tpl(a, lambda);
}

void sym_eig(const DMatrix<float> &a, DVector<float> &lambda,
             DMatrix<float> &z)
{
  sym_eig_tpl(a, lambda, z);
}

int sym_eig(const DMatrix<double> &a, DVector<double> &lambda)
{
  return sym_eig_tpl(a, lambda);
}

void sym_eig(const DMatrix<double> &a, DVector<double> &lambda,
             DMatrix<double> &z)
{
  sym_eig_tpl(a, lambda, z);
}

// ---------------- Non-symmetric Standard -----------------------------------

template <class MatrixType, class CpxVectorType>
int real_eig_tpl(const MatrixType &a, CpxVectorType &lambda)
{
  assert(a.nrows() == a.ncols());

#ifndef HAVE_NO_LAPACK

  typedef typename CpxVectorType::value_type complex_type;
  typedef DVector<typename MatrixType::value_type> WorkArray;
  lapack::lpint status, n(a.nrows());
  WorkArray wi(n), wr(n), work(n);
  MatrixType b(a), u, v;

  u.resize(n, n);
  v.resize(n, n);

  // workspace query
  lapack::geev('N', 'N', n, b.pointer(), n, &(wr[0]), &(wi[0]),
               u.pointer(), n, v.pointer(), n,
               &(work[0]), -1, status);

  if (status != 0)
    return status;

  work.resize((size_t)work[0]);

  // decomposition
  lapack::geev('N', 'N', n, b.pointer(), n, &(wr[0]), &(wi[0]),
               u.pointer(), n, v.pointer(), n,
               &(work[0]), work.size(), status);

  if (status != 0)
    return status;

  lambda.resize(n);
  for (int i = 0; i < n; ++i)
    lambda[i] = complex_type(wr[i], wi[i]);

  return 0;

#else

  lambda.allocate(a.nrows());

  typedef typename MatrixType::EigenMatrix EigenMatrix;
  eeigen::EigenSolver<EigenMatrix> solver(a.cmap(), false);
  if (solver.info() != eeigen::Success)
    return 1;

  lambda.mmap() = solver.eigenvalues();
  return 0;

#endif
}

template <class CpxMatrixType, class CpxVectorType>
int cplx_eig_tpl(const CpxMatrixType &a, CpxVectorType &lambda)
{
  assert(a.nrows() == a.ncols());

#ifndef HAVE_NO_LAPACK

  typedef typename CpxVectorType::value_type complex_type;
  typedef typename detail::real_version<complex_type>::real_type real_type;
  typedef DVector<complex_type> CWorkArray;
  typedef DVector<real_type> RWorkArray;
  lapack::lpint status, n(a.nrows());
  CWorkArray cwork;
  RWorkArray rwork(2 * n);

  CpxMatrixType b(a), u(n, n), v(n, n);

  // workspace query
  lambda.resize(n);
  lapack::geev('N', 'N', n, b.pointer(), n, lambda.pointer(),
               u.pointer(), n, v.pointer(), n,
               cwork.pointer(), -1, rwork.pointer(), status);

  if (status != 0)
    return status;

  size_t lwork = std::max(size_t(2 * n), size_t(std::real(cwork[0])));
  cwork.resize(lwork);

  // decomposition
  lapack::geev('N', 'N', n, b.pointer(), n, lambda.pointer(),
               u.pointer(), n, v.pointer(), n,
               cwork.pointer(), cwork.size(), rwork.pointer(), status);

  if (status != 0)
    return status;

  return 0;

#else

  lambda.allocate(a.nrows());

  typedef typename CpxMatrixType::EigenMatrix EigenMatrix;
  eeigen::ComplexEigenSolver<EigenMatrix> solver(a.cmap(), false);
  if (solver.info() != eeigen::Success)
    return 1;

  lambda.mmap() = solver.eigenvalues();
  return 0;

#endif
}

// instanciated overloads

int eig(const DMatrix<float> &a, DVector<std::complex<float>> &lambda)
{
  return real_eig_tpl(a, lambda);
}

int eig(const DMatrix<double> &a, DVector<std::complex<double>> &lambda)
{
  return real_eig_tpl(a, lambda);
}

int eig(const DMatrix<std::complex<float>> &a,
        DVector<std::complex<float>> &lambda)
{
  return cplx_eig_tpl(a, lambda);
}

int eig(const DMatrix<std::complex<double>> &a,
        DVector<std::complex<double>> &lambda)
{
  return cplx_eig_tpl(a, lambda);
}

#ifndef HAVE_NO_LAPACK

template <class MatrixType, class CpxVectorType>
void real_eig_tpl(const MatrixType &a, CpxVectorType &lambda,
                  MatrixType &u, MatrixType &v)
{
  assert(a.nrows() == a.ncols());

  typedef typename CpxVectorType::value_type complex_type;
  typedef std::vector<typename MatrixType::value_type> WorkArray;
  lapack::lpint status, n(a.nrows());
  WorkArray wi(n), wr(n), work(n);
  MatrixType b(a);

  u.resize(n, n);
  v.resize(n, n);

  // workspace query
  lapack::geev('V', 'V', n, b.pointer(), n, &(wr[0]), &(wi[0]),
               u.pointer(), n, v.pointer(), n, &(work[0]), -1, status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (*geev).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }
  work.resize((size_t)work[0]);

  // decomposition
  lapack::geev('V', 'V', n, b.pointer(), n, &(wr[0]), &(wi[0]),
               u.pointer(), n, v.pointer(), n, &(work[0]), work.size(), status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (*geev).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }

  lambda.resize(n);
  for (int i = 0; i < n; ++i)
    lambda[i] = complex_type(wr[i], wi[i]);
}

template <class CpxMatrixType, class CpxVectorType>
void cplx_eig_tpl(const CpxMatrixType &a, CpxVectorType &lambda,
                  CpxMatrixType &u, CpxMatrixType &v)
{
  assert(a.nrows() == a.ncols());

  typedef typename CpxVectorType::value_type complex_type;
  typedef typename detail::real_version<complex_type>::real_type real_type;
  typedef DVector<complex_type> CWorkArray;
  typedef DVector<real_type> RWorkArray;
  lapack::lpint status, n(a.nrows());
  CWorkArray cwork;
  RWorkArray rwork(2 * n);

  CpxMatrixType b(a);

  // workspace query
  lambda.resize(n);
  u.resize(n, n);
  v.resize(n, n);
  lapack::geev('V', 'V', n, b.pointer(), n, lambda.pointer(),
               u.pointer(), n, v.pointer(), n,
               cwork.pointer(), -1, rwork.pointer(), status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (*geev).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }

  size_t lwork = std::max(size_t(2 * n), size_t(std::real(cwork[0])));
  cwork.resize(lwork);

  // decomposition
  lapack::geev('V', 'V', n, b.pointer(), n, lambda.pointer(),
               u.pointer(), n, v.pointer(), n,
               cwork.pointer(), cwork.size(), rwork.pointer(), status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (*geev).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }
}

void eig(const DMatrix<float> &a, DVector<std::complex<float>> &lambda,
         DMatrix<float> &u, DMatrix<float> &v)
{
  real_eig_tpl(a, lambda, u, v);
}

void eig(const DMatrix<double> &a, DVector<std::complex<double>> &lambda,
         DMatrix<double> &u, DMatrix<double> &v)
{
  real_eig_tpl(a, lambda, u, v);
}

void eig(const DMatrix<std::complex<float>> &a,
         DVector<std::complex<float>> &lambda,
         DMatrix<std::complex<float>> &u,
         DMatrix<std::complex<float>> &v)
{
  cplx_eig_tpl(a, lambda, u, v);
}

void eig(const DMatrix<std::complex<double>> &a,
         DVector<std::complex<double>> &lambda,
         DMatrix<std::complex<double>> &u,
         DMatrix<std::complex<double>> &v)
{
  cplx_eig_tpl(a, lambda, u, v);
}

// ---------------- Generalized ---------------------------------------------

void gen_eig(const CpxMatrix &a, const CpxMatrix &b, CpxVector &lambda)
{
  assert(a.nrows() == a.ncols());
  assert(b.nrows() == b.ncols());
  assert(a.nrows() == b.nrows());

  lapack::lpint status, n(a.nrows()), lwork(2 * a.nrows());
  CpxMatrix ac(a), bc(b);
  CpxVector work(2 * n), alpha(n), beta(n);
  Vector rwork(8 * n);

  // workspace query
  lapack::zggev_('N', 'N', n, ac.pointer(), n, bc.pointer(), n,
                 alpha.pointer(), beta.pointer(),
                 0, n, 0, n,
                 work.pointer(), -1, rwork.pointer(), status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (zggev).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }
  lwork = static_cast<int>(real(work[0]));
  lwork = max(lwork, 2 * n);
  work.resize(lwork);

  // compute eigenvalues
  lapack::zggev_('N', 'N', n, ac.pointer(), n, bc.pointer(), n,
                 alpha.pointer(), beta.pointer(),
                 0, n, 0, n,
                 work.pointer(), lwork, rwork.pointer(), status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (zggev).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }

  lambda.resize(n);
  for (int i = 0; i < n; ++i)
    lambda[i] = alpha[i] / beta[i];
}

void gen_eig(const CpxMatrix &a, const CpxMatrix &b, CpxVector &lambda,
             CpxMatrix &u, CpxMatrix &v)
{
  assert(a.nrows() == a.ncols());
  assert(b.nrows() == b.ncols());
  assert(a.nrows() == b.nrows());

  int status, n(a.nrows()), lwork(2 * a.nrows());
  CpxMatrix ac(a), bc(b);
  CpxVector work(2 * n), alpha(n), beta(n);
  Vector rwork(8 * n);

  u.resize(n, n);
  v.resize(n, n);

  // workspace query
  lapack::zggev_('V', 'V', n, ac.pointer(), n, bc.pointer(), n,
                 alpha.pointer(), beta.pointer(),
                 u.pointer(), n, v.pointer(), n,
                 work.pointer(), -1, rwork.pointer(), status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (zggev).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }
  lwork = static_cast<int>(real(work[0]));
  lwork = max(lwork, 2 * n);
  work.resize(lwork);

  // compute eigenvalues
  lapack::zggev_('V', 'V', n, ac.pointer(), n, bc.pointer(), n,
                 alpha.pointer(), beta.pointer(),
                 u.pointer(), n, v.pointer(), n,
                 work.pointer(), lwork, rwork.pointer(), status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (zggev).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }

  lambda.resize(n);
  for (int i = 0; i < n; ++i)
    lambda[i] = alpha[i] / beta[i];
}

void gen_eig(const CpxMatrix &a, const CpxMatrix &b,
             CpxVector &lambda, CpxMatrix &v)
{
  assert(a.nrows() == a.ncols());
  assert(b.nrows() == b.ncols());
  assert(a.nrows() == b.nrows());

  int status, n(a.nrows()), lwork(2 * a.nrows());
  CpxMatrix ac(a), bc(b);
  CpxVector work(2 * n), alpha(n), beta(n);
  Vector rwork(8 * n);

  v.resize(n, n);

  // workspace query
  lapack::zggev_('N', 'V', n, ac.pointer(), n, bc.pointer(), n,
                 alpha.pointer(), beta.pointer(),
                 v.pointer(), n, v.pointer(), n,
                 work.pointer(), -1, rwork.pointer(), status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (zggev).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }
  lwork = static_cast<int>(real(work[0]));
  lwork = max(lwork, 2 * n);
  work.resize(lwork);

  // compute eigenvalues
  lapack::zggev_('N', 'V', n, ac.pointer(), n, bc.pointer(), n,
                 alpha.pointer(), beta.pointer(),
                 v.pointer(), n, v.pointer(), n,
                 work.pointer(), lwork, rwork.pointer(), status);

  if (status != 0)
  {
    std::stringstream ss;
    ss << "Eigenvalue decompositon failed in Lapack (zggev).\n";
    ss << "info = " << status;
    throw Error(ss.str());
  }

  lambda.resize(n);
  for (int i = 0; i < n; ++i)
    lambda[i] = alpha[i] / beta[i];
}

#endif
