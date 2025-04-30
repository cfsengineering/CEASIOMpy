
/* ------------------------------------------------------------------------
 * file:       csmgenerator.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Constructs sumo assembly from CEASIOM definition
 * ------------------------------------------------------------------------ */

#ifndef SUMO_CSMGENERATOR_H
#define SUMO_CSMGENERATOR_H

#include "assembly.h"
#include "csmwing.h"
#include "csmbody.h"

class XmlElement;

/** Interpret CEASIOM geometry definition.

  This is the top-level interpreter for CEASIOM geometry definition files.
  It is meant to read their xml representation and generate a sumo assembly 
  which matches the defined geometry as closely as possible.

*/
class CsmGenerator
{
  public:
    
    /// default empty generator
    CsmGenerator() {}

    /// read from file 
    void read(const std::string & fname);
    
    /// generate a complete assembly from currently supported data 
    AssemblyPtr create() const;
    
    /// post a warning message
    static void warning(const std::string & s);

    /// post an info message
    static void information(const std::string & s);

    /// access messages
    static const std::string & msg() {return messages;}

  private:
    
    /// interpret xml file 
    void fromXml(const XmlElement & xe);
    
  private:
    
    /// csm component representation
    CsmComponentArray cpa;

    /// conversion warning/error messages
    static std::string messages;
};

Real floatFromNode(const XmlElement & xe, const std::string & s);
Real floatFromNode(const XmlElement & xe, const std::string & s, Real df);
int intFromNode(const XmlElement & xe, const std::string & s);
int intFromNode(const XmlElement & xe, const std::string & s, int df);
std::string csmCanonicalStr(const std::string & s);

#endif
