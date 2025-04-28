//
// project:      genua
// file:         alignedarray.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Cacheline-aligned contiguous storage

#ifndef GENUA_ALIGNEDARRAY_H
#define GENUA_ALIGNEDARRAY_H

#include <cassert>
#include <utility>
#include <cstring>
#include "b64arrayops.h"

/** Long vector for POD values.

  AlignedArray is a specialized container template for objects for which a plain
  byte-copy is a valid copy construction. The contents of the array are
  stored in contiguous memory with guaranteed alignment to 64 bytes.

  The alignment properties incurs a certain memory overhead, so that AlignedArray
  is not particularly suited for storing few elements. For that purpose,
  you may consider std::vector or a fixed-size static array.

  This container is (for now) intended for experiments with vectorization.

  */
template <class Type>
class AlignedArray
{
  public:

    typedef Type value_type;
    typedef Type* iterator;
    typedef const Type* const_iterator;
    typedef Type& reference;
    typedef const Type& const_reference;

    /// default empty construction, does not allocate memory
    AlignedArray() : block(0), mroot(0), n(0), cap(0) {}

    /// allocate memory
    explicit AlignedArray(size_t ns) : block(0), mroot(0), n(0), cap(0) {
      resize(ns);
    }

    /// allocate memory
    explicit AlignedArray(size_t ns, value_type t) : block(0), mroot(0), n(0), cap(0) {
      resize(ns);
      detail::block64<Type>::blockfill(block, t, n);
    }

    /// copy construction
    AlignedArray(const AlignedArray & a) : block(0), mroot(0), n(0), cap(0) {
      if (&a != this) {
        resize(a.n);
        detail::block64<Type>::blockcopy(block, a.block, n);
      }
    }

    /// destruction
    ~AlignedArray() {
      detail::block64<Type>::deallocate(mroot);
    }

    /// assignment
    AlignedArray & operator= (const AlignedArray & a) {
      if (&a != this) {
        resize(a.n);
        detail::block64<Type>::blockcopy(block, a.block, n);
      }
      return *this;
    }

    /// assignment
    AlignedArray & operator= (value_type t) {
      detail::block64<Type>::blockfill(block, t, n);
      return *this;
    }

    /// retrieve pointer to data block
    value_type *pointer() {return block;}

    /// retrieve pointer to data block
    const value_type *pointer() const {return block;}

    /// elements in use
    size_t size() const {return n;}

    /// number of 64byte blocks used
    size_t nblock64() const {
      return (n*sizeof(value_type) + 63) / 64;
    }

    /// return true if size() == 0
    bool empty() const {return (n == 0);}

    /// storage capacity
    size_t capacity() const {return cap;}

    /// access element
    const_reference operator[] (size_t i) const {
      assert(i < n);
      return block[i];
    }

    /// access element
    reference operator[] (size_t i) {
      assert(i < n);
      return block[i];
    }

    /// iterator access
    iterator begin() {return block;}

    /// iterator access
    const_iterator begin() const {return block;}

    /// iterator access
    iterator end() {return block+n;}

    /// iterator access
    const_iterator end() const {return block+n;}

    /// first element
    reference front() {return block[0];}

    /// first element
    const_reference front() const {return block[0];}

    /// last element
    reference back() {return block[n-1];}

    /// last element
    const_reference back() const {return block[n-1];}

    /// allocate storage, does not change size
    void reserve(size_t ns) {
      if (ns > cap) {
        cap = allocate(ns, &block, &mroot);
      }
    }

    /// resize vector, invalidates content
    void resize(size_t ns) {
      reserve(ns);
      n = ns;
    }

    /// resize vector, fill completely with t
    void resize(size_t ns, value_type t) {
      resize(ns);
      detail::block64<Type>::blockfill(block, t, n);
    }

    /// reset size to zero, keep allocation
    void clear() {n = 0;}

    /// release all storage
    void free() {
      if (n != 0) {
        detail::block64<Type>::deallocate(mroot);
        block = mroot = 0;
        n = cap = 0;
      }
    }

    /// add element to end, grow vector as needed
    void push_back(value_type x) {
      if (n == cap) {
        value_type *newblock, *newroot;
        size_t ncap = allocate(2*cap, &newblock, &newroot);
        detail::block64<Type>::blockcopy(newblock, block, n);
        swap(ncap, newblock, newroot);
      }
      block[n] = x;
      ++n;
    }

    /// insert element at arbitrary position (expensive, O(n))
    iterator insert(iterator pos, value_type val) {
      assert(pos >= begin());
      assert(pos <= end());
      if (pos == end()) {
        push_back(val);
        return block+n;
      } else {
        size_t nbcopy = size_t(block+n-pos)*sizeof(value_type);
        if (n < cap) {
          detail::block64<Type>::bytemove(pos+1, pos, nbcopy);
          *pos = val;
          ++n;
          return pos+1;
        } else {

          // reallocate with 2*cap
          value_type *newblock, *newroot;
          size_t ncap = allocate(2*cap, &newblock, &newroot);

          // copy old values ahead of pos
          size_t offset = pos - block;
          size_t nahead = offset*sizeof(value_type);
          detail::block64<Type>::blockcopy(newblock, block, offset);

          // copy old values above pos
          newblock[offset] = val;

          // copy remaining stuff, not necessarily aligned
          detail::block64<Type>::bytecopy(newblock+offset+1, block+offset, nbcopy);

          // now, the old data is copied, can delete
          swap(ncap, newblock, newroot);
          ++n;
          return &block[offset+1];
        }
      }
    }

    /// insert a range of values
    void insert(iterator pos, const_iterator from, const_iterator to) {
      assert(pos >= begin());
      assert(pos <= end());
      size_t nin = (to-from);
      size_t nbin = nin*sizeof(value_type);
      size_t offset = pos-block;
      if (n+nin <= cap) {

        // make space for new values
        detail::block64<Type>::bytemove(pos+nin, pos, (n-offset)*sizeof(value_type));

        // insert new values
        detail::block64<Type>::bytecopy(pos, from, nbin);

        // adjust size
        n += nin;
      } else {

        // need to reallocate
        value_type *newblock, *newroot;
        size_t ncap = allocate(2*cap, &newblock, &newroot);

        // copy old values ahead of pos
        // size_t nahead = offset*sizeof(value_type);
        detail::block64<Type>::blockcopy(newblock, block, offset);

        // insert new values next
        detail::block64<Type>::bytecopy(&newblock[offset], from, nbin);

        // append old values behind inserted range
        detail::block64<Type>::bytecopy(&newblock[offset+nin], pos, (n-offset)*sizeof(value_type) );

        // delete old storage block, adjust size
        swap(ncap, newblock, newroot);
        n += nin;
      }
    }

    /// erase a single value
    iterator erase(iterator pos) {
      assert(pos >= begin());
      assert(pos < end());
      size_t ipos = pos - block;
      size_t nbmove = (n - ipos - 1)*sizeof(value_type);
      detail::block64<Type>::bytemove(pos, pos+1, nbmove);
      --n;
      return pos;
    }

    /// erase a range of values
    iterator erase(iterator from, iterator to) {
      assert(from >= begin());
      assert(from < end());
      assert(to > from);
      assert(to >= begin());
      assert(to < end());
      size_t ito = to - block;
      size_t nbmove = (n - ito)*sizeof(value_type);
      detail::block64<Type>::bytemove(from, to, nbmove);
      n -= (to - from);
      return from;
    }

    /// swap pointers
    void swap(AlignedArray & a) {
      std::swap(a.block, block);
      std::swap(a.mroot, mroot);
      std::swap(a.n, n);
      std::swap(a.cap, cap);
    }

  private:

    /// allocate, but do not touch stored pointers, return capacity
    size_t allocate(size_t ns, Type **data, Type **root) const {
      return detail::block64<Type>::allocate(ns, data, root);
    }

    /// use different pointers, delete old storage
    void swap(size_t c, Type *data, Type *root) {
      detail::block64<Type>::deallocate(mroot);
      block = data;
      mroot = root;
      cap = c;
    }

  private:

    /// storage
    value_type *block, *mroot;

    /// size and capacity
    size_t n, cap;
};

// inject swap into namespace std

namespace std
{
  template <class Type>
  inline void swap(AlignedArray<Type> & a, AlignedArray<Type> & b) {a.swap(b);}
}

#endif // ALIGNEDARRAY_H
