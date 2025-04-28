
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
 
#ifndef GENUA_NZHASHTABLE_H
#define GENUA_NZHASHTABLE_H

#include "ssemalloc.h"
#include "algo.h"
#include <cstddef>
#include <cassert>

template <class Item>
class NzHashTable
{
public:

  /// construct with initial size
  NzHashTable(size_t initialSize = 8) : m_capacity(initialSize), m_population(0)
  {
    assert((m_capacity & (m_capacity - 1)) == 0);  // Must be a power of 2
    m_cells = (Item *) allocate_aligned( m_capacity*sizeof(Item) );
    memset(m_cells, 0, sizeof(Item) * m_capacity);
  }

  /// destroy, release storage
  ~NzHashTable()
  {
    destroy_aligned(m_cells);
  }

  /// locate item with key, return zero if not found
  template <class KeyFunction>
  Item *lookup(KeyFunction f, size_t key) const
  {
    assert(key != 0);
    for (Item *cell = firstCell(hashOf(key));; cell = nextCell(cell)) {
      size_t ck = f(cell);
      if (ck == key)
        return cell;
      else if (ck == 0)
        return nullptr;
    }
  }

  /// if element with key exists, return that; otherwise, return pointer to new
  template <class KeyFunction>
  Item *insert(KeyFunction f, size_t key)
  {
    assert(key != 0);
    size_t hk = hashOf(key);
    for (;;) {
      for (Item *cell = firstCell(hk);; cell = nextCell(cell)) {
        size_t ck = f(cell);
        if (ck == key)  // Found
          return cell;
        if (ck == 0) {  // Insert here
          if ( hint_unlikely((m_population + 1) * 4 >= m_capacity * 3) ) {
            repopulate(f, 2*m_capacity); // Time to resize
            break;
          }
          ++m_population;
          return cell;
        }
      }
    }
  }

  /// erase a cell by its key
  template <class KeyFunction>
  void erase(KeyFunction f, size_t key)
  {
    Item *value = lookup(f, key);
    if (value != nullptr)
      this->erase(f, value);
  }

  /// erase an internal cell
  template <class KeyFunction>
  void erase(KeyFunction f, Item *cell)
  {
    assert(cell >= m_cells && size_t(cell - m_cells) < m_capacity);
    assert(f(cell) != 0);

    // Remove this cell by shuffling neighboring cells
    // so there are no gaps in anyone's probe chain
    for (Item *neighbor = nextCell(cell);; neighbor = nextCell(neighbor)) {
      size_t nbk = f(neighbor);
      if (nbk == 0) {
        // There's nobody to swap with.
        // Go ahead and clear this cell, then return
        memset(cell, 0, sizeof(Item));
        --m_population;
        return;
      }
      Item *ideal = firstCell(hashOf(nbk));
      if (circularOffset(ideal, cell) < circularOffset(ideal, neighbor)) {
        // Swap with neighbor, then make neighbor the new cell to remove.
        // *cell = *neighbor;
        memcpy(cell, neighbor, sizeof(Item));
        cell = neighbor;
      }
    }
  }

private:

  /// access first item
  Item *firstCell(size_t hash) const {
    return m_cells + ((hash) & (m_capacity - 1));
  }

  /// next cell, with wrap-around
  Item *nextCell(Item *c) const {
    return ((c) + 1 != m_cells + m_capacity ? (c) + 1 : m_cells);
  }

  /// index offset for circular addressing
  size_t circularOffset(Item *a, Item *b) const {
    return ((b) >= (a) ? (b) - (a) : m_capacity + (b) - (a));
  }

  /// compute hash value for a key
  static size_t hashOf(size_t h) {
    if (sizeof(size_t) == 8) {
      h ^= h >> 33;
      h *= 0xff51afd7ed558ccd;
      h ^= h >> 33;
      h *= 0xc4ceb9fe1a85ec53;
      h ^= h >> 33;
    } else {
      h ^= h >> 16;
      h *= 0x85ebca6b;
      h ^= h >> 13;
      h *= 0xc2b2ae35;
      h ^= h >> 16;
    }
    return h;
  }

  /// change size
  template <class KeyFunction>
  void repopulate(KeyFunction f, size_t desiredSize)
  {
    assert((desiredSize & (desiredSize - 1)) == 0);  // Must be a power of 2
    assert(m_population * 4 <= desiredSize * 3);

    // Get start/end pointers of old array
    Item *oldCells = m_cells;
    Item *end = m_cells + m_capacity;

    // Allocate new array
    m_capacity = desiredSize;
    m_cells = (Item *) allocate_aligned( m_capacity*sizeof(Item) );
    memset(m_cells, 0, sizeof(Item) * m_capacity);

    // Iterate through old array
    for (Item *c = oldCells; c != end; ++c) {
      size_t ck = f(c);
      if (ck != 0) {
        // Insert this element into new array
        for (Item *cell = firstCell(hashOf(ck));; cell = nextCell(cell)) {
          size_t khere = f(cell);
          if (khere == 0) { // Insert here
            // *cell = *c;
            memcpy(cell, c, sizeof(Item));
            break;
          }
        }
      }
    }

    // Delete old array
    destroy_aligned(oldCells);
  }

private:

  /// linear item array
  Item *m_cells;

  /// capacity and current population
  size_t m_capacity, m_population;
};

#endif // NZHASHTABLE_H

