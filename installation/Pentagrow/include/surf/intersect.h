
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
 
#ifndef SURF_INTERSECT_H
#define SURF_INTERSECT_H

#include <set>
#include <deque>

#include "edgefaceisec.h"

class TriMesh;
class MeshPatch;
class IsecLinePoint;
class MeshFields;
class BndRect;

typedef std::set<EdgeFaceIsec> IsecTags;

struct XsrSpot 
{
  Vct2 ctr;
  Real ru, rv, maxsr;
  
  bool overlaps(const XsrSpot & a) const {
    Real du = fabs(ctr[0] - a.ctr[0]);
    Real dv = fabs(ctr[1] - a.ctr[1]);
    if (du < ru+a.ru and dv < rv+a.rv)
      return true;
    else
      return false; 
  }
  
  void merge(const XsrSpot & a) {
    Real umin = std::min(ctr[0]-ru, a.ctr[0]-a.ru);
    Real umax = std::max(ctr[0]+ru, a.ctr[0]+a.ru);
    Real vmin = std::min(ctr[1]-rv, a.ctr[1]-a.rv);
    Real vmax = std::max(ctr[1]+rv, a.ctr[1]+a.rv);
    ctr[0] = 0.5*(umin + umax);
    ctr[1] = 0.5*(vmin + vmax);
    ru = 0.5*(umax - umin);
    rv = 0.5*(vmax - vmin);
    maxsr = std::max(maxsr, a.maxsr);
  }
};

typedef std::vector<XsrSpot> XsrSpotArray;

struct IsecTopology
{
  std::vector<BndRect> bb;
  XsrSpotArray xsa;
  int shape;
};

/** Locates intersection lines.
 *
 * Intersector computes surface intersection lines by means of intersecting
 * tessellations of the surfaces. The resulting discrete line segments can
 * then be gradually refined in order to obtain better accuracy.
 *
 * \deprecated
 *
 * \ingroup geometry
 * \sa EdgeFaceIsec
 */
class Intersector
{
  public:

    /// initialize with two discretized surfaces
    Intersector(MeshPatch *sred, MeshPatch *sblue);

    /// find all intersection lines
    const IsecSet & findIntersections(Real maxgap = 1e-4);
    
    /// number of intersection lines found
    uint nlines() const {return isc.size();}

    /// after locating, drop uninteresting or duplicate intersection points
    const IsecSet & filter(Real maxphi, Real maxlen, Real minlen);
    
    /// reduce number of intersection points using a local size criterion
    const IsecSet & reduce(Real maxphi, Real minlen, Real bntol = 1e-4);

    /// sort loose intersection lines so that they begin on boundary 
    void sortLooseLines(Real ptol = 1e-4);
    
    /// test if loose end may be caused by unconnected leading edge 
    bool openLeadingEdge(uint i, uint j, Real ptol = 1e-4) const;
    
    /// try to connect across unconnected leading edge 
    bool connectLeadingEdge(const Indices & vi, const Indices & vj);
    
    /// check if all intersection lines are closed in 3D
    bool closedLoops(Real tol = gmepsilon) const;
    
    /// check if open intersection lines are connected
    bool connectedLines(Real tol = gmepsilon) const;
    
    /// check if the intersection lines end on boundaries
    bool endsOnBoundaries(Real ptol = 1e-4) const;
    
    /// join seam lines if possible 
    uint joinSeamLines(Real tol, Real ptol = 1e-4);
    
    /// create vizualization of the intersection points and lines
    void addViz(MeshFields & mvz) const;

    /// compute bounding rectangles of intersections
    void boxes(std::vector<BndRect> & bra, std::vector<BndRect> & brb) const;
    
    /// compute bounding rectangles of regions where size ration s is exceeded
    void sboxes(Real s, std::vector<BndRect> & bra, std::vector<BndRect> & brb) const;

    /// locate spots with excessive size ratio for all intersections 
    void locateXsrSpots(Real s, XsrSpotArray & xsa, XsrSpotArray & xsb) const; 
    
  private:

    /// identify the corresponding meshpatch
    const MeshPatch *patch(const TriMesh *psf) const;

    /// obtain intersection parameter set
    std::pair<Vct2, Vct2> parameter(const EdgeFaceIsec & is) const;

    /// identify the corresponding meshpatch
    const MeshPatch *patch(const TriEdge & e) const;

    /// identify the corresponding meshpatch
    const MeshPatch *patch(const TriFace & f) const;

    /// convert size ratio to ratio sa/sb 
    Real sizeRatio(uint i, uint j) const;
    
    /// convert size ratio to ratio sa/sb 
    Real sizeRatio(uint i, uint j, Vct2 & ctr, Vct2 & r) const;
    
    /// find starting point, returns 0 if unsuccessfull
    const EdgeFaceIsec *findFirst(const IsecTags & t) const;

    /// find next intersection object, return 0 if unsuccesfull
    const EdgeFaceIsec *findNext(const IsecLinePoint & last) const;

    /// find closest intersection among the nb edges of i
    const EdgeFaceIsec *findNearest(const IsecLinePoint & last,
                                    const MeshPatch *psf,
                                    uint i, Real & mdist) const;

    /// merge overlapping xsr spots 
    void mergeOverlaps(XsrSpotArray & xsa) const;
    
    /// join connected intersection lines 
    void joinConnectedLines(Real tol);
    
  private:

    /// two discretized surfaces
    MeshPatch *sa, *sb;

    /// all intersection lines
    IsecSet isc;

    /// map faces to intersections
    FaceIsecMap mf;

    /// map edges to intersections
    EdgeIsecMap me;
};

#endif

