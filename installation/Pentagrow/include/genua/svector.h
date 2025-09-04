
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

#ifndef GENUA_SVECTOR_H
#define GENUA_SVECTOR_H

#include <iostream>
#include <algorithm>
#include <string>
#include <sstream>
#include <initializer_list>

#include "forward.h"
#include "algo.h"
#include <boost/static_assert.hpp>
#include <eeigen/Core>
#include <cmath>

/** Fixed size vector.

  A constant size (stack-allocated) array which is mainly used for geometry
  and the corresponding linear algebra work. SVector defines some typedefs
  and memeber functions which make it more compatible with STL algorithms
  than the conventional data structure for geoemtric points
  (struct {float x,y,z};).

  Operators are defined in the naive way, i.e. using temporaries, because
  testing showed that expresseion templates (using PETE) did not provide
  any improvements, neither with gcc-3.2 nor icc-8.0, perhaps because of
  the "named return value" optimization which helps to avoid temporaries.

  */
template <uint N, class Type>
class SVector
{
public:
  typedef Type *iterator;
  typedef const Type *const_iterator;
  typedef Type value_type;
  typedef Type &reference;
  typedef const Type &const_reference;

  /// for interfacing with the eeigen library
  typedef eeigen::Matrix<Type, int(N), 1> EigenMatrix;
  typedef eeigen::Map<EigenMatrix> EigenMap;
  typedef eeigen::Map<const EigenMatrix> ConstEigenMap;

  /// default: zero vector
  SVector()
  {
    for (uint i = 0; i < N; ++i)
      data[i] = 0.0;
  }

  /// construction, initialization
  explicit SVector(const Type &x)
  {
    for (uint i = 0; i < N; ++i)
      data[i] = x;
  }

  /// list initialization, uses std::copy to convert type
  template <typename ConvertibleType>
  explicit SVector(std::initializer_list<ConvertibleType> list)
  {
    assert(list.size() == N);
    std::copy(list.begin(), list.end(), begin());
  }

  /// element-wise construction for dimension 2
  explicit SVector(const Type &x1, const Type &x2)
  {
    BOOST_STATIC_ASSERT(N == 2);
    data[0] = x1;
    data[1] = x2;
  }

  /// element-wise construction for dimension 3
  explicit SVector(const Type &x1, const Type &x2, const Type &x3)
  {
    BOOST_STATIC_ASSERT(N == 3);
    data[0] = x1;
    data[1] = x2;
    data[2] = x3;
  }

  /// element-wise construction for dimension 4
  explicit SVector(const Type &x1, const Type &x2,
                   const Type &x3, const Type &x4)
  {
    BOOST_STATIC_ASSERT(N == 4);
    data[0] = x1;
    data[1] = x2;
    data[2] = x3;
    data[3] = x4;
  }

  /// type conversion
  template <class OtherType>
  explicit SVector(const SVector<N, OtherType> &a)
  {
    for (uint i = 0; i < N; ++i)
      data[i] = static_cast<Type>(a[i]);
  }

  /// assembly
  template <class OtherType>
  explicit SVector(const SVector<N - 1, OtherType> &a, OtherType last)
  {
    for (uint i = 0; i < N - 1; ++i)
      data[i] = static_cast<Type>(a[i]);
    data[N - 1] = static_cast<Type>(last);
  }

  /// initialized construction
  explicit SVector(const Type *x)
  {
    for (uint i = 0; i < N; ++i)
      data[i] = x[i];
  }

  /// construction using a string, e.g of the form "0.5 0.6 1.2"
  explicit SVector(const std::string &s)
  {
    std::stringstream ss(s);
    for (uint i = 0; i < N; ++i)
      ss >> data[i];
  }

  /// copy construction
  SVector(const SVector<N, Type> &x)
  {
    for (uint i = 0; i < N; ++i)
      data[i] = x.data[i];
  }

  /// assignment
  SVector<N, Type> &operator=(const SVector<N, Type> &src)
  {
    if (&src == this)
      return *this;
    for (uint i = 0; i < N; ++i)
      data[i] = src[i];
    return *this;
  }

  /// conversion assignment
  template <typename SrcType>
  SVector<N, Type> &operator=(const SVector<N, SrcType> &src)
  {
    for (uint i = 0; i < N; ++i)
      data[i] = static_cast<Type>(src[i]);
    return *this;
  }

  /// assignment from a scalar
  SVector<N, Type> &operator=(const Type &x)
  {
    for (uint i = 0; i < N; ++i)
      data[i] = x;
    return *this;
  }

  /// data pointer
  Type *pointer() { return data; }

  /// data pointer
  const Type *pointer() const { return data; }

  /// assign from pointer
  void assign(const Type *ptr)
  {
    memcpy(data, ptr, sizeof(data));
  }

  /// mutable access[]
  reference operator[](uint i)
  {
    assert(i < N);
    return data[i];
  }

  /// const access[]
  const_reference operator[](uint i) const
  {
    assert(i < N);
    return data[i];
  }

  /// mutable access()
  reference operator()(uint i)
  {
    assert(i < N);
    return data[i];
  }

  /// const access()
  const_reference operator()(uint i) const
  {
    assert(i < N);
    return data[i];
  }

  /// equality element by element
  bool operator==(const SVector<N, Type> &rhs) const
  {
    return std::equal(begin(), end(), rhs.begin());
  }

  /// at least one element different
  bool operator!=(const SVector<N, Type> &rhs) const
  {
    return !(*this == rhs);
  }

  /// mutable start pointer
  iterator begin() { return data; }

  /// const start pointer
  const_iterator begin() const { return data; }

  /// one-past-end pointer
  iterator end() { return data + N; }

  /// one-past-end pointer
  const_iterator end() const { return data + N; }

  /// first value (const)
  const_reference front() const { return data[0]; }

  /// first value (mutable)
  reference front() { return data[0]; }

  /// last value (const)
  const_reference back() const { return data[N - 1]; }

  /// last value (mutable)
  reference back() { return data[N - 1]; }

  /// number of entries
  uint size() const { return N; }

  /// unary minus
  SVector<N, Type> operator-() const
  {
    SVector<N, Type> a(*this);
    for (uint i = 0; i < N; ++i)
      a[i] = -a[i];
    return a;
  }

  /// returns a new vector, normalized to length = 1.
  const SVector<N, Type> normalized() const
  {
    Type len(0);
    for (uint i = 0; i < N; ++i)
      len += data[i] * data[i];
    if (len != 0)
      return *this / std::sqrt(len);
    else
      return *this;
  }

  /// overwrite with zero
  void clear()
  {
    for (uint i = 0; i < N; ++i)
      data[i] = 0.0;
  }

  /// create a mutable map object for interfacing with eeigen
  EigenMap mmap()
  {
    return EigenMap(pointer(), size(), 1);
  }

  /// create a mutable map object for interfacing with eeigen
  ConstEigenMap cmap() const
  {
    return ConstEigenMap(pointer(), size(), 1);
  }

private:
  /// static array
  Type data[N];
};

template <uint N, class Type>
std::ostream &operator<<(std::ostream &os, const SVector<N, Type> &a)
{
  os << " ";
  for (uint i = 0; i < N; ++i)
    os << a[i] << " ";
  return os;
}

template <uint N, class Type>
std::istream &operator>>(std::istream &is, SVector<N, Type> &a)
{
  for (uint i = 0; i < N; ++i)
    is >> a[i];
  return is;
}

// cross product of two vectors (both with length 3)
template <class Type>
inline SVector<3, Type> cross(const SVector<3, Type> &a,
                              const SVector<3, Type> &b)
{
  SVector<3, Type> c;
  c[0] = a[1] * b[2] - b[1] * a[2];
  c[1] = a[2] * b[0] - b[2] * a[0];
  c[2] = a[0] * b[1] - b[0] * a[1];
  return c;
}

template <class Type, uint N>
inline Type dot(const SVector<N, Type> &a, const SVector<N, Type> &b)
{
  Type sqs(0);
  for (uint i = 0; i < N; ++i)
    sqs += a[i] * b[i];
  return sqs;
}

template <class Type, uint N>
inline Type norm(const SVector<N, Type> &a)
{
  Type sqs(0);
  for (uint i = 0; i < N; ++i)
    sqs += a[i] * a[i];
  return std::sqrt(sqs);
}

template <class Type, uint N>
inline SVector<N, Type> clamp(const SVector<N, Type> &a,
                              const SVector<N, Type> &amin,
                              const SVector<N, Type> &amax)
{
  SVector<N, Type> b;
  CPHINT_SIMD_LOOP
  for (uint i = 0; i < N; ++i)
    b[i] = clamp(a[i], amin[i], amax[i]);
  return b;
}

template <class Type, uint N>
inline SVector<N, Type> clamp(const SVector<N, Type> &a,
                              const Type &amin, const Type &amax)
{
  SVector<N, Type> b;
  CPHINT_SIMD_LOOP
  for (uint i = 0; i < N; ++i)
    b[i] = clamp(a[i], amin, amax);
  return b;
}

// string conversion
template <class Type, uint N>
std::string str(const SVector<N, Type> &v)
{
  std::stringstream ss;
  ss << v;
  return ss.str();
}

// not a general algorithm, but needed frequently
template <class Type, uint N>
inline void split_vct(const SVector<2 * N, Type> &a,
                      SVector<N, Type> &a1, SVector<N, Type> &a2)
{
  for (uint i = 0; i < N; ++i)
  {
    a1[i] = a[i + 0];
    a2[i] = a[i + N];
  }
}

template <class Type, uint N>
inline void join_vct(const SVector<N, Type> &a1, const SVector<N, Type> &a2,
                     SVector<2 * N, Type> &a)
{
  for (uint i = 0; i < N; ++i)
  {
    a[i + 0] = a1[i];
    a[i + N] = a2[i];
  }
}

/* ---------------- factory functions ----------------------------------- */

inline Vct2 vct(Real x, Real y)
{
  Vct2 v;
  v[0] = x;
  v[1] = y;
  return v;
}

inline Vct3 vct(Real x, Real y, Real z)
{
  Vct3 v;
  v[0] = x;
  v[1] = y;
  v[2] = z;
  return v;
}

inline Vct4 vct(Real x, Real y, Real z, Real w)
{
  Vct4 v;
  v[0] = x;
  v[1] = y;
  v[2] = z;
  v[3] = w;
  return v;
}

inline Vct6 vct(Real x, Real y, Real z, Real u, Real v, Real w)
{
  Vct6 r;
  r[0] = x;
  r[1] = y;
  r[2] = z;
  r[3] = u;
  r[4] = v;
  r[5] = w;
  return r;
}

template <typename Type, uint N>
inline Type sq(const SVector<N, Type> &a)
{
  Type sum(0);
  for (uint i = 0; i < N; ++i)
    sum += a[i] * a[i];
  return sum;
}

template <typename Type, uint N>
inline SVector<N, Type> realpart(const SVector<N, std::complex<Type>> &a)
{
  SVector<N, Type> b;
  for (uint i = 0; i < N; ++i)
    b[i] = a[i].real();
  return b;
}

template <typename Type, uint N>
inline SVector<N, Type> imagpart(const SVector<N, std::complex<Type>> &a)
{
  SVector<N, Type> b;
  for (uint i = 0; i < N; ++i)
    b[i] = a[i].imag();
  return b;
}

template <typename AType, typename BType, uint N>
inline void convert(const SVector<N, AType> &a, SVector<N, BType> &b)
{
  for (uint i = 0; i < N; ++i)
    b[i] = static_cast<BType>(a[i]);
}

inline Complex dot(const CpxVct2 &a, const CpxVct2 &b)
{
  return a[0] * std::conj(b[0]) + a[1] * std::conj(b[1]);
}

inline Complex dot(const CpxVct3 &a, const CpxVct3 &b)
{
  return a[0] * std::conj(b[0]) + a[1] * std::conj(b[1]) + a[2] * std::conj(b[2]);
}

template <typename Type, uint N>
inline std::complex<Type> dot(const SVector<N, Type> &a,
                              const SVector<N, std::complex<Type>> &b)
{
  std::complex<Type> sum(0);
  for (uint i = 0; i < N; ++i)
    sum += a[i] * b[i];
  return sum;
}

template <typename Type, uint N>
inline std::complex<Type> dot(const SVector<N, std::complex<Type>> &a,
                              const SVector<N, Type> &b)
{
  std::complex<Type> sum(0);
  for (uint i = 0; i < N; ++i)
    sum += a[i] * b[i];
  return sum;
}

template <typename Type>
inline void extend_basis(SVector<3, Type> &a,
                         SVector<3, Type> &b, SVector<3, Type> &c)
{
  normalize(a);
  b = Type(0.0);

  Type x = fabs(a[0]);
  Type y = fabs(a[1]);
  Type z = fabs(a[2]);
  if (x <= y and x <= z)
    b[0] = 1.0;
  else if (y <= x and y <= z)
    b[1] = 1.0;
  else
    b[2] = 1.0;

  b -= dot(b, a) * a;
  normalize(b);
  c = cross(a, b);
  normalize(c);
}

template <typename Type, uint N>
bool finite(const SVector<N, Type> &a)
{
  bool fin = true;
  for (uint i = 0; i < N; ++i)
    fin &= std::isfinite(a[i]);
  return fin;
}

#include "svector_ops.h"
#include "trigo.h"

#endif
