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

#include "parbilu.h"

void detail::split_sparsity(const ConnectMap &amap,
                            ConnectMap &lmap, ConnectMap &umap)
{
  const size_t nbr = amap.size();

  // counting pass
  lmap.beginCount(nbr);
  umap.beginCount(nbr);
  for (size_t i=0; i<nbr; ++i) {
    const uint nj = amap.size(i);
    const uint *idx = amap.first(i);
    for (uint k=0; k<nj; ++k) {
      uint j = idx[k];
      if (j >= i)
        umap.incCount(j);
      else
        lmap.incCount(i);
    }
  }
  lmap.endCount();
  umap.endCount();

  // assignment pass
  for (size_t i=0; i<nbr; ++i) {
    const uint nj = amap.size(i);
    const uint *idx = amap.first(i);
    for (uint k=0; k<nj; ++k) {
      uint j = idx[k];
      if (j >= i)
        umap.append(j,i);
      else
        lmap.append(i,j);
    }
  }

  // todo : compute levels

  lmap.close();
  umap.sort();
  umap.close();
}
