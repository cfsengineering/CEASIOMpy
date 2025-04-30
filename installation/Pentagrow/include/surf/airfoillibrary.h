
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
 
#ifndef SURF_AIRFOILLIBRARY_H
#define SURF_AIRFOILLIBRARY_H

#include <iostream>
#include "airfoilcollection.h"

/** Set of airfoil collections.
  */
class AirfoilLibrary
{
  public:
    
    /// empty library 
    AirfoilLibrary() {}
    
    /// number of collection 
    uint size() const {return lib.size();}
    
    /// add collection from xml stream
    uint addCollection(std::istream & in);
  
    /// add collection from xml stream
    uint addCollection(const AirfoilCollectionPtr & afp) {
      lib.push_back(afp);
      return lib.size()-1;
    }
    
    /// access collection i 
    const AirfoilCollection & collection(uint i) const {
      assert(i < size());
      return *(lib[i]);
    }
    
    /// find collection by name 
    uint findCollection(const std::string & s) const;
    
    /// retrieve airfoil by name (empty object if not found)
    AirfoilPtr airfoilByCoordName(const std::string & cname) const;
    
    /// retrieve airfoil by file name (empty object if not found)
    AirfoilPtr airfoilByFileName(const std::string & fname) const;
    
    /// retrieve airfoil by file name (empty object if not found)
    AirfoilPtr airfoilByFileName(const std::string & clt, 
                                 const std::string & fname) const;
    
    /// delete contents 
    void clear() {lib.clear();}
    
  private:
    
    /// pointers to collections 
    std::vector<AirfoilCollectionPtr> lib;
};

#endif
