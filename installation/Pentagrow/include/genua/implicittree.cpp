
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
 
#include "implicittree.h"
#include "strutils.h"

XmlElement ImplicitTree::toXml(bool share) const
{
  XmlElement xe("ImplicitTree");
  xe["nitem"] = str(nitem);
  xe["ntop"] = str(ntop);
  xe["minsize"] = str(minsize);
  xe.asBinary(items.size(), &items[0], share);
  return xe;
}

void ImplicitTree::fromXml(const XmlElement &xe)
{
  nitem = Int(xe.attribute("nitem"));
  ntop = Int(xe.attribute("ntop"));
  minsize = Int(xe.attribute("minsize"));
  items.resize(nitem);
  xe.fetch(nitem, &items[0]);

  // rebuild ranges
  const uint nn = nnodes();
  if (nn > 0) {
    irange.resize(2*nn);
    irange[0] = 0;
    irange[1] = nitem;
    for (uint k=1; k<nn; ++k) {
      uint p = this->parent(k);
      uint pbegin = this->begin(p);
      uint pend = this->end(p);
      if (k & 0x1) {
        irange[2*k+0] = pbegin;
        irange[2*k+1] = (pbegin + pend) / 2;
      } else {
        irange[2*k+0] = (pbegin + pend) / 2;
        irange[2*k+1] = pend;
      }
    }
  } else {
    irange.clear();
  }
}

float ImplicitTree::megabyte() const
{
  float b = sizeof(ImplicitTree);
  b += items.capacity() * sizeof(ItemArray::value_type);
  b += irange.capacity() * sizeof(Indices::value_type);
  return 1e-6f*b;
}
