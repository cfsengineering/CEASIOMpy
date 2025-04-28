
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
 
#ifndef SURF_TRITETWRITER_H
#define SURF_TRITETWRITER_H

#include <iostream>
#include <string>
#include <genua/defines.h>
#include <genua/trimesh.h>

/** Writes triangular boundary mesh in tritet boundary format.

    \deprecated
*/
class TritetWriter
{
  public:
    
    /// initialized with mesh to write
    TritetWriter(const TriMesh & m, const std::string & name = "Body");

    /// specify case name 
    void caseName(const std::string & s) {casename = s;}
    
    /// add a boundary specification 
    void setBoundary(const std::string & bname, const Indices & idx);
    
    /// add a boundary specification for faces [n1,n2[
    void setBoundary(const std::string & bname, int n1, int n2);
    
    /// add spherical farfield boundary to mesh 
    void sphericalFarfield(Real radius, int nref);
    
    /// write to stream 
    void write(std::ostream & os) const;
    
    /// experimental : write in tetgen format (.smesh)
    void writeTetgen(std::ostream & os) const;
    
  private:
    
    /// mesh to write
    TriMesh msh;
    
    /// boundary tags 
    Indices ibnd;
    
    /// case name 
    std::string casename;
    
    /// list of boundary names
    StringArray bnames;
    
    /// mesh center 
    Vct3 mctr;
};

#endif
