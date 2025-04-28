
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#include "airfoillibrary.h"

using namespace std;

uint AirfoilLibrary::addCollection(std::istream & in)
{
  XmlElement xe;
  xe.read(in, XmlElement::PlainText);

  AirfoilCollectionPtr acp(new AirfoilCollection);
  acp->fromXml(xe);
  lib.push_back(acp);
  return lib.size()-1;
}

AirfoilPtr AirfoilLibrary::airfoilByCoordName(const std::string & cname) const
{
  const uint nc = size();
  for (uint i=0; i<nc; ++i) {
    uint idx = lib[i]->findByCoordName(cname);
    if (idx != NotFound)
      return lib[i]->foil(idx);
  }
  
  return AirfoilPtr();
}
    
AirfoilPtr AirfoilLibrary::airfoilByFileName(const std::string & fname) const
{
  string flower(fname);
  const int n = flower.size();
  for (int i=0; i<n; ++i)
    flower[i] = tolower(flower[i]);
  
  const uint nc = size();
  for (uint i=0; i<nc; ++i) {
    uint idx = lib[i]->findByFileName(flower);
    if (idx != NotFound)
      return lib[i]->foil(idx);
  }
  
  return AirfoilPtr();
}

AirfoilPtr AirfoilLibrary::airfoilByFileName(const std::string & clt, 
                                             const std::string & fname) const
{
  uint ic = findCollection(clt);
  if (ic == NotFound)
    return AirfoilPtr();
  
  uint ai = lib[ic]->findByFileName(fname);
  if (ai == NotFound)
    return AirfoilPtr();
  
  return lib[ic]->foil(ai);
}

uint AirfoilLibrary::findCollection(const std::string & s) const
{
  const int nc = lib.size();
  for (int i=0; i<nc; ++i) {
    if (lib[i]->name() == s)
      return i;
  }
  return NotFound;
}




