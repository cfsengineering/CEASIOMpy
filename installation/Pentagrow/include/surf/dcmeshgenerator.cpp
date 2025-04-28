#include "dcmeshgenerator.h"
#include "surface.h"
#include <genua/timing.h>
#include <genua/dbprint.h>
#include <genua/pattern.h>
#include <iostream>

using namespace std;

void DcMeshGenerator::initMap(SurfacePtr psf)
{
  PatchMeshGenerator::initMap(psf);

  // extract patterns for mesh initialization
  Vector up, vp;
  m_psf->initGridPattern(up, vp);
  if (up.size() < 4)
    up = equi_pattern(4);
  if (vp.size() < 4)
    vp = equi_pattern(4);

  m_pmg.init(psf, up, vp);
  m_pmg.twoQuads();
}

size_t DcMeshGenerator::enforceConstraint(const Indices &cvi, int tag)
{
  return m_pmg.insertConstraint(cvi, tag);
}

size_t DcMeshGenerator::enforceConstraint(const PointList2d &uvp, int tag)
{
  return m_pmg.insertConstraint(uvp, tag);
}

size_t DcMeshGenerator::refineBoundaries()
{
  return m_pmg.refineBoundaries(*m_pmc);
}

size_t DcMeshGenerator::generate(const PointList2d &uvini)
{
  dbprint("generateMesh on ", m_psf->name());
  assert(m_psf);
  assert(m_pmc);

  Wallclock clk;
  clk.start();

  m_pmg.removeOutsideCorners();
  m_pmg.enableExtension(false);

  // reset list of vertices inserted on constraints
  m_pmg.verticesOnConstraints().clear();

  if (m_pmg.nfaces() == 0) {
    TriMesh::clear();
    dbprint("Face",m_psf->name(),"eliminated; no closed constraints.");
    return 0;
  }

  // insert initial points
  const size_t nini = uvini.size();
  for (size_t i=0; i<nini; ++i)
    m_pmg.insertVertex(uvini[i]);

  // perform mesh refinement in the interior domain
  m_pmg.refineInternal(*m_pmc);

  clk.stop();
  clog << "[t] Refinement: " << clk.elapsed() << endl;

  clk.start();
  m_pmg.smooth(m_pmc->nSmooth(), m_pmc->wSmooth());
  clk.stop();
  clog << "[t] Smoothing: " << clk.elapsed() << endl;

  // carve out internal boundaries
  for (size_t i=0; i<m_holes.size(); ++i)
    m_pmg.punchHole( m_holes[i] );

  clk.start();
  m_uvp = m_pmg.uvVertices();
  Indices tri;
  m_pmg.triangles(tri);

  TriMesh::clear();
  TriMesh::importMesh(m_pmg.xyzVertices(), m_pmg.xyzNormals(), tri, false);

  // debug
  clog << m_psf->name() << " : " << nvertices() << " vertices." << endl;

  return TriMesh::nfaces();
}

void DcMeshGenerator::smooth()
{
  m_pmg.smooth( m_pmc->nSmooth(), m_pmc->wSmooth() );
}

void DcMeshGenerator::importMesh(const PointList2d &uvp,
                                  const Indices &tri, int tag)
{
  PatchMeshGenerator::importMesh(uvp, tri, tag);
  m_pmg.initMesh(uvp, tri);
}
