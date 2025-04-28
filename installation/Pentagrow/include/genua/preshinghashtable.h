
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
 
#ifndef GENUA_PRESHINGHASHTABLE_H
#define GENUA_PRESHINGHASHTABLE_H

#include "forward.h"

/** Integer hash table by Jeff Preshing.
 *
 * Maps pointer-sized integers to pointer-sized integers, using open addressing
 * with linear probing.
 *
 * In the m_cells array, key = 0 is reserved to indicate an unused cell.
 * Actual value for key 0 (if any) is stored in m_zeroCell.
 * The hash table automatically doubles in size when it becomes 75% full.
 * The hash table never shrinks in size, even after clear(), unless you
 * explicitly call compact().
 *
 * This code is in the public domain.
 * https://github.com/preshing/CompareIntegerMaps
 *
 * \ingroup utility
 * \sa std::map, JudyMap
 */
class PreshingTable
{
public:
  struct Cell {
    size_t key;
    size_t value;
  };

public:

  /// preallocate a desired size
  PreshingTable(size_t initialSize = 8);

  /// move into another table
  PreshingTable(PreshingTable &&t)
    : m_cells(t.m_cells), m_arraySize(t.m_arraySize),
      m_population(t.m_population), m_zeroCell(t.m_zeroCell),
      m_zeroUsed(t.m_zeroUsed)
  {
    t.m_cells = nullptr;
    t.m_arraySize = t.m_population = 0;
  }

  /// deallocate
  ~PreshingTable();

  /// number of values presently stored
  size_t size() const {return m_population;}

  /// present container size
  size_t capacity() const {return m_arraySize;}

  /// lookup key
  Cell *lookup(size_t key);

  /// lookup key
  const Cell *clookup(size_t key) const;

  /// insert key
  Cell *insert(size_t key);

  /// erase by cell
  void erase(Cell *cell);

  /// erase by key
  void erase(size_t key)
  {
    Cell *value = lookup(key);
    if (value)
      erase(value);
  }

  /// clear table
  void clear();

  /// reduce memory footprint
  void compact();

  friend class Iterator;

  /// iterate over table
  class Iterator
  {
  public:
    /// create begin iterator
    Iterator(PreshingTable &table, bool toBegin = true) : m_table(table)
    {
      if (toBegin) {
        m_cur = &m_table.m_zeroCell;
        if (!m_table.m_zeroUsed)
          next();
      } else {
        m_cur = NULL;
      }
    }

    /// move to next cell
    Cell *next();

    /// dereference
    inline Cell *operator*() const { return m_cur; }

    /// dereference
    inline Cell *operator->() const { return m_cur; }

  private:
    PreshingTable &m_table;
    Cell *m_cur;
  };

private:
  /// change size
  void repopulate(size_t desiredSize);

private:
  /// linear array of cells
  Cell *m_cells;

  /// size of array; must be a power of 2
  size_t m_arraySize;

  /// number of items currently in array
  size_t m_population;

  /// the item for key 0
  Cell m_zeroCell;

  /// whether key 0 is used
  bool m_zeroUsed;
};

#endif  // PRESHINGHASHTABLE_H
