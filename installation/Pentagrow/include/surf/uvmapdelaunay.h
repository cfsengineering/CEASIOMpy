
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
 
#ifndef UVMAPDELAUNAY_H
#define UVMAPDELAUNAY_H

#include "forward.h"
#include "delaunaycore.h"
#include "dcplanegeometry.h"
#include "uvmapping.h"

/** Mapped Delaunay surface mesh generation.

  This is the main interface for Delaunay triangulation of arbitrary surfaces
  using the mapped plane approach. The parameter domain (u,v) is mapped to
  a proxy domain (s,t) in which stretch and skew are similar to the values
  encountered in three dimensions. To achieve this, the mapping (s,t) is
  constructed such that the ratio of the partial derivatives and the angle
  between them is as close as possible to the same ratios in 3D space.
  Hence, the 2D Delaunay property which guarantees optimality in a certain sense
  can be used to efficiently generate a quality surface mesh even on highly
  stretched and skewed surfaces such as a highly swept delta wing.

  \ingroup meshgen
  \sa DelaunayCore, DcGeometry
  */
class UvMapDelaunay
{
public:

  /// create empty surface mesh generator
  UvMapDelaunay() : geo(0.0, 1.0), core(geo) {}

  /// determine pattern from surface functions (initGridPattern)
  UvMapDelaunay(SurfacePtr psf);

  /// copy existing mapping
  UvMapDelaunay(SurfacePtr psf, const UvMapping &uvmap, Real mergeTol = 1e-6);

  /// create initialized surface mesh generator
  UvMapDelaunay(SurfacePtr psf, const Vector & up,
                const Vector & vp, Real mergeTol = 1e-6);

  /// initialize from surface and existing mapping
  void init(SurfacePtr psf, const UvMapping &uvmap, Real mergeTol = 1e-6);

  /// initialize from surface and (s,t)-map sampling grid
  void init(SurfacePtr psf, const Vector & up, const Vector & vp,
            Real mergeTol = 1e-6);

  /// enable/disable extension of meshed domain when vertex inserted
  void enableExtension(bool flag) {core.enableExtension(flag);}

  /// access mapping (u,v) to (s,t)
  const UvMapping & map() const {return uvm;}

  /// access point merge tolerance (squared distance)
  Real sqMergeTolerance() const {return geo.pointTolerance();}

  /// number of triangles present
  uint nfaces() const {return core.nValidFaces();}

  /// simplest possible mesh initialization with two triangles
  void twoQuads();

  /// initialize with enclosing rectangle
  void initEnclosing();

  /// remove four enclosing vertices after initial constraint insertion
  void removeOutsideCorners();

  /// enable splitting of constrained edges
  void enableConstraintSplitting(bool flag);

  /// initialization with given mesh (result may not be Delaunay in (s,t)-domain)
  void initMesh(const PointList<2> & uv, const Indices & tri);

  /// initialization with given grid
  void initMesh(const Vector & up, const Vector & vp);

  /// insert a single vertex
  void insertVertex(const Vct2 &uv, bool legalizeEdges = true) {
    core.insertVertex( append(uv), legalizeEdges );
  }

  /// insert constraint polygon connecting previously inserted vertices
  uint insertConstraint(const Indices &cvi,
                        int edgeflags = DcEdge::Constrained,
                        bool legalizeEdges=true);

  /// insert constraint polygon in (u,v) coordinate
  uint insertConstraint(const PointList<2> & uvc,
                        int edgeflags = DcEdge::Constrained,
                        bool legalizeEdges=true);

  /// insert constraint polygon in (u,v) coordinate
  uint insertConstraint(const PointList<2> & uvc, Indices &cvi,
                        int edgeflags = DcEdge::Constrained,
                        bool legalizeEdges=true);

  /// refine mesh boundaries using criterion
  uint refineBoundaries(DcMeshCritBase & c);

  /// refine internal edges using criterion
  uint refineInternal(DcMeshCritBase & c);

  /// apply some iterations of lapacian smoothing to vertex positions
  void smooth(uint niter=1, Real omega=0.5);

  /// start removing triangles starting from hole marker point
  uint punchHole(const Vct2 & phole);

  /// access mesh triangles
  void triangles(Indices & tri) const {
    core.triangles(tri);
  }

  /// sorted set of boundary vertices
  void sortedBoundary(Indices & bvx) const;

  /// access mesh vertices in (u,v) plane
  const PointList<2> & uvVertices() const {return puv;}

  /// access vertices in (s,t) plane
  const PointList<2> & stVertices() const {return geo.stVertices();}

  /// access mesh vertices in (x,y,z) space
  const PointList<3> & xyzVertices() const {return pxy;}

  /// access surface normals at vertices
  const PointList<3> & xyzNormals() const {return pnm;}

  /// access vertices which where inserted on constrained edges
  const Indices & verticesOnConstraints() const {
    return core.verticesOnConstraints();
  }

  /// access vertices which where inserted on constrained edges
  Indices & verticesOnConstraints() {
    return core.verticesOnConstraints();
  }

  /// clear out all data
  void clear();

  /// dump mapping and mesh (debugging)
  void dbgDump(const std::string & fname) const;

private:

  /// evaluate surface and mapping, append vertex
  uint append(const Vct2 & uv);

  /// append vertex without evaluating surface
  uint stAppend(const Vct2 & st);

  /// apply Laplacian smoothing to vertex i
  void smoothVertex(uint iv, uint nnb, const uint *nbf, Real omega);

  /// compute circumcenter of face fi in (u,v)-plane
  bool uvCircumCenter(uint fi, Vct2 &uv) const;

private:

  /// surface to mesh
  SurfacePtr srf;

  /// plane geometry in the (s,t)-plane
  DcPlaneGeometry geo;

  /// Delaunay topology management
  DelaunayCore core;

  /// triangulation vertices in the (u,v) plane
  PointList<2> puv;

  /// triangulation vertices in (x,y,z) space
  PointList<3> pxy;

  /// surface normals in (x,y,z) space
  PointList<3> pnm;

  /// plane mapping (u,v) -> (s,t)
  UvMapping uvm;

  /// list of vertices used for virtual (enclosing) triangles
  Indices virtVertices;
};

#endif // UVMAPDELAUNAY_H
