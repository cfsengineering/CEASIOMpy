#ifndef SURF_PATCHMESHGENERATOR_H
#define SURF_PATCHMESHGENERATOR_H

#include "forward.h"
#include "uvmapping.h"
#include "dcmeshcrit.h"
#include "jrstriangle/jrstrianglewrapper.h"
#include <genua/radialsort.h>
#include <genua/trimesh.h>

class PatchMeshGenerator : public TriMesh
{
public:

  /// do nothing
  PatchMeshGenerator() {}

  /// destruct
  virtual ~PatchMeshGenerator() {}

  /// assigned surface
  SurfacePtr surface() const {return m_psf;}

  /// assign criterion
  void criterion(DcMeshCritBasePtr pmc);

  /// initialize 2D space mapping
  virtual void initMap(SurfacePtr psf);

  /// mark point as hole
  virtual void punchHole(const Vct2 &ph);

  /// insert a set of boundary points, check for equality with existing points
  Indices insertSegmentPoints(const PointList2d &pts);

  /// add a set of constraints in (u,v) space as a polyline
  virtual size_t enforceConstraint(const PointList2d &uvp, int tag = 0);

  /// add a set of constraints as a polyline connecting points in cvi
  virtual size_t enforceConstraint(const Indices &cvi, int tag = 0) = 0;

  /// use the assigned criterion to refine any boundary segments
  virtual size_t refineBoundaries() = 0;

  /// create mesh from initial points and perform refinement passes
  virtual size_t generate(const PointList2d &uvini) = 0;

  /// apply some barycentric smoothing iterations
  virtual void smooth() = 0;

  /// access points in (u,v) space
  const PointList2d &uvVertices() const {return m_uvp;}

  /// import entire mesh in parameter domain
  virtual void importMesh(const PointList2d &uvp,
                          const Indices &tri, int tag=0);

protected:

  /// initialize 2D space mapping
  void initUvMap(SurfacePtr psf, UvMapping &uvmap);

  /// generate a radius-ordering of current (u,v) points
  RadialOrdering radiusOrder() const;

  /// insert a single point using the sq-distance ordering, return new index
  uint insertSegmentPoint(RadialOrdering &porder, const Vct2 &p);

protected:

  /// surface to mesh
  SurfacePtr m_psf;

  /// mesh points in (u,v) space
  PointList2d m_uvp;

  /// holes in uv-plane (if any)
  PointList2d m_holes;

  /// criterion used for meshing
  DcMeshCritBasePtr m_pmc;

  /// cast to specialization or null
  DcMeshCritPtr m_mcp;  

  /// when two points are regarded as identical
  Real m_sqmergetol = 1e-7;
};

#endif // PATCHMESHGENERATOR_H
