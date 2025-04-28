
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
 
#include "sparseblockmatrix.h"

void detail::block_sparsity(int M, const ConnectMap &espty, ConnectMap &bmap)
{
  size_t ner = espty.size();
  size_t nbr = (ner / M);
  if (M*nbr < ner)
    ++nbr;

  bmap.beginCount(nbr);
  for (size_t i=0; i<ner; ++i)
    bmap.incCount( i/M, espty.size(i) );
  bmap.endCount();
  for (size_t i=0; i<ner; ++i) {
    size_t ibr = i/M;
    ConnectMap::const_iterator itr, last = espty.end(i);
    for (itr = espty.begin(i); itr != last; ++itr)
      bmap.append( ibr, (*itr) / M );
  }
  bmap.compress();
}

uint detail::nzproduct_pairs(const ConnectMap &a, int arow,
                             const ConnectMap &b, int brow, uint pairs[])
{
  const uint *acol = a.first(arow);
  const uint *bcol = b.first(brow);
  uint na = a.size(arow);
  uint nb = b.size(brow);
  uint aoffs = a.offset(arow);
  uint boffs = b.offset(brow);
  if (na == 0 or nb == 0)
    return 0;

  uint np(0);
  uint ia(0), ib(0);
  do {
    uint ca = acol[ia];
    uint cb = bcol[ib];
    if (ca < cb) {
      ++ia;
    } else if (ca > cb) {
      ++ib;
    } else {
      pairs[np+0] = aoffs + ia;
      pairs[np+1] = boffs + ib;
      np += 2;
      ++ia;
      ++ib;
    }
  } while (ia < na and ib < nb);

  return np;
}
