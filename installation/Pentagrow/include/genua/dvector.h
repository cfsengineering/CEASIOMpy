
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

#ifndef GENUA_DVECTOR_H
#define GENUA_DVECTOR_H

#include <cstring>
#include <algorithm>
#include <vector>
#include <string>
#include <sstream>
#include <complex>
#include <initializer_list>

#include "strutils.h"
#include "forward.h"
#include "algo.h"
#include "allocator.h"

#include <eeigen/Core>

/** Heap-allocated array.

  This is a very thin wrapper layer around the std::vector template, which
  adds checked access, mathematical operations such as array + array, etc.

  Currently, no expression templates are used. As a result, vector
  expressions involve a lot of copying and are utterly inefficient unless
  you write out everything fortran-style. However, DVector is meant to be
  used for small- to medium size problems (n < 1000), so that this usually
  is not a problem. For large problems, consider POOMA.

  Element access is checked using assert(), so you can switch it off by
  defining the macro NDEBUG at compile time.

*/
template <class Type>
class DVector
{
public:
  typedef std::vector<Type, AlignedAllocator<Type, 64>> container;
  typedef typename container::iterator iterator;
  typedef typename container::const_iterator const_iterator;
  typedef typename container::reverse_iterator riterator;
  typedef typename container::const_reverse_iterator const_riterator;
  typedef Type value_type;
  typedef Type &reference;
  typedef const Type &const_reference;

  /// for interfacing with the eeigen library
  typedef eeigen::Matrix<Type, eeigen::Dynamic, eeigen::Dynamic> EigenMatrix;
  typedef eeigen::Map<EigenMatrix, eeigen::Aligned> EigenMap;
  typedef eeigen::Map<const EigenMatrix, eeigen::Aligned> ConstEigenMap;

  /// empty vector
  DVector() {}

  /// zero-initialized sized construction
  explicit DVector(size_t n) : data(n)
  {
    if (n > 0)
      memset(pointer(), 0, n * sizeof(Type));
  }

  /// construction, initialization
  explicit DVector(size_t n, const Type &x) : data(n, x) {}

  /// initialized construction
  explicit DVector(const Type *x, size_t n) : data(n)
  {
    if (n > 0)
      memcpy(pointer(), x, n * sizeof(Type));
  }

  /// list initialization, uses std::copy to convert type
  template <typename ConvertibleType>
  explicit DVector(std::initializer_list<ConvertibleType> list)
      : data(list.begin(), list.end()) {}

  /// initialized construction
  template <class InputIterator>
  explicit DVector(InputIterator a, InputIterator b) : data(a, b) {}

  /// initialized construction
  template <class AnotherType>
  explicit DVector(const DVector<AnotherType> &x) : data(x.begin(), x.end()) {}

  /// construct by reordering another vector
  template <class AnotherType>
  explicit DVector(const DVector<AnotherType> &x, const Indices &idx)
  {
    const size_t n = idx.size();
    data.resize(n);
    for (size_t i = 0; i < n; ++i)
      data[i] = x[idx[i]];
  }

  /// assignment of a string e.g. of the form "3.4 5.6 0.3 0.5"
  explicit DVector(const std::string &s)
  {
    Type x;
    std::stringstream ss(s);
    while (ss >> x)
      push_back(x);
  }

  /// conversion from eeigen matrix
  template <class AnotherType>
  explicit DVector(const eeigen::Matrix<AnotherType, eeigen::Dynamic, eeigen::Dynamic> &a)
  {
    assert(a.cols() == 1);
    const size_t n = a.rows() * a.cols();
    data.resize(n);
    std::copy(a.data(), a.data() + n, pointer());
  }

  /// conversion from eeigen map
  template <class AnotherType>
  explicit DVector(const eeigen::Map<const eeigen::Matrix<AnotherType,
                                                          eeigen::Dynamic, eeigen::Dynamic>> &a)
  {
    assert(a.cols() == 1);
    const size_t n = a.rows() * a.cols();
    data.resize(n);
    std::copy(a.data(), a.data() + n, pointer());
  }

  /// copy construction
  DVector(const DVector<Type> &x) : data(x.data) {}

  /// move constructor
  DVector(DVector<Type> &&t) : data(std::move(t.data)) {}

  /// move assignment
  DVector<Type> &operator=(DVector<Type> &&tmp)
  {
    if (&tmp != this)
      data = std::move(tmp.data);
    return *this;
  }

  DVector<Type> &operator=(const DVector<Type> &rhs)
  {
    if (&rhs != this)
      data = rhs.data;
    return *this;
  }

  inline DVector<Type> operator-() const
  {
    DVector<Type> a(*this);
    for (size_t i = 0; i < size(); ++i)
      a[i] = -a[i];
    return a;
  }

  DVector<Type> &operator=(const Type &x)
  {
    std::fill(begin(), end(), x);
    return *this;
  }

  /// equality element-by-element
  bool operator==(const DVector<Type> &rhs) const
  {
    return std::equal(rhs.begin(), rhs.end(), begin(), end());
  }

  /// equality element-by-element
  bool operator!=(const DVector<Type> &rhs) const
  {
    return !(std::equal(rhs.begin(), rhs.end(), begin(), end()));
  }

  /// pointer to first element
  Type *pointer()
  {
#if defined(GENUA_MSVC) && !defined(NDEBUG)
    // MSVC doesn't permit taking pointer of empty std::vector in debug mode
    return data.empty() ? nullptr : &(data[0]);
#else
    return &(data[0]);
#endif
  }

  /// pointer to first element
  const Type *pointer() const
  {
#if defined(GENUA_MSVC) && !defined(NDEBUG)
    // MSVC doesn't permit taking pointer of empty std::vector in debug mode
    return data.empty() ? nullptr : &(data[0]);
#else
    return &(data[0]);
#endif
  }

  /// iterator to first element
  iterator begin() { return data.begin(); }

  /// iterator to first element
  const_iterator begin() const { return data.begin(); }

  /// iterator pointing to one-past last
  iterator end() { return data.end(); }

  /// iterator to first element
  const_iterator end() const { return data.end(); }

  /// iterator to first element of reversed vector
  riterator rbegin() { return data.rbegin(); }

  /// iterator to first element of reversed vector
  const_riterator rbegin() const { return data.rbegin(); }

  /// iterator pointing to one-past last (of reversed vector)
  riterator rend() { return data.rend(); }

  /// iterator to first element (of reversed vector)
  const_riterator rend() const { return data.rend(); }

  /// return size
  size_t size() const { return data.size(); }

  /// number of bytes actually occupied (not capacity)
  size_t bytes() const { return data.size() * sizeof(Type); }

  /// true if size() == 0
  bool empty() const { return data.empty(); }

  /// checked access
  reference operator[](size_t i)
  {
    assert(i < size());
    return data[i];
  }

  /// checked access
  const_reference operator[](size_t i) const
  {
    assert(i < size());
    return data[i];
  }

  /// construct a subset
  DVector<Type> operator[](const Indices &idx) const
  {
    return DVector<Type>(*this, idx);
  }

  /// checked access
  reference operator()(size_t i)
  {
    assert(i < size());
    return data[i];
  }

  /// checked access
  const_reference operator()(size_t i) const
  {
    assert(i < size());
    return data[i];
  }

  /// append after end
  void push_back(const Type &x) { data.push_back(x); }

  /// erase last element
  void pop_back() { data.pop_back(); }

  /// change size, zero out
  void resize(size_t n)
  {
    allocate(n);
    std::fill(begin(), end(), Type(0));
  }

  /// just allocate space, do not zero out
  void allocate(size_t n)
  {
    data.clear();
    data.resize(n);
    assert((n == 0) or (pointer_aligned<64>(&data[0])));
  }

  /// expend size with value v
  void expand(size_t n, const Type &v)
  {
    data.resize(n, v);
  }

  /// currently allocated space
  size_t capacity() const { return data.capacity(); }

  /// NOTE Changed semantic to match std::vector ...
  void clear() { data.clear(); }

  /// reference to first element
  reference front() { return data.front(); }

  /// copy of first element
  const_reference front() const { return data.front(); }

  /// reference to last element
  reference back() { return data.back(); }

  /// copy of last element
  const_reference back() const { return data.back(); }

  /// insert x before pos
  iterator insert(iterator pos, const Type &x)
  {
    return data.insert(pos, x);
  }

  /// insert range before pos
  template <typename Iterator>
  void insert(iterator pos, Iterator first, Iterator last)
  {
    data.insert(pos, first, last);
  }

  /// erase element
  iterator erase(iterator p1)
  {
    return data.erase(p1);
  }

  /// erase elements
  iterator erase(iterator p1, iterator p2)
  {
    return data.erase(p1, p2);
  }

  /// reserve storage
  void reserve(size_t n) { data.reserve(n); }

  /// swap contents with other array
  void swap(DVector<Type> &v) { data.swap(v.data); }

  /// create a mutable map object for interfacing with eeigen (column vector)
  EigenMap mmap()
  {
    return EigenMap(pointer(), size(), 1);
  }

  /// create a mutable map object for interfacing with eeigen (row vector)
  EigenMap rmmap()
  {
    return EigenMap(pointer(), 1, size());
  }

  /// create a constant map object for interfacing with eeigen (column vector)
  ConstEigenMap cmap() const
  {
    return ConstEigenMap(pointer(), size(), 1);
  }

  /// create a constant map object for interfacing with eeigen (row vector)
  ConstEigenMap rcmap() const
  {
    return ConstEigenMap(pointer(), 1, size());
  }

  void writeBin(std::ostream &os)
  {
    size_t n(size());
    os.write((const char *)&n, sizeof(size_t));
    os.write((const char *)pointer(), n * sizeof(Type));
  }

  void readBin(std::istream &is)
  {
    size_t n;
    is.read((char *)&n, sizeof(size_t));
    resize(n);
    is.read((char *)pointer(), n * sizeof(Type));
  }

private:
  /// storage
  container data;
};

template <class Type>
std::ostream &operator<<(std::ostream &os, const DVector<Type> &a)
{
  for (size_t i = 0; i < a.size(); ++i)
    os << a[i] << " ";
  return os;
}

template <class Type>
std::istream &operator>>(std::istream &is, DVector<Type> &a)
{
  for (size_t i = 0; i < a.size(); ++i)
    is >> a[i];
  return is;
}

inline std::ostream &operator<<(std::ostream &os, const VectorArray &a)
{
  for (size_t i = 0; i < a.size(); ++i)
  {
    for (size_t j = 0; j < a[i].size(); ++j)
      os << a[i][j] << " ";
    os << std::endl;
  }
  return os;
}

inline std::istream &operator>>(std::istream &is, VectorArray &a)
{
  Real val;
  std::string line;
  while (std::getline(is, line))
  {
    line = strip(line);
    if (line.empty())
      continue;
    std::stringstream sst(line);
    Vector tmp;
    while (sst >> val)
      tmp.push_back(val);
    a.push_back(tmp);
  }
  return is;
}

// the following specializations are here to simplify vectorization
// icc v10 correctly vectorizes all of these

inline Real dot(const Vector &a, const Vector &b)
{
  assert(a.size() == b.size());
  Real sum(0.0);
  const Real *pa(&a[0]);
  const Real *pb(&b[0]);
  const int n(a.size());
  CPHINT_SIMD_LOOP
  for (int i = 0; i < n; ++i)
    sum += pa[i] * pb[i];
  return sum;
}

// will not be vectorized
// inline Complex dot(const CpxVector & a, const CpxVector & b)
// {
//   assert(a.size() == b.size());
//   Complex sum(0.0);
//   const Complex *pa(&a[0]);
//   const Complex *pb(&b[0]);
//   const int n(a.size());
//   for (int i=0; i<n; ++i)
//     sum += pa[i] * std::conj(pb[i]);
//   return sum;
// }

inline Complex dot(const CpxVector &a, const CpxVector &b)
{
  typedef Complex::value_type vtype;
  assert(a.size() == b.size());
  const vtype *abase = (const vtype *)(&a[0]);
  const vtype *bbase = (const vtype *)(&b[0]);
  vtype ra, rb, ia, ib, rsum(0.0), isum(0.0);
  const int n(a.size());
  CPHINT_SIMD_LOOP
  for (int i = 0; i < n; ++i)
  {
    ra = abase[2 * i];
    ia = abase[2 * i + 1];
    rb = bbase[2 * i];
    ib = bbase[2 * i + 1];
    rsum += ra * rb + ia * ib;
    isum += ia * rb - ra * ib;
  }
  return Complex(rsum, isum);
}

inline Real norm(const Vector &v)
{
  Real sum(0.0);
  const Real *pv(&v[0]);
  const int n(v.size());
  CPHINT_SIMD_LOOP
  for (int i = 0; i < n; ++i)
  {
    sum += sq(pv[i]);
  }
  return std::sqrt(sum);
}

inline Real mean(const Vector &v)
{
  Real sum(0.0);
  const Real *pv(&v[0]);
  const int n(v.size());
  CPHINT_SIMD_LOOP
  for (int i = 0; i < n; ++i)
  {
    sum += pv[i];
  }
  return sum / n;
}

inline Real norm(const CpxVector &v)
{
  typedef Complex::value_type vtype;
  Real sum(0.0);
  const vtype *base = (vtype *)(&v[0]);
  const int n(2 * v.size());
  CPHINT_SIMD_LOOP
  for (int i = 0; i < n; ++i)
  {
    sum += sq(base[i]);
  }
  return std::sqrt(sum);
}

// y = a*x + b*y
template <typename Type>
inline void axpby(Type a, const DVector<Type> &x, Type b, DVector<Type> &y)
{
  assert(x.size() == y.size());
  const Type *px(&x[0]);
  Type *py(&y[0]);
  const int n(y.size());
  CPHINT_SIMD_LOOP
  for (int i = 0; i < n; ++i)
    py[i] = a * px[i] + b * py[i];
}

// z = a*x + b*y + c*z
template <typename Type>
inline void axpbypcz(Type a, const DVector<Type> &x,
                     Type b, const DVector<Type> &y,
                     Type c, DVector<Type> &z)
{
  assert(x.size() == y.size());
  assert(y.size() == z.size());
  const Type *px(&x[0]);
  const Type *py(&y[0]);
  Type *pz(&z[0]);
  const int n(z.size());
  CPHINT_SIMD_LOOP
  for (int i = 0; i < n; ++i)
    pz[i] = a * px[i] + b * py[i] + c * pz[i];
}

// trapezoidal integration
template <typename Type>
inline Type trapz(const DVector<Type> &x, const DVector<Type> &f)
{
  assert(x.size() == f.size());
  Type sum(0), mid, dst;
  size_t n = x.size() - 1;
  CPHINT_SIMD_LOOP
  for (size_t i = 0; i < n; ++i)
  {
    mid = 0.5 * (f[i] + f[i + 1]);
    dst = x[i + 1] - x[i];
    sum += dst * mid;
  }
  return dst;
}

// maximum element
template <typename Type>
inline Type max(const DVector<Type> &x)
{
  Type mxe(-huge);
  for (size_t i = 0; i < x.size(); ++i)
    mxe = std::max(mxe, x[i]);
  return mxe;
}

// minimum element
template <typename Type>
inline Type min(const DVector<Type> &x)
{
  Type mne(huge);
  for (size_t i = 0; i < x.size(); ++i)
    mne = std::min(mne, x[i]);
  return mne;
}

// real part (complex vector only)
template <typename Type>
inline DVector<Type> real(const DVector<std::complex<Type>> &a)
{
  const size_t n(a.size());
  DVector<Type> b(n);
  for (size_t i = 0; i < n; ++i)
    b[i] = a[i].real();
  return b;
}

// imaginary part (complex vector only)
template <typename Type>
inline DVector<Type> imag(const DVector<std::complex<Type>> &a)
{
  const size_t n(a.size());
  DVector<Type> b(n);
  for (size_t i = 0; i < n; ++i)
    b[i] = a[i].imag();
  return b;
}

#include "dvector_ops.h"
#include "mvop.h"

#endif
