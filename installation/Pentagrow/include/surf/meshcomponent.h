
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
 
#ifndef SURF_MESHCOMPONENT_H
#define SURF_MESHCOMPONENT_H

#include "forward.h"
#include "dnmesh.h"
#include "sides.h"
#include <genua/trimesh.h>

/** Mesh component.
  
  This object contains the discrete mesh on a single spline surface.
  It holds references to the surface and the mesh quality criterion
  and allows to generate unconstrained meshes (premesh), add constraints
  resulting from multiple patch intersections, and generate refined
  meshes which comply to the constraints imposed. 

  This class is not meant to be called directly as the interface implies
  a lot of preconditions. 

  \ingroup meshgen
*/
class MeshComponent : public TriMesh
{
  public:
    
    /// every component is attached to a surface object
    MeshComponent(const SurfacePtr & s);

    /// every component is attached to a surface object
    MeshComponent(const SurfacePtr & s, const DnRefineCriterionPtr & pc);
      
    /// destruction
    virtual ~MeshComponent() {}
    
    /// access bound surface
    const SurfacePtr & surface() const {return psf;}
    
    /// access bound surface
    void surface(const SurfacePtr & srf) {psf = srf; bFreshMesh=false;}
    
    /// change mesh generation criterion 
    void criterion(const DnRefineCriterionPtr & pc) {pcrit = pc;}
    
    /// access criterion
    const DnRefineCriterionPtr & criterion() const {return pcrit;}
    
    /// set section tag
    void tag(uint t) {iTag = t;}

    /// access section tag
    uint tag() const {return iTag;}

    /// set iterative refinement flag
    void allowRefinement(bool flag) {bRefine = flag;}
    
    /// set dirty flag whenever surface changed
    void surfaceChanged(bool flag=true) {bFreshMesh=!flag;}
    
    /// access flag indicating if mesh is up-to-date
    bool freshMesh() const {return bFreshMesh;}

    /// use algorithm to generate streched mesh
    void stretchedMesh(bool flag) {bStretchedMesh = flag;}
    
    /// access anisotropic mesh setting
    bool stretchedMesh() const {return bStretchedMesh;}
    
    /// access smoothing parameters
    void smoothingIterations(uint n) {nSmooth = n;}
    
    /// access smoothing parameters
    uint smoothingIterations() {return nSmooth;}
    
    /// access smoothing parameters
    void smoothingFactor(Real w) {wSmooth = w;}
    
    /// access smoothing parameters
    Real smoothingFactor() {return wSmooth;}
    
    /// access kink limiter
    void kinkLimit(Real k) {rKinkLimit = k;}
    
    /// access kink limiter
    Real kinkLimit() const {return rKinkLimit;}
    
    /// return number of neighbors registered
    uint nNeighbors() const {return tnb.size();}

    /// register another surface as touching neighbor
    void registerNeighbor(const MeshComponent *nb);

    /// test if surface a is a non-intersecting neighbor
    bool isNeighbor(const MeshComponent *a) const;

    /// erase neighborhood information
    void clearNeighbors() {tnb.clear();}

    /// number of components which need to be meshed first
    uint nParents() const {return parents.size();}

    /// register another component as parent of this one
    void registerParent(const MeshComponent *nb);

    /// test if surface a is a non-intersecting neighbor
    bool isParent(const MeshComponent *a) const;

    /// test if component a is a child of this one
    bool isChild(const MeshComponent *a) const {
      assert(a != 0);
      return a->isParent(this);
    }

    /// clear dependency information
    void clearParents() {parents.clear();}

    /// access parameter coordinates
    const Vct2 & parameter(uint k) const {return ppt[k];}
    
    /// generate mesh without constraints
    virtual void premesh(const PointGrid<2> & pgi = PointGrid<2>());

    /// copy initial mesh generated externally
    virtual void premesh(const PointList<2> & pp, const Indices & tri);
    
    /// extract the mesh vertices which are on a boundary
    void boundary(side_t s, Indices & si) const;
    
    /// add constraint in uv-space, return false if that failed
    bool constrain(const PointList<2> & uvc, const PointList<3> & rep);

    /// apply the same set of constraints again
    bool reconstrain();
    
	  /// number of constraints defined
	  uint nConstraint() const {return icon.size();}
	
    /// insert boundary point into mesh
    bool insertBoundaryPoints(const PointList<2> & uvc, const PointList<3> & rep);
    
    /// perform a refinement step on the constrained mesh
    virtual void refine();
    
    /// perform a refinement step around vertices vlist
    virtual void refineAround(const Indices & vlist);
    
    /// mesh adaptation call (base class implementation empty)
    virtual void adapt();

    /// clear all data, but keep constraints
    virtual void clear();
    
    /// clear constraints only 
    void clearConstraints() {
      pcon.clear(); rcon.clear(); icon.clear();
    }
    
    /// access error message from DnMesh
    const std::string & lastError() const {return mg.lastError();}
    
    /// debugging: write current mesh to file
    void dbStoreMesh(const std::string & fname) const;

  protected:
    
    /// generate stretched mesh
    void genStretched();

    /// check and ensure that the triangle normal matches surface normal
    uint fixNormals();

    /// transfer mesh from mesh generator
    virtual void transfer();

  protected:
    
    /// surface to which mesh is pinned
    SurfacePtr psf;
    
    /// vertices in parameter space
    PointList<2> ppt;
    
    /// mesh generator for this patch 
    DnMesh mg;

    /// criterion for mesh generation
    DnRefineCriterionPtr pcrit;
    
    /// mesh constraints in parameter space
    std::vector<PointList<2> > pcon;
    
    /// replacement points for constrained vertices
    std::vector<PointList<3> > rcon;
    
    /// indices of constrained mesh vertices
    std::vector<Indices> icon;

    /// components marked as non-intersecting neighbors
    std::vector<const MeshComponent*> tnb;

    /// components which must be meshed first (dependencies)
    std::vector<const MeshComponent*> parents;
    
    /// smoothing parameter, kink limit
    Real wSmooth, rKinkLimit;
    
    /// smoothing iterations
    uint nSmooth;

    /// tag to identify mesh sections
    uint iTag;
    
    /// flag to control mesh generation
    bool bFreshMesh, bRefine, bStretchedMesh;
};

#endif
