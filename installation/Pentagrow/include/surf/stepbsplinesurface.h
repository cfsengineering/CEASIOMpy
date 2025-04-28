
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
 
#ifndef STEPBSPLINESURFACE_H
#define STEPBSPLINESURFACE_H

#include "stepentity.h"
#include <genua/dvector.h>
#include <genua/point.h>

class StepFile;

/**



  */
class StepBSplineSurface : public StepEntity
{
public:

  /// empty surface
  StepBSplineSurface() : StepEntity(BSplineSurface, NotFound), rows(0), cols(0) {}

  /// read content from line
  StepBSplineSurface(const char *s)
    : StepEntity(BSplineSurface, NotFound), rows(0), cols(0)
  {
    StepLine line(s);
    readLine( line );
  }

  /// control point grid dimensions
  uint nrows() const {return rows;}

  /// control point grid dimensions
  uint ncols() const {return cols;}

  /// access control point entity id
  uint cpIndex(uint i, uint j) const {
    assert(i < rows);
    assert(j < cols);
    return cpix[j*rows+i];
  }

  /// assemble control point grid
  bool cpGrid(const StepFile & file, PointGrid<3> & grid) const;

  /// read content from line
  virtual bool readLine(StepLine & line);

  /// every entity must be able to write itself to stream
  virtual void write(std::ostream & os) const;

public:

  /// control point array entity ids
  Indices cpix;

  /// rows and columns of the above
  uint rows, cols;

  /// degree in u- and v-direction
  int uDegree, vDegree;
};

class StepBSplineSurfaceWithKnots : public StepBSplineSurface
{
public:

  /// empty surface
  StepBSplineSurfaceWithKnots() : StepBSplineSurface()
  {
    typeCode = BSplineSurfaceWithKnots;
  }

  /// read content from line
  StepBSplineSurfaceWithKnots(const char *s) : StepBSplineSurface()
  {
    typeCode = BSplineSurfaceWithKnots;
    StepLine line(s);
    readLine( line );
  }

  /// test whether dimensions fit together
  virtual StepEntity::Validity valid() const;

  /// read content from line
  virtual bool readLine(StepLine & line);

  /// every entity must be able to write itself to stream
  virtual void write(std::ostream & os) const;

public:

  /// knot multiplicities
  Indices uMulti, vMulti;

  /// knot vectors
  DVector<double> uKnots, vKnots;
};

#endif // STEPBSPLINESURFACE_H
