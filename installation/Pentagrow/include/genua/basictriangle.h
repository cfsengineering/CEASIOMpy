
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
 
#ifndef GENUA_BASICTRIANGLE_H
#define GENUA_BASICTRIANGLE_H

#include "defines.h"
#include <set>

/** Basic linear triangle object.

  BasicTriangle defines a three-node linear triangle object which owns its
  vertex index storage (12 bytes) and defines an ordering for use with
  sorted associative containers.

  \ingroup geometry
  \sa BasicEdge
*/
class BasicTriangle
{
public:

  /// undefined triangle
  BasicTriangle() {}

  /// create triangle from three vertices
  BasicTriangle(const uint v[]) {
    order(v[0],v[1],v[2]);
  }

  /// create triangle from three vertices
  BasicTriangle(uint a, uint b, uint c) {
    order(a,b,c);
  }

  /// assign three vertices
  void assign(uint a, uint b, uint c) {
    order(a,b,c);
  }

  /// assign three vertices
  void assign(const uint v[]) {
    order(v[0],v[1],v[2]);
  }

  /// access contents
  const uint *vertices() const {return vi;}

  /// check if any two vertices are identical
  bool degenerate() const {
    if (vi[0] == vi[1] or vi[0] == vi[2] or vi[1] == vi[2])
      return true;
    else
      return false;
  }

  /// not degenerate
  bool regular() const {return !degenerate();}

  /// sorting criterion
  bool operator< (const BasicTriangle & a) const {
    if (vi[0] < a.vi[0])
      return true;
    else if (vi[0] > a.vi[0])
      return false;
    else if (vi[1] < a.vi[1])
      return true;
    else if (vi[1] > a.vi[1])
      return false;
    else
      return (vi[2] < a.vi[2]);
  }

  /// equivalence
  bool operator== (const BasicTriangle & a) const {
    if (vi[0] != a.vi[0])
      return false;
    else if (vi[1] != a.vi[1])
      return false;
    else if (vi[2] != a.vi[2])
      return false;
    else
      return true;
  }

  /// difference
  bool operator!= (const BasicTriangle & a) const {
    return !(*this == a);
  }

protected:

  /// set vertices in correct order
  void order(uint a, uint b, uint c) {
    if (a < b and a < c) {
      vi[0] = a;
      vi[1] = b;
      vi[2] = c;
    } else if (b < a and b < c) {
      vi[0] = b;
      vi[1] = c;
      vi[2] = a;
    } else {
      vi[0] = c;
      vi[1] = a;
      vi[2] = b;
    }
  }

protected:

  /// vertex indices
  uint vi[3];
};

#endif // BASICTRIANGLE_H
