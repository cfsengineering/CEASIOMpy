#ifndef SURF_DCMESHGENERATOR_H
#define SURF_DCMESHGENERATOR_H

#include "patchmeshgenerator.h"
#include "uvmapdelaunay.h"

class DcMeshGenerator : public PatchMeshGenerator
{
public:

  /// do nothing
  DcMeshGenerator() : PatchMeshGenerator() {}

  /// initialize mapping
  void initMap(SurfacePtr psf);

  /// clear all constraints
  void clearConstraints();

  /// add a set of constraints as a polyline connecting points in cvi
  size_t enforceConstraint(const Indices &cvi, int tag = 0);

  /// add a set of constraints in (u,v) space as a polyline
  size_t enforceConstraint(const PointList2d &uvp, int tag = 0);

  /// use the assigned criterion to refine any boundary segments
  size_t refineBoundaries();

  /// create mesh from initial points
  size_t generate(const PointList2d &uvini);

  /// apply some barycentric smoothing iterations
  void smooth();

  /// import entire mesh in parameter domain
  virtual void importMesh(const PointList2d &uvp,
                          const Indices &tri, int tag=0);

private:

  /// mesh generator kept alive
  UvMapDelaunay m_pmg;
};

#endif // DCMESHGENERATOR_H
