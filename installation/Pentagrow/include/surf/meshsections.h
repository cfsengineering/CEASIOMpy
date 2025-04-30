
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
 
#ifndef SURF_MESHSECTIONS_H
#define SURF_MESHSECTIONS_H

#include <iosfwd>
#include <boost/shared_ptr.hpp>
#include <genua/bounds.h>
#include "facetree.h"

class TriMesh;
class Plane;

/** Compute slices through a triangular surface mesh

  \deprecated
  */
class MeshSections
{
  public:

    /// initialize section generator with mesh 
    MeshSections(const TriMesh & m);

    /// find set of polygons
    uint findPolygons(const Plane & pln);
    
    /// number of current polygons
    uint npolygons() const {return pgs.size();} 
    
    /// compute area of all polygons
    Real area(const Plane & pln) const;
    
    /// convenience function: area from n slices
    void areaDistribution(Real alpha, int n, Matrix & xa);
    
    /// join multiple open polygons if possible
    void joinPolygons(Real tol = gmepsilon);

    /// access point set for polygon i
    const PointList<3> & polygon(int i) const {return pgs[i];}
    
    /// add polygons to visu
    void addViz(MeshFields & mvz) const;

    /// write sections to plain text file
    void writePlain(std::ostream & os) const;
    
  private:

    /// construct triangle from plane
    void triangleFromPlane(const Plane & pln);
    
    /// test for intersection
    bool fintersect(uint ti, Vct3 & ps, Vct3 & pt) const;
    
    /// start new polygon from scratch
    uint newPolygon(Indices & tix);
    
    /// find next triangle of candidates
    uint nextTriangle(uint ti, Indices & tix, 
                      const Vct3 & plast, Vct3 & pnext) const;
    
  private:
    
    /// reference to mesh
    const TriMesh & msh;

    /// tree used to quickly find intersection candidates
    FaceTree ftree;

    /// bounding box of the complete mesh
    BndBox bb;
    
    /// current triangle vertices
    Vct3 ptri[3];
    
    /// polygons identified
    std::vector<PointList<3> > pgs;
};

typedef boost::shared_ptr<MeshSections> MeshSectionsPtr;

#endif
