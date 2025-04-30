
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
 
#ifndef GENUA_CGNSFILE_H
#define GENUA_CGNSFILE_H

#include <string>
#include "point.h"
#include "cgnszone.h"

/** CGNS file with a single base.
 *
 * The CGNS wrapper classes help to avoid the rather cumbersome original
 * CGNS interface for simple applications.
 *
 * This class is only available if CGNS support is enabled.
 *
 * \ingroup mesh
 * \sa CgnsBoco, CgnsDescriptor
 */
class CgnsFile
{
  public:
    
    typedef DMatrix<int> IndexMatrix;
    typedef DVector<int> IndexVector;
    
    /// new cgns file (closed) 
    CgnsFile();
    
    /// release resources, close files 
    virtual ~CgnsFile();
    
    /// test if file is cgns
    static bool isCgns(const std::string & s);
    
    /// open file for writing 
    void wopen(const std::string & fname);

    /// open file for reading
    void ropen(const std::string & fname, int ibase=1);
    
    /// file index 
    int index() const {return fileindex;}
     
    /// base index 
    int base() const {return baseindex;}
    
    /// create an unstructured zone, return zone index
    int uzone(const std::string & name, int nvertex, int ncell);

    /// number of zones in this file
    int nzones() const;
    
    /// number of sections 
    int nsections(int zix) const;
    
    /// number of boundary conditions 
    int nbocos(int zix) const;
    
    /// access zone i 
    CgnsZone readZone(int i) const {return CgnsZone(fileindex, baseindex, i);}
    
    /// create zone 
    CgnsZone newZone(const std::string & name, int nvertex, int ncell);
    
    /// read unstructured zone with index i
    std::string readZone(int izone, int & nvertex, int & ncell, int & nbndv);
    
    /// read grid coordinates in zone izone
    void readNodes(int zix, int np, PointList<3> & pts);
    
    /// write node coordinates to zone zix
    void writeNodes(int zix, const PointList<3> & pts);
    
    /// read section isec in zone zix
    std::string readSection(int zix, int isec, int & elmType, 
                            IndexMatrix & ielm);
    
    /// write tetraheder elements 
    int writeTets(int zix, const std::string & name, 
                  const IndexMatrix & ielem);
    
    /// write boundary triangles 
    int writeTriBoundary(int zix, const std::string & name, 
                         const IndexMatrix & ielem);
    
    /// read boundary condition data 
    std::string readBoundaryCondition(int zix, int ibc, IndexVector & elix,
                                      int & boco);
    
    /// write boundary condition (currently uses BCUserDefined)
    int writeBoundaryCondition(int zix, const std::string & name, 
                               const IndexVector & elix, int boco=-1);
    
  private:
    
    /// cgns integer indices and element offset counter
    int fileindex, baseindex, eloff;
    
    /// single base for now
    std::string basename;
};

#endif
