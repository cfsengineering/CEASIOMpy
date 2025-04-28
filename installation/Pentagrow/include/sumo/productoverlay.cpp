
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
 
#include "productoverlay.h"
#include "tritree.h"
#include "frameprojector.h"
#include <genua/timing.h>
#include <genua/trimesh.h>
#include <iostream>

#ifdef _OPENMP
#include <omp.h>
#endif

using namespace std;

void ProductOverlay::tesselate(const IgesFile &file)
{
  clear();

#ifdef _OPENMP
  int pre_nthreads = omp_get_num_threads();
  omp_set_num_threads( 4*omp_get_num_procs() );
#endif

  Wallclock clk;
  clk.start();
  m_product.fromIges( file, IgesEntity::SurfaceClass );
  clk.stop();
  cout << "IGES surface construction: " << clk.elapsed() << endl;

  clk.start();
  m_product.tessellate();
  clk.stop();
  cout << "Tessellation: " << clk.elapsed() << endl;

  // if the IGES file does not contain any structure and there are
  // more than nsmax mesh nodes, collapse the overlay mesh
  const ProductTreePtr & rootNode( m_product.rootNode() );
  if (rootNode)
    cout << "Tree depth: " << rootNode->depth() << endl;

  const uint nMaxSurfaces = 100;
  if (rootNode and rootNode->depth() < 3) {
    if (m_product.nsurfaces() > nMaxSurfaces) {
      cout << m_product.nsurfaces() << " surfaces, collapsing..." << endl;
      clk.start();
      m_product.collapseMesh();
      clk.stop();
      cout << "Collapse mesh: " << clk.elapsed() << endl;
    }
  }

  clk.start();
  m_painter.init(m_product);
  clk.stop();
  cout << "Painter build: " << clk.elapsed() << endl;

#ifdef _OPENMP
  omp_set_num_threads( pre_nthreads );
#endif
}

void ProductOverlay::tesselate(const StepFile &file)
{
  clear();

#ifdef _OPENMP
  int pre_nthreads = omp_get_num_threads();
  omp_set_num_threads( 4*omp_get_num_procs() );
#endif

  Wallclock clk;
  clk.start();
  m_product.fromStep(file);
  clk.stop();
  cout << "STEP surface construction: " << clk.elapsed() << endl;

  clk.start();
  uint ntri = m_product.tessellate();
  clk.stop();
  cout << "Tessellation: " << clk.elapsed() << endl;
  cout << "Triangles: " << ntri << endl;

  // as of now, STEP import does not support product structure, so
  // we collapse the mesh into the root node for more efficient rendering
  m_product.collapseMesh();

  clk.start();
  m_painter.init(m_product);
  clk.stop();
  cout << "Painter build: " << clk.elapsed() << endl;

#ifdef _OPENMP
  omp_set_num_threads( pre_nthreads );
#endif
}

void ProductOverlay::fromSTL(const StringArray &files)
{
  clear();
  m_product.fromSTL(files);
  m_painter.init(m_product);
}

void ProductOverlay::fromCGNS(const std::string & fname)
{
  clear();

  MxMesh mx;
  mx.readCgns(fname);
  m_product.fromMx(mx);
  m_painter.init(m_product);
}

void ProductOverlay::fromBmsh(const string &bmsh)
{
  clear();

  MxMesh mx;
  mx.readFFA(bmsh);
  m_product.fromMx(mx);
  m_painter.init(m_product);
}

void ProductOverlay::fromMx(const MxMesh &mx)
{
  clear();
  m_product.fromMx(mx);
  m_painter.init(m_product);
}

void ProductOverlay::fromXml(const XmlElement &xe)
{
  clear();
  m_product.fromXml(xe);
  m_painter.init(m_product);
}

void ProductOverlay::build()
{
  m_painter.build();
}

void ProductOverlay::draw() const
{
  if (m_visible)
    m_painter.draw();
}

void ProductOverlay::collectMesh(TriMesh &tm) const
{
  typedef std::pair<CgMeshPtr,Mtx44f> MSet;
  std::vector<MSet> cgm;

  // collect meshes
  std::vector<ProductTreePtr> stack;
  stack.push_back( m_product.rootNode() );
  while (not stack.empty()) {
    ProductTreePtr ptp = stack.back();
    stack.pop_back();
    CgMeshPtr cgr = ptp->cgRep();
    if (cgr) {
      Mtx44f tfm;
      ptp->currentTransform().matrix(tfm);
      cgm.push_back( make_pair(cgr,tfm) );
    } else {
      for (uint i=0; i<ptp->nchildren(); ++i)
        stack.push_back(ptp->child(i));
    }
  }

  CgMesh merged;
  const int ncg = cgm.size();

#pragma omp parallel
  {
    // thread-private merged mesh
    CgMesh tpm;

#pragma omp for schedule(dynamic)
    for (int i=0; i<ncg; ++i) {
      const CgMesh & cg( *(cgm[i].first) );
      const Mtx44f & tfm( cgm[i].second );
      tpm.merge( cg, tfm );
    }

#pragma omp critical
    merged.merge(tpm);
  }

  // convert to TriMesh for clients
  tm.clear();
  PointList<3> vtx(merged.vertices());
  Indices tri;
  merged.toTriangles(tri);
  tm.importMesh(vtx, tri);
}

void ProductOverlay::rebuildProjector(FrameProjector &fp) const
{
  fp.buildTree( m_product );
}

void ProductOverlay::extendBox(float lo[], float hi[]) const
{
  Vct3f plo(lo), phi(hi);
  m_painter.boundingBox(plo, phi);

  // debug
  cout << "Overlay bb lo " << plo << " hi " << phi << endl;
  std::copy(plo.begin(), plo.end(), lo);
  std::copy(phi.begin(), phi.end(), hi);
}

void ProductOverlay::clear()
{
  m_product = Product();
  m_painter = ProductPainter();
  m_visible = true;
}
