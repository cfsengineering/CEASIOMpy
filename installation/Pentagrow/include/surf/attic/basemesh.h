
/* ------------------------------------------------------------------------
 * project:    Surf
 * file:       basemesh.h
 * begin:      Feb 2004
 * copyright:  (c) 2004 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * refactored interface to Shewchuk's triangle.c
 * ------------------------------------------------------------------------
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * ------------------------------------------------------------------------ */

#ifndef _SURF_BASEMESH_H
#define _SURF_BASEMESH_H

#include <vector>
#include <iosfwd>
#include <genua/point.h>

class TriQuality;

/** BaseMesh triangle. */
struct BmFace
{
  BmFace(uint r, uint g, uint b) {
    v[0] = r; v[1] = g; v[2] = b;
  }
  uint v[3];
};

typedef std::vector<BmFace> BmFaceArray;

/** Edge for BaseMesh */
struct BmEdge
{
  BmEdge(int from, int to) : src(from), trg(to) {}
  int src, trg;
};

typedef std::vector<BmEdge> BmEdgeArray;

/** Mesh in parameter space.

  */
class BaseMesh
{
  public:

    typedef BmFaceArray::const_iterator face_iterator;

    /// empty construction
    BaseMesh() {}

    /// add a constraint (polyline)
    void addConstraint(const PointList<2> & c);

    /// add a vertex which must appear in the mesh
		void addVertex(const Vct2 & p) {ppt.push_back(p);}

    /// add a hole marker (triangle.c needs this)
    void addHoleMarker(const Vct2 & hp);

    /// create a 2D triangulation with area and angle constraints
    uint generate(Real maxarea, Real minangle = 15.0);

		/// create a 2D triangulation using an acceptance functor
		uint generate(TriQuality & f, Real maxarea, Real minangle = 15.0);

    /// count vertices
    uint nvertices() const {return ppt.size();}

		/// count faces
		uint nfaces() const {return faces.size();}

    /// access vertices
		const Vct2 & vertex(uint i) {return ppt[i];}

    /// access faces
		face_iterator face_begin() const {return faces.begin();}

    /// access faces
		face_iterator face_end() const {return faces.end();}

    /// delete everything
    void clear();

    /// write 2D oogl output
    void writeOogl(std::ostream & os) const;

  private:

    /// parameter points
    PointList<2> ppt;

    /// triangles
    BmFaceArray faces;

    /// constraints
    BmEdgeArray con;

    /// internal holes
    PointList<2> holes;

		/// flag to allow splitting constraints
};

#endif
