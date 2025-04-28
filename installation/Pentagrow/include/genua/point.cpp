
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
 
#include "point.h"

Vct2 point(Real x, Real y)
{
  Vct2 pt;
  pt[0] = x;
  pt[1] = y;
  return pt;
}

Vct3 point(Real x, Real y, Real z)
{
  Vct3 pt;
  pt[0] = x;
  pt[1] = y;
  pt[2] = z;
  return pt;
}

Vct4 point(Real x, Real y, Real z, Real w)
{
  Vct4 pt;
  pt[0] = x;
  pt[1] = y;
  pt[2] = z;
  pt[3] = w;
  return pt;
}

PointGrid<4> homogenize(const PointGrid<3> & pg3d, Real w)
{   
  // elevation to 4D space
  PointGrid<4> pg4d(pg3d.nrows(), pg3d.ncols());
  for (uint i=0; i<pg3d.size(); i++)
    pg4d[i] = homogenize(pg3d[i], w);
  return pg4d;
}

// projection to 3D space
PointGrid<3> project(const PointGrid<4> & pg4d)
{
  PointGrid<3> pg3d(pg4d.nrows(), pg4d.ncols());
  for (uint i=0; i<pg4d.size(); i++)
    pg3d[i] = project(pg4d[i]);
  return pg3d;
}

