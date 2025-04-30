
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
 
#include "trimesh.h"
#include "triedge.h"

Real TriEdge::length() const
{
  const Vct3 & p1( msh->vertex(v[0]) );
  const Vct3 & p2( msh->vertex(v[1]) );
  return norm(p2-p1);
}

Real TriEdge::direction(Vct3 & dv) const
{
  const Vct3 & p1( msh->vertex(v[0]) );
  const Vct3 & p2( msh->vertex(v[1]) );
  dv = p2-p1;
  return normalize(dv);
}
