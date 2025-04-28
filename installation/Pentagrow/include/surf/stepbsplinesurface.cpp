
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
 
#include "stepbsplinesurface.h"
#include "stepline.h"
#include "stepcartesianpoint.h"
#include "stepfile.h"

// debug
#include <iostream>
using namespace std;

bool StepBSplineSurface::cpGrid(const StepFile & file,
                                PointGrid<3> & grid) const
{
  const int nr = nrows();
  const int nc = ncols();
  grid.resize(nr,nc);
  const StepCartesianPoint *pp(0);
  for (int j=0; j<nc; ++j) {
    for (int i=0; i<nr; ++i) {
      uint idx = file.find( cpIndex(i, j) );
      if (idx == NotFound)
        return false;
      if (not file.as(idx, &pp))
        return false;
      grid(i,j) = pp->pt;
    }
  }

  return true;
}

bool StepBSplineSurface::readLine(StepLine & line)
{
  entId = line.entityId();
  if (entId == NotFound)
    return false;

  // label not used, skip
  line.skipAttr();

  // polynomial degree
  uDegree = line.parseInt();
  vDegree = line.parseInt();

  // list of list of control point entities
  StepListRep cplist = line.parseList();
  if (not cplist.valid())
    return false;

  // matrix dimensions
  cols = cplist.nChildLists();
  uint ncp = cplist.nComma() + 1;
  rows = ncp / cols;

  // dump into linear array
  cpix.clear();
  cpix.reserve(ncp);
  cplist.parseIds(cpix);
  if (cpix.size() != ncp)
    return false;

  line.move(cplist.end());

  // skip four attributes
  for (int k=0; k<4; ++k)
    line.skipAttr();

  return true;
}

void StepBSplineSurface::write(std::ostream & os) const
{
  writeHead(os);
  os << "''," << uDegree << ',' << vDegree << ',' << "(";
  for (uint j=0; j<cols; ++j) {
    os << '(';
    for (uint i=0; i<rows-1; ++i)
      os << '#' << cpIndex(i,j) << ',';
    os << '#' << cpIndex(rows-1,j) << ")";
    if (j < cols-1)
      os << ',';
  }
  os << "),.UNSPECIFIED.,.F.,.F.,.U.";
}

// -------------------- *WithKnots -------------------------

StepEntity::Validity StepBSplineSurfaceWithKnots::valid() const
{
  if (uMulti.size() < 2)
    return StepEntity::NoContent;
  if (vMulti.size() < 2)
    return StepEntity::NoContent;
  if (uKnots.size() < 2)
    return StepEntity::NoContent;
  if (vKnots.size() < 2)
    return StepEntity::NoContent;

  if (uMulti.size() != uKnots.size())
    return StepEntity::KnotSizeMismatch;
  if (vMulti.size() != vKnots.size())
    return StepEntity::KnotSizeMismatch;

  return StepEntity::Valid;
}

bool StepBSplineSurfaceWithKnots::readLine(StepLine & line)
{
  if (not StepBSplineSurface::readLine(line))
    return false;

  uMulti.clear();
  vMulti.clear();
  uKnots.clear();
  vKnots.clear();

  StepListRep list = line.parseList();
  if (not list.parseInts(uMulti))
    return false;
  line.move( list.end() );

  list = line.parseList();
  if (not list.parseInts(vMulti))
    return false;
  line.move( list.end() );

  list = line.parseList();
  if (not list.parseFloats(uKnots))
    return false;
  line.move( list.end() );

  list = line.parseList();
  if (not list.parseFloats(vKnots))
    return false;
  line.move( list.end() );

  return true;
}

void StepBSplineSurfaceWithKnots::write(std::ostream & os) const
{
  StepBSplineSurface::write(os);
  os << ",(";
  for (uint i=0; i<uMulti.size()-1; ++i)
    os << uMulti[i] << ',';
  os << uMulti.back() << "),(";
  for (uint i=0; i<vMulti.size()-1; ++i)
    os << vMulti[i] << ',';
  os << vMulti.back() << "),(";
  for (uint i=0; i<uKnots.size()-1; ++i)
    os << uKnots[i] << ',';
  os << uKnots.back() << "),(";
  for (uint i=0; i<vKnots.size()-1; ++i)
    os << vKnots[i] << ',';
  os << vKnots.back() << "),.UNSPECIFIED.";
}

