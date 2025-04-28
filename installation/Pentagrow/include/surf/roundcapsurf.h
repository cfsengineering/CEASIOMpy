
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
 
#ifndef SURF_ROUNDCAPSURF_H
#define SURF_ROUNDCAPSURF_H
 
#include <genua/triangulation.h>
#include "surface.h"

class TriMesh;

/** Round cap surface.

  RoundCapSurf is a semi-elliptic half-open surface used to close tubular
  interpolation surfaces such as fuselage or nacelle bodies. It is especially
  useful for approximately circular openings.

  The surface geometry is interpolated from elliptic arcs running from the
  boundary points toward an elevated mid-point. Since the arcs are constructed
  in the same manner for all boundary points, the shape is well suited for
  a circular or elliptic contour of the open boundary. Boundaries with sharp
  edges lead to a strongly degraded shape of the cap surface.

  \ingroup geometry
  \sa Surface

  */
class RoundCapSurf : public Surface
{
  public:

    /// construct from boundary points and mid elevation
    RoundCapSurf(const PointList<3> & pts, Real elv);
    
    /// construct from point set 
    void init(const PointList<3> & pts, Real elv);
    
    /// evaluation interface
    Vct3 eval(Real u, Real v) const;

    /// derive at (u,v)
    Vct3 derive(Real u, Real v, uint du, uint dv) const;
        
    /// coordinate transformation 
    void apply();

    /// XML output (disabled)
    XmlElement toXml(bool share=false) const;
    
    /// XML input (disabled)
    void fromXml(const XmlElement &);
    
    /// generate clone 
    RoundCapSurf *clone() const {return new RoundCapSurf(*this);}
    
    /// generate initial mesh
    void initMesh(const DnRefineCriterion & c, DnMesh & gnr) const;
    
    /// create a mesh matching the boundary, and merge with tmerge
    void merge(uint n, TriMesh & tmerge) const;
    
    /// create a mesh matching the boundary, and merge with tmerge
    void merge(const Vct3 & nref, uint n, TriMesh & tmerge) const;
    
    /// simplified mesh generation (hybrid)
    Triangulation mesh(uint n) const;

    /// return boundary points
    PointList<2> boundary() const;

    /// access mesh generation limits
    void mgLimits(Real & lmax, Real & phimax) const;
    
  private:
    
    /// identify segment
    uint segment(Real u) const;
    
  private:

    /// average radius
    Real rmean, elevation;
    
    /// center point and normal vector
    Vct3 ctr, nrm;
    
    /// parametrization
    Vector useg;      
    
    /// radius vectors and boundary points
    PointList<3> radius, pts;
};

#endif
