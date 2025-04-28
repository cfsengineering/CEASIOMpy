
/* ------------------------------------------------------------------------
 * file:       csmgenerator.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Constructs sumo assembly from CEASIOM definition
 * ------------------------------------------------------------------------ */

#include <ctype.h>
#include <iostream>
#include "csmgenerator.h"

using namespace std;

// --------------- file scope ----------------------------------------------

Real floatFromNode(const XmlElement & xe, const string & s)
{
  string sl = toLower(s);
  XmlElement::const_iterator itr, last;
  itr = xe.begin();
  last = xe.end();
  while (itr != last and toLower(itr->name()) != sl)
    ++itr;
  
  if (itr == xe.end()) {
    string msg = "CEASIOM import: XML element '" + xe.name();
    msg += "' does not have mandatory child '" + s + "'. ";
    msg += "Please preprocess CEASIOM ";
    msg += " input files with 'Geo' module first.";
    throw Error(msg);
  } else {
    return Float(itr->text());
  }
}

Real floatFromNode(const XmlElement & xe, const string & s, Real df)
{
  string sl = toLower(s);
  XmlElement::const_iterator itr, last;
  itr = xe.begin();
  last = xe.end();
  while (itr != last and toLower(itr->name()) != sl)
    ++itr;
  
  if (itr == xe.end())
    return df;
  else
    return Float(itr->text());
}

int intFromNode(const XmlElement & xe, const string & s)
{
  string sl = toLower(s);
  XmlElement::const_iterator itr, last;
  itr = xe.begin();
  last = xe.end();
  while (itr != last and toLower(itr->name()) != sl)
    ++itr;
  
  if (itr == xe.end()) {
    string msg = "CEASIOM import: Mandatory child node ";
    msg += s + " not present. Please preprocess CEASIOM ";
    msg += " input files with 'Geo' module first.";
    throw Error(msg);
  } else {
    return Int(itr->text());
  }
}

int intFromNode(const XmlElement & xe, const string & s, int df)
{
  string sl = toLower(s);
  XmlElement::const_iterator itr, last;
  itr = xe.begin();
  last = xe.end();
  while (itr != last and toLower(itr->name()) != sl)
    ++itr;
  
  if (itr == xe.end())
    return df;
  else
    return Int(itr->text());
}

std::string csmCanonicalStr(const std::string & s)
{
  string cs, ls = toLower(s);
  string::size_type n = ls.size();
  for (string::size_type i=0; i<n; ++i) {
    char c = ls[i];
    if ( (not isspace(c)) and c != '_' )
    // if (c != ' ' and c != '\t' and c != '_' and c != '\n' and c != '\r')
      cs.push_back(c);
  }
  return cs;
}

// --------------------------- CsmGenerator -----------------------------------

std::string CsmGenerator::messages;

void CsmGenerator::warning(const std::string & s)
{
  messages += "<b>[W]</b> " + s + "<br/>\n";
}

void CsmGenerator::information(const std::string & s)
{
  messages += "<b>[i]</b> " + s + "<br/>\n";
}

AssemblyPtr CsmGenerator::create() const
{
  if (cpa.empty())
    throw Error("CEASIOM importer: No supported geoemtry elements found.");
  
  AssemblyPtr asp(new Assembly);
  asp->clear();
  const int nc = cpa.size();
  for (int i=0; i<nc; ++i) {
    ComponentPtr scp = cpa[i]->create();
    if (scp)
      asp->append(scp);
  }  

  // append additional data to final assembly
  for (int i=0; i<nc; ++i)
    cpa[i]->postAttach(*asp);

  return asp;
}
    
void CsmGenerator::read(const std::string & fname)
{
  messages.clear();

  cpa.clear();
  XmlElement xe;
  xe.read(fname);
  fromXml(xe);
  
  // all components collected, connect them
  const int nc = cpa.size();
  for (int i=0; i<nc; ++i)
    cpa[i]->attach(cpa);
}
    
void CsmGenerator::fromXml(const XmlElement & xe)
{
  CsmComponentPtr cp;
  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    string tag = toLower(itr->name());
    string mtag = tag.substr(0, tag.size()-1);
    if (mtag == "engines") {
      fromXml(*itr);
    } else {
      cp = CsmComponent::createFromXml(*itr);
      if (cp)
        cpa.push_back(cp);
    }
  }
}

