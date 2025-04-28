
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
 
#ifndef GENUA_JUDYMAP_H
#define GENUA_JUDYMAP_H

#ifdef HAVE_JUDY

#ifdef NDEBUG
#define JUDYERROR_NOTEST 1
#endif

#include <Judy.h>
#include <vector>
#include <cassert>
#include <stdint.h>

template <class Value>
class JudyIterator
{
public:

  /// construct invalid iterator on array a
  JudyIterator(Pvoid_t a = 0, Value *pos = 0, size_t key = 0)
      : m_pjlarray(a), m_pos(pos), m_key(key) {}

  /// check for validity
  bool valid() const {return (m_pos != 0);}

  /// move to first key equal to or larger than k
  void first(size_t k) {
    m_key = k;
    Pvoid_t pv(0);
    JLF(pv, m_pjlarray, m_key);
    m_pos = reinterpret_cast<Value*>(pv);
  }

  /// move to last key equal or smaller than k
  void last(size_t k) {
    m_key = k;
    Pvoid_t pv(0);
    JLL(pv, m_pjlarray, m_key);
    m_pos = reinterpret_cast<Value*>(pv);
  }

  void next() {
    Pvoid_t pv(0);
    JLN(pv, m_pjlarray, m_key);
    m_pos = reinterpret_cast<Value*>(pv);
  }

  void previous() {
    Pvoid_t pv(0);
    JLP(m_pos, m_pjlarray, m_key);
    m_pos = reinterpret_cast<Value*>(pv);
  }

  /// dereference
  Value & operator* () const {assert(m_pos != 0); return *m_pos;}

  /// increment
  JudyIterator<Value> & operator++ () {
    next();
    return *this;
  }

  /// decrement
  JudyIterator<Value> & operator-- () {
    previous();
    return *this;
  }

  /// test for equality
  bool operator== (const JudyIterator<Value> & a) const {
    return m_pos == a.m_pos;
  }

  /// test inequality
  bool operator!= (const JudyIterator<Value> & a) const {
    return m_pos != a.m_pos;
  }

private:

  /// opaque pointer to Judy array
  Pvoid_t m_pjlarray;

  /// pointer to current value
  Value *m_pos;

  /// key corresponding to pos
  size_t m_key;
};


/** Interface for Judy arrays.
 *
 * The template parameter can be size_t (intptr_t or uintptr_t) or a pointer,
 * nothing else. Other objects must be allocated or stored somewhere else
 * and their index/pointer stored in the JudyArray.
 *
 *
 *
 * Judy is a LGPL-licensed library invented by Doug Baskins and
 * implemented by Hewlett-Packard, available at http://judy.sourceforge.net/
 *
 * \ingroup utility
 * \sa JudyMap
 */
template <class Value>
class JudyArray
{
public:

  typedef Value* pointer;
  typedef JudyIterator<Value> iterator;

  /// create empty array
  JudyArray() : m_pjlarray(NULL) {}

  /// free allocated storage
  ~JudyArray() {
    clear();
  }

  /// insert key/value, return iterator to inserted item
  pointer insert(size_t key, Value value) {
    Pvoid_t pv(0);
    JLI(pv, m_pjlarray, key);
    assert(pv != 0);
    pointer pos = reinterpret_cast<pointer>( pv );
    *pos = value;
    return pos;
  }

  /// erase key from array, return true if value was present
  bool erase(size_t key) {
    int rc;
    JLD(rc, m_pjlarray, key);
    assert(rc != JERR);
    return (rc == 1);
  }

  /// return iterator to first element
  iterator begin() const {
    iterator itr(m_pjlarray);
    itr.first(0);
    return itr;
  }

  /// return iterator to first element
  iterator end() const {
    iterator itr(m_pjlarray);
    return itr;
  }

  /// fetch the iterator for key, return 0 if not found
  iterator find(size_t key) const {
    Pvoid_t pv(0);
    JLG(pv, m_pjlarray, key);
    pointer pos = reinterpret_cast<pointer>(pv);
    return (pv != 0) ? iterator(m_pjlarray, pos, key) : end();
  }

  /// return iterator to first element with index greater or equal to 'key'
  pointer first(size_t & key) const {
    Pvoid_t pv(0);
    JLF(pv, m_pjlarray, key);
    return reinterpret_cast<pointer>( pv );
  }

  /// convenience interface for compatibility
  iterator lower_bound(size_t key) const {
    iterator itr(m_pjlarray);
    itr.first(key);
    return itr;
  }

  /// return iterator to first element with index greater than 'key'
  pointer next(size_t & key) const {
    Pvoid_t pv(0);
    JLN(pv, m_pjlarray, key);
    return reinterpret_cast<pointer>( pv );
  }

  /// return iterator to last element with index less or equal to 'key'
  pointer last(size_t & key) const {
    Pvoid_t pv(0);
    JLL(pv, m_pjlarray, key);
    return reinterpret_cast<pointer>( pv );
  }

  /// convenience interface for compatibility
  iterator upper_bound(size_t key) const {
    iterator itr(m_pjlarray);
    itr.last(key);
    return itr;
  }

  /// return memory used
  size_t memoryUsed() const {
    return JudyLMemUsed(m_pjlarray);
  }

  /// release storage
  void clear() {
    intptr_t rc;
    JLFA(rc, m_pjlarray);
  }

private:

  /// judy array
  Pvoid_t m_pjlarray;
};

/** Generic ordered set implemented using Judy arrays.
 *
 * JudyMap can be used to map objects of any type to unique keys of type
 * size_t. Internally, objects are stored in a value-based std::vector and
 * their indices are kept in the judy array. The interface differs intentionally
 * from the one of std::set<>, which provides similar functionality, because
 * the Judy array requires that each object is unique identified with a size_t
 * key -- this cannot always be achieved.
 *
 * \sa JudyArray
 */
template <class Value>
class JudyMap
{
public:

  typedef typename std::vector<Value>::iterator iterator;
  typedef typename std::vector<Value>::const_iterator const_iterator;
  typedef typename JudyArray<size_t>::iterator judy_iterator;

  /// this value is returned to indicate a failed query (key not present)
  static const size_t npos = ~size_t(0x0);

  /// reserve storage in linear array
  void reserve(size_t n) {
    m_values.reserve(n);
  }

  /// access linear array (not map!)
  const Value & operator[] (size_t index) const {
    assert(index < m_values.size());
    return m_values[index];
  }

  /// access linear array (not map!)
  Value & operator[] (size_t index) {
    assert(index < m_values.size());
    return m_values[index];
  }

  /// number of values in array storage
  size_t size() const {return m_values.size();}

  /// insert a value into map, return linear index
  size_t appendValue(size_t key, const Value & v) {
    size_t index = m_values.size();
    m_values.push_back(v);
    m_jmap.insert(key, index);
    return index;
  }

  /// overwrite value at index with new value with key
  void insertValue(size_t key, const Value & v, size_t index) {
    assert(index < m_values.size());
    m_values[index] = v;
    m_jmap.insert(key, index);
  }

  /// erase element (does not change linear array)
  bool eraseKey(size_t key) {
    return m_jmap.erase(key);
  }

  /// return linear index for value matching key, else npos
  size_t findKey(size_t key) const {
    size_t *pos = m_jmap.find(key);
    return (pos != 0) ? *pos : npos;
  }

  /// find index nearest to key
  size_t lowerBound(size_t key) const {
    size_t *pos = m_jmap.first(key);
    return (pos != 0) ? *pos : npos;
  }

  /// find index nearest to key
  size_t upperBound(size_t & key) const {
    size_t *pos = m_jmap.last(key);
    return (pos != 0) ? *pos : npos;
  }

  /// recompute keys for all values currently stored
  template <class Functor>
  void remap(const Functor & keyFcn) {
    m_jmap.clear();
    const size_t n = m_values.size();
    for (size_t i=0; i<n; ++i)
      m_jmap.insert( keyFcn(m_values[i]), i );
  }

  /// clear storage
  void clear() {
    m_values.clear();
    m_jmap.clear();
  }

private:

  /// plain vector owns elements
  std::vector<Value> m_values;

  /// map keys to index
  JudyArray<size_t> m_jmap;
};


/** Primitive static hash table backed by judy arrays.
 *
 * Depending on the size, this implementation of a hash table is often
 * competitive with boost::unordered_set<> up to a certain size.
 *
 * Benchmarking is strongly recommended before using this hash table.
 *
 * \sa JudyArray
 */
template <class Value, int NShift = 8>
class JudyHashTable
{
public:

  typedef Value* pointer;
  enum { BucketMask = ((1 << NShift) - 1), NBucket = BucketMask+1};
  static const size_t npos = ~size_t(0x0);

  /// insert key/value pair, return iterator to inserted item
  pointer insert(size_t key, Value val) {
    return m_buckets[ key & BucketMask ].insert( key >> NShift, val );
  }

  /// erase item for key
  bool erase(size_t key) {
    return m_buckets[ key & BucketMask ].erase( key >> NShift );
  }

  /// return 0 if no such key found, otherwise iterator to item
  pointer find(size_t key) const {
    return m_buckets[ key & BucketMask ].find( key >> NShift );
  }

private:

  /// key collisions handled by judy arrays
  JudyArray<Value> m_buckets[NBucket];
};

#endif // HAVE_JUDY

#endif // JUDYMAP_H
