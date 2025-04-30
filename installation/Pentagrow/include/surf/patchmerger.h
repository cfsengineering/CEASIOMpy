
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
 
#ifndef SURF_PATCHMERGER_H
#define SURF_PATCHMERGER_H

#include <genua/trimesh.h>
#include "surface.h"
#include "dnrefine.h"
#include "meshpatch.h"

class MeshFields;

/** Top-level mesh generator.

  PatchMerger is used to generate meshes for multiple surface patches which
  may intersect in pairs of two. First, a surface object is added the the
  assembly together with an appropriate refinement criterion. After that, 
  each surface is discretized on its own using premesh() as a preparation 
  for intersection computations. Then, intersections can be determined for
  each pair of surfaces idependently. Should any of the intersections yield
  unsatisfactory results, the computation can be repeated several times with
  progressivley (and locally) refined meshes. If even this fails, then the
  geometry is likely not valid, i.e. contains intersections of open surfaces
  which cannot be repaired. 

  Once all intersections are found, the main mesh generation phase can be 
  started using mainPass(). After that, triangles which end up inside other
  surfaces, along with duplicate vertices, are removed in finalize().

  Optionally, any remaining aperture loops in the mesh can be plugged using
  closeHoles().

  \deprecated

  \ingroup meshgen

  */
class PatchMerger : public TriMesh
{
  public:
    
    /// empty generator
    PatchMerger() : haveIsecs(false) {}

    /// add a surface to collection, returns index of this surface
    uint addSurface(const SurfacePtr & srf, const DnRegionCriterionPtr & tq);
    
    /// add parametric constraints to patch i (for structural mesh)
    void addConstraints(uint i, const PointList<2> & c);

    /// number of surfaces in this set
    uint npatches() const {return patches.size();}

    /// access patch i
    MeshPatchPtr patch(uint i) const {
      assert(i < patches.size());
      return patches[i];
    }
    
    /// premesh patch, before intersections can be computed
    void premesh(uint i, bool psm = true);
    
    /** Determine intersections between surface i and j */
    bool findIntersections(uint i, uint j, IsecTopology & si, IsecTopology & sj,
                           MeshFields & itrack);
    
    /** Refine primary meshes.
    The most common reason for insufficient accuracy in the detection of intersection lines
    is a coarse primary mesh. This functions allows to refine intersection regions on the
    primary mesh. This function is not suitable to be called multiple times with the same
    intersection regions. */
    void refineIntersectionRegions(uint i, uint j, Real rf,
                                   const IsecTopology & si, const IsecTopology & sj);

    /// add a refinement region to one surface only 
    void refineRegion(uint i, const DnRefineRegion & rg);
    
    /// remove temporary refinement regions
    void resetMeshCriteria();
    
    /// mesh generation pass for patch i
    MgError mainPass(uint i, bool psm=true, bool xcoarse=false, bool pir=true);

    /// join seams and remove internal triangles, return if succeeded  
    bool finalize();
    
    /// discrete postprocessing: close holes in resulting mesh by adding bulges
    bool closeHoles();
    
    /// discrete postprocessing : carefully remove stretched triangles  
    uint destretch(Real maxstr=-1.0, Real maxphi=-1.0, int npass=3);
    
    /// access location of failure, if possible
    const Vct3 & failPosition() const {return pfail;}

  protected:

    /// construct surface which caps hole delimited by vertices idx (heuristic)
    void buildCapSurface(TriMesh & tmerge, const Indices & idx);

    /// trace a closed boundary line, return true if successfull
    bool traceBoundary(Indices & bde, std::deque<uint> & lni) const;
    
    /// try to find a continuation for an apparently open boundary line
    bool contBoundaryLine(std::deque<uint> & bdi) const;
    
    /// reset refinement regions to initial state 
    void resetRegions(uint i);
    
    /// called to indicate mesh generation phase
    virtual void progress(const std::string & msg) const;

  private:
    
    /// continuous surfaces
    SurfaceArray surfaces;
    
    /// mesh patches
    MeshPatchList patches;
    
    /// individual meshing criterions for surfaces
    std::vector<DnRegionCriterionPtr> mcrits;

    /// number of original refinement regions 
    Indices noreg;
    
    /// stores the location of a detected problem
    Vct3 pfail;
    
    /// flag set if any intersections have been processed
    bool haveIsecs;
};

#endif


