
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

#ifndef GENUA_LAPACK_H
#define GENUA_LAPACK_H

#include "lu.h"
#include "lls.h"
#include "eig.h"
#include "svd.h"

#ifndef HAVE_NO_LAPACK
#include "lapack_interface.h"
#else
#include <eeigen/Core>
#endif

#include "dmatrix.h"

// simpler interface to blas3 GEMM
// c = alfa*a*b + beta*c
template <class NType>
inline void gemm(NType alfa, const DMatrix<NType> &a, const DMatrix<NType> &b,
                 NType beta, DMatrix<NType> &c)
{
  assert(a.ncols() == b.nrows());
  assert(c.nrows() == a.nrows());
  assert(b.ncols() == c.ncols());

#ifndef HAVE_NO_LAPACK

  // check for argument aliasing
  assert(a.pointer() != c.pointer());
  assert(b.pointer() != c.pointer());
  lapack::gemm('N', 'N', a.nrows(), b.ncols(), a.ncols(),
               alfa, a.pointer(), a.nrows(),
               b.pointer(), b.nrows(),
               beta, c.pointer(), c.nrows());

#else

  typename DMatrix<NType>::EigenMatrix tmp;
  tmp = alfa * a.cmap() * b.cmap() + beta * c.cmap();
  c = DMatrix<NType>(tmp);

#endif
}

// simpler interface to blas2 GEMV
// y = alfa*a*x + beta*y
template <class NType>
inline void gemv(NType alfa, const DMatrix<NType> &a, const DVector<NType> &x,
                 NType beta, DVector<NType> &y)
{
  assert(a.ncols() == x.size());
  assert(a.nrows() == y.size());

#ifndef HAVE_NO_LAPACK

  // check for argument aliasing
  assert(x.pointer() != y.pointer());
  lapack::gemv('N', a.nrows(), a.ncols(), alfa, a.pointer(), a.nrows(),
               x.pointer(), 1,
               beta, y.pointer(), 1);
#else

  typename DMatrix<NType>::EigenMatrix tmp;
  tmp = alfa * a.cmap() * x.cmap() + beta * y.cmap();
  y = DVector<NType>(tmp);

#endif
}

#endif
