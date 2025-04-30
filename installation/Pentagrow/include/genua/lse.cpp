
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
 
#include "lse.h"
#include "lapack_interface.h"
#include "dmatrix.h"
#include "xcept.h"

template <class MatrixType, class VectorType>
int lse_solve_mv(MatrixType &a, MatrixType &b, VectorType &c, VectorType &d,
                 VectorType &x)
{
 #ifndef HAVE_NO_LAPACK
  // workspace type
  typedef std::vector<typename MatrixType::value_type> WorkArray;

  lapack::lpint m = a.nrows();
  lapack::lpint n = a.ncols();
  lapack::lpint p = b.nrows();
  assert(b.ncols() >= size_t(n));
  assert(c.size() >= size_t(m));
  assert(d.size() >= size_t(p));
  lapack::lpint lda = a.ldim();
  lapack::lpint ldb = b.ldim();

  // allocate space for solution
  x.resize(n);

  // workspace
  lapack::lpint info, lwork(-1);
  WorkArray work(m + p + n);

  // workspace query
  lapack::gglse(m, n, p, a.pointer(), lda, b.pointer(), ldb, c.pointer(),
                d.pointer(), x.pointer(), &work[0], lwork, info);
  if (info != 0)
    return info;
  lwork = static_cast<lapack::lpint>(std::real(work[0]));
  work.resize(lwork);

  // work call
  lapack::gglse(m, n, p, a.pointer(), lda, b.pointer(), ldb, c.pointer(),
                d.pointer(), x.pointer(), &work[0], lwork, info);
  return info;

#else

  throw Error("libgenua compiled without LAPACK support:"
              " lse_solve not available.");
  return 0;

#endif
}

int lse_solve(DMatrix<float> &a, DMatrix<float> &b, DVector<float> &c,
              DVector<float> &d, DVector<float> &x)
{
  return lse_solve_mv(a, b, c, d, x);
}

int lse_solve(DMatrix<double> &a, DMatrix<double> &b, DVector<double> &c,
              DVector<double> &d, DVector<double> &x)
{
  return lse_solve_mv(a, b, c, d, x);
}

int lse_solve(DMatrix<std::complex<float>> &a, DMatrix<std::complex<float>> &b,
              DVector<std::complex<float>> &c, DVector<std::complex<float>> &d,
              DVector<std::complex<float>> &x)
{
  return lse_solve_mv(a, b, c, d, x);
}

int lse_solve(DMatrix<std::complex<double>> &a,
              DMatrix<std::complex<double>> &b,
              DVector<std::complex<double>> &c,
              DVector<std::complex<double>> &d,
              DVector<std::complex<double>> &x)
{
  return lse_solve_mv(a, b, c, d, x);
}

// As above, but for multiple right-hand sides sequentially.
//  there is no LAPACK interface for this problem, but why not?
template <class MatrixType>
int lse_msolve_tpl(MatrixType &a, MatrixType &b, MatrixType &c, MatrixType &d,
                   MatrixType &x)
{
#ifndef HAVE_NO_LAPACK
  typedef std::vector<typename MatrixType::value_type> WorkArray;

  lapack::lpint nrhs = c.ncols();
  assert(d.ncols() == size_t(nrhs));
  x.resize(a.ncols(), nrhs);

  lapack::lpint m = a.nrows();
  lapack::lpint n = a.ncols();
  lapack::lpint p = b.nrows();
  assert(b.ncols() >= uint(n));
  assert(c.nrows() >= uint(m));
  assert(d.nrows() >= uint(p));
  lapack::lpint lda = a.ldim();
  lapack::lpint ldb = b.ldim();

  // workspace
  int info, lwork(-1);
  WorkArray work(m + p + n);

  // workspace query
  lapack::gglse(m, n, p, a.pointer(), lda, b.pointer(), ldb, c.pointer(),
                d.pointer(), x.pointer(), &work[0], lwork, info);
  if (info != 0)
    return info;
  lwork = static_cast<lapack::lpint>(std::real(work[0]));
  work.resize(lwork);

  MatrixType ta, tb;
  for (lapack::lpint i = 0; i < nrhs; ++i) {

    ta = a;
    tb = b;

    // call for column i
    lapack::gglse(m, n, p, ta.pointer(), lda, tb.pointer(), ldb,
                  c.colpointer(i), d.colpointer(i), x.colpointer(i), &work[0],
                  lwork, info);

    if (info != 0)
      return info;
  }
  return 0;
#else

  throw Error("libgenua compiled without LAPACK support:"
              " lse_solve not available.");
  return 0;

#endif
}

int lse_msolve(DMatrix<float> &a, DMatrix<float> &b, DMatrix<float> &c,
               DMatrix<float> &d, DMatrix<float> &x)
{
  return lse_msolve_tpl(a, b, c, d, x);
}

int lse_msolve(DMatrix<double> &a, DMatrix<double> &b, DMatrix<double> &c,
               DMatrix<double> &d, DMatrix<double> &x)
{
  return lse_msolve_tpl(a, b, c, d, x);
}

int lse_msolve(DMatrix<std::complex<float>> &a, DMatrix<std::complex<float>> &b,
               DMatrix<std::complex<float>> &c, DMatrix<std::complex<float>> &d,
               DMatrix<std::complex<float>> &x)
{
  return lse_msolve_tpl(a, b, c, d, x);
}

int lse_msolve(DMatrix<std::complex<double>> &a,
               DMatrix<std::complex<double>> &b,
               DMatrix<std::complex<double>> &c,
               DMatrix<std::complex<double>> &d,
               DMatrix<std::complex<double>> &x)
{
  return lse_msolve_tpl(a, b, c, d, x);
}
