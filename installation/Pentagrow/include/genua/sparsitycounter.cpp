
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
 
#include "connectmap.h"
#include "sparsitycounter.h"

void SparsityCounter::append(const ConnectMap & map)
{
  const uint nr = map.size();
  for (uint i=0; i<nr; ++i)
    append(i, map.size(i), map.first(i));
}


