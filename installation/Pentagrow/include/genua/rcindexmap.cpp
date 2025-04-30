
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
 
#include "rcindexmap.h"
#include "connectmap.h"
#include "algo.h"
#include <algorithm>

void RCIndexMap::identity(uint n, uint shift)
{
  m_shift = shift;
  m_rowmap.clear();
  m_rowmap.resize(n);
  m_colmap.clear();
  m_colmap.resize(n);
  for (uint i=0; i<n; ++i)
    m_rowmap[i] = m_colmap[i] = i;
}

uint RCIndexMap::maxRowIndex() const
{
  const size_t n = m_rowmap.size();
  uint idx = 0;
  for (size_t i=0; i<n; ++i) {
    uint x = m_rowmap[i];
    if (x != NotFound)
      idx = std::max(x, idx);
  }
  return m_shift + idx;
}

uint RCIndexMap::maxColIndex() const
{
  const size_t n = m_colmap.size();
  uint idx = 0;
  for (size_t i=0; i<n; ++i) {
    uint x = m_colmap[i];
    if (x != NotFound)
      idx = std::max(x, idx);
  }
  return m_shift + idx;
}

void RCIndexMap::constrain(uint n, const Indices &inodes)
{
  assert(n > inodes.size());
  assert(std::is_sorted(inodes.begin(), inodes.end()));
  m_rowmap = Indices(n, NotFound);
  m_colmap = Indices(n, NotFound);

  uint pos(0);
  m_colnode.clear();
  m_colnode.reserve( n - inodes.size() );
  for (uint i=0; i<n; ++i) {
    if ( not std::binary_search(inodes.begin(), inodes.end(), i) ) {
      m_colnode.push_back(i);  // m_colnode[pos] = i
      m_rowmap[i] = m_colmap[i] = pos;
      ++pos;
    }
  }
}

void RCIndexMap::assignMap(const Indices &inodes, Indices &map)
{
  const size_t n = inodes.size();
  for (size_t i=0; i<n; ++i)
    map[inodes[i]] = i;
}


void RCIndexMap::expandSparsity(int ne, ConnectMap &spty) const
{
  const size_t n = spty.size();
  ConnectMap map;
  map.beginCount(m_shift + ne*nfree());
  for (size_t i=0; i<n; ++i) {
    uint r = rowOf(i);
    if ( hint_unlikely(r == NotFound) )
      continue;
    for (int k=0; k<ne; ++k)
      map.incCount( m_shift + ne*r+k, spty.size(i)*ne );
  }
  map.endCount();
  for (size_t i=0; i<n; ++i) {
    uint r = rowOf(i);
    if ( hint_unlikely(r == NotFound) )
      continue;
    const uint nnb = spty.size(i);
    const uint *nbv = spty.first(i);
    for (uint j=0; j<nnb; ++j) {
      uint c = colOf( nbv[j] );
      if ( hint_unlikely(c == NotFound) )
        continue;
      for (int ki=0; ki<ne; ++ki) {
        for (int kj=0; kj<ne; ++kj)
          map.append( ne*r+ki, ne*c+kj );
      }
    }
  }
  map.compress();
  spty.swap(map);
}
