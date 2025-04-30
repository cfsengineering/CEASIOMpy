
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
 
#ifndef SURF_DCEDGETABLE_H
#define SURF_DCEDGETABLE_H

#include "dcedge.h"
#include <genua/preshinghashtable.h>
#include <boost/static_assert.hpp>
#include <boost/functional/hash.hpp>
#include <boost/unordered/unordered_set.hpp>

/** Edge hash table.
 *
 * A linearly stored, open-adressing hash table for DcEdge objects. Works
 * in 64bit systems only, because it relies on the ability to store both
 * edge vertex indices in a single size_t value.
 *
 * \todo
 * - Use first 8 bytes as key instead of key computation
 * - Pack entire DcEdge objects into table and let table own edges
 * - Store src+1 and trg+1 to eliminate key==0 case, elide branches
 *
 * \ingroup meshgen
 * \sa DcEdge, PreshingTable
 */
class DcEdgeOpenTable
{
public:

  /// initialize with size guess
  DcEdgeOpenTable(size_t initialSize = 512) : m_imap(initialSize)
  {
    BOOST_STATIC_ASSERT(sizeof(size_t) == sizeof(uint64_t));
  }

  /// number of edges presently stored in container
  size_t size() const {return m_imap.size();}

  /// lookup edge
  DcEdge *find(uint src, uint trg)
  {
    if (src > trg)
      std::swap(src, trg);
    PreshingTable::Cell *cell = m_imap.lookup(keyOf(src, trg));
    return decode(cell);
  }

  /// insert edge
  void insert(DcEdge *pe)
  {
    size_t key = keyOf(pe->source(), pe->target());
    PreshingTable::Cell *cell = m_imap.insert(key);
    assert(cell != nullptr);
    cell->value = encode(pe);
  }

  /// erase edge
  void erase(uint src, uint trg) {
    if (src > trg)
      std::swap(src, trg);
    m_imap.erase(keyOf(src, trg));
  }

  /// erase contents
  void clear() { m_imap.clear(); }

  friend class Iterator;

  class Iterator
  {
  public:

    /// create a 'begin' iterator
    Iterator(PreshingTable &table, bool toBegin = true) : m_iter(table, toBegin)
    {
    }

    /// prefix increment
    inline Iterator &operator++()
    {
      m_iter.next();
      return *this;
    }

    /// dereference
    inline DcEdge *operator*() const
    {
      PreshingTable::Cell *cell = *m_iter;
      return DcEdgeOpenTable::decode(cell);
    }

    /// dereference
    inline DcEdge *operator->() const
    {
      PreshingTable::Cell *cell = *m_iter;
      return DcEdgeOpenTable::decode(cell);
    }

    /// equality
    bool operator==(const Iterator &other) const
    {
      return *m_iter == *(other.m_iter);
    }

    /// inequality
    bool operator!=(const Iterator &other) const
    {
      return *m_iter != *(other.m_iter);
    }

  private:
    /// iterator to integer map
    PreshingTable::Iterator m_iter;
  };

  /// iteration over all edges
  Iterator begin() { return DcEdgeOpenTable::Iterator(m_imap, true); }

  /// iteration over all edges
  Iterator end() { return DcEdgeOpenTable::Iterator(m_imap, false); }

private:

  /// compute key for src/target combination
  static inline uint64_t keyOf(uint src, uint trg)
  {
    return (uint64_t(src) << 32) | uint64_t(trg);
  }

  /// decode content pointer
  static inline DcEdge *decode(const PreshingTable::Cell *c) {
    if (c != nullptr) {
      union { size_t s; DcEdge *p; } u;
      u.s = c->value;
      return u.p;
    }
    return nullptr;
  }

  /// encode content pointer
  static inline size_t encode(const DcEdge *ptr) {
    union { size_t s; const DcEdge *p; } u;
    u.p = ptr;
    return u.s;
  }

private:

  /// 64bit integer key-value map
  PreshingTable m_imap;
};

class DcEdgeHashTable
{
public:

  /// backend : hash set from boost
  typedef boost::unordered_set<DcEdge*, DcEdge::Hasher,
                                        DcEdge::PtrEqual> HashSet;

  /// iterator type
  typedef HashSet::iterator Iterator;

  /// initialize with an guess for the size
  DcEdgeHashTable(size_t initialSize = 512) { m_set.reserve(initialSize); }

  /// number of edges presently stored in container
  size_t size() const {return m_set.size();}

  /// lookup edge
  DcEdge *find(uint src, uint trg)
  {
    DcEdge test(src, trg);
    HashSet::const_iterator pos = m_set.find(&test);
    return (pos != m_set.end()) ? *pos : nullptr;
  }

  /// insert edge
  void insert(DcEdge *pe)
  {
    m_set.insert(pe);
  }

  /// erase edge
  void erase(uint src, uint trg) {
    DcEdge test(src, trg);
    HashSet::const_iterator pos = m_set.find(&test);
    if (pos != m_set.end())
      m_set.erase(pos);
  }

  /// erase contents
  void clear() { m_set.clear(); }

  /// iterate over map
  Iterator begin() {return m_set.begin();}

  /// iterate over map
  Iterator end() {return m_set.end();}

private:

  /// actual storage
  HashSet m_set;
};

#ifdef GENUA_64BIT
typedef DcEdgeOpenTable DcEdgeTable;
#else
typedef DcEdgeHashTable DcEdgeTable;
#endif

#endif  // DCEDGETABLE_H
