
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
 
#ifndef SURF_NSTCOORDSYS_H
#define SURF_NSTCOORDSYS_H

#include <genua/smatrix.h>
#include <genua/dmatrix.h>

/** Cartesian coordinate system (Nastran)
	
  \ingroup structures
  \sa NstMesh
*/
class NstCoordSys
{
  public:
    
    /// create default coordinate system
    NstCoordSys() { xyz(0,0)=xyz(1,1)=xyz(2,2)=1.0; }
  
    /// change origin
    void origin(const Vct3 & p) {org = p;}
    
    /// change axis directions
    void axes(const Vct3 & ax, const Vct3 & ay, const Vct3 & az);
    
    /// construct from CORD2R representation 
    void fromCord2r(const Vct3 & a, const Vct3 & b, const Vct3 & c);
    
    /// transform a point from local into global coordinates 
    Vct3 toGlobal(const Vct3 & p) const {
      return org + xyz * p;
    }
    
    /// transform row i in modeshape 
    void toGlobal(uint i, Matrix & z) const;
    
  private:
    
    /// origin 
    Vct3 org;
    
    /// axis directions in columns
    Mtx33 xyz;
};

#endif
