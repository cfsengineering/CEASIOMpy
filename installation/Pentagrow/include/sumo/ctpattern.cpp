
/* ------------------------------------------------------------------------
 * file:       ctpattern.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Stores data for combined control surface deflections
 * ------------------------------------------------------------------------ */

#include <genua/xcept.h>
#include "ctpattern.h"
#include <iostream>

using namespace std;

uint CtPattern::find(const std::string & s) const
{
  StringArray::const_iterator pos;
  pos = std::find(cnames.begin(), cnames.end(), s);
  if (pos == cnames.end())
    return NotFound;
  else
    return std::distance(cnames.begin(), pos);
}

void CtPattern::get(uint i, std::string & s, Real & f) const
{
  if (i >= pcf.size() or i >= cnames.size()) {
    clog << "CtPattern::get() - No control surface at " 
         << i << " (" << pcf.size() << ")" << endl;
    return;
  }
  s = cnames[i];
  f = pcf[i];
}

void CtPattern::set(uint i, const std::string & s, Real f)
{
   if (i >= pcf.size() or i >= cnames.size()) {
    clog << "CtPattern::set() - No control surface at " 
         << i << " (" << pcf.size() << ")" << endl;
    return;
  }
  cnames[i] = s;
  pcf[i] = f;
}

void CtPattern::clear()
{
  pcf.clear();
  cnames.clear();
}

uint CtPattern::append(const std::string & s, Real f)
{
  cnames.push_back(s);
  pcf.push_back(f);
  return pcf.size() - 1;
}

void CtPattern::remove(uint i)
{
  if (i >= pcf.size() or i >= cnames.size()) {
    clog << "CtPattern::remove() - No control surface at " 
         << i << " (" << pcf.size() << ")" << endl;
    return;
  }
  cnames.erase(cnames.begin() + i);
  pcf.erase(pcf.begin() + i);
}

void CtPattern::remove(const std::string & s)
{
  const uint np(cnames.size());
  uint kfirst(np), klast(0);
  for (uint i=0; i<np; ++i) {
    if (cnames[i].find(s) != string::npos) {
      kfirst = min(kfirst, i);
      klast = max(klast, i+1);
    }
  }
  
  if (kfirst < np) {
    cnames.erase(cnames.begin()+kfirst, cnames.begin()+klast);
    pcf.erase(pcf.begin()+kfirst, pcf.begin()+klast);
  }
}

void CtPattern::rename(const std::string & idold, const std::string & idnew)
{
  const uint np(cnames.size());
  const uint ns(idold.size());
  for (uint i=0; i<np; ++i) {
    string::size_type pos = cnames[i].find(idold);
    if (pos != string::npos) 
      cnames[i].replace(pos, ns, idnew);
    else
      throw Error("No such control surface: "+idold);
  }
}

void CtPattern::fromXml(const XmlElement & xe)
{
  const string & xname(xe.name());
  if (xname != "Control")
    throw Error("Incompatible xml representation for "
        "CtPattern: " + xname);
  
  id = xe.attribute("name");
  XmlElement::const_iterator ite, first, last;
  first = xe.begin();
  last = xe.end();
  for (ite = first; ite != last; ++ite) {
    if (ite->name() == "Participation") {
      string s = ite->attribute("id");
      Real f = Float(ite->attribute("factor"));
      cnames.push_back(s);
      pcf.push_back(f);
    }
  }
}
    
XmlElement CtPattern::toXml() const
{
  XmlElement xe("Control");
  
  xe["name"] = id;
  const uint np(pcf.size());
  assert(cnames.size() == np);
  for (uint i=0; i<np; ++i) {
    if (pcf[i] != 0.0) {
      XmlElement xp("Participation");
      xp["id"] = cnames[i];
      xp["factor"] = str(pcf[i]);
      xe.append(xp);
    }
  }
  
  return xe;
}
