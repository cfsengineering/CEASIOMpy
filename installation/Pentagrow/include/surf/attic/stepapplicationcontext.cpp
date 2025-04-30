//
// project:      surf
// file:         stepapplicationcontext.cpp
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// STEP application context entity

#include "stepapplicationcontext.h"

bool StepApplicationContext::readLine(StepLine & line)
{
  entId = line.entityId();
  if (entId == NotFound)
    return false;

  return line.parseString(application);
}

void StepApplicationContext::write(std::ostream & os) const
{
  writeHead(os);
  os << '\'' << application << '\'';
}
