
/* ------------------------------------------------------------------------
 * file:       ctsystem.cpp
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Stores control system data
 * ------------------------------------------------------------------------ */
 
#include <genua/xcept.h>
#include "ctsystem.h"

using namespace std;

void CtSystem::clear()
{
  surfaces.clear();
  patterns.clear();
}

void CtSystem::removeSurface(uint idx)
{
  // delete surface object
  assert(idx < surfaces.size());
  string s( surfaces[idx].name() );
  surfaces.erase(surfaces.begin() + idx);
  
  // delete references to this surface
  const uint np(patterns.size());
  for (uint i=0; i<np; ++i) 
    patterns[i].remove(s);
  
  dropEmptyPatterns();
}

void CtSystem::removePattern(uint idx)
{
  assert(idx < patterns.size());
  patterns.erase(patterns.begin() + idx);
}

void CtSystem::renameSurface(uint idx, const std::string & s)
{
  assert(idx < surfaces.size());
  string oldname( surfaces[idx].name() );
  surfaces[idx].rename(s);
  
  // change references to this surface
  const uint np(patterns.size());
  for (uint i=0; i<np; ++i) 
    patterns[i].rename(oldname, s);
}

void CtSystem::segments(StringArray & sgs) const
{
  for (uint i=0; i<nsurf(); ++i)
    surfaces[i].segments(sgs);
}

void CtSystem::updateGeometry()
{
  const int ns(surfaces.size());
  for (int i=0; i<ns; ++i)
    surfaces[i].updateGeometry();
}

void CtSystem::draw() const
{
  if (not bVisible)
    return;
  
  const uint n(surfaces.size());
  for (uint i=0; i<n; ++i)
    surfaces[i].draw();
}

void CtSystem::fromXml(const XmlElement & xe, const Assembly & asy)
{
  const string & xname(xe.name());
  if (xname != "ControlSystem")
    throw Error("Incompatible xml representation for "
        "CtSystem: " + xname);
  
  XmlElement::const_iterator ite, first, last;
  first = xe.begin();
  last = xe.end();
  
  for (ite = first; ite != last; ++ite) {
    if (ite->name() == "ControlSrf") {
      CtSurface cs;
      cs.fromXml(*ite, asy);
      surfaces.push_back(cs);
    } else if (ite->name() == "Control") {
      CtPattern cp;
      cp.fromXml(*ite);
      patterns.push_back(cp);
    }      
  }
}

XmlElement CtSystem::toXml() const
{
  XmlElement xe("ControlSystem");
  for (uint i=0; i<surfaces.size(); ++i)
    xe.append(surfaces[i].toXml());
  for (uint i=0; i<patterns.size(); ++i)
    xe.append(patterns[i].toXml());
  return xe;
}

XmlElement CtSystem::meshXml() const
{
  XmlElement xe("ControlSystem");
  for (uint i=0; i<surfaces.size(); ++i)
    xe.append(surfaces[i].meshXml());
  for (uint i=0; i<patterns.size(); ++i)
    xe.append(patterns[i].toXml());
  return xe;
}

void CtSystem::dropEmptyPatterns()
{
  std::vector<CtPattern> tmp;
  const int np = patterns.size();
  tmp.reserve(np);
  for (int i=0; i<np; ++i) {
    if (patterns[i].npart() > 0)
      tmp.push_back(patterns[i]);
  }
  patterns.swap(tmp);
}

