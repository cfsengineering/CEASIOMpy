
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

#ifndef GENUA_SMATRIX_H
#define GENUA_SMATRIX_H

#include <iostream>
#include <algorithm>
#include <string>
#include <sstream>
#include <cmath>

#include "forward.h"
#include "algo.h"
#include "svector.h"

#include <eeigen/Core>

/** Fixed size matrix.

  Matrix template for applications where the dimensions are known at compile
  time, e.g.
  \verbatim
    SMatrix<3,2,float>  m1;
    SMatrix<4,4,double>  m2;
  \endverbatim
  The first template argument is the number of rows. Default initialization
  sets all values to zero.

  GCC > 3.3 will unroll most operations on SMatrix if you specify the compiler
  option -funroll-loops. Note that most operations on SMatrix and SVector have
  value copy semantics. Since GCC performs named return value optimization,
  it will eliminate many of the temporaries, but it also means that SMatrix is
  not a good choice for large dimensions (say, M,N > 20).

*/
template <uint N, uint M, class Type>
class SMatrix
{
public:
  typedef Type *iterator;
  typedef const Type *const_iterator;
  typedef Type value_type;
  typedef Type &reference;
  typedef const Type &const_reference;

  /// for interfacing with the eeigen library
  typedef eeigen::Matrix<Type, int(N), int(M)> EigenMatrix;
  typedef eeigen::Map<EigenMatrix> EigenMap;
  typedef eeigen::Map<const EigenMatrix> ConstEigenMap;

  /// create zero matrix
  SMatrix()
  {
    for (uint i = 0; i < N * M; ++i)
      data[i] = Type(0.0);
  }

  /// initialized constructor
  explicit SMatrix(const Type &init)
  {
    for (uint i = 0; i < N * M; ++i)
      data[i] = init;
  }

  /// initialized constructor from column-major data
  explicit SMatrix(const Type *v)
  {
    for (uint i = 0; i < N * M; ++i)
      data[i] = v[i];
  }

  /// copy construction
  template <typename OtherFloat>
  SMatrix(const SMatrix<N, M, OtherFloat> &src)
  {
    for (uint i = 0; i < N * M; ++i)
      data[i] = Type(src[i]);
  }

  /// set the first two columns
  template <typename ConvertibleType>
  explicit SMatrix(const SVector<N, ConvertibleType> &c0,
                   const SVector<N, ConvertibleType> &c1)
  {
    std::copy(c0.begin(), c0.end(), colpointer(0));
    std::copy(c1.begin(), c1.end(), colpointer(1));
  }

  /// set the first three columns
  template <typename ConvertibleType>
  explicit SMatrix(const SVector<N, ConvertibleType> &c0,
                   const SVector<N, ConvertibleType> &c1,
                   const SVector<N, ConvertibleType> &c2)
  {
    std::copy(c0.begin(), c0.end(), colpointer(0));
    std::copy(c1.begin(), c1.end(), colpointer(1));
    std::copy(c2.begin(), c2.end(), colpointer(2));
  }

  /// assignment to another matrix
  SMatrix<N, M, Type> &operator=(const SMatrix<N, M, Type> &src)
  {
    if (&src == this)
      return *this;
    for (uint i = 0; i < N * M; ++i)
      data[i] = src.data[i];
    return *this;
  }

  /// assign a scalar to all values
  SMatrix<N, M, Type> &operator=(const Type &x)
  {
    for (uint i = 0; i < N * M; ++i)
      data[i] = x;
    return *this;
  }

  /// element comparison
  bool operator==(const SMatrix<N, M, Type> &rhs) const
  {
    return std::equal(begin(), end(), rhs.begin());
  }

  /// element comparison
  bool operator!=(const SMatrix<N, M, Type> &rhs) const
  {
    return (not(*this == rhs));
  }

  /// data pointer
  Type *pointer() { return data; }

  /// data pointer
  const Type *pointer() const { return data; }

  /// column pointer
  Type *colpointer(uint j) { return &data[j * N]; }

  /// column pointer
  const Type *colpointer(uint j) const { return &data[j * N]; }

  /// assign from pointer
  void assign(const Type *ptr)
  {
    memcpy(data, ptr, sizeof(data));
  }

  /// leading dimensions
  uint ldim() const { return N; }

  /// mutable linear access
  reference operator[](uint i)
  {
    assert(i < N * M);
    return data[i];
  }

  /// const linear access, returns object
  const_reference operator[](uint i) const
  {
    assert(i < N * M);
    return data[i];
  }

  /// mutable linear access
  reference operator()(uint i)
  {
    assert(i < N * M);
    return data[i];
  }

  /// const linear access, returns object
  const_reference operator()(uint i) const
  {
    assert(i < N * M);
    return data[i];
  }

  /// mutable 2D access
  reference operator()(uint r, uint c)
  {
    assert(r < N);
    assert(c < M);
    return data[r + c * N];
  }

  /// const 2D access
  const_reference operator()(uint r, uint c) const
  {
    assert(r < N);
    assert(c < M);
    return data[r + c * N];
  }

  /// row count
  uint nrows() const { return N; }

  /// column count
  uint ncols() const { return M; }

  /// total size
  uint size() const { return N * M; }

  /// mutable start pointer
  iterator begin() { return data; }

  /// const start pointer
  const_iterator begin() const { return data; }

  /// one-past-end pointer
  iterator end() { return data + size(); }

  /// one-past-end pointer
  const_iterator end() const { return data + size(); }

  /// convenience shortcut to make numerical method code more expressive
  void assignColumn(size_t jcol, const SVector<N, Type> &c)
  {
    for (uint i = 0; i < N; ++i)
      (*this)(i, jcol) = c[i];
  }

  /// convenience shortcut (stride-N access!)
  void assignRow(size_t irow, const SVector<M, Type> &c)
  {
    for (uint j = 0; j < M; ++j)
      (*this)(irow, j) = c[j];
  }

  /// convenience shortcut
  SVector<N, Type> column(size_t jcol) const
  {
    return SVector<N, Type>(colpointer(jcol));
  }

  /// convenience shortcut
  SVector<M, Type> row(size_t irow) const
  {
    SVector<M, Type> r;
    for (uint j = 0; j < M; ++j)
      r[j] = (*this)(irow, j);
    return r;
  }

  /// sign inversion
  inline SMatrix<N, M, Type> operator-() const
  {
    Type tmp[M * N];
    for (uint i = 0; i < M * N; ++i)
      tmp[i] = -data[i];
    return SMatrix<N, M, Type>(tmp);
  }

  /// return transposed copy
  SMatrix<M, N, Type> transposed() const
  {
    SMatrix<M, N, Type> result;
    for (uint j = 0; j < N; ++j)
      for (uint i = 0; i < M; ++i)
        result(j, i) = data[i + j * N];
    return result;
  }

  /// transpose multiplication
  SVector<N, Type> trans_mult(const SVector<M, Type> &a) const
  {
    SVector<N, Type> r;
    vecmatmul(a, *this, r);
    return r;
  }

  /// create a mutable map object for interfacing with eeigen
  EigenMap mmap()
  {
    return EigenMap(pointer(), nrows(), ncols());
  }

  /// create a mutable map object for interfacing with eeigen
  ConstEigenMap cmap() const
  {
    return ConstEigenMap(pointer(), nrows(), ncols());
  }

  /// fill with zeros
  void clear()
  {
    for (uint i = 0; i < N * M; ++i)
      data[i] = Type(0.0);
  }

  /// create identity matrix
  static SMatrix<N, M, Type> identity()
  {
    SMatrix<N, M, Type> m;
    const int k = std::min(M, N);
    for (int i = 0; i < k; ++i)
      m(i, i) = Type(1);
    return m;
  }

private:
  /// static array
  Type data[M * N];
};

/* -------------------- i/o --------------------------------------------- */

template <class Type, uint N, uint M>
std::ostream &operator<<(std::ostream &os, const SMatrix<N, M, Type> &m)
{
  for (uint i = 0; i < N; ++i)
  {
    for (uint j = 0; j < M; ++j)
      os << m(i, j) << " ";
    os << std::endl;
  }
  return os;
}

template <class Type, uint N, uint M>
std::istream &operator>>(std::istream &is, SMatrix<N, M, Type> &m)
{
  for (uint i = 0; i < N; ++i)
  {
    for (uint j = 0; j < M; ++j)
      is >> m(i, j);
  }
  return is;
}

/*---------- Matrix multiply & Co. ----------------------------------------*/

// inplace transposition for square matrices
template <class Type, uint N>
void matrix_transpose(SMatrix<N, N, Type> &m)
{
  for (uint i = 0; i < N; ++i)
    for (uint j = i + 1; j < N; ++j)
      std::swap(m(i, j), m(j, i));
}

// matrix-matrix multiplication
template <class Type, uint N, uint M, uint O>
inline SMatrix<N, O, Type>
operator*(const SMatrix<N, M, Type> &lhs, const SMatrix<M, O, Type> &rhs)
{
  SMatrix<N, O, Type> result;
  matmul(lhs, rhs, result);
  return result;
}

// matrix-vector multiplication
template <uint N, uint M, class Type>
inline SVector<N, Type>
operator*(const SMatrix<N, M, Type> &lhs, const SVector<M, Type> &rhs)
{
  SVector<N, Type> result;
  matvecmul(lhs, rhs, result);
  return result;
}

// specialization for important case 3x3
template <class Type>
inline SVector<3, Type>
operator*(const SMatrix<3, 3, Type> &lhs, const SVector<3, Type> &rhs)
{
  SVector<3, Type> res;
  res(0) = lhs(0, 0) * rhs(0) + lhs(0, 1) * rhs(1) + lhs(0, 2) * rhs(2);
  res(1) = lhs(1, 0) * rhs(0) + lhs(1, 1) * rhs(1) + lhs(1, 2) * rhs(2);
  res(2) = lhs(2, 0) * rhs(0) + lhs(2, 1) * rhs(1) + lhs(2, 2) * rhs(2);
  return res;
}

// vector-matrix multiplication
template <uint N, uint M, class Type>
inline SVector<M, Type>
operator*(const SVector<N, Type> &lhs, const SMatrix<N, M, Type> &rhs)
{
  SVector<M, Type> result;
  vecmatmul(lhs, rhs, result);
  return result;
}

// specialization for important case 3x3
template <class Type>
inline SVector<3, Type>
operator*(const SVector<3, Type> &lhs, const SMatrix<3, 3, Type> &rhs)
{
  SVector<3, Type> res;
  res(0) = lhs(0) * rhs(0, 0) + lhs(1) * rhs(1, 0) + lhs(2) * rhs(2, 0);
  res(1) = lhs(0) * rhs(0, 1) + lhs(1) * rhs(1, 1) + lhs(2) * rhs(2, 1);
  res(2) = lhs(0) * rhs(0, 2) + lhs(1) * rhs(1, 2) + lhs(2) * rhs(2, 2);
  return res;
}

// dyadic product v*v^T
template <uint N, uint M, class Type>
inline SMatrix<N, M, Type>
dyadic(const SVector<N, Type> &lhs, const SVector<M, Type> &rhs)
{
  SMatrix<N, M, Type> result;
  for (uint i = 0; i < N; i++)
    for (uint j = 0; j < M; j++)
      result(i, j) = lhs[i] * rhs[j];
  return result;
}

// vector cross matrix, by columns
template <class Type>
inline SMatrix<3, 3, Type>
cross(const SVector<3, Type> &v, const SMatrix<3, 3, Type> &m)
{
  SMatrix<3, 3, Type> a;

  a(0, 0) = v[1] * m(2, 0) - v[2] * m(1, 0);
  a(1, 0) = v[2] * m(0, 0) - v[0] * m(2, 0);
  a(2, 0) = v[0] * m(1, 0) - v[1] * m(0, 0);

  a(0, 1) = v[1] * m(2, 1) - v[2] * m(1, 1);
  a(1, 1) = v[2] * m(0, 1) - v[0] * m(2, 1);
  a(2, 1) = v[0] * m(1, 1) - v[1] * m(0, 1);

  a(0, 2) = v[1] * m(2, 2) - v[2] * m(1, 2);
  a(1, 2) = v[2] * m(0, 2) - v[0] * m(2, 2);
  a(2, 2) = v[0] * m(1, 2) - v[1] * m(0, 2);

  return a;
}

// return A such that cross(a,b) = A*b
template <class Type>
inline SMatrix<3, 3, Type> cross_matrix(const SVector<3, Type> &a)
{
  SMatrix<3, 3, Type> A;
  A(0, 0) = 0;
  A(1, 0) = a[2];
  A(2, 0) = -a[1];

  A(0, 1) = -a[2];
  A(1, 1) = 0;
  A(2, 1) = a[0];

  A(0, 2) = a[1];
  A(1, 2) = -a[0];
  A(2, 2) = 0;
  return A;
}

// inversion, special case 2x2
template <class Type>
void inverse(const SMatrix<2, 2, Type> &m, SMatrix<2, 2, Type> &mi)
{
  Type det = m(0, 0) * m(1, 1) - m(0, 1) * m(1, 0);
  assert(det != 0);
  Type idet = Type(1) / det;
  mi(0, 0) = m(1, 1) * idet;
  mi(1, 0) = -m(1, 0) * idet;
  mi(0, 1) = -m(0, 1) * idet;
  mi(1, 1) = m(0, 0) * idet;
}

// determinant, special case 2x2
template <class Type>
inline Type det(const SMatrix<2, 2, Type> &a)
{
  return a(0, 0) * a(1, 1) - a(0, 1) * a(1, 0);
}

// determinant, special case 3x3
template <class Type>
inline Type det(const SMatrix<3, 3, Type> &a)
{
  Type sum(0);
  sum = a(0, 0) * a(1, 1) * a(2, 2);
  sum += a(0, 1) * a(1, 2) * a(2, 0);
  sum += a(0, 2) * a(1, 0) * a(2, 1);

  sum -= a(0, 2) * a(1, 1) * a(2, 0);
  sum -= a(0, 1) * a(1, 0) * a(2, 2);
  sum -= a(1, 2) * a(2, 1) * a(0, 0);

  return sum;
}

template <typename Type, uint N, uint M>
inline SMatrix<N, M, Type> realpart(const SMatrix<N, M, std::complex<Type>> &a)
{
  SMatrix<N, M, Type> b;
  for (uint i = 0; i < (N * M); ++i)
    b[i] = a[i].real();
  return b;
}

template <typename Type, uint N, uint M>
inline SMatrix<N, M, Type> imagpart(const SMatrix<N, M, std::complex<Type>> &a)
{
  SMatrix<N, M, Type> b;
  for (uint i = 0; i < (N * M); ++i)
    b[i] = a[i].imag();
  return b;
}

template <uint N, typename Type>
inline SMatrix<N, N, Type> diag(const SVector<N, Type> &b)
{
  SMatrix<N, N, Type> A;
  for (uint i = 0; i < N; ++i)
    A(i, i) = b[i];
  return A;
}

template <typename Type, uint N, uint M>
bool finite(const SMatrix<N, M, Type> &a)
{
  bool fin = true;
  for (uint i = 0; i < N * M; ++i)
    fin &= std::isfinite(a[i]);
  return fin;
}

#include "smatrix_ops.h"

#endif
