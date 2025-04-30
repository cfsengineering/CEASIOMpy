
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
 
#ifndef GENUA_POINT_H
#define GENUA_POINT_H

#include <iostream>
#include <string>
#include <vector>
#include <sstream>

#include "forward.h"
#include "xmlelement.h"
#include "xcept.h"
#include "svector.h"
#include "dmatrix.h"
#include "ptinpoly.h"
#include "allocator.h"

/** Points on a rectangular grid.

 PointGrid organizes n-dimensional points in a rectangular grid
 (a point matrix). It is often used to represent structural mesh
 patches (of quadrilateral elements).

  \ingroup geometry
  \sa PointList
*/
template <uint N, class Type>
class PointGrid
{
public:

  typedef SVector<N,Type> point_type;
  typedef std::vector<point_type, AlignedAllocator<point_type,64> > container;
  // typedef std::vector< SVector<N,Type> > container;
  typedef typename container::iterator iterator;
  typedef typename container::const_iterator const_iterator;
  typedef typename container::value_type value_type;
  typedef typename container::reference reference;
  typedef typename container::const_reference const_reference;
  typedef typename container::pointer pointer_type;

  /// default empty constructor
  PointGrid() : rows(0), cols(0) {}

  /// sized construction
  explicit PointGrid(uint r, uint c) : rows(r), cols(c), data(r*c) {}

  /// copy construction
  PointGrid(const PointGrid<N,Type> & src)
    : rows(src.rows), cols(src.cols), data(src.data) {}

  /// assignment operator
  PointGrid<N,Type> & operator=(const PointGrid<N,Type> & rhs) {
    if (&rhs == this)
      return *this;
    rows = rhs.rows;
    cols = rhs.cols;
    data = rhs.data;
    return *this;
  }

  /// element equality
  bool operator== (const PointGrid<N,Type> & rhs) const {
    return std::equal(begin(), end(), rhs.begin(), rhs.end());
  }

  /// pointer to first element
  const Type *pointer() const {
    assert(!data.empty());
    return data[0].pointer();
  }

  /// pointer to first element of first point
  Type *pointer() {
    assert(!data.empty());
    return data[0].pointer();
  }

  /// mutable linear access
  reference operator[] (uint i) {
    assert(rows*cols > i);
    return data[i]; }

  /// const linear access
  const_reference operator[] (uint i) const {
    assert(rows*cols > i);
    return data[i]; }

  /// mutable linear access
  reference operator() (uint i) {
    assert(rows*cols > i);
    return data[i]; }

  /// const linear access
  const_reference operator() (uint i) const {
    assert(rows*cols > i);
    return data[i]; }

  /// mutable 2D access
  reference operator() (uint r, uint c) {
    assert(uint(r) < rows);
    assert(uint(c) < cols);
    return data[r+c*rows]; }

  /// const 2D access
  const_reference operator() (uint r, uint c) const {
    assert(uint(r) < rows);
    assert(uint(c) < cols);
    return data[r+c*rows]; }

  /// row count
  uint nrows() const {return rows;}

  /// column count
  uint ncols() const {return cols;}

  /// total size
  uint size() const {return data.size();}

  /// check for content
  bool empty() const {return data.empty();}

  /// clear content
  void clear() {data.clear(); rows=cols=0;}

  /// reset to zero points
  void zero() {
    SVector<N,Type> zero;
    std::fill(begin(), end(), zero);
  }

  /// set new size of memory block
  void resize(uint r, uint c) {
    rows = r;
    cols = c;
    data.resize(r*c);
    SVector<N,Type> zero;
    std::fill(begin(), end(), zero);
  }

  /// start pointer
  const_iterator begin() const {return data.begin();}

  /// one-past-end pointer
  const_iterator end() const {return data.end();}

  /// start pointer
  iterator begin() {return data.begin();}

  /// one-past-end pointer
  iterator end() {return data.end();}

  /// scale
  void operator*= (Real f) {
    iterator itr;
    for (itr = data.begin(); itr != data.end(); itr++)
      *itr *= f;
  }

  /// scale
  void operator/= (Real f) {
    iterator itr;
    for (itr = data.begin(); itr != data.end(); itr++)
      *itr /= f;
  }

  /// offset
  const PointGrid<N,Type> & operator+= (const PointGrid<N,Type> & a) {
    assert(a.size() == data.size());
    for (uint i=0; i<a.size(); i++)
      data[i] += a[i];
    return *this;
  }

  /// offset
  const PointGrid<N,Type> & operator-= (const PointGrid<N,Type> & a) {
    assert(a.size() == data.size());
    for (uint i=0; i<a.size(); i++)
      data[i] -= a[i];
    return *this;
  }

  /// add
  PointGrid<N,Type> operator+ (const PointGrid<N,Type> & a) {
    assert(a.size() == data.size());
    PointGrid<N,Type> b(*this);
    for (uint i=0; i<a.size(); i++)
      b[i] += a[i];
    return b;
  }

  /// substract
  PointGrid<N,Type> operator- (const PointGrid<N,Type> & a) {
    assert(a.size() == data.size());
    PointGrid<N,Type> b(*this);
    for (uint i=0; i<a.size(); i++)
      b[i] -= a[i];
    return b;
  }

  /// convert to xml representation
  XmlElement toXml() const {
    XmlElement xe("PointGrid");
    xe["dim"] = str(N);
    xe["rows"] = str(rows);
    xe["cols"] = str(cols);

    std::stringstream ss;
    for (uint i=0; i<size(); ++i)
      ss << data[i] << std::endl;
    xe.text() = ss.str();
    return xe;
  }

  /// read from xml representation
  void fromXml(const XmlElement & xe) {
    if (xe.name() != "PointGrid")
      throw Error("PointGrid: Incompatible XML representation: "+xe.name());
    rows = Int(xe.attribute("rows"));
    cols = Int(xe.attribute("cols"));
    assert(Int(xe.attribute("dim")) == N);
    data.resize(rows*cols);
    std::stringstream ss;
    ss << xe.text();
    for (uint i=0; i<data.size(); ++i)
      ss >> data[i];
  }

  /// swap pointers
  void swap(PointGrid<N,Type> & a) {
    std::swap(rows, a.rows);
    std::swap(cols, a.cols);
    data.swap(a.data);
  }

private:

  /// size
  uint rows, cols;
  
  /// storage
  container data;
};

/** Comparator to sort points by coordinate.

  \ingroup geometry
  \sa PointList
  */
template <uint N, class Type, uint C>
struct point_less
{
  bool operator() (const SVector<N,Type> & a,
                   const SVector<N,Type> & b) const
  {
    return a[C] < b[C];
  }
};

/** Contiguously stored array of n-d points.
 *
 * This is a thin wrapper around a std::vector of SVector elements which adds
 * some member functions which are often needed, such as a euclidian-distance
 * based unique(), bounds() and XML/binary data i/o.
 *
 * Very old.
 *
 * \ingroup geometry
 * \sa PointGrid, Transformation, SVector
 */
template <uint N, class Type>
class PointList
{
public:

  // typedef SVector<N,Type>  PtType;
  // typedef std::vector<PtType> container;
  typedef SVector<N,Type> point_type;
  typedef std::vector<point_type, AlignedAllocator<point_type,64> > container;
  typedef typename container::const_iterator const_iterator;
  typedef typename container::iterator iterator;
  typedef typename container::value_type value_type;
  typedef typename container::reference reference;
  typedef typename container::const_reference const_reference;

  /// default construction
  PointList() {}

  /// move construction
  PointList(PointList<N,Type> &&src) : data(std::move(src.data)) {}

  /// copy construction
  PointList(const PointList<N,Type> &) = default;

  /// sized construction
  explicit PointList(uint n) : data(n) {}

  /// conversion construction
  template <class AType>
  explicit PointList(const PointList<N,AType> & a) {
    const uint n = a.size();
    data.resize(n);
    for (uint i=0; i<n; ++i)
      data[i] = SVector<N,Type>( a[i] );
  }

  /// range initialization
  template <class Iterator>
  explicit PointList(Iterator first, Iterator last) {
    data.assign(first, last);
  }

  /// construct by reordering another list
  template <class AType>
  explicit PointList(const PointList<N,AType> &a, const Indices &idx) {
    const size_t n = idx.size();
    data.resize(n);
    for (size_t i=0; i<n; ++i)
      data[i] = a[idx[i]];
  }

  /// move assignment
  PointList<N,Type> & operator= (PointList<N,Type> &&src) {
    if (this != &src)
      data = std::move(src.data);
    return *this;
  }

  /// copy assignment
  PointList<N,Type> & operator= (const PointList<N,Type> & src) {
    if (this != &src)
      data.assign(src.begin(), src.end());
    return *this;
  }

  /// fill list with one value
  PointList<N,Type> & operator= (const point_type & src) {
    std::fill(begin(), end(), src);
    return *this;
  }

  /// const access
  const_iterator begin() const {return data.begin();}

  /// access
  iterator begin() {return data.begin();}

  /// const access
  const_iterator end() const {return data.end();}

  /// access
  iterator end() {return data.end();}

  /// subscript access
  const_reference operator[] (uint i) const {
    assert(data.size() > i);
    return data[i];
  }

  /// subscript access
  reference operator[] (uint i) {
    assert(data.size() > i);
    return data[i];
  }

  /// construct a subset
  PointList<N,Type> operator[] (const Indices &idx) const {
    return PointList<N,Type>(*this, idx);
  }

  /// subscript access
  const_reference operator() (uint i) const {
    assert(data.size() > i);
    return data[i];
  }

  /// subscript access
  reference operator() (uint i) {
    assert(data.size() > i);
    return data[i];
  }

  /// first object
  const_reference front() const {
    assert(not empty());
    return data.front();
  }

  /// first object
  reference front() {
    assert(not empty());
    return data.front();
  }

  /// last object
  const_reference back() const {
    assert(not empty());
    return data.back();
  }

  /// last object
  reference back() {
    assert(not empty());
    return data.back();
  }

  /// indexed from behind
  const_reference back(uint i) const {
    assert(data.size() > i);
    return data[data.size()-1-i];
  }

  /// indexed from behind
  reference back(uint i) {
    assert(data.size() > i);
    return data[data.size()-1-i];
  }

  /// pointer to first value of first point
  const Type *pointer() const {
    assert(not empty());
    return front().pointer();
  }

  /// pointer to first value of first point
  Type *pointer() {
    assert(not empty());
    return front().pointer();
  }

  /// vector length
  uint size() const {return data.size();}

  /// storage capacity
  uint capacity() const {return data.capacity();}

  /// check for content
  bool empty() const {return data.empty();}

  /// change length
  void resize(uint n) {data.resize(n);}

  /// change length
  void resize(uint n, const value_type & t) {data.resize(n, t);}

  /// reserve storage
  void reserve(uint n) {data.reserve(n);}

  /// append and return index of appended point
  uint push_back(const value_type & x) {
    data.push_back(x);
    return data.size()-1;
  }

  template < class... Args >
  void emplace_back(Args&&... args) {
    data.emplace_back(std::forward<Args>(args)...);
  }

  /// range insert
  template <class InputIterator>
  void insert(iterator pos, InputIterator a, InputIterator b) {
    data.insert(pos,a,b);
  }

  /// item insert
  iterator insert(iterator pos, const_reference a) {
    return data.insert(pos,a);
  }

  /// erase element
  iterator erase(iterator pos) {return data.erase(pos);}

  /// erase range
  iterator erase(iterator from, iterator to) {return data.erase(from, to);}

  /// clear storage
  void clear() {data.clear();}

  /// compute sum of segment lengths
  Real length() const {
    Real len(0);
    const_iterator prev, itr;
    prev = itr = data.begin();
    while (++itr != data.end()) {
      len += norm(*itr - *prev);
      prev++;
    }
    return len;
  }

  /// append, return new size
  uint append(const PointList<N> & a) {
    data.insert(data.end(), a.begin(), a.end());
    return data.size();
  }

  /// remove last element
  void pop_back() {
    if (!data.empty())
      data.pop_back();
  }

  /// remove consecutive duplicates
  void unique(Real tol=gmepsilon) {
    if (data.empty())
      return;

    iterator itr = data.begin();
    container tmp;
    tmp.reserve(data.size());
    tmp.push_back(data.front());
    const Real sqt = sq(tol);
    while (++itr != data.end()) {
      if (sq(*itr - tmp.back()) > sqt)
        tmp.push_back(*itr);
    }
    data.swap(tmp);
  }

  /// scale
  void operator*= (Real f) {
    iterator itr;
    for (itr = data.begin(); itr != data.end(); itr++)
      *itr *= f;
  }

  /// scale
  void operator/= (Real f) {
    iterator itr;
    for (itr = data.begin(); itr != data.end(); itr++)
      *itr /= f;
  }

  /// offset
  const PointList<N> & operator+= (const PointList<N> & a) {
    assert(a.size() == data.size());
    for (uint i=0; i<a.size(); i++)
      data[i] += a[i];
    return *this;
  }

  /// offset
  const PointList<N> & operator-= (const PointList<N> & a) {
    assert(a.size() == data.size());
    for (uint i=0; i<a.size(); i++)
      data[i] -= a[i];
    return *this;
  }

  /// add
  PointList<N> operator+ (const PointList<N> & a) const {
    assert(a.size() == data.size());
    PointList<N> b(data);
    for (uint i=0; i<a.size(); i++)
      b[i] += a[i];
    return b;
  }

  /// substract
  PointList<N> operator- (const PointList<N> & a) const {
    assert(a.size() == data.size());
    PointList<N> b(data);
    for (uint i=0; i<a.size(); i++)
      b[i] -= a[i];
    return b;
  }

  /// find index of point with smallest c coordinate
  template <uint C>
  uint cmin() const {
    point_less<N,Type,C> pless;
    const_iterator pos;
    pos = std::min_element(begin(), end(), pless);
    return std::distance(begin(), pos);
  }

  /// find index of point with largest c coordinate
  template <uint C>
  uint cmax() const {
    point_less<N,Type,C> pless;
    const_iterator pos;
    pos = std::max_element(begin(), end(), pless);
    return std::distance(begin(), pos);
  }

  /// determine bounding box
  template <typename BType>
  void bounds(SVector<N,BType> &plo, SVector<N,BType> &phi,
              bool initBounds = true) const
  {
    if (initBounds) {
      plo = std::numeric_limits<BType>::max();
      phi = -plo;
    }
    const size_t n = size();
    for (size_t i=0; i<n; ++i) {
      const point_type &p( data[i] );
      for (uint k=0; k<N; ++k) {
        plo[k] = std::min( plo[k], BType(p[k]) );
        phi[k] = std::max( phi[k], BType(p[k]) );
      }
    }
  }

  /// zero out everything
  void zero() {
    size_t nbytes = data.size() * N * sizeof(Type);
    memset( &data[0], 0, nbytes );
  }

  /// swap contents with other point list
  void swap(PointList<N,Type> & other) {data.swap(other.data);}

  /// convert to xml representation
  XmlElement toXml() const {
    XmlElement xe("PointList");
    xe["dim"] = str(N);
    xe["size"] = str(this->size());

    std::stringstream ss;
    for (uint i=0; i<size(); ++i)
      ss << data[i] << std::endl;
    xe.text() = ss.str();
    return xe;
  }

  /// read from xml representation
  void fromXml(const XmlElement & xe) {
    if (xe.name() != "PointList")
      throw Error("PointList: Incompatible XML representation: "+xe.name());
    uint n = Int(xe.attribute("size"));
    assert(Int(xe.attribute("dim")) == N);
    data.resize(n);
    std::stringstream ss;
    ss << xe.text();
    for (uint i=0; i<data.size(); ++i)
      ss >> data[i];
  }

private:

  /// dynamic storage
  container data;
};

/* ----------------- Functions ------------------------------------------------ */

template <uint N, typename FloatType>
std::ostream & operator<< (std::ostream & os, const PointList<N,FloatType> & pts)
{
  for (uint i=0; i<pts.size(); ++i)
    os << pts[i] << std::endl;
  return os;
}

template <uint N>
std::ostream & operator<< (std::ostream & os, const PointGrid<N> & pts)
{
  for (uint i=0; i<pts.size(); ++i)
    os << pts[i] << std::endl;
  return os;
}

template <uint N, typename FloatType>
std::istream & operator>> (std::istream & is, PointList<N, FloatType> & pts)
{
  const int np(pts.size());
  for (int i=0; i<np; ++i)
    is >> pts[i];
  return is;
}

template <uint N>
std::istream & operator>> (std::istream & is, PointGrid<N> & pts)
{
  const int np(pts.size());
  for (int i=0; i<np; ++i)
    is >> pts[i];
  return is;
}

template <class AType, class BType, uint N>
inline void convert(const PointList<N,AType> & a, PointList<N,BType> & b)
{
  const int n = a.size();
  b.resize(n);
  for (int i=0; i<n; ++i)
    convert(a[i], b[i]);
}

// scalar * pointgrid
template <uint N>
inline PointGrid<4> operator* (Real x, const PointGrid<N> & pg)
{return pg*x;}

// elevation to 4D space
PointGrid<4> homogenize(const PointGrid<3> & pg3d, Real w = 1);

// projection to 3D space
PointGrid<3> project(const PointGrid<4> & pg4d);

template <class FloatType>
bool point_in_polygon(const PointList<2,FloatType> & vtx,
                      const SVector<2,FloatType> & p)
{
  return point_in_polygon(vtx.size(), vtx.pointer(), p.pointer());
}

// ------------- legacy interfaces

/// factory functions for legacy programs
Vct2 point(Real x, Real y);
Vct3 point(Real x, Real y, Real z);
Vct4 point(Real x, Real y, Real z, Real w);

/// elevate into 4D homgeneous space
inline Vct4 homogenize(const Vct3 & pt, Real w = 1)
{
  Vct4 p;
  p(0) = pt(0)*w;
  p(1) = pt(1)*w;
  p(2) = pt(2)*w;
  p(3) = w;
  return p;
}

/// project into 3D space
inline Vct3 project(const Vct4 & pt)
{
  Vct3 p;
  Real w = pt(3);
  p(0) = pt(0)/w;
  p(1) = pt(1)/w;
  p(2) = pt(2)/w;
  return p;
}

#endif

