
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
 
#ifndef GENUA_CGNSZONE_H
#define GENUA_CGNSZONE_H

#include <string>
#include "point.h"
#include "cgnssection.h"
#include "cgnsboco.h"
#include "cgnssol.h"

/** Zone in a cgns file.
 * The CGNS wrapper classes help to avoid the rather cumbersome original
 * CGNS interface for simple applications.
 *
 * This class is only available if CGNS support is enabled.
 *
 * \ingroup mesh
 * \sa CgnsFile
 */
class CgnsZone
{
  public:
    
    /// initialize with file and base index
    CgnsZone(int f, int b, int z) : fileindex(f), baseindex(b), zoneindex(z) {}
  
    /// file index
    int findex() const {return fileindex;}
    
    /// base index
    int bindex() const {return baseindex;}
    
    /// zone index 
    int index() const {return zoneindex;}
    
    /// zone name 
    std::string name() const {return std::string(zname);}
    
    /// change name 
    void rename(const std::string & s);

    /// number of sections in this zone 
    int nsections() const;
    
    /// number of boundary condition definitions 
    int nbocos() const;

    /// number of flow solutions in this zone
    int nsols() const;
    
    /// retrieve grid coordinates of this zone 
    void readNodes(PointList<3> & pts);
    
    /// write grid coordinates 
    void writeNodes(const PointList<3> & pts);
    
    /// create a new flow solution node 
    CgnsSol newSolution(const std::string & s, 
                        cgns::GridLocation_t loc = cgns::Vertex);
    
    /// return section i 
    CgnsSection readSection(int i);
    
    /// return boundary condition spec i 
    CgnsBoco readBoco(int i);

    /// return flow solution spec i
    CgnsSol readSol(int i);
    
  private:
    
    /// zone name 
    char zname[40];
    
    /// zone index
    int fileindex, baseindex, zoneindex;
};

#endif
