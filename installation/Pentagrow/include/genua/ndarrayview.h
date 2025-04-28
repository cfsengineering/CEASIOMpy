
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
 
#ifndef GENUA_NDARRAYVIEW_H
#define GENUA_NDARRAYVIEW_H

#include "ndarraybase.h"

template <int ND, typename Type>
class NDArrayView : public NDArrayBase<ND,Type>
{
public:

  typedef Type value_type;
  typedef Type* iterator;
  typedef const Type* const_iterator;
  typedef Type& reference;
  typedef const Type& const_reference;

  /// default constructor, empty array
  NDArrayView(Type *ptr = 0) : NDArrayBase<ND,Type>(), store(ptr) {}

  /// special constructor, allocates n elements only
  NDArrayView(Type *ptr, size_t n) : NDArrayBase<ND,Type>(n), store(ptr) {}

  /// constructor for two dimensions
  NDArrayView(Type *ptr, size_t n0, size_t n1)
    : NDArrayBase<ND,Type>(n0,n1), store(ptr) {}

  /// constructor for three dimensions
  NDArrayView(Type *ptr, size_t n0, size_t n1, size_t n2)
    : NDArrayBase<ND,Type>(n0,n1,n2), store(ptr) {}

  /// constructor for four dimensions
  NDArrayView(Type *ptr, size_t n0, size_t n1, size_t n2, size_t n3)
    : NDArrayBase<ND,Type>(n0,n1,n2,n3), store(ptr) {}

  /// constructor for five dimensions
  NDArrayView(Type *ptr, size_t n0, size_t n1, size_t n2, size_t n3, size_t n4)
    : NDArrayBase<ND,Type>(n0,n1,n2,n3,n4), store(ptr) {}

  /// compute array size
  size_t size() const {return NDArrayBase<ND,Type>::computeSize();}

  /// return length of dimension k
  size_t size(size_t k) const {
    assert(k < ND);
    return dim[k];
  }

  /// access pointer to first element
  value_type *pointer() {return store;}

  /// retrieve pointer to data block
  const value_type *pointer() const {return store;}

  /// linear access
  const_reference operator[] (size_t i) const {
    assert(i < size());
    return store[i];
  }

  /// linear
  reference operator[] (size_t i) {
    assert(i < size());
    return store[i];
  }

  /// N-dimensional access
  const_reference operator() (size_t i0, size_t i1) const {
    BOOST_STATIC_ASSERT(ND == 2);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    return store[lindex(idx)];
  }

  /// N-dimensional access
  reference operator() (size_t i0, size_t i1) {
    BOOST_STATIC_ASSERT(ND == 2);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    return store[lindex(idx)];
  }

  /// N-dimensional access
  const_reference operator() (size_t i0, size_t i1, size_t i2) const {
    BOOST_STATIC_ASSERT(ND == 3);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    idx[2] = i2;
    return store[lindex(idx)];
  }

  /// N-dimensional access
  reference operator() (size_t i0, size_t i1, size_t i2) {
    BOOST_STATIC_ASSERT(ND == 3);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    idx[2] = i2;
    return store[lindex(idx)];
  }

  /// N-dimensional access
  const_reference operator() (size_t i0, size_t i1, size_t i2, size_t i3) const {
    BOOST_STATIC_ASSERT(ND == 4);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    idx[2] = i2;
    idx[3] = i3;
    return store[lindex(idx)];
  }

  /// N-dimensional access
  reference operator() (size_t i0, size_t i1, size_t i2, size_t i3) {
    BOOST_STATIC_ASSERT(ND == 4);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    idx[2] = i2;
    idx[3] = i3;
    return store[lindex(idx)];
  }

  /// N-dimensional access
  const_reference operator() (size_t i0, size_t i1, size_t i2,
                              size_t i3, size_t i4) const {
    BOOST_STATIC_ASSERT(ND == 5);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    idx[2] = i2;
    idx[3] = i3;
    idx[4] = i4;
    return store[lindex(idx)];
  }

  /// N-dimensional access
  reference operator() (size_t i0, size_t i1, size_t i2,
                        size_t i3, size_t i4) {
    BOOST_STATIC_ASSERT(ND == 5);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    idx[2] = i2;
    idx[3] = i3;
    idx[4] = i4;
    return store[lindex(idx)];
  }

  /// array slice along the last dimension
  NDArrayView<ND-1,Type> slice(size_t k) {
    size_t idx[ND];
    for (int i=0; i<ND-1; ++i)
      idx[i] = 0;
    idx[ND-1] = k;
    NDArrayView<ND-1,Type> b;
    b.store = &store[lindex(idx)];
    for (int i=0; i<ND-1; ++i)
      b.dim[i] = dim[i];
    return b;
  }

protected:

  /// rebind pointed-to storage
  void rebind(Type *ptr) {store = ptr;}

private:

  /// referred-to storage
  Type *store;

  /// dimensions
  size_t dim[ND];
};

template <int ND, typename Type>
class ConstNDArrayView : public NDArrayBase<ND,Type>
{
public:

  typedef NDArrayBase<ND,Type> Base;
  typedef Type value_type;
  typedef Type* iterator;
  typedef const Type* const_iterator;
  typedef Type& reference;
  typedef const Type& const_reference;

  /// default constructor, empty array
  ConstNDArrayView(const Type *ptr = 0) : NDArrayBase<ND,Type>(), store(ptr) {}

  /// special constructor, allocates n elements only
  ConstNDArrayView(const Type *ptr, size_t n)
    : NDArrayBase<ND,Type>(n), store(ptr) {}

  /// constructor for two dimensions
  ConstNDArrayView(const Type *ptr, size_t n0, size_t n1)
    : NDArrayBase<ND,Type>(n0, n1), store(ptr) {}

  /// constructor for three dimensions
  ConstNDArrayView(const Type *ptr, size_t n0, size_t n1, size_t n2)
    : NDArrayBase<ND,Type>(n0, n1, n2), store(ptr) {}

  /// constructor for four dimensions
  ConstNDArrayView(const Type *ptr, size_t n0, size_t n1, size_t n2, size_t n3)
    : NDArrayBase<ND,Type>(n0, n1, n2, n3), store(ptr) {}

  /// constructor for five dimensions
  ConstNDArrayView(const Type *ptr, size_t n0, size_t n1, size_t n2,
                   size_t n3, size_t n4)
    : NDArrayBase<ND,Type>(n0, n1, n2, n3, n4), store(ptr) {}

  /// compute array size
  size_t size() const {return NDArrayBase<ND,Type>::computeSize();}

  /// retrieve pointer to data block
  const value_type *pointer() const {return store;}

  /// linear access
  const_reference operator[] (size_t i) const {
    assert(i < size());
    return store[i];
  }

  /// N-dimensional access
  const_reference operator() (size_t i0, size_t i1) const {
    BOOST_STATIC_ASSERT(ND == 2);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    return store[lindex(idx)];
  }

  /// N-dimensional access
  const_reference operator() (size_t i0, size_t i1, size_t i2) const {
    BOOST_STATIC_ASSERT(ND == 3);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    idx[2] = i2;
    return store[lindex(idx)];
  }

  /// N-dimensional access
  const_reference operator() (size_t i0, size_t i1,
                              size_t i2, size_t i3) const {
    BOOST_STATIC_ASSERT(ND == 4);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    idx[2] = i2;
    idx[3] = i3;
    return store[lindex(idx)];
  }

  /// N-dimensional access
  const_reference operator() (size_t i0, size_t i1, size_t i2,
                              size_t i3, size_t i4) const {
    BOOST_STATIC_ASSERT(ND == 5);
    size_t idx[ND];
    idx[0] = i0;
    idx[1] = i1;
    idx[2] = i2;
    idx[3] = i3;
    idx[4] = i4;
    return store[lindex(idx)];
  }

  /// array slice along the last dimension
  ConstNDArrayView<ND-1,Type> slice(size_t k) const {
    size_t idx[ND];
    for (int i=0; i<ND-1; ++i)
      idx[i] = 0;
    idx[ND-1] = k;
    ConstNDArrayView<ND-1,Type> b;
    b.store = &store[lindex(idx)];

    size_t *bd = b.dim;
    for (int i=0; i<ND-1; ++i)
      bd[i] = Base::dim[i];
    return b;
  }

protected:

  /// rebind pointed-to storage
  void rebind(const Type *ptr) {store = ptr;}

private:

  /// referred-to storage
  const Type *store;
};

#endif // GENUA_NDARRAYVIEW_H

