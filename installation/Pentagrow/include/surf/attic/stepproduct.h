//
// project:      surf
// file:         stepproduct.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Product entity in step file

#ifndef SURF_STEPPRODUCT_H
#define SURF_STEPPRODUCT_H

#include "stepentity.h"

/** STEP Product data.

  Top-level product data; required by most postprocessors.

*/
class StepProduct : public StepEntity
{
public:

  /// create an empty entity
  StepProduct() : StepEntity(StepEntity::Product) {}

  /// create from line
  StepProduct(const char *s) : StepEntity(StepEntity::Product)
  {
    StepLine line(s);
    readLine( line );
  }

  /// read from line
  virtual bool readLine(StepLine & line);

  /// write line
  virtual void write(std::ostream & os) const;

public:

  /// contents
  std::string prodId, prodName, prodDescription;

  /// product context entity
  Indices prodContext;
};

/** STEP Product context.

  Reference to application context.

*/
class StepProductContext : public StepEntity
{
public:

  /// create an empty entity
  StepProductContext() : StepEntity(StepEntity::ProductContext) {}

  /// create from line
  StepProductContext(const char *s) : StepEntity(StepEntity::ProductContext)
  {
    StepLine line(s);
    readLine( line );
  }

  /// read from line
  virtual bool readLine(StepLine & line);

  /// write line
  virtual void write(std::ostream & os) const;

public:

  /// context name and 'discipline type'
  std::string name, discipline;

  /// enitity reference to application context
  uint appContext;
};

class StepProductDefinition : public StepEntity
{
public:

  /// create an empty entity
  StepProductDefinition() : StepEntity(StepEntity::ProductDefinition) {}

  /// create from line
  StepProductDefinition(const char *s) : StepEntity(StepEntity::ProductDefinition)
  {
    StepLine line(s);
    readLine( line );
  }

  /// read from line
  virtual bool readLine(StepLine & line);

  /// write line
  virtual void write(std::ostream & os) const;

public:

  // string entities ignored

  /// formation and frame of reference
  uint formation, frameOfReference;
};

#endif // STEPPRODUCT_H
