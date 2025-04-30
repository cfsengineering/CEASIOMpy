//
// project:      surf
// file:         stepproduct.cpp
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Product entity in step file

#include "stepproduct.h"

// ------------------- Product ----------------------------------------

bool StepProduct::readLine(StepLine & line)
{
  entId = line.entityId();
  if (entId == NotFound)
    return false;

  // parse id, name, description
  bool ok = true;
  ok &= line.parseString(prodId);
  ok &= line.parseString(prodName);
  ok &= line.parseString(prodDescription);
  if (not ok)
    return false;

  prodContext.clear();
  StepListRep list = line.parseList();
  if (not list.parseIds(prodContext))
    return false;

  return true;
}

void StepProduct::write(std::ostream & os) const
{
  writeHead(os);
  os << '\'' << prodId << "\',\'" << prodName << "\',\'"
     << prodDescription << "\',(";
  for (uint i=0; i<prodContext.size()-1; ++i)
    os << '#' << prodContext[i] << ',';
  os << '#' << prodContext.back() << ')';
}

// ------------------- ProductContext ---------------------------------

bool StepProductContext::readLine(StepLine & line)
{
  entId = line.entityId();
  if (entId == NotFound)
    return false;

  // parse id, name, description
  bool ok = true;
  ok &= line.parseString(name);
  appContext = line.parseId();
  ok &= (appContext != NotFound);
  ok &= line.parseString(discipline);
  if (not ok)
    return false;

  return true;
}

void StepProductContext::write(std::ostream & os) const
{
  writeHead(os);
  os << '\'' << name << "\',#" << appContext << ",\'"
     << discipline << '\'';
}

// ------------------- ProductDefinition ---------------------------------

bool StepProductDefinition::readLine(StepLine & line)
{
  entId = line.entityId();
  if (entId == NotFound)
    return false;

  // ignore strings : id, description
  line.skipAttr();
  line.skipAttr();

  formation = line.parseId();
  frameOfReference = line.parseId();

  return true;
}

void StepProductDefinition::write(std::ostream & os) const
{
  writeHead(os);
  os << "'','',#" << formation << ",#" << frameOfReference;
}
