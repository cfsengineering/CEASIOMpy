
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
 
#ifndef SURF_WAKETRACE_H
#define SURF_WAKETRACE_H

#include <genua/point.h>

class TriMesh;
class MeshFields;

/** Discrete wake surface definition.
	
  \deprecated
*/
class WakeTrace
{
  public:
    
    /// create empty trace attached to mesh m
    WakeTrace(const TriMesh & m);
    
    /// compute trace starting from vertex i  
    void search(uint ifirst, const Vct3 & v);
  
    /// attach line visualization to object
    void addViz(MeshFields & mvz) const;
    
  private:
    
    /// determine if triangle f is intersected
    uint touched(uint fix, const Vct3 & prev, const Vct3 & v) const;
    
    /// determine if edge e is intersected 
    int esliced(const Vct3 & p, const Vct3 & v, const Vct3 & fn,
                uint e) const;
    
    /// determine intersection point
    Vct3 itspoint(const Vct3 & p, const Vct3 & v, const Vct3 & fn, 
                  uint e) const;
    
    /// determine and register next point 
    bool advance(const Vct3 & v);
    
  private:
    
    /// mesh of the body
    const TriMesh & msh;
    
    /// indices of faces and edges intersected 
    Indices ifaces, iedges;
    
    /// point trace 
    PointList<3> pts;
    
    /// stopping criteria 
    static Real csSharpEdge;
};

#endif
