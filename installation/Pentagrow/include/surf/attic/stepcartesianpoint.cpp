//
// project:      surf
// file:         stepcartesianpoint.cpp
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Geometric point (3D) in STEP file (AP203)

#include "stepcartesianpoint.h"
#include "stepline.h"

// debug
#include <iostream>
using namespace std;

bool StepCartesianPoint::readLine(StepLine & line)
{
  entId = line.entityId();
  if (entId == NotFound)
    return false;

  // label not used, skip
  line.skipAttr();

  StepListRep list = line.parseList();
  if (not list.parseFloats<3>(pt.pointer()))
    return false;

  return true;
}

void StepCartesianPoint::write(std::ostream & os) const
{
  // no label
  writeHead(os);
  os << "'',(" << pt[0] << ',' << pt[1] << ',' << pt[2] << ')';
}
