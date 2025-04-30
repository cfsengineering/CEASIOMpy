//
// project:      surf
// file:         stepcartesianpoint.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Geometric point (3D) in STEP file (AP203)

#ifndef SURF_STEPCARTESIANPOINT_H
#define SURF_STEPCARTESIANPOINT_H

#include "stepentity.h"
#include <genua/svector.h>

class StepCartesianPoint : public StepEntity
{
public:

  /// create point w/o ID
  StepCartesianPoint() : StepEntity(StepEntity::CartesianPoint) {}

  /// create from line
  StepCartesianPoint(const char *s)
    : StepEntity(StepEntity::CartesianPoint)
  {
    StepLine line(s);
    readLine( line );
  }

  /// read from file
  virtual bool readLine(StepLine & line);

  /// write CARTESIAN_POINT line
  virtual void write(std::ostream & os) const;

public:

  /// coordinates
  Vct3 pt;
};

#endif // STEPCARTESIANPOINT_H
