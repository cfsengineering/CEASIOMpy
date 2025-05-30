
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
 

// mathematical operators for  DMatrix<NumType>
// file generated by genua/tools/opsprint.py

template <class NumType>
inline DMatrix<NumType> operator+ (const DMatrix<NumType> & a, const DMatrix<NumType> & b)
{
  assert(a.size() == b.size());
  DMatrix<NumType> c(a);
  for (size_t i=0; i<a.size(); ++i)
    c[i] += b[i];
  return c;
}

template <class NumType>
inline DMatrix<NumType> & operator+= (DMatrix<NumType> & a, const DMatrix<NumType> & b)
{
  assert(a.size() == b.size());
  for (size_t i=0; i<a.size(); ++i)
    a[i] += b[i];
  return a;
}

template <class NumType>
inline DMatrix<NumType> operator+ (const DMatrix<NumType> & a, NumType b)
{
  DMatrix<NumType> c(a);
  for (size_t i=0; i<a.size(); ++i)
    c[i] += b;
  return c;
}

template <class NumType>
inline DMatrix<NumType> & operator+= (DMatrix<NumType> & a, NumType b)
{
  for (size_t i=0; i<a.size(); ++i)
    a[i] += b;
  return a;
}

template <class NumType>
inline DMatrix<NumType> operator+ (NumType a, const DMatrix<NumType> & b)
{
  DMatrix<NumType> c(b.nrows(), b.ncols());
  for (size_t i=0; i<b.size(); ++i)
    c[i] = a + b[i];
  return c;
}

template <class NumType>
inline DMatrix<NumType> operator- (const DMatrix<NumType> & a, const DMatrix<NumType> & b)
{
  assert(a.size() == b.size());
  DMatrix<NumType> c(a);
  for (size_t i=0; i<a.size(); ++i)
    c[i] -= b[i];
  return c;
}

template <class NumType>
inline DMatrix<NumType> & operator-= (DMatrix<NumType> & a, const DMatrix<NumType> & b)
{
  assert(a.size() == b.size());
  for (size_t i=0; i<a.size(); ++i)
    a[i] -= b[i];
  return a;
}

template <class NumType>
inline DMatrix<NumType> operator- (const DMatrix<NumType> & a, NumType b)
{
  DMatrix<NumType> c(a);
  for (size_t i=0; i<a.size(); ++i)
    c[i] -= b;
  return c;
}

template <class NumType>
inline DMatrix<NumType> & operator-= (DMatrix<NumType> & a, NumType b)
{
  for (size_t i=0; i<a.size(); ++i)
    a[i] -= b;
  return a;
}

template <class NumType>
inline DMatrix<NumType> operator- (NumType a, const DMatrix<NumType> & b)
{
  DMatrix<NumType> c(b.nrows(), b.ncols());
  for (size_t i=0; i<b.size(); ++i)
    c[i] = a - b[i];
  return c;
}

template <class NumType>
inline DMatrix<NumType> operator* (const DMatrix<NumType> & a, NumType b)
{
  DMatrix<NumType> c(a);
  for (size_t i=0; i<a.size(); ++i)
    c[i] *= b;
  return c;
}

template <class NumType>
inline DMatrix<NumType> & operator*= (DMatrix<NumType> & a, NumType b)
{
  for (size_t i=0; i<a.size(); ++i)
    a[i] *= b;
  return a;
}

template <class NumType>
inline DMatrix<NumType> operator* (NumType a, const DMatrix<NumType> & b)
{
  DMatrix<NumType> c(b.nrows(), b.ncols());
  for (size_t i=0; i<b.size(); ++i)
    c[i] = a * b[i];
  return c;
}

template <class NumType>
inline DMatrix<NumType> operator/ (const DMatrix<NumType> & a, NumType b)
{
  DMatrix<NumType> c(a);
  NumType ib(1.0/b);
  for (size_t i=0; i<a.size(); ++i)
    c[i] *= ib;
  return c;
}

template <class NumType>
inline DMatrix<NumType> & operator/= (DMatrix<NumType> & a, NumType b)
{
  NumType ib(1.0/b);
  for (size_t i=0; i<a.size(); ++i)
    a[i] *= ib;
  return a;
}

template <class NumType>
inline DMatrix<NumType> operator/ (NumType a, const DMatrix<NumType> & b)
{
  DMatrix<NumType> c(b.nrows(), b.ncols());
  for (size_t i=0; i<b.size(); ++i)
    c[i] = a / b[i];
  return c;
}

template <class NumType>
inline DMatrix<NumType> sin(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = sin(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> cos(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = cos(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> tan(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = tan(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> asin(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = asin(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> acos(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = acos(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> atan(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = atan(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> exp(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = exp(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> log(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = log(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> sqrt(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = sqrt(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> ceil(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = ceil(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> floor(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = floor(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> sinh(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = sinh(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> cosh(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = cosh(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> tanh(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = tanh(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> fabs(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = fabs(a[i]);
  return b;
}

template <class NumType>
inline DMatrix<NumType> log10(const DMatrix<NumType> & a)
{
  DMatrix<NumType> b(a.nrows(), a.ncols());
  for (size_t i=0; i<a.size(); ++i)
    b[i] = log10(a[i]);
  return b;
}

