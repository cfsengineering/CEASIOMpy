
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
 
#ifndef SURF_INITGRID_H
#define SURF_INITGRID_H

#include "forward.h"
#include <genua/dvector.h>

/** Utility class to generate simple quad mesh.

  InitGrid is used to generate coarse quadrilateral discretizations from which
  the triangular mesh generator DnMesh can be initialized. 

  \ingroup meshgen
  \sa CascadeMesh
  */
class InitGrid
{
  public:
    
    /// construct grid generator
    InitGrid(const Surface *p) : psf(p) {}
    
    /// define an initial pattern to start from
    void initPattern(const Vector & u, const Vector & v);
    
    /// use existing pattern as a starting guess 
    void initPattern(const PointGrid<2> & pg);
    
    /// create a grid without any knowledge about the surface
    void refine(Real lmax, Real lmin, Real phimax);
    
    /** Adapt distribution. While keeping the row point count constant, 
    redistribute points so that angular and length criteria are met. Returns
    the quality of the worst remaining segment (>1 if criteria violated) */
    Real uAdapt(Real lmax, Real lmin, Real phimax, uint numax = 0);
    
    /// adapt spacing by insertion, so that lmax criterion is fullfilled
    void uRefineByLength(Real lmax);
    
    /// adapt spacing by insertion, so that lmax criterion is fullfilled
    void vRefineByLength(Real lmax);
    
    /// adapt spacing to avoid excissive approximation error (gap)
    Real vRefineByGap(Real maxgap);
    
    /// adapt spacing (once) to avoid large v-direction kinks 
    Real vRefineByAngle(Real maxphi);
    
    /// adapt v-spacing so that stretch ratio is reduced 
    Real vRefineByStretch(uint nvmax, Real smax); 
    
    /// adapt spacing by insertion, so that phimax criterion is fullfilled
    void uRefineByAngle(Real phimax, Real lmin);
    
    /// equilibrate by performing laplacian smoothing between cuts 
    void vsmooth(uint niter);
    
    /// equilibrate by performing laplacian smoothing within cuts 
    void usmooth(uint niter);
    
    /// enforce symmetry about u = 0.5
    void enforceUSymmetry();
    
    /// enforce symmetry about v = 0.5
    void enforceVSymmetry();
    
    /// force kink columns to be present
    void enforceColumns(const Vector & vpos);
    
    /// current size 
    uint nrows() const {return up[0].size();}
    
    /// current size 
    uint ncols() const {return vp.size();}
    
    /// create grid from parameter arrays
    void collect(PointGrid<2> & pts) const;
    
  private:
    
    /// create a regular initial pattern (default initial guess)
    void initPattern(uint nu, uint nv);
    
    /// compute cosines of local kink angles at section j
    void kinks(uint j, Vector & cphi) const;
    
    /// shift nodes in one section in order to decrease kink angles
    void shift(uint j, Real cminphi, const Vector & cphi);
    
    /// insert an evenly spaced frame at v, return new frame index
    uint insertFrame(Real v, uint nu);
    
    /// insert a new u values in all frames
    void insertStringer(Real u);
    
    /// smooth u-distribution at vj
    void usmoothColumn(uint j, uint niter);
    
    /// adapte a single u-line
    Real adaptULine(uint i, uint nu, Real lmax, Real lmin, Real phimax); 
    
    /// determine if the surface is smooth at u=0/1 
    bool smoothSeam(Real v) const;
    
  private:
    
    /// pointer to surface 
    const Surface *psf;
    
    /// v-parameter values for the frames
    Vector vp;
    
    /// u-parameter values of the frames
    VectorArray up;
};

#endif
