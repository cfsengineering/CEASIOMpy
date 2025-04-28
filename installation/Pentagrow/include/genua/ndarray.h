
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
 

#ifndef GENUA_NDARRAY_H
#define GENUA_NDARRAY_H

#include "ndarrayview.h"
#include "dvector.h"
#include "xmlelement.h"
#include "xcept.h"
#include "typecode.h"
#include <boost/static_assert.hpp>

template <int ND, typename Type>
class NDArray : public NDArrayView<ND,Type>
{
public:

  typedef NDArrayView<ND,Type> ViewBase;
  typedef Type value_type;
  typedef Type* iterator;
  typedef const Type* const_iterator;
  typedef Type& reference;
  typedef const Type& const_reference;

  /// default constructor, empty array
  NDArray() : NDArrayView<ND,Type>() {}

  /// special constructor, allocates n elements only
  NDArray(size_t n) : NDArrayView<ND,Type>(0, n) {
    data.resize( NDArrayView<ND,Type>::size() );
    ViewBase::rebind( data.empty() ? 0 : &data[0] );
  }

  /// constructor for two dimensions
  NDArray(size_t n0, size_t n1) : NDArrayView<ND,Type>(0, n0, n1) {
    data.resize( NDArrayView<ND,Type>::size() );
    ViewBase::rebind( data.empty() ? 0 : &data[0] );
  }

  /// constructor for three dimensions
  NDArray(size_t n0, size_t n1, size_t n2)
    : NDArrayView<ND,Type>(0, n0, n1, n2)
  {
    data.resize( NDArrayView<ND,Type>::size() );
    ViewBase::rebind( data.empty() ? 0 : &data[0] );
  }

  /// constructor for four dimensions
  NDArray(size_t n0, size_t n1, size_t n2, size_t n3)
    : NDArrayView<ND,Type>(0, n0, n1, n2, n3)
  {
    data.resize( NDArrayView<ND,Type>::size() );
    ViewBase::rebind( data.empty() ? 0 : &data[0] );
  }

  /// constructor for five dimensions
  NDArray(size_t n0, size_t n1, size_t n2, size_t n3, size_t n4)
    : NDArrayView<ND,Type>(0, n0, n1, n2, n3, n4)
  {
    data.resize( NDArrayView<ND,Type>::size() );
    ViewBase::rebind( data.empty() ? 0 : &data[0] );
  }

  /// allocates n elements only, first dimension n, all else 1
  void resize(size_t n) {
    NDArrayBase<ND,Type>::dim[0] = n;
    for (int i=1; i<ND; ++i)
      NDArrayBase<ND,Type>::dim[i] = 1;
    data.resize( NDArrayView<ND,Type>::size() );
    ViewBase::rebind( data.empty() ? 0 : &data[0] );
  }

  /// allocator for two dimensions
  void resize(size_t n0, size_t n1) {
    BOOST_STATIC_ASSERT(ND == 2);
    NDArrayBase<ND,Type>::dim[0] = n0;
    NDArrayBase<ND,Type>::dim[1] = n1;
    data.resize( NDArrayView<ND,Type>::size() );
    ViewBase::rebind( data.empty() ? 0 : &data[0] );
  }

  /// allocator for three dimensions
  void resize(size_t n0, size_t n1, size_t n2) {
    BOOST_STATIC_ASSERT(ND == 3);
    NDArrayBase<ND,Type>::dim[0] = n0;
    NDArrayBase<ND,Type>::dim[1] = n1;
    NDArrayBase<ND,Type>::dim[2] = n2;
    data.resize( NDArrayView<ND,Type>::size() );
    ViewBase::rebind( data.empty() ? 0 : &data[0] );
  }

  /// allocator for four dimensions
  void resize(size_t n0, size_t n1, size_t n2, size_t n3) {
    BOOST_STATIC_ASSERT(ND == 4);
    NDArrayBase<ND,Type>::dim[0] = n0;
    NDArrayBase<ND,Type>::dim[1] = n1;
    NDArrayBase<ND,Type>::dim[2] = n2;
    NDArrayBase<ND,Type>::dim[3] = n3;
    data.resize( NDArrayView<ND,Type>::size() );
    ViewBase::rebind( data.empty() ? 0 : &data[0] );
  }

  /// allocator for five dimensions
  void resize(size_t n0, size_t n1, size_t n2, size_t n3, size_t n4) {
    BOOST_STATIC_ASSERT(ND == 5);
    NDArrayBase<ND,Type>::dim[0] = n0;
    NDArrayBase<ND,Type>::dim[1] = n1;
    NDArrayBase<ND,Type>::dim[2] = n2;
    NDArrayBase<ND,Type>::dim[3] = n3;
    NDArrayBase<ND,Type>::dim[4] = n4;
    data.resize( NDArrayView<ND,Type>::size() );
    ViewBase::rebind( data.empty() ? 0 : &data[0] );
  }

  /// compute array capacity
  size_t capacity() const {
    return data.capacity();
  }

  /// access pointer to first element
  value_type *pointer() {return data.pointer();}

  /// retrieve pointer to data block
  const value_type *pointer() const {return data.pointer();}

  /// create XML representation for array
  XmlElement toXml(bool share = false) const {
    XmlElement xe("NDArray");
    xe["ndim"] = str(ND);
    xe["elementTypeCode"] = create_typecode<Type>().toString();
    std::stringstream ss;
    for (int i=0; i<ND; ++i)
      ss << NDArrayBase<ND,Type>::dim[i] << ' ';
    xe["dim"] = ss.str();

    xe.asBinary(data.size(), data.pointer(), share);
    return xe;
  }

private:

  /// linear array used to store values
  DVector<Type> data;
};

#endif // NDARRAY_H
