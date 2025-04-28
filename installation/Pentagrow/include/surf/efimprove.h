
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
 
#ifndef SURF_EFIMPROVE_H
#define SURF_EFIMPROVE_H

#include "surface.h"

class EdgeFaceIsec;
class MeshPatch;

/** Improves accuracy in intersection handling.
 *
 * \deprecated
 *
 * \ingroup geometry
 * \sa EdgeFaceIsec, Intersector
 */
class EfImprove
{
  public:
 
    /// initialize with intersection specification
    EfImprove(const EdgeFaceIsec & is);
       
    /// error margin (gap) of the current recursion
    Real gap() const;
    
    /// recursively refine until gap smaller than tolerance
    Real refine(Real tol, uint maxit = 32);
    
    /// current guess for intersection parameter on edge surface
    Vct2 eparameter() const;
    
    /// current guess for intersection parameter on face surface
    Vct2 fparameter() const;  
    
  private:  

    /// construct edges, triangles, evaluate surfaces
    void init(const Vct2 e[2], const Vct2 f[3]);

    /// project point pt on triangle j
    Vct3 project(uint j, const Vct3 & pt) const;
            
    /// check for intersection
    bool intersects(uint i, uint j);
    
    /// limit coordinates to [0,1]
    void limit(Vct2 & p) const;
    
  private:
    
    /// two surfaces, one for the edge, one for the face
    SurfacePtr esf, fsf;
    
    /// two edges, that's three points
    Vct2 qe, eq[3];
    Vct3 ep[3];
    
    /// four faces, six points [015],[123],[135],[345]
    Vct2 qf, fq[6];
    Vct3 fp[6];
    
    /// current intersection point
    Vct3 uvt;
    
    /// indices of current intersection
    uint si, sj;
};

#endif
