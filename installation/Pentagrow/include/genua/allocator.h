
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
 
#ifndef GENUA_ALLOCATOR_H
#define GENUA_ALLOCATOR_H

#ifdef _MSC_VER
#pragma warning(disable:4100)
#endif

#include "ssemalloc.h"

/** STL-compatible aligned-memory allocator.

  This is an allocator which can be used with STL containers to guarantee that
  the memory allocated is aligned to a certain size. This is useful to guarantee
  that data in a std::vector is aligned to 16 byte (SSE), 32 byte (AVX) or
  64 byte (cachelines).

  The memory block returned is always sized to a multiple of the alignment
  value (default is 64 bytes). Vectorized or blocked algorithms which process
  one cacheline at a time can therefore always operate in blocks without
  safeguards against buffer overruns.

  Example: When AlignedAllocator<float,64> is asked for space for 17 floats,
  i.e. 68 bytes, it will allocate 128 bytes. A blocked algorithm may hence
  process two blocks of 16 floats.

  \ingroup utility
  \sa DVector, DMatrix
*/
template<typename T, size_t algn=64>
class AlignedAllocator
{
public :

  typedef T value_type;
  typedef value_type* pointer;
  typedef const value_type* const_pointer;
  typedef value_type& reference;
  typedef const value_type& const_reference;
  typedef std::size_t size_type;
  typedef std::ptrdiff_t difference_type;

  /// used in conversion constructor
  template<typename U>
  struct rebind {
    typedef AlignedAllocator<U> other;
  };

public :

  /// allocator has no state
  inline AlignedAllocator() {}

  /// converson from allocator of different type
  template<typename U>
  inline AlignedAllocator(AlignedAllocator<U> const&) {}

  /// std interface
  inline pointer address(reference r) { return &r; }

  /// std interface
  inline const_pointer address(const_reference r) { return &r; }

  /// allocate, return aligned pointer
  inline pointer allocate(size_type cnt,
                          typename std::allocator<void>::const_pointer = 0)
  {
    size_type bytes = cnt*sizeof(T);
    size_type chunks = bytes/algn + ((bytes & (algn-1)) != 0);
    return reinterpret_cast<pointer>( allocate_aligned(algn*chunks, algn) );
  }

  /// frees allocated memory
  inline void deallocate(pointer p, size_type) { destroy_aligned(p); }

  /// the maximum number of objects which can be allocated (upper limit)
  inline size_type max_size() const {
    return std::numeric_limits<size_type>::max() / sizeof(T);
  }

  /// use placement new to construct a T at p
  inline void construct(pointer p, const T& t) { new(p) T(t); }

  /// calls the destructor; MSVC emits a warning about 'unused parameter p' here.
  inline void destroy(pointer p) { p->~T(); }

  /// allocators are equal if the can be used to allocate exchangeable types
  inline bool operator== (AlignedAllocator const&) { return true; }

  /// AlignedAllocators are never unequal
  inline bool operator!= (AlignedAllocator const& a) { return !operator==(a); }
};

#endif // ALLOCATOR_H
