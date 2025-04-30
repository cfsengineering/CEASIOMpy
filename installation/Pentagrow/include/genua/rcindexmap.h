
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
 
#ifndef GENUA_RCINDEXMAP_H
#define GENUA_RCINDEXMAP_H

#include "forward.h"

/** Row/column index map.
 *
 *  This class contains index vectors which map node indices to row/column
 *  indices. Such a mapping is often needed in numerical algorithms where
 *  Dirichlet boundary conditions are associated with some nodes. Eliminating
 *  the corresponding indices using such an index map is one option to handle
 *  the boundary condition.
 *
 *  \ingroup numerics
 *  \sa ConnectMap
 */
class RCIndexMap
{
public:

  /// undefined map
  RCIndexMap() : m_shift(0) {}

  /// default map for n nodes (all map to NotFound)
  explicit RCIndexMap(uint n)
    : m_rowmap(n, NotFound), m_colmap(n, NotFound), m_shift(0) {}

  /// identity map (no constraints)
  void identity(uint n, uint shift = 0);

  /// change row and column offset
  void indexShift(size_t n) {m_shift = n;}

  /// access present index shift
  uint indexShift() const {return m_shift;}

  /// access row of vertex k
  force_inline uint rowOf(uint k) const {
    assert(k < m_rowmap.size());
    uint row = m_rowmap[k];
    return (row != NotFound) ? (m_shift + row) : NotFound;
  }

  /// access column index for vertex k
  force_inline uint colOf(uint k) const {
    assert(k < m_colmap.size());
    uint col = m_colmap[k];
    return (col != NotFound) ? (m_shift + col) : NotFound;
  }

  /// largest row indexed
  uint maxRowIndex() const;

  /// largest column indexed
  uint maxColIndex() const;

  /// number of free vertices
  force_inline uint nfree() const {return m_colnode.size();}

  /// return index i of vertex associated with column j, colOf(i) == j
  force_inline uint columnNode(uint j) const {
    assert(j >= m_shift);
    assert(j < m_colnode.size()+m_shift);
    return m_colnode[j - m_shift];
  }

  /// direct access to map
  const Indices &rowmap() const {return m_rowmap;}

  /// direct access to map
  Indices &rowmap() {return m_rowmap;}

  /// direct access to map
  const Indices &colmap() const {return m_colmap;}

  /// direct access to map
  Indices &colmap() {return m_colmap;}

  /// assign from index set such that rowOf(inodes[i]) == i
  void assignRows(const Indices &inodes) {
    assignMap(inodes, m_rowmap);
  }

  /// assign from index set such that colOf(inodes[i]) == i
  void assignCols(const Indices &inodes) {
    assignMap(inodes, m_colmap);
    m_colnode = inodes;
  }

  /// use column index array to expand xcol to xnodal
  template <class VectorType>
  void xexpand(const VectorType &xcol, VectorType &xnodal) const {
    const size_t n = m_colnode.size();
    for (size_t i=0; i<n; ++i)
      xnodal[m_colnode[i]] = xcol[i];
  }

  /// build symmetric row and column map from set of constrained nodes
  void constrain(uint n, const Indices &inodes);

  /// expand a nodal sparsity pattern to full global equation sparsity
  void expandSparsity(int ne, ConnectMap &spty) const;

protected:

  /// assign from index set such that map[inodes[i]] == i
  void assignMap(const Indices &inodes, Indices &map);

private:

  /// maps global vertex indices to rows of a linear system
  Indices m_rowmap;

  /// maps global vertex indices to columns of a linear system
  Indices m_colmap;

  /// "inverse" of column map: node associated to column
  Indices m_colnode;

  /// shift value to apply to row and column indices
  uint m_shift;
};

#endif // RCINDEXMAP_H
