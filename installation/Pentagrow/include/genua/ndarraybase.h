
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
 
#ifndef GENUA_NDARRAYBASE_H
#define GENUA_NDARRAYBASE_H

#include <boost/static_assert.hpp>
#include "defines.h"

/** Base class for N-diemsnional arrays.

  This class is responsible for indexing n-dimensional arrays. The indexing
  is similar to the fortran or matlab (column-major, first-index-fastest)
  convention.

*/
template <int ND, typename Type>
class NDArrayBase
{
public:

  typedef Type value_type;
  typedef Type* iterator;
  typedef const Type* const_iterator;
  typedef Type& reference;
  typedef const Type& const_reference;

  /// default constructor, empty array
  NDArrayBase() {
    BOOST_STATIC_ASSERT(ND >= 1);
    for (int i=0; i<ND; ++i)
      dim[i] = 0;
  }

  /// special constructor, allocates n elements only
  NDArrayBase(size_t n) {
    BOOST_STATIC_ASSERT(ND >= 1);
    dim[0] = n;
    for (int i=1; i<ND; ++i)
      dim[i] = 1;
  }

  /// constructor for two dimensions
  NDArrayBase(size_t n0, size_t n1) {
    BOOST_STATIC_ASSERT(ND == 2);
    dim[0] = n0;
    dim[1] = n1;
  }

  /// constructor for three dimensions
  NDArrayBase(size_t n0, size_t n1, size_t n2) {
    BOOST_STATIC_ASSERT(ND == 3);
    dim[0] = n0;
    dim[1] = n1;
    dim[2] = n2;
  }

  /// constructor for four dimensions
  NDArrayBase(size_t n0, size_t n1, size_t n2, size_t n3) {
    BOOST_STATIC_ASSERT(ND == 4);
    dim[0] = n0;
    dim[1] = n1;
    dim[2] = n2;
    dim[3] = n3;
  }

  /// constructor for five dimensions
  NDArrayBase(size_t n0, size_t n1, size_t n2, size_t n3, size_t n4)
  {
    BOOST_STATIC_ASSERT(ND == 5);
    dim[0] = n0;
    dim[1] = n1;
    dim[2] = n2;
    dim[3] = n3;
    dim[4] = n4;
  }

  /// compute linear array size
  size_t computeSize() const {
    size_t s(1);
    for (int i=0; i<ND; ++i)
      s *= dim[i];
    return s;
  }

  /// compute linear from multi-index
  size_t lindex(const size_t idx[]) const {
    assert(idx[0] < dim[0]);
    size_t slice(dim[0]), lix(idx[0]);
    for (int i=1; i<ND; ++i) {
      assert(idx[i] < dim[i]);
      lix += slice * idx[i];
      slice *= dim[i];
    }
    return lix;
  }

protected:

  /// dimensions
  size_t dim[ND];
};

#endif // NDARRAYBASE_H
