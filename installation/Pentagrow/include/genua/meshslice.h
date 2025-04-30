
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
 
#ifndef GENUA_MESHSLICE_H
#define GENUA_MESHSLICE_H

#include "defines.h"
#include "dvector.h"
#include "line.h"
#include "point.h"

class ConfigParser;
class Triangulation;
class TriMesh;

/** Intersection of line and triangle.

  LineFaceIsec holds data for the intersection of a triangular mesh face and
  a line. The intersection is computed in any case, but inside() only returns
  true if the intersection point lies within the triangle and between the
  end points of the line

  */
class LineFaceIsec
{
  public:

    /// undefined intersection
    LineFaceIsec() : u(2), v(2), w(2) {}
    
    /// initialize with vertices and point list
    LineFaceIsec(const PointList<3> & vtx, const uint *vix, const Line<3> & ln);

    /// test if the intersection is inside the element
    bool inside() const {
      if (u >= 0 and v >= 0 and w >= 0 and t >= 0 and t <= 1)
        return true;
      else
        return false;
    }

    /// compute position of intersection
    const Vct3 & position() const {return pos;}

    /// parametric position along intersecting line
    Real foot() const {return t;}
    
    /// evaluate the mesh field x at the intersection point
    template <typename Type>
    Type eval(const DVector<Type> & x) const {
      return w*x[vi[0]] + u*x[vi[1]] + v*x[vi[2]];
    }
  
  private:

    /// surface element parameters at intersection
    Real u, v, w, t;

    /// intersection position
    Vct3 pos;

    /// triangle vertices
    uint vi[3];
};

typedef std::vector<LineFaceIsec> LfiArray;

/** Create a plane slice through a triangular mesh.

  MeshSlice computes the intersections of the elements of a triangular mesh
  with a limited-size plane rectangular window. Values of any scalar surface
  field associated with the mesh can then be evaluated at the intersection
  points.

  The window is defined using three points: The origin, base and top point.
  Imagine that a baseline is drawn between origin and base point. Starting
  from this line, intersecting rays are emitted in the direction towards
  top as seen from origin. These rays intersect the mesh and data points for
  the intersections are computed.

  */
class MeshSlice
{
  public:

    /// create undefined slice
    MeshSlice() {}

    /// set slice plane between three points
    MeshSlice(const Vct3 & q1, const Vct3 & q2, const Vct3 & q3, uint n = 50) :
      p1(q1), p2(q2), p3(q3), nxp(n) {}

    /// read slice geometry from config file
    void configure(const ConfigParser & cfg);

    /// cut through mesh, return number of intersections
    uint cut(const Triangulation & tg);
    
    /// cut through mesh, return number of intersections
    uint cut(const TriMesh & tg);

    /// return positions of upper/lower intersection points
    void positions(PointList<3> & plower, PointList<3> & pupper) const;

    /// number of "upper" intersection points
    uint nupper() const {return lfupper.size();}

    /// number of "lower" intersection points
    uint nlower() const {return lflower.size();}

    /// evaluate upper and lower values of scalar field x
    template <typename Type>
    void eval(const DVector<Type> & x, DVector<Type> & xlo, 
              DVector<Type> & xup) const {
      uint nu(lfupper.size()), nl(lflower.size());
      xup.resize(nu);
      xlo.resize(nl);
      for (uint i=0; i<nu; ++i)
        xup[i] = lfupper[i].eval(x);
      for (uint i=0; i<nl; ++i)
        xlo[i] = lflower[i].eval(x);
    }
    
  private:

    /// corner points of the plane
    Vct3 p1, p2, p3;

    /// number of lines in plane (equidistant by default)
    uint nxp;
    
    /// intersected surface elements
    LfiArray lfupper, lflower;
};

#endif
