
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
 
#ifndef GENUA_CGNSSOL_H
#define GENUA_CGNSSOL_H

#include "cgnsfwd.h"

/** Flow solution node in CGNS file.
 *
 * The CGNS wrapper classes help to avoid the rather cumbersome original
 * CGNS interface for simple applications.
 *
 * This class is only available if CGNS support is enabled.
 *
 * \ingroup mesh
 * \sa CgnsFile
 */
class CgnsSol
{
  public:
    
    /// create solution node 
    CgnsSol(int f, int b, int z, int s) : fileindex(f), baseindex(b),
      zoneindex(z), solindex(s) {}

    /// fetch solution info from file
    void readInfo();

    /// vertex- or cell-based data?
    cgns::GridLocation_t location() const {return loc;}

    /// solution index
    int solutionIndex() const {return solindex;}

    /// number of solution fields
    int nfields();

    /// retrieve field info - name and datatype
    void fieldInfo(int i, std::string & fname, cgns::DataType_t & dtype);

    /// retrieve double precision field
    void readField(const char *field, int & imin, int & imax, double a[]);

    /// retrieve integer field
    void readField(const char *field, int & imin, int & imax, int a[]);
    
    /// write a solution array 
    int writeField(const std::string & fname, const double a[],
                   cgns::DataType_t dtype = cgns::RealDouble);
      
    /// write a solution array 
    int writeField(const std::string & fname, const float a[],
                   cgns::DataType_t dtype = cgns::RealSingle);
    
    /// write a solution array (integer)
    int writeField(const std::string & fname, const int a[]);
    
  private:
    
    /// solution node name (used when reading only)
    char name[40];
    
    /// file, base, zone index
    int fileindex, baseindex, zoneindex, solindex;

    /// vertex- or cell based data?
    cgns::GridLocation_t loc;
};

#endif
