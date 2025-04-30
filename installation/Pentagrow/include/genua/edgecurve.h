
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
 
#ifndef GENUA_EDGECURVE_H
#define GENUA_EDGECURVE_H

#include "triangulation.h"

/** Cubic curve over edge.

  If a triangulated surface is fully defined, including a outward-pointing
  normal vector per vertex (which can be approximated from a closed-body
  triangulation), vertex coordinates and normals can be used to construct cubic
  curves which pass through the vertices and are perpendicular to the normals
  in those points.
  
  */
class EdgeCurve
{
  public:
  
    /// empty construction
    EdgeCurve() : defined(false) {}
  
    /// construction with associated triangulated surface and edge
    EdgeCurve(const Edge & e);
    
    /// evaluate at curve parameter t
    Vct3 eval(Real t) const;
    
    /// reverse curve direction, return flag
    bool reverse()
      {rev = !rev; return rev;}
  
  private:
  
    /// polynomial coefficients
    Vct3 a0, a1, a2, a3;    
    
    /// reversal flag
    bool rev, defined;
};

#endif

