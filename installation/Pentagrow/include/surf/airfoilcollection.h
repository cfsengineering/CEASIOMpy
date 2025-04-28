
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
 
#ifndef SURF_AIRFOILCOLLECTION_H
#define SURF_AIRFOILCOLLECTION_H

#include <genua/xmlelement.h>
#include <genua/binfilenode.h>
#include "airfoil.h"

/** Collection of airfoil coordinates.

  This is a simple array of airfoil coordinates which is used to provide a
  "database" of airfoils to an interactive modeling program.

  \todo Move this to sumo.
  
  \ingroup geometry
*/
class AirfoilCollection
{

  public:
    
    /// create empty collection
    AirfoilCollection() {}

    /// name of this collection
    const std::string & name() const {return clname;}
    
    /// change collection name 
    void rename(const std::string & s) {
      clname = s;
    }
    
    /// set comment on collection
    void comment(const std::string & s) {descr = s;}
    
    /// acccess comment (may be empty)
    const std::string & comment() const {return descr;}
    
    /// number of airfoils in the collection 
    uint size() const {return foils.size();}
    
    /// access airfoil at i 
    AirfoilPtr foil(uint i) const {
      assert(i < foils.size());
      return AirfoilPtr(new Airfoil(foils[i].cname, foils[i].crd));
    }
    
    /// access airfoil coordinate name 
    const std::string & coordName(uint i) const {
      assert(i < foils.size());
      return foils[i].cname;
    }
    
    /// access airfoil coordinate name 
    const std::string & fileName(uint i) const {
      assert(i < foils.size());
      return foils[i].fname;
    }
    
    /// find index of foil named cname 
    uint findByCoordName(const std::string & cname) const;
    
    /// find index of foil which originated from file fname 
    uint findByFileName(const std::string & fname) const;
    
    /// add an airfoil file, try to guess the proper name 
    uint addFile(const std::string & fname);
    
    /// generate xml representation of the complete collection 
    XmlElement toXml() const;
    
    /// read collection from xml file 
    void fromXml(const XmlElement & xe);
    
    /// write to binary file 
    BinFileNodePtr toBinary() const;
    
    /// recover from binary file
    void fromBinary(const BinFileNodePtr & bfn);
    
    /// sort by coordinate names
    void sort() {
      std::sort(foils.begin(), foils.end());
    }
    
    /// delete collection data 
    void clear() {
      clname.clear();
      descr.clear();
      foils.clear();
    }
    
  private:
    
    struct AfcEntry {
      
      std::string cname, fname;
      PointList<2> crd;
      
      AfcEntry() {}

      AfcEntry(const std::string & c, const std::string & f, 
               const PointList<2> & pts) : cname(c), fname(f), crd(pts) {}
      
      bool operator== (const AfcEntry & a) const {
        return cname == a.cname;
      }
      
      bool operator<(const AfcEntry & a) const {
        return cname < a.cname;
      }
      
      void fromXml(const XmlElement & xe);
      
      XmlElement toXml() const;
      
      BinFileNodePtr toBinary() const;
      
      void fromBinary(const BinFileNodePtr & bfn);
      
    };
    
  private:
    
    /// name of this collection 
    std::string clname, descr;
    
    /// the airfoils themselves 
    std::vector<AfcEntry> foils;
};

typedef boost::shared_ptr<AirfoilCollection> AirfoilCollectionPtr;



#endif
