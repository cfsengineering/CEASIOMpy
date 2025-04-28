
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

#ifndef GENUA_BASICEDGE_H
#define GENUA_BASICEDGE_H

#include "defines.h"
#include "forward.h"
#include <utility>
#include <set>

/** Basic two-vertex edge object.

  BasicEdge defines an undirected mesh edge with unique ordering. It can be
  used to collect a unique set of element edges in a mesh e.g. for visualization,
  or to identify edges for mesh promotion (linear-to-quadratic).

  \ingroup geometry
  \sa BasicTriangle
*/
class BasicEdge
{
public:

  /// default construction
  BasicEdge() {}

  /// construct from two vertex indices
  BasicEdge(uint s, uint t)  {
    assign(s,t);
  }

  /// assign source and target vertex
  void assign(uint s, uint t) {
    src = std::min(s,t);
    trg = std::max(s,t);
  }

  /// access source vertex index
  uint source() const {return src;}

  /// access target vertex index
  uint target() const {return trg;}

  /// define ordering
  bool operator< (const BasicEdge & a) const {

    //    // bitfiddling tricks. works, but doesn't help
    //    if (sizeof(BasicEdge) == sizeof(uint64_t)) {
    //      union { const BasicEdge *pe; const uint64_t *pi; } x, y;
    //      x.pe = this;
    //      y.pe = &a;
    //      return *(x.pi) < *(y.pi);
    //    } else {
    //      uint64_t x(src), y(a.src);
    //      x = (x << 32) | uint64_t(trg);
    //      y = (y << 32) | uint64_t(a.trg);
    //      return x < y;
    //    }

    if (src < a.src)
      return true;
    else if (src > a.src)
      return false;
    else
      return trg < a.trg;
  }

  /// define equality
  bool operator== (const BasicEdge & a) const {
    return ((src == a.src) and (trg == a.trg));
  }

  /// define equality
  bool operator!= (const BasicEdge & a) const {
    return ((src != a.src) or (trg != a.trg));
  }

  /// generate three edges from triangle vertices
  static void createEdges(const uint *v, BasicEdge e[]) {
    e[0].assign( v[0], v[1] );
    e[1].assign( v[1], v[2] );
    e[2].assign( v[2], v[0] );
  }

protected:

  /// source and target vertex
  uint32_t src, trg;
};

#endif // BASICEDGE_H
