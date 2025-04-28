
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
 
#ifndef SURF_MESHPATCH_H
#define SURF_MESHPATCH_H

#include <boost/shared_ptr.hpp>
#include <genua/trimesh.h>
#include <genua/boxsearchtree.h>
#include <genua/bounds.h>
#include "edgefaceisec.h"
#include "surface.h"

class DnRefineCriterion;
struct IsecTopology;

typedef std::vector<PointList<2> > IpointSet;

typedef enum { MgSuccess=0,
               MgBoundaryReplacementMismatch,
               MgCollidingIntersections } MgError;

typedef enum { IsNoIntersection,
                 IsSingleLoop,
                 IsTwinLoop,
                 IsSingleDivision,
                 IsTwinDivision,
                 IsEdgeBite,
                 IsTwinEdgeBite,
                 IsCornerBite,
                 IsOpenCut,
                 IsMultiple,
                 IsStrangeShape,
                 IsSpatialLoopNotClosed,
                 IsUnclassified
               } IsecShape;               

               
/** Generates the triangulation of a single surface.

  MeshPatch is a triangular mesh patch which stores both parametric (u,v) and
  spatial coordinates (x,y,z). It is used as an intermediate object to compute
  surface-surface intersections and to generate patch meshes which are later
  postprocessed and merged by PatchMerger. 

  \deprecated

  \ingroup meshgen
*/
class MeshPatch : public TriMesh
{
  public:

    /// empty constructor
    MeshPatch() {}

    /// initialize with surface pointer
    MeshPatch(SurfacePtr psf) : srf(psf) {}

    /// number of hole markers
    uint nholes() const {return holes.size();}

    /// access hole marker point (for manual modifications)
    Vct2 & phole(uint i) {
      assert(i < holes.size());
      return holes[i];
    }
    
    /// add arbitrary additional constraints
    void addConstraints(const PointList<2> & c);

    /// add constraints from intersection lines (manual, no hole processing)
    void addIntersections(const IsecSet & isl);
    
    /// generate an unconstrained patch mesh (should never fail)
    void premesh(const DnRefineCriterion & crit, bool psm=false);
    
    /// generate a constrained patch mesh (may fail in constraint handling)
    MgError mesh(const DnRefineCriterion & crit, bool psm=true, bool pir=true);
    
    /// specialized version to generate coarse wing mesh 
    MgError meshCoarse(const DnRefineCriterion & crit);
    
    /// access parameter values
    const Vct2 & parameter(uint i) const {
      assert(i < ppt.size());
      return ppt[i];
    }

    /// evaluate underlying surface
    Vct3 eval(Real u, Real v) const {return srf->eval(u,v);}

    /// compute normal on underlying surface
    Vct3 normal(Real u, Real v) const {return srf->normal(u,v);}

    /// access spline surface
    const SurfacePtr & surface() const {return srf;}

    /// overload triangulation fixate: create search tree
    virtual void fixate();
    
    /// identify boundary points in 3D 
    void boundaryPoints(side_t s, Indices & si) const;
    
  protected:
    
    /// convert from IsecLine to list of parameter points
    void convert(const IsecLine & line, PointList<2> & pts) const;
    
    /// convert from IsecSet to an array of parameter point vectors
    void convert(const IsecSet & isl, IpointSet & pts) const;
        
    /// construct constraint points and 3D replacements
    void filterConstraint(const IsecLine & isl, PointList<2> & cpt, 
                          PointList<3> & rpt) const;
    
  private:

    /// pointer to surface
    SurfacePtr srf;

    /// boundary discretization and final parameter point set
    PointList<2> bdd, ppt, holes;
    
    /// intersections and additional constraints for structural model
    IpointSet ipl, stc;
    
    /// indices of replacement points
    Indices rpi;
    
    /// coordinates of replacement points
    PointList<3> rpp;
    
    /// search tree for nearest neighbor searches
    BSearchTree tree;
    
    /// number of constrained points
    // uint ncp;
};

typedef boost::shared_ptr<MeshPatch> MeshPatchPtr;
typedef std::vector<MeshPatchPtr> MeshPatchList;

#endif

