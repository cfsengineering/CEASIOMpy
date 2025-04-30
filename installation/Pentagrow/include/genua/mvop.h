
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
 
#ifndef GENUA_MVOP_H
#define GENUA_MVOP_H

#include "defines.h"

/** Generalized matrix multiply.
 
  This routine assumes data is stored 'column-major': row index
  runs faster, so that a(r,c) == a->data[r+c*a.nrows()]. */
template <class LContainer, class RContainer, class TContainer>
void matmul(const LContainer & lhs, const RContainer & rhs, TContainer & result)
{
  assert(lhs.ncols() == rhs.nrows());
  assert(result.nrows() == lhs.nrows());
  assert(result.ncols() == rhs.ncols());

  typename TContainer::iterator itr;
  typename LContainer::const_iterator a;
  typename RContainer::const_iterator b;

  uint left_row, right_col, i(0), k;

  for (itr = result.begin(); itr != result.end(); ++itr) {
    left_row = i % lhs.nrows();
    right_col = i / lhs.nrows();

    // compute first product seperately, for *itr need not be zero
    // initially.
    a = lhs.begin() + left_row;
    b = rhs.begin() + right_col*rhs.nrows();
    *itr = (*a) * (*b);
    for (k=1; k<lhs.ncols(); k++) {
      a = lhs.begin() + left_row + k*lhs.nrows();
      b = rhs.begin() + k + right_col*rhs.nrows();
      *itr += (*a) * (*b);
    }
    i++;
  }
}

/** Generic Vector-Matrix product.
 
  Performs the operation: result = result + v * m */

template <class RVectorType, class MatrixType, class LVectorType>
inline void
vecmatmul(const RVectorType & v, const MatrixType & m, LVectorType & result)
{
  assert(result.size() == m.ncols());
  uint i,j;
  for (i=0; i<m.nrows(); i++)
    for (j=0; j<m.ncols(); j++)
      result[j] += m(i,j) * v[i];
}


/** Generic Matrix-Vector product
 
  Performs the operation result = result + m * v;
*/
template <class RVectorType, class MatrixType, class LVectorType>
inline void
matvecmul(const MatrixType & m, const RVectorType & v, LVectorType & result)
{
  assert(result.size() == m.nrows());
  uint i,j;
  for (i=0; i<m.nrows(); i++)
    for (j=0; j<m.ncols(); j++)
      result[i] += m(i,j) * v[j];
}

/** Generalized dot product. */
template<class VectorType>
inline typename VectorType::value_type
dot(const VectorType & a, const VectorType &b)
{
  assert(a.size() == b.size());

  typename VectorType::value_type res(0);
  typename VectorType::const_iterator a_itr, b_itr;
  b_itr = b.begin();
  for (a_itr = a.begin(); a_itr != a.end(); ++a_itr, ++b_itr)
    res += (*a_itr) * (*b_itr);

  return res;
}

/** Generalized two-norm. */
template<class VectorType>
inline typename VectorType::value_type
norm(const VectorType & a)
{ return std::sqrt(fabs(dot(a,a))); }

/** Normalization.
  */
template<class VectorType>
inline typename VectorType::value_type
normalize(VectorType & v)
{
  typedef typename VectorType::value_type Scalar;
  Scalar nrm(0);
  const size_t n(v.size());
  for (size_t i=0; i<n; ++i)
    nrm += v[i] * v[i];
  nrm = std::sqrt(nrm);
  Scalar t = Scalar(1)/nrm;
  for (size_t i=0; i<n; ++i)
    v[i] *= t;
  return nrm;
}

/** Create a unit matrix */
template <class MatrixType>
inline void unity(MatrixType & a)
{
  typedef typename MatrixType::value_type Scalar;
  a = Scalar(0.0);
  const int n = std::min(a.ncols(), a.nrows());
  for (int i=0; i<n; ++i)
    a(i,i) = Scalar(1.0);
}

/** Replace elements with reciprocal values. */
template<class VectorType>
inline void reciprocal(VectorType & x)
{
  typename VectorType::value_type one(1);
  const int n = x.size();
  for (int i=0; i<n; ++i)
    x[i] = one / x[i];
}

#endif

