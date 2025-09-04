
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

#ifndef GENUA_DMATRIX_H
#define GENUA_DMATRIX_H

#include <cstring>
#include <iostream>
#include <algorithm>
#include <vector>
#include <string>
#include <sstream>
#include <complex>

#include "forward.h"
#include "algo.h"
#include "dvector.h"
#include "lapack.h"
#include <eeigen/Core>

/** Matrix template.

  Simple matrix class using heap allocation. The pointer to the first
  element is guaranteed to be 64-byte aligned in order to simplify
  vectorization. Likewise, the allocated space is always an integer multiple
  of 64 bytes.

  When the size of a matrix is known at compile time (and not very large),
  use class SMatrix instead.

  DMatrix and DVector define arithmetic operators to simplify writing algorithm
  prototypes. Where applicable, operators call LAPACK when available. Many
  functions in the linear algebra domain use eiter LAPACK or interface to the
  eeigen library when LAPACK is not found.

  \ingroup numerics
  \sa DVector, SVector, SMatrix, lu.h, lls.h, eig.h
  */
template <class Type>
class DMatrix
{

public:
  typedef DVector<Type> container;
  typedef typename container::iterator iterator;
  typedef typename container::const_iterator const_iterator;
  typedef Type value_type;
  typedef Type &reference;
  typedef const Type &const_reference;

  /// for interfacing with the eeigen library
  typedef eeigen::Matrix<Type, eeigen::Dynamic, eeigen::Dynamic> EigenMatrix;
  typedef eeigen::Map<EigenMatrix, eeigen::Aligned> EigenMap;
  typedef eeigen::Map<const EigenMatrix, eeigen::Aligned> ConstEigenMap;

  /// default empty constructor
  DMatrix() : rows(0), cols(0) {}

  /// sized construction
  explicit DMatrix(size_t r, size_t c) : rows(r), cols(c), data(r * c) {}

  /// conversion from different type
  template <class AnotherType>
  explicit DMatrix(const DMatrix<AnotherType> &src)
      : rows(src.nrows()), cols(src.ncols()),
        data(src.begin(), src.end()) {}

  /// conversion from different type
  template <class AnotherType>
  explicit DMatrix(const DVector<AnotherType> &src)
      : rows(src.size()), cols(1),
        data(src.begin(), src.end()) {}

  /// conversion from eeigen matrix
  template <class AnotherType>
  explicit DMatrix(const eeigen::Matrix<AnotherType,
                                        eeigen::Dynamic, eeigen::Dynamic> &a)
      : rows(a.rows()), cols(a.cols())
  {
    const size_t n = rows * cols;
    data.allocate(n);
    if (n > 0)
      std::copy(a.data(), a.data() + n, data.pointer());
  }

  /// conversion from eeigen map
  template <class AnotherType>
  explicit DMatrix(const eeigen::Map<const eeigen::Matrix<AnotherType,
                                                          eeigen::Dynamic, eeigen::Dynamic>> &a)
      : rows(a.rows()), cols(a.cols())
  {
    const size_t n = rows * cols;
    data.allocate(n);
    if (n > 0)
      std::copy(a.data(), a.data() + n, data.pointer());
  }

  /// copy construction
  DMatrix(const DMatrix<Type> &src)
      : rows(src.rows), cols(src.cols), data(src.data) {}

  /// move constructor
  DMatrix(DMatrix<Type> &&t)
      : rows(t.rows), cols(t.cols), data(std::move(t.data)) {}

  /// move assignment
  DMatrix<Type> &operator=(DMatrix<Type> &&rhs)
  {
    if (&rhs == this)
      return *this;
    rows = rhs.rows;
    cols = rhs.cols;
    data = std::move(rhs.data);
    return *this;
  }

  /// assignment operator
  DMatrix<Type> &operator=(const DMatrix<Type> &rhs)
  {
    if (&rhs == this)
      return *this;
    rows = rhs.rows;
    cols = rhs.cols;
    data = rhs.data;
    return *this;
  }

  /// assignament to scalar
  DMatrix<Type> &operator=(const Type &x)
  {
    std::fill(data.begin(), data.end(), x);
    return *this;
  }

  /// element equality
  bool operator==(const DMatrix<Type> &rhs) const
  {
    assert(size() == rhs.size());
    return std::equal(begin(), end(), rhs.begin(), rhs.end());
  }

  /// data pointer
  const Type *pointer() const
  {
#if defined(GENUA_MSVC) && !defined(NDEBUG)
    // MSVC doesn't permit taking pointer of empty std::vector in debug mode
    return data.empty() ? nullptr : &(data[0]);
#else
    return &(data[0]);
#endif
  }

  /// data pointer
  Type *pointer()
  {
#if defined(GENUA_MSVC) && !defined(NDEBUG)
    // MSVC doesn't permit taking pointer of empty std::vector in debug mode
    return data.empty() ? nullptr : &(data[0]);
#else
    return &(data[0]);
#endif
  }

  /// pointer to the top of column j
  Type *colpointer(size_t j)
  {
    assert(j < ncols());
    return &(data[j * rows]);
  }

  /// pointer to one past the end of column j
  Type *colend(size_t j)
  {
    return colpointer(j) + nrows();
  }

  /// pointer to the top of column j
  const Type *colpointer(size_t j) const
  {
    assert(j < ncols());
    return &(data[j * rows]);
  }

  /// pointer to one past the end of column j
  const Type *colend(size_t j) const
  {
    return colpointer(j) + nrows();
  }

  /// mutable linear access
  reference operator[](size_t i)
  {
    assert(rows * cols > i);
    return data[i];
  }

  /// const linear access
  const_reference operator[](size_t i) const
  {
    assert(rows * cols > i);
    return data[i];
  }

  /// mutable linear access
  reference operator()(size_t i)
  {
    assert(rows * cols > i);
    return data[i];
  }

  /// const linear access
  const_reference operator()(size_t i) const
  {
    assert(rows * cols > i);
    return data[i];
  }

  /// mutable 2D access
  reference operator()(size_t r, size_t c)
  {
    assert(size_t(r) < rows);
    assert(size_t(c) < cols);
    return data[r + c * rows];
  }

  /// const 2D access
  const_reference operator()(size_t r, size_t c) const
  {
    assert(size_t(r) < rows);
    assert(size_t(c) < cols);
    return data[r + c * rows];
  }

  /// row count
  size_t nrows() const { return rows; }

  /// column count
  size_t ncols() const { return cols; }

  /// total size
  size_t size() const { return data.size(); }

  /// number of bytes actually occupied (not capacity)
  size_t bytes() const { return data.size() * sizeof(Type); }

  /// leading dimension
  size_t ldim() const { return rows; }

  /// change size and clear memory
  void resize(size_t r, size_t c)
  {
    rows = r;
    cols = c;
    data.resize(r * c);
    std::fill(begin(), end(), Type(0));
  }

  /// allocate space only
  void allocate(size_t r, size_t c)
  {
    rows = r;
    cols = c;
    data.clear();
    data.resize(r * c);
  }

  /// change size, do not initialize memory
  void reserve(size_t r, size_t c)
  {
    rows = r;
    cols = c;
    data.resize(r * c);
  }

  /// append column, data in ptr must be at least nrows() long
  void appendColumn(const Type *ptr)
  {
    const Type *pend = ptr + nrows();
    data.insert(data.end(), ptr, pend);
    ++cols;
  }

  /// start pointer
  const_iterator begin() const { return data.begin(); }

  /// one-past-end pointer
  const_iterator end() const { return data.end(); }

  /// start pointer
  iterator begin() { return data.begin(); }

  /// one-past-end pointer
  iterator end() { return data.end(); }

  /// convenience shortcut to make numerical method code more expressive
  template <class VectorType>
  void assignColumn(size_t jcol, const VectorType &c)
  {
    assert(c.size() <= nrows());
    std::copy(c.begin(), c.end(), colpointer(jcol));
  }

  /// convenience shortcut (strided access!)
  template <class VectorType>
  void assignRow(size_t irow, const VectorType &c)
  {
    assert(c.size() <= ncols());
    for (uint j = 0; j < cols; ++j)
      (*this)(irow, j) = c[j];
  }

  /// convenience shortcut
  template <typename FloatType>
  void scaleColumn(size_t icol, const FloatType &a)
  {
    const size_t n = nrows();
    Type *col = colpointer(icol);
    for (size_t i = 0; i < n; ++i)
      col[i] *= a;
  }

  /// convenience shortcut (strided access)
  template <typename FloatType>
  void scaleRow(size_t irow, const FloatType &a)
  {
    const size_t n = ncols();
    for (size_t i = 0; i < n; ++i)
      (*this)(irow, i) *= a;
  }

  /// negation
  inline DMatrix<Type> operator-() const
  {
    DMatrix<Type> a(*this);
    for (size_t i = 0; i < a.size(); ++i)
      a[i] = -a[i];
    return a;
  }

  DVector<Type> trans_mult(const DVector<Type> &a) const
  {
    assert(a.size() == rows);
    DVector<Type> r(cols);
    vecmatmul(a, *this, r);
    return r;
  }

  /// return transposed copy
  DMatrix<Type> transposed() const
  {
    DMatrix<Type> b(cols, rows);
    for (size_t i = 0; i < rows; ++i)
      for (size_t j = 0; j < cols; ++j)
        b(j, i) = data[i + j * rows];
    return b;
  }

  /// transpose in place (inefficient but simple)
  void transpose()
  {
    DMatrix<Type> b(cols, rows);
    for (size_t i = 0; i < rows; ++i)
      for (size_t j = 0; j < cols; ++j)
        b(j, i) = data[i + j * rows];
    swap(b);
  }

  /// swap contents with a
  void swap(DMatrix<Type> &a)
  {
    data.swap(a.data);
    std::swap(rows, a.rows);
    std::swap(cols, a.cols);
  }

  /// release storage
  void clear()
  {
    data.clear();
    rows = cols = 0;
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

  void writeBin(std::ostream &os)
  {
    os.write((const char *)&rows, sizeof(size_t));
    os.write((const char *)&cols, sizeof(size_t));
    os.write((const char *)pointer(), rows * cols * sizeof(Type));
  }

  void readBin(std::istream &is)
  {
    is.read((char *)&rows, sizeof(size_t));
    is.read((char *)&cols, sizeof(size_t));
    resize(rows, cols);
    is.read((char *)pointer(), rows * cols * sizeof(Type));
  }

private:
  /// array sizes
  size_t rows, cols;

  /// pointer to data
  container data;
};

// import operators

#include "dmatrix_ops.h"

// overload matrix multiplication using blas-3

template <typename Type>
inline void matmul(const DMatrix<Type> &a,
                   const DMatrix<Type> &b,
                   DMatrix<Type> &c)
{
  assert(a.ncols() == b.nrows());
  c.allocate(a.nrows(), b.ncols());

#ifndef HAVE_NO_LAPACK
  lapack::gemm('N', 'N', a.nrows(), b.ncols(), a.ncols(), 1.0f,
               a.pointer(), a.nrows(), b.pointer(), b.nrows(), 1.0f,
               c.pointer(), a.nrows());
#else
  c.mmap() = a.cmap() * b.cmap();
#endif
}

// overload matrix-vector multiplication

template <typename Type>
inline void matvecmul(const DMatrix<Type> &a,
                      const DVector<Type> &b,
                      DVector<Type> &c)
{
  assert(a.ncols() == b.size());
  c.allocate(a.nrows());

#ifndef HAVE_NO_LAPACK
  lapack::gemv('N', a.nrows(), a.ncols(), 1.0, a.pointer(), a.nrows(),
               b.pointer(), 1, 0.0, c.pointer(), 1);
#else
  c.mmap() = a.cmap() * b.cmap();
#endif
}

template <typename Type>
inline void vecmatmul(const DVector<Type> &a,
                      const DMatrix<Type> &b,
                      DVector<Type> &c)
{
  assert(a.size() == b.nrows());
  c.allocate(b.ncols());

#ifndef HAVE_NO_LAPACK
  lapack::gemv('T', b.nrows(), b.ncols(), 1.0, b.pointer(), b.nrows(),
               a.pointer(), 1, 0.0, c.pointer(), 1);
#else
  c.rmmap() = a.rcmap() * b.cmap();
#endif
}

// matrix-matrix and matrix-vector product

template <typename Type>
inline DMatrix<Type> operator*(const DMatrix<Type> &a,
                               const DMatrix<Type> &b)
{
  assert(a.ncols() == b.nrows());
  DMatrix<Type> c(a.nrows(), b.ncols());
  matmul(a, b, c);
  return c;
}

template <typename Type>
inline DVector<Type> operator*(const DMatrix<Type> &a,
                               const DVector<Type> &b)
{
  assert(a.ncols() == b.size());
  DVector<Type> c(b.size());
  matvecmul(a, b, c);
  return c;
}

template <typename Type>
inline DVector<Type> operator*(const DVector<Type> &b,
                               const DMatrix<Type> &a)
{
  assert(a.nrows() == b.size());
  DVector<Type> c(b.size());
  vecmatmul(b, a, c);
  return c;
}

/* ------------------ Functions ------------------------------------------ */

template <class Type>
DMatrix<Type> dyadic(const DVector<Type> &a, const DVector<Type> &b)
{
  DMatrix<Type> c(a.size(), b.size());
  size_t i, j;
  for (i = 0; i < a.size(); i++)
  {
    for (j = 0; j < b.size(); j++)
      c(i, j) = a(i) * b(j);
  }
  return c;
}

template <class Type>
std::ostream &operator<<(std::ostream &os, const DMatrix<Type> &m)
{
  for (size_t i = 0; i < m.nrows(); ++i)
  {
    for (size_t j = 0; j < m.ncols(); ++j)
    {
      os << m(i, j) << " ";
    }
    os << std::endl;
  }
  return os;
}

template <class Type>
std::istream &operator>>(std::istream &is, DMatrix<Type> &m)
{
  assert(m.size() != 0);
  for (size_t i = 0; i < m.nrows(); ++i)
    for (size_t j = 0; j < m.ncols(); ++j)
      is >> m(i, j);
  return is;
}

inline void toMatrix(const VectorArray &v, Matrix &m)
{
  if (v.empty())
    return;

  const int ncol = v.size();
  const int nrow = v[0].size();
  m.resize(nrow, ncol);
  for (int j = 0; j < ncol; ++j)
    memcpy(m.colpointer(j), v[j].pointer(), nrow * sizeof(Vector::value_type));
}

inline void fromMatrix(const Matrix &m, VectorArray &v)
{
  const int ncol = m.ncols();
  const int nrow = m.nrows();
  v.resize(ncol);
  for (int j = 0; j < ncol; ++j)
  {
    Vector tmp(m.colpointer(j), nrow);
    v[j].swap(tmp);
  }
}

#endif
