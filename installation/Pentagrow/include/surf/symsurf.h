
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
 
#ifndef SURF_SYMSURF_H
#define SURF_SYMSURF_H

#include <genua/plane.h>
#include "curve.h"
#include "surface.h"

/** Symmetric surface.

  SymSurf automatically generates surfaces which are symmetric about a
  mirror plane (which, by default, is the xz-plane), and adapts derivatives
  and mesh initializers accordingly.

  It is stronlgy recommended that the mirrored surface reaches the mirror
  plane exactly for v = 1, otherwise, the symmetric surface will either have
  a gap or have self-intersections.

  Note that this class re-parameterizes such that v in (0,0.5) yields points
  on the original surface, and v > 0.5 yields points on the mirror-copy side.

  \ingroup geometry
  \sa Surface

  */
class SymSurf : public Surface
{
  public:
    
    /// named construction
    SymSurf(const std::string & name);
     
    /// copy construction 
    SymSurf(const SymSurf & s) : Surface(s.ids) { init(*s.psf); }
    
    /// initialize with surface to mirror (clones)
    void init(const Surface & srf);

    /// initialize with surface to mirror (shallow copy)
    void init(const SurfacePtr & psrf) {psf = psrf;}
    
    /// change the mirror plane
    void setMirrorPlane(const Vct3 & orig, const Vct3 & nrm) {
      mipo = orig;
      mipn = nrm;
    }

    /// access base surface, that is, the one half
    SurfacePtr baseSurface() const {return psf;}
    
    /// evaluation interface
    Vct3 eval(Real u, Real v) const;

    /// derive at (u,v)
    Vct3 derive(Real u, Real v, uint du, uint dv) const;

    /// compute point and tangent derivatives at (u,v), for efficiency
    void plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const; 
    
    /// compute normal vector
    Vct3 normal(Real u, Real v) const;    

    /// coordinate transformation
    void apply();

    /// derive a grid pattern from mirrored surface
    void initGridPattern(Vector & up, Vector & vp) const;
    
    /// create an unconstrained point grid as initialization for mesh generator
    void initGrid(Real lmax, Real lmin, Real phimax, PointGrid<2> & pts) const;
    
    /// initialize mesh generator (marks kink edges)
    void initMesh(const DnRefineCriterion & c, DnMesh & gnr) const;
    
    /// XML output
    XmlElement toXml(bool share=false) const;
    
    /// XML input
    void fromXml(const XmlElement & xe);
    
    /// write IGES entities and mirror them 
    int toIges(IgesFile & file, int tfi=0) const;
    
    /// generate a clone 
    SymSurf *clone() const {return new SymSurf(*this);}
    
  protected:
    
    /// compute the mirror image
    void mirror(const Vct3 & p, Vct3 & mp) const {
      mp = p - 2.0*dot( (p-mipo), mipn )*mipn;
    }
    
  private:
    
    /// the right wing surface which is mirrored
    SurfacePtr psf;
    
    /// mirror plane (default: xz-plane)
    Vct3 mipo, mipn;
};

#endif
