
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
 
#ifndef GENUA_CGNSSECTION_H
#define GENUA_CGNSSECTION_H

#include <string>
#include "cgnsfwd.h"

/** Sections, containing element data in CGNS files
 *
 * The CGNS wrapper classes help to avoid the rather cumbersome original
 * CGNS interface for simple applications. A section is a set of elements
 * of the same type in a CGNS mesh. Some systems also use CGNS sections to
 * identify boundary conditions, even though the CGNS specification defines
 * a separate boundary condition tag for that purpose.
 *
 * This class is only available if CGNS support is enabled.
 *
 * \ingroup mesh
 * \sa CgnsFile
 */
class CgnsSection
{
  public:
    
    /// section in file, base, zone 
    CgnsSection(int f, int b, int z, int s) : 
      fileindex(f), baseindex(b), zoneindex(z), sindex(s),
      elmtype(cgns::ElementTypeNull), nelm(0), parentflag(0), eloff(0) {}
    
    /// zone name 
    std::string name() const {return std::string(sname);}
    
    /// change name 
    void rename(const std::string & s);
    
    /// read section info from file 
    void readInfo();
    
    /// access element type 
    cgns::ElementType_t elementType() const {return elmtype;}
    
    /// change element type 
    void elementType(cgns::ElementType_t t) {elmtype = t;}

    /// set element index  offset 
    void elementOffset(int off) {eloff = off;}
    
    /// read elements 
    void readElements(CgnsIntMatrix & ielm);
    
    /// write elements 
    void writeElements(CgnsIntMatrix & ielm);
    
    /// number of nodes per element 
    static int nodesPerElement(cgns::ElementType_t t);
    
  private:
    
    /// section name 
    char sname[40];
    
    /// indices
    int fileindex, baseindex, zoneindex, sindex;

    /// element type 
    cgns::ElementType_t elmtype;
    
    /// number of elements, parent flag 
    int nelm, parentflag;
    
    /// element offset counter 
    int eloff;
};

#endif
