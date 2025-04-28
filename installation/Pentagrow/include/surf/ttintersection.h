/* Copyright (C) 2015 David Eller <david@larosterna.com>
 *
 * This program is free software; you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free Software
 * Foundation; either version 2 of the License, or (at your option) any later
 * version. This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details. You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
 */

#ifndef SURF_TTINTERSECTION_H
#define SURF_TTINTERSECTION_H

#include <deque>
#include <boost/shared_ptr.hpp>
#include <genua/svector.h>
#include <genua/defines.h>
#include "surface.h"

class TriFace;
class TTIntersector;
class MeshFields;
class MeshComponent;

class TTIntersection;
typedef boost::shared_ptr<TTIntersection> TTIntersectionPtr;
typedef std::deque<TTIntersectionPtr> TTIntersectionArray;

/** Triangle-triangle intersection

  \ingroup meshgen
  \sa MeshComponent, TTIntersector
*/
class TTIntersection
{
  public:

    enum TTiConTop {tti_s2s, tti_s2t, tti_t2s, tti_t2t, tti_none};

    /// undefined intersection
    TTIntersection() : itor(0), bEnforced(false) {}
  
    /// initialize defined, but untested intersection
    TTIntersection(const TTIntersector *tti, uint t1, uint t2);
    
    /// initialize as enforced matching segment
    TTIntersection(const TTIntersector *tti, uint t1, uint t2,
                   const Vct3 & ps, const Vct3 & pt);

    /// return whether this intersection was enforced explicitly
    bool enforced() const {return bEnforced;}

    /// access triangle index
    uint first() const {return itri1;}
      
    /// access triangle index
    uint second() const {return itri2;}
    
    /// access mesh patch
    const MeshComponent *firstPatch() const;
    
    /// access mesh patch
    const MeshComponent *secondPatch() const;
    
    /// set node number
    void source(uint i) {nsrc = i;}
    
    /// set node number 
    void target(uint i) {ntrg = i;}
    
    /// access node number 
    uint source() const {return nsrc;}
    
    /// access node number 
    uint target() const {return ntrg;}
    
    /// opposed node 
    uint opposed(uint n) const {
      if (n == nsrc)
        return ntrg;
      else if (n == ntrg)
        return nsrc;
      else
        return NotFound;
    }
    
    /// access segment start point
    const Vct3 & srcPoint() const {return isrc;}
    
    /// access segment start point
    const Vct3 & trgPoint() const {return itrg;}
    
    /// parameter position of src point
    void srcParameter(Vct2 & q1, Vct2 & q2) const;
    
    /// parameter position of trg point
    void trgParameter(Vct2 & q1, Vct2 & q2) const;
    
    /// check if source point is on a boundary 
    void srcOnBoundary(Real tol, bool & ubound, bool & vbound) const;
    
    /// check if target point is on a boundary 
    void trgOnBoundary(Real tol, bool & ubound, bool & vbound) const;
    
    /// pointer to surfaces
    void surfaces(SurfacePtr & psf1, SurfacePtr & psf2) const;
    
    /// compute likely connection pattern 
    TTiConTop nearestConnection(const TTIntersection & a, Real & dist) const;
    
    /// segment length
    Real length() const {return norm(isrc-itrg);}
      
    /// local length: minimum of sqrt(area) of both triangles
    Real localDimension() const;
    
    /// compute 3d intersection using Guige's method
    bool intersect();
    
    /// add line to visualization object
    void addViz(MeshFields & mvz) const;
    
    /// check if this intersection segment intersects test triangle tt
    Real intersectsFace(uint tt) const;
    
    /// split, change this and return a new segment at triangle tt
    TTIntersectionPtr split(Real t);
    
  private:
    
    /// compute parametric value of a projection 
    Vct2 uvProjection(const TriFace & f, const Vct3 & p) const;
    
  private:
  
    /// intersection points in space
    Vct3 isrc, itrg;
    
    /// pointer to intersector
    const TTIntersector *itor;
    
    /// triangles involved
    uint itri1, itri2;
    
    /// nodes corresponding to isrc and itrg
    uint nsrc, ntrg;

    /// enforced point - cannot be filtered out
    bool bEnforced;
};

inline bool operator< (const TTIntersectionPtr & a, const TTIntersectionPtr & b)
{
  uint a1 = a->first();
  uint b1 = b->first();
  if (a1 < b1)
    return true;
  else if (a1 > b1)
    return false;
  else 
    return (a->second() < b->second());
}

inline bool operator== (const TTIntersectionPtr & a, const TTIntersectionPtr & b)
{
  return ((a->first() == b->first()) and (a->second() == b->second()));
}

inline bool less_by_nodes(const TTIntersectionPtr & a, const TTIntersectionPtr & b)
{
  uint a1 = a->source();
  uint b1 = b->source();
  if (a1 < b1)
    return true;
  else if (a1 > b1)
    return false;
  else 
    return (a->target() < b->target());
}

inline bool equal_by_nodes(const TTIntersectionPtr & a, const TTIntersectionPtr & b)
{
  return ((a->source() == b->source()) and (a->target() == b->target()));
}

#endif
