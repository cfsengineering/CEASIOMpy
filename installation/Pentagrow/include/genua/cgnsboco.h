
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
 
#ifndef GENUA_CGNSBOCO_H
#define GENUA_CGNSBOCO_H

#include <string>
#include "cgnsfwd.h"

/** Boundary condition specification in cgns files.
 *
 * The CGNS wrapper classes help to avoid the rather cumbersome original
 * CGNS interface for simple applications.
 *
 * This class is only available if CGNS support is enabled.
 *
 * \ingroup mesh
 * \sa MxMesh, CgnsFile
 */
class CgnsBoco
{
  public:
    
    /// create boco object
    CgnsBoco(int f, int b, int z, int i) : fileindex(f), baseindex(b),
      zoneindex(z), bcindex(i), bctype(cgns::BCGeneral), 
      pstype(cgns::ElementList), npnts(0) {}

    /// zone name 
    std::string name() const {return std::string(bname);}
    
    /// change name 
    void rename(const std::string & s);
    
    /// access boundary condition type 
    cgns::BCType_t bcType() const {return bctype;}
    
    /// access boundary condition type 
    void bcType(cgns::BCType_t t) {bctype = t;}
    
    /// access point set type 
    cgns::PointSetType_t pointSet() const {return pstype;}
    
    /// change point set type 
    void pointSet(cgns::PointSetType_t t) {pstype = t;}
      
    /// read boco info from file 
    void readInfo();
    
    /// read point set 
    void readPoints(CgnsIntVector & elix);
    
    /// write point set 
    void writePoints(CgnsIntVector & elix);
    
  private:
    
    /// boundary condition name 
    char bname[40];
    
    /// file, base, zone, boco index
    int fileindex, baseindex, zoneindex, bcindex;
    
    /// type of boco 
    cgns::BCType_t bctype;
    
    /// type of point set 
    cgns::PointSetType_t pstype;
    
    /// number of entries in point list 
    int npnts;
};

#endif
