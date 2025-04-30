#ifndef SURF_JRSMESHGENERATOR_H
#define SURF_JRSMESHGENERATOR_H

#include "jrstrianglewrapper.h"
#include <surf/patchmeshgenerator.h>

class JrsMeshGenerator : public PatchMeshGenerator
{
public:

  /// do nothing
  JrsMeshGenerator() : PatchMeshGenerator() {}

  /// initialize (uv) to (st) map
  void initMap(SurfacePtr psf) override;

  /// add a set of constraints as a polyline connecting points in cvi
  size_t enforceConstraint(const Indices &cvi, int tag = 0) override;

  /// use the assigned criterion to refine any boundary segments
  size_t refineBoundaries() override;

  /// create mesh from initial points, run refinement and smoothing passes
  size_t generate(const PointList2d &uvini) override;

  /// apply some barycentric smoothing iterations
  void smooth() override;

  /// import entire mesh in parameter domain
  void importMesh(const PointList2d &uvp, const Indices &tri, int tag=0) override;

protected:

  enum Orient { Clockwise, Colinear, CounterClockwise };

  /// create mesh from initial points
  size_t firstpass(const PointList2d &uvini);

  /// refine stored mesh indirectly using sizing field
  size_t refine();

  /// compute area ratio, (x,y,z) size of unit square at u,v
  Real areaRatio(Real u, Real v) const;

  /// setup points in (s,t) plane and transfer to wrapper, return splitBoundary
  bool stTransfer(const PointList2d &uvini);

  /// extract mesh from wrapper, compute (u,v) and (x,y,z) points
  void extractMesh();

  /// compute desired (s,t) space area for given triangle
  Real targetArea(const uint *v, Real maxPhi,
                  Real maxXArea, Real minXArea = 0.0) const;

  /// apply some barycentric smoothing iterations
  void smooth(uint niter, Real omega, size_t vbegin = 0, size_t vend = NotFound);

  /// move location of vertex iv closer to barycenter of its 1-ring
  void smoothVertex(uint iv, uint nnb, const uint *nbf, Real omega);

  /// determine ordering using robust predicates
  int orientationPlanar(const Vct2 &pa, const Vct2 &pb, const Vct2 &pc) const;

  /// determine how moving a to pa changes the ordering of triangle vi
  int orientChanged(const uint vi[], uint a, const Vct2 &pa) const;

  /// check two segments for intersection, split if necessary
  uint combineSegments(RadialOrdering &porder, uint iseg, uint jseg);

protected:

  /// interface wrapper for triangle.c
  JrsTriangleWrapper m_wrp;

  /// maps from uv-space to st-space
  UvMapping m_uvmap;

  /// mesh points in (s,t) space
  PointList2d m_stp;

  /// boundary segments
  Indices m_segments;

  /// boundary segment markers
  Indices m_segmark;

  /// index of vertices in m_uvp which were inserted due to constraint intersections
  Indices m_segisec;

  /// do not reduce triangle area by more than this in each pass
  Real m_maxAreaReduction = 0.125;

  /// keep track of time
  Real m_tsmooth = 0.0, m_tjrs = 0.0;
};

#endif // JRSMESHGENERATOR_H
