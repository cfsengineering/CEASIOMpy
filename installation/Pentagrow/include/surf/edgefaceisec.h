
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
 
#ifndef SURF_EDGEFACEISEC_H
#define SURF_EDGEFACEISEC_H

#include <map>
#include <deque>
#include <genua/defines.h>
#include <genua/triedge.h>
#include <genua/triface.h>
#include "sides.h"

class MeshPatch;

/** Intersection between edge and triangular face.
 *
 * \deprecated
 *
 * \ingroup geometry
 * \sa Intersector
 */
class EdgeFaceIsec
{
  public:

    /// create undefined intersection point
    EdgeFaceIsec() {}
    
    /// default construction
    EdgeFaceIsec(const TriFace & t, const TriEdge & s);

    /// required to use sets and maps with this class
    bool operator< (const EdgeFaceIsec & rhs) const;

    /// check if intersection point lies within triangle and edge
    bool valid(bool disjoint = true) const;

    /// check if intersection is on an edge/vertex
    bool touching(Real threshold = gmepsilon) const;
    
    /// return the intersection parameters (face/edge flat geometry)
    const Vct3 & location() const {return uvt;}
    
    /// compute corresponding 3D point on the discrete surfaces
    Vct3 eval() const;

    /// compute 3D point averaged between smooth surfaces
    Vct3 midpoint() const;

    /// tangent to intersection line
    Vct3 tangent() const;

    /// face parameters (u,v)
    Vct2 fparameter() const;

    /// edge parameter (u,v)
    Vct2 eparameter() const;

    /// pick right parameter pair
    Vct2 parameter(const MeshPatch *mp) const;

    /// access triangle
    const TriFace & triangle() const {return f;}

    /// access edge
    const TriEdge & segment() const {return e;}

    /// apply iterative refinement, return resulting gap
    Real refine(Real tol, uint maxit = 32);
    
    /// try to refine using Newton's method
    Real erefine(Real tol, uint maxit = 32);
    
    /// compute local feature size
    Real localSize() const;
    
    /// compute size ratio (mean triangle edge length over edge length)
    Real sizeRatio() const;
    
    /// check if any of the points is on an edge
    side_t onBoundary(Real tol) const;
    
    /// if point is closer than tol to boundary, force it upon it
    void forceToBoundary(Real tol);
    
    /// generate fake intersection point on the opposite side of a u-seam 
    bool fakeOpposedPoint(Real ptol, EdgeFaceIsec & fop) const;
    
  private:

    /// triangle
    TriFace f;

    /// segment
    TriEdge e;

    /// intersection parameter
    Vct3 uvt;
    
    /// flag indicating if iterative refinement is performed
    bool refined;
    
    /// parametric positions after refinement
    Vct2 rqe, rqf;
    
    /// position and tangent after refinement
    Vct3 rpt, rtg;
};

typedef std::deque<EdgeFaceIsec> IsecLine;
typedef std::vector<IsecLine> IsecSet;

#if defined(HAVE_TR1)

#include <tr1/unordered_map>
#include <tr1/unordered_set>
             
typedef std::tr1::unordered_map<TriEdge, std::vector<EdgeFaceIsec>, edge_hash, global_edge_equal> EdgeIsecMap;
typedef std::tr1::unordered_map<TriFace, std::vector<EdgeFaceIsec>, face_hash, global_face_equal> FaceIsecMap;
typedef std::tr1::unordered_set<TriEdge, edge_hash, global_edge_equal> EdgeSet;

#elif defined(HAVE_SGI_STL)

#include <ext/hash_map>
#include <ext/hash_set>          
             
typedef __gnu_cxx::hash_map<TriEdge, std::vector<EdgeFaceIsec>, edge_hash, global_edge_equal> EdgeIsecMap;
typedef __gnu_cxx::hash_map<TriFace, std::vector<EdgeFaceIsec>, face_hash, global_face_equal> FaceIsecMap;
typedef __gnu_cxx::hash_set<TriEdge, edge_hash, global_edge_equal> EdgeSet;

#else

#include <map>
#include <set>

typedef std::map<TriFace, std::vector<EdgeFaceIsec>, global_face_less> FaceIsecMap;
typedef std::map<TriEdge, std::vector<EdgeFaceIsec>, global_edge_less> EdgeIsecMap;
typedef std::set<TriEdge, global_edge_less> EdgeSet;

#endif 

#endif

