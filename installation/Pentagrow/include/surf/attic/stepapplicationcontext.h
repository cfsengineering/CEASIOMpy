//
// project:      surf
// file:         stepapplicationcontext.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// STEP application context entity

#ifndef SURF_STEPAPPLICATIONCONTEXT_H
#define SURF_STEPAPPLICATIONCONTEXT_H

#include "stepentity.h"

/** STEP Application contect

  Referenced by StepProductContext.

*/
class StepApplicationContext : public StepEntity
{
public:

  /// create an empty entity
  StepApplicationContext()
    : StepEntity(StepEntity::ApplicationContext), application("config control design") {}

  /// create from line
  StepApplicationContext(const char *s) : StepEntity(StepEntity::ApplicationContext)
  {
    StepLine line(s);
    readLine( line );
  }

  /// read from line
  virtual bool readLine(StepLine & line);

  /// write line
  virtual void write(std::ostream & os) const;

public:

  std::string application;
};

#endif // STEPAPPLICATIONCONTEXT_H
