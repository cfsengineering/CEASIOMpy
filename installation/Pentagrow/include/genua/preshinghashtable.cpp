
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
 
#include "preshinghashtable.h"
#include "algo.h"
#include <cassert>
#include <cstring>
#include <cstdlib>

// ----------- file scope -----------------------------------------------

template <typename IntType> inline static IntType upper_power_of_two(IntType v)
{
  v--;
  v |= v >> 1;
  v |= v >> 2;
  v |= v >> 4;
  v |= v >> 8;
  v |= v >> 16;
  if (sizeof(IntType) == 8)
    v |= v >> 32;
  v++;
  return v;
}

// from code.google.com/p/smhasher/wiki/MurmurHash3

template <typename IntType> inline static IntType integerHash(IntType h)
{
  if (sizeof(IntType) == 8) {
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

#undef FIRST_CELL
#undef CIRCULAR_NEXT
#undef CIRCULAR_OFFSET

#define FIRST_CELL(hash) (m_cells + ((hash) & (m_arraySize - 1)))
#define CIRCULAR_NEXT(c) ((c) + 1 != m_cells + m_arraySize ? (c) + 1 : m_cells)
#define CIRCULAR_OFFSET(a, b) ((b) >= (a) ? (b) - (a) : m_arraySize + (b) - (a))

// ------------- HashTable --------------------------------------------

PreshingTable::PreshingTable(size_t initialSize)
{
  // Initialize regular cells
  m_arraySize = initialSize;
  assert((m_arraySize & (m_arraySize - 1)) == 0);  // Must be a power of 2
  m_cells = new Cell[m_arraySize];
  // m_cells = (Cell *) allocate_aligned(m_arraySize * sizeof(Cell));
  memset(m_cells, 0, sizeof(Cell) * m_arraySize);
  m_population = 0;

  // Initialize zero cell
  m_zeroUsed = 0;
  m_zeroCell.key = 0;
  m_zeroCell.value = 0;
}

PreshingTable::~PreshingTable()
{
  // Delete regular cells
  delete[] m_cells;
  // if (m_arraySize != 0)
  //  destroy_aligned(m_cells);
}

PreshingTable::Cell *PreshingTable::lookup(size_t key)
{
  if (key) {
    // Check regular cells
    for (Cell *cell = FIRST_CELL(integerHash(key));;
         cell = CIRCULAR_NEXT(cell)) {
      if (cell->key == key)
        return cell;
      if (!cell->key)
        return NULL;
    }
  } else {
    // Check zero cell
    if (m_zeroUsed)
      return &m_zeroCell;
    return NULL;
  }
}

const PreshingTable::Cell *PreshingTable::clookup(size_t key) const
{
  if (key) {
    // Check regular cells
    for (Cell *cell = FIRST_CELL(integerHash(key));;
         cell = CIRCULAR_NEXT(cell)) {
      if (cell->key == key)
        return cell;
      if (!cell->key)
        return NULL;
    }
  } else {
    // Check zero cell
    if (m_zeroUsed)
      return &m_zeroCell;
    return NULL;
  }
}

PreshingTable::Cell *PreshingTable::insert(size_t key)
{
  if (key) {
    // Check regular cells
    for (;;) {
      for (Cell *cell = FIRST_CELL(integerHash(key));;
           cell = CIRCULAR_NEXT(cell)) {
        if (cell->key == key)
          return cell;  // Found
        if (cell->key == 0) {
          // Insert here
          if ( hint_unlikely((m_population + 1) * 4 >= m_arraySize * 3)) {
            // Time to resize
            repopulate(m_arraySize * 2);
            break;
          }
          ++m_population;
          cell->key = key;
          return cell;
        }
      }
    }
  } else {
    // Check zero cell
    if (!m_zeroUsed) {
      // Insert here
      m_zeroUsed = true;
      if ( hint_unlikely(++m_population * 4 >= m_arraySize * 3) ) {
        // Even though we didn't use a regular slot, let's keep the
        // sizing rules consistent
        repopulate(m_arraySize * 2);
      }
    }
    return &m_zeroCell;
  }
}

void PreshingTable::erase(Cell *cell)
{
  if (cell != &m_zeroCell) {
    // Delete from regular cells
    assert(cell >= m_cells && size_t(cell - m_cells) < m_arraySize);
    assert(cell->key);

    // Remove this cell by shuffling neighboring cells
    // so there are no gaps in anyone's probe chain
    for (Cell *neighbor = CIRCULAR_NEXT(cell);;
         neighbor = CIRCULAR_NEXT(neighbor)) {
      if (!neighbor->key) {
        // There's nobody to swap with.
        // Go ahead and clear this cell, then return
        cell->key = 0;
        cell->value = 0;
        m_population--;
        return;
      }
      Cell *ideal = FIRST_CELL(integerHash(neighbor->key));
      if (CIRCULAR_OFFSET(ideal, cell) < CIRCULAR_OFFSET(ideal, neighbor)) {
        // Swap with neighbor, then make neighbor the new cell to remove.
        *cell = *neighbor;
        cell = neighbor;
      }
    }
  } else {
    // Delete zero cell
    assert(m_zeroUsed);
    m_zeroUsed = false;
    cell->value = 0;
    m_population--;
    return;
  }
}

void PreshingTable::clear()
{
  // (Does not resize the array)
  // Clear regular cells
  memset(m_cells, 0, sizeof(Cell) * m_arraySize);
  m_population = 0;
  // Clear zero cell
  m_zeroUsed = false;
  m_zeroCell.value = 0;
}

void PreshingTable::compact()
{
  repopulate(upper_power_of_two((m_population * 4 + 3) / 3));
}

void PreshingTable::repopulate(size_t desiredSize)
{
  assert((desiredSize & (desiredSize - 1)) == 0);  // Must be a power of 2
  assert(m_population * 4 <= desiredSize * 3);

  // Get start/end pointers of old array
  Cell *oldCells = m_cells;
  Cell *end = m_cells + m_arraySize;

  // Allocate new array
  m_arraySize = desiredSize;
  m_cells = new Cell[m_arraySize];
  // m_cells = (Cell *) allocate_aligned( m_arraySize*sizeof(Cell) );
  memset(m_cells, 0, sizeof(Cell) * m_arraySize);

  // Iterate through old array
  for (Cell *c = oldCells; c != end; c++) {
    if (c->key) {
      // Insert this element into new array
      for (Cell *cell = FIRST_CELL(integerHash(c->key));;
           cell = CIRCULAR_NEXT(cell)) {
        if (!cell->key) {
          // Insert here
          *cell = *c;
          break;
        }
      }
    }
  }

  // Delete old array
  delete[] oldCells;
  // destroy_aligned(oldCells);
}

PreshingTable::Cell *PreshingTable::Iterator::next()
{
  // Already finished?
  if (!m_cur)
    return m_cur;

  // Iterate past zero cell
  if (m_cur == &m_table.m_zeroCell)
    m_cur = &m_table.m_cells[-1];

  // Iterate through the regular cells
  Cell *end = m_table.m_cells + m_table.m_arraySize;
  while (++m_cur != end) {
    if (m_cur->key)
      return m_cur;
  }

  // Finished
  return m_cur = NULL;
}
