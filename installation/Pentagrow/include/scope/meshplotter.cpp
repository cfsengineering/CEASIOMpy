
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
 
#include "meshplotter.h"
#include "glew.h"
#include <surf/nstmesh.h>
#include <genua/dbprint.h>
#include <genua/mxmesh.h>
#include <genua/timing.h>
#include <genua/trimesh.h>
#include <genua/basicedge.h>
#include <iostream>

using namespace std;

typedef SectionPlotter::ElementColor ElementColor;
typedef SectionPlotter::ElementColorArray ElementColorArray;

MeshPlotter::MeshPlotter() : m_visible(true)
{
  m_bblo = std::numeric_limits<float>::max();
  m_bbhi = - m_bblo;
}

MxMeshPtr MeshPlotter::load(const string &fname)
{ 
  MxMeshPtr pmx = boost::make_shared<MxMesh>();

  // test if this could be NASTRAN, just check filename extension
  string sfx = toLower(filename_suffix(fname));
  bool loaded = false;
  if (sfx == ".f06" or sfx == ".blk" or sfx == ".bdf" or
      sfx == ".dat" or sfx == ".pch") {
    NstMesh nsm;
    nsm.nstread(fname);
    nsm.toMx(*pmx);
    loaded = true;
  } else {
    loaded = pmx->loadAny(fname);
  }

  if (not loaded)
    return MxMeshPtr();

  // the following sanity checks are really fast, typically only about
  // 3-4 milliseconds per 1 million nodes, so just do them on every load,
  // because it avoids crashes on undefined geometry.

  // check for NaNs
  const PointList<3> & vtx( pmx->nodes() );
  const int nv = vtx.size();
  for (int i=0; i<nv; ++i) {
    for (int k=0; k<3; ++k) {
      if (std::isnan(vtx[i][k])) {
        stringstream ss;
        ss << fname << " contains node with NaN coordinate." << endl;
        ss << "Node " << i+1 << " coordinate " << k+1 << endl;
        throw Error(ss.str());
      }
    }
  }

  // check for elements indexing out-of range
  const size_t nn = pmx->nnodes();
  for (uint j=0; j<pmx->nsections(); ++j) {
    const MxMeshSection &sec( pmx->section(j) );
    const size_t nv = size_t(sec.nelements()) * sec.nElementNodes();
    if (nv == 0)
      continue;
    const uint *v = sec.element(0);
    for (size_t i=0; i<nv; ++i) {
      if (v[i] >= nn) {
        stringstream ss;
        ss << fname << " contains element which indexes node number " << endl;
        ss << v[i] << ", while only " << nn << " nodes are present." << endl;
        throw Error(ss.str());
      }
    }
  }

  assign(pmx);
  return m_pmx;
}

MxMeshPtr MeshPlotter::loadStl(const string &fname,
                               double featureAngle, double mergeThreshold)
{
  MxMeshPtr pmx = boost::make_shared<MxMesh>();

  TriMesh tm;
  tm.readSTL(fname);

  if (featureAngle > 0)
    tm.detectEdges( featureAngle, mergeThreshold );
  else
    tm.cleanup( mergeThreshold );

  if (tm.nfaces() > 0) {
    uint tsec = pmx->appendSection(tm);
    pmx->section(tsec).rename(fname);
  }

  if (featureAngle > 0) {
    std::vector<BasicEdge> redges;
    const size_t ne = tm.nedges();
    for (size_t i=0; i<ne; ++i) {
      if (tm.edegree(i) != 2) {
        const TriEdge & edg( tm.edge(i) );
        redges.push_back( BasicEdge( edg.source(), edg.target()) );
      }
    }
    std::sort(redges.begin(), redges.end());
    redges.erase( std::unique(redges.begin(), redges.end()), redges.end() );

    const size_t nre = redges.size();
    Indices rlv(2*nre);
    for (size_t i=0; i<nre; ++i) {
      rlv[2*i+0] = redges[i].source();
      rlv[2*i+1] = redges[i].target();
    }
    if (not rlv.empty()) {
      uint rsec = pmx->appendSection(Mx::Line2, rlv);
      pmx->section(rsec).rename("Ridges");
    }
  }

  assign(pmx);

  // first section is triangle section; switch off edge display by default
  if (not m_secplot.empty())
    m_secplot.front().showEdges(false);

  return pmx;
}

bool MeshPlotter::addFields(const string &fname)
{
  if (not m_pmx)
    return false;

  // main use case: import .bout files from EDGE
  if ( fname.find(".bout") != string::npos ) {
    return m_pmx->appendFFAFields(fname);
  } else if ( fname.find(".bdis") != string::npos ) {
    MxMeshField f(m_pmx.get());
    bool ok = f.readBdis(fname);
    if (ok) {
      m_pmx->appendField(std::move(f));
      clog << "Loaded .bdis file: " << fname << endl;
    } else {
      clog << "Failed to load .bdis file: " << fname << endl;
    }
    return ok;
  } else {

    // TODO : load full mesh, then transfer fields if compatible

    return false;

  }

  return false;
}

void MeshPlotter::assign(MxMeshPtr pmx)
{
  Wallclock clk;
  clk.start();

  m_secplot.clear();
  m_hhplot.clear();
  m_pmx = pmx;
  if (m_pmx == nullptr)
    return;

  rebuildSections();

  cout << "assign - rebuildSections(): " << clk.stop() << endl; clk.start();

  // cannot have bocos which are all grey - assign colors
  const Color grey(0.5f, 0.5f, 0.5f);
  const int nbc = m_pmx->nbocos();
  for (int i=0; i<nbc; ++i) {
    MxMeshBoco & bc(m_pmx->boco(i));
    if (bc.displayColor() == grey) {
      const int val = 90;
      const int sat = 190;
      bc.displayColor( Color::sequence(sat, val, i) );
    }

    // for those BCs which map directly to one section, look at the
    // BC type flags and switch off farfield and wake BCs
    uint isec = m_pmx->mappedSection(i);
    if (isec != NotFound) {
      Mx::BocoType bct = bc.bocoType();
      if (bct == Mx::BcFarfield or bct == Mx::BcWakeSurface)
        m_secplot[isec].visible(false);
    }

  }
  m_bcVisible.clear();
  m_bcVisible.resize(nbc, true);

  updateNodeTree();
  cout << "assign - updateNodeTree: " << clk.stop() << endl;
}

void MeshPlotter::rebuildSections()
{
  if (m_pmx == nullptr)
    return;

  const int ns = m_pmx->nsections();
  m_secplot.clear();
  m_secplot.resize( ns );
  for (int i=0; i<ns; ++i)
    m_secplot[i].assign(m_pmx, i);
}

void MeshPlotter::eraseSection(uint isec)
{
  const uint nsec = m_secplot.size();
  if (isec >= nsec or (not m_pmx))
    return;

  dbprint("MeshPlotter: eraseSection:",isec);
  m_secplot.erase(m_secplot.begin() + isec);
  m_pmx->eraseSection(isec);

  for (uint i=isec; i<m_pmx->nsections(); ++i)
    m_secplot[i].assign(m_pmx, i);
}

uint MeshPlotter::addMappedBoco(uint isec)
{
  if ((not m_pmx) or isec >= m_pmx->nsections())
    return NotFound;

  size_t begin = m_pmx->section(isec).indexOffset();
  size_t end = begin + m_pmx->section(isec).nelements();

  MxMeshBoco bc;
  bc.setRange(begin, end);
  bc.rename( m_pmx->section(isec).name() );
  uint ibc = m_pmx->appendBoco(bc);
  m_bcVisible.push_back(true);

  return ibc;
}

void MeshPlotter::eraseBoco(uint iboco)
{
  if ((not m_pmx) or iboco >= m_pmx->nbocos())
    return;

  m_pmx->eraseBoco(iboco);
  m_bcVisible.erase( m_bcVisible.begin() + iboco );
}

void MeshPlotter::boundingBox(float plo[], float phi[])
{
  if (not m_visible)
    return;
  for (uint i=0; i<m_secplot.size(); ++i) {
    const SectionPlotter & sp( m_secplot[i] );
    if (sp.showEdges() or sp.showElements())
      sp.boundingBox(plo, phi);
  }
  for (int k=0; k<3; ++k) {
    m_bblo[k] = plo[k];
    m_bbhi[k] = phi[k];
  }
}

void MeshPlotter::sectionColors()
{
  if (not m_pmx)
    return;
  const int ns = m_secplot.size();
  for (int i=0; i<ns; ++i) {
    m_secplot[i].solidColor( m_pmx->section(i).displayColor() );
  }
}

void MeshPlotter::bocoColors()
{
  if (not m_pmx)
    return;
  const int ns = m_secplot.size();
  const int nb = m_pmx->nbocos();
  ElementColorArray ecol;
  for (int i=0; i<nb; ++i) {
    const MxMeshBoco & bc( m_pmx->boco(i) );
    uint isec = m_pmx->mappedSection(i);
    // cout << "Boco " << i << " color: " << bc.displayColor().str() << endl;
    if (isec != NotFound) {
      m_secplot[isec].solidColor( bc.displayColor() );
    } else {
      Indices elix;
      bc.elements(elix);
      ElementColorArray tmp(elix.size());
      for (int j=0; j<int(elix.size()); ++j) {
        tmp[j].gelix = elix[j];
        tmp[j].color = bc.displayColor();
      }
      ecol.insert(ecol.end(), tmp.begin(), tmp.end());
    }
  }

  sort_unique(ecol);
  if (not ecol.empty()) {
    for (int i=0; i<ns; ++i)
      m_secplot[i].updateColors(ecol);
  }
}

void MeshPlotter::bocoVisible(uint ibc, bool flag)
{
  if (not m_pmx)
    return;

  uint isec = m_pmx->mappedSection(ibc);
  if (isec != NotFound) {
    m_secplot[isec].visible(flag);
  } else {
    Indices elix;
    m_pmx->boco(ibc).elements(elix);
    for (uint i=0; i<m_secplot.size(); ++i) {
      bool needBuild = m_secplot[i].showElements(elix, flag);
      if (needBuild)
        m_secplot[i].build();
    }
  }
  m_bcVisible[ibc] = flag;
}

void MeshPlotter::cutMesh(const Plane &pln)
{
  if (not m_pmx)
    return;

  Wallclock clk;

  std::vector<bool> nodesBelowPlane;
  m_pmx->nodesBelow( pln, nodesBelowPlane );
  for (uint j=0; j<m_secplot.size(); ++j)
    m_secplot[j].cutVolumeElements(nodesBelowPlane);

  clk.stop();
  cout << "MeshPlotter::cutMesh: " << clk.elapsed() << "s." << endl;
}

void MeshPlotter::displayVolumeElements(const Indices &gix, bool flag)
{
  if (not m_pmx)
    return;

  const int nsec = m_pmx->nsections();
  for (int i=0; i<nsec; ++i) {
    if ( m_pmx->section(i).volumeElements() ) {
      if (m_secplot[i].showElements(gix, flag)) {
        cout << "Rebuilding volume section: " << m_pmx->section(i).name() << endl;
        m_secplot[i].showElements(true);
        m_secplot[i].showEdges(true);
        m_secplot[i].build();
      }
    }
  }
}

void MeshPlotter::clearVolumeElements()
{
  if (not m_pmx)
    return;

  const int nsec = m_pmx->nsections();
  for (int i=0; i<nsec; ++i) {
    if ( m_pmx->section(i).volumeElements() ) {
      m_secplot[i].markAllElements(false);
    }
  }
}

void MeshPlotter::colorLimits(uint ifield, float &blue, float &red,
                              float spread, int vfm) const
{
  if (not m_pmx)
    return;
  if (ifield >= m_pmx->nfields())
    return;

  const MxMeshField & field( m_pmx->field(ifield) );
  DVector<float> val;
  if (field.realField()) {
    const int nv = field.nodal() ? m_pmx->nnodes() : m_pmx->nelements();
    val.allocate( nv );
    if (field.ndimension() == 1) {
      //const Real *rp = field.realPointer();
      //std::copy(rp, rp+nv, val.begin());
      field.fetch(val);
    } else {
      field.condensed(vfm, val);
    }
    Color::colorLimits(val.size(), val.pointer(), spread, blue, red);
  }
}

void MeshPlotter::fieldColors(uint ifield, float blue, float red,
                              int vfm)
{
  if (not m_pmx)
    return;
  if (ifield >= m_pmx->nfields())
    return;

  const MxMeshField & field(m_pmx->field(ifield));
  if (field.realField() and field.nodal()) {
    if (field.ndimension() == 1) {
      for (uint i=0; i<m_secplot.size(); ++i)
        m_secplot[i].updateColors(field, blue, red);
    } else {
      DVector<float> cf( m_pmx->nnodes() );
      field.condensed(vfm, cf);
      for (uint i=0; i<m_secplot.size(); ++i)
        m_secplot[i].updateColors(cf, blue, red);
    }
  } else if ((not field.nodal()) and (field.ndimension() == 1)) {


    const int nelem = m_pmx->nelements();

    if (field.realField()) {

      Vector x(nelem);
      field.fetch(x);

      // generate color array for elements
      const int nsec = m_pmx->nsections();
      for (int i=0; i<nsec; ++i) {
        const MxMeshSection & sec( m_pmx->section(i) );
//        if (not sec.surfaceElements())
//          continue;
        const int offset = sec.indexOffset();
        const int nselm = sec.nelements();
        ElementColorArray ecl(nselm);
        for (int j=0; j<nselm; ++j) {
          ecl[j].gelix = offset + j;
          ecl[j].color.map(blue, red, x[offset + j]);
        }
        m_secplot[i].updateColors(ecl);
      }

    } else {

      // map element-wise integer field values to colors
      std::vector<int> ip(nelem), uival(nelem);
      field.fetch(ip);
      uival = ip;
      std::sort(uival.begin(), uival.end());
      uival.erase( std::unique(uival.begin(), uival.end()), uival.end() );

      const int ncol = uival.size();
      int sat(140), val(170), huestep;
      huestep = std::max(19, int(360.0f/(ncol-1)));
      ColorArray ucol(ncol);
      for (int i=0; i<ncol; ++i)
        ucol[i] = Color::hsvColor((i*huestep)%360, sat, val);

      // generate color array for elements
      const int nsec = m_pmx->nsections();
      for (int i=0; i<nsec; ++i) {
        const MxMeshSection & sec( m_pmx->section(i) );
        if (not sec.surfaceElements())
          continue;
        const int offset = sec.indexOffset();
        const int nselm = sec.nelements();
        ElementColorArray ecl(nselm);
        for (int j=0; j<nselm; ++j) {
          const uint ipos = sorted_index(uival, ip[offset + j]);
          assert(ipos != NotFound);
          ecl[j].gelix = offset + j;
          ecl[j].color = ucol[ipos];
        }
        m_secplot[i].updateColors(ecl);
      }

    } // integer field

  } else {
    cerr << "Cannot display field data: " << field.name()
         << ((field.realField()) ? (" real, ") : (" int, "))
         << "ndim " << field.ndimension()
         << ((field.nodal()) ? (" nodal") : (" elemental")) << endl;
  }
}

void MeshPlotter::prepareSingleMode(uint ifield, Real scale)
{
  if (not m_pmx)
    return;
  if (ifield >= m_pmx->nfields())
    return;

  const MxMeshField & field( m_pmx->field(ifield) );
  if ((not field.nodal()) or (not field.realField()))
    return;
  if (field.ndimension() < 3)
    return;

  cout << "prepare mode " << ifield << " scale: " << scale << endl;

  const int ns = m_secplot.size();
  for (int j=0; j<ns; ++j) {
    m_secplot[j].setDeformationBasis(ifield, scale);
    m_secplot[j].resetUndeformed();
  }

  m_lastDispA = m_lastDispB = 0;
}

void MeshPlotter::animateSingleMode(Real adisp)
{
  cerr << "adisp = " << adisp << endl;
  float dx = adisp - m_lastDispA;

  // no point in computing zero changes
  if (dx == 0.0f)
    return;

  m_lastDispA = adisp;
  const int ns = m_secplot.size();
  for (int j=0; j<ns; ++j) {
    if (m_secplot[j].visible())
      m_secplot[j].basisDeform(dx);
  }
}

void MeshPlotter::deformNodes(uint ifield, Real scale)
{
  if (not m_pmx)
    return;
  if (ifield >= m_pmx->nfields())
    return;

  const MxMeshField & field( m_pmx->field(ifield) );
  if ((not field.nodal()) or (not field.realField()))
    return;
  if (field.ndimension() < 3)
    return;

  // FIXME: def.size() can be very large for volume meshes; typically,
  // animations will only access a fraction of the total nodes
  PointList<3,float> def( m_pmx->nodes() );
  const int nvis = m_visibleNodes.size();
  float fscale(scale);

  BEGIN_PARLOOP_CHUNK(0, nvis, 512)
      for (int i=a; i<b; ++i) {
    Vct3f dx;
    uint idx = m_visibleNodes[i];
    field.value(idx, dx);
    def[idx] += fscale * dx;
  }
  END_PARLOOP

      for (uint j=0; j<m_secplot.size(); ++j)
      m_secplot[j].updateVertices( def );
}

bool MeshPlotter::ipolDeformation(uint idef, Real time, Real scale)
{
  if (not m_pmx)
    return false;
  if (idef >= m_pmx->ndeform())
    return false;

  MxMeshDeform & defo( m_pmx->deform(idef) );
  if (not defo.hasSpline())
    defo.buildSpline();

  Vector dss;
  bool inside = defo.interpolateSubspace(time, dss);

  PointList<3> vdef( m_pmx->nnodes() );
  defo.deformElastic(scale, dss, vdef);

  PointList<3,float> fvdef(vdef);
  for (uint j=0; j<m_secplot.size(); ++j)
    m_secplot[j].updateVertices( fvdef );

  return inside;
}

bool MeshPlotter::ipolTrajectory(uint idef, Real time,
                                 Real defScale, Real rbScale)
{
  if (not m_pmx)
    return false;
  if (idef >= m_pmx->ndeform())
    return false;

  MxMeshDeform & defo( m_pmx->deform(idef) );
  if (not defo.isFlightPath())
    return ipolDeformation(idef, time, defScale);

  if (not defo.hasSpline())
    defo.buildSpline();

  // evaluate subspace vector
  Vector dss;
  bool inside = defo.interpolateSubspace(time, dss);

  // apply nodal displacement
  PointList<3> vdef;
  defo.deformElastic(defScale, dss, vdef);

  // add rigid-body motion
  m_rbrot = defo.rbTransform(m_cog, rbScale, dss, vdef);
  Real u = dss[6];
  Real v = dss[7];
  Real w = dss[8];
  Real q = std::sqrt(sq(u) + sq(v) + sq(w));
  m_curalpha = std::atan2(-w, -u);
  m_curbeta = std::asin(v/q);
  m_curcog = m_cog + rbScale*Vct3(dss[0], dss[1], dss[2]);

  PointList<3,float> fvdef(vdef);
  for (uint j=0; j<m_secplot.size(); ++j)
    m_secplot[j].updateVertices( fvdef );

  return inside;
}

PathPlotter & MeshPlotter::flightPath(uint idef, Real rbScale)
{
  if (not m_pmx)
    return m_fpplot;

  const Real width = 0.03*norm(m_bbhi - m_bblo);
  m_fpplot.assign(*m_pmx, idef, m_cog, width, rbScale);

  return m_fpplot;
}

void MeshPlotter::undeformedGeometry()
{
  if (not m_pmx)
    return;

  cout << "MeshPlotter::undeformedGeometry()" << endl;

  PointList<3,float> fnodes(m_pmx->nnodes());
  for (uint i=0; i<m_secplot.size(); ++i) {
    m_secplot[i].updateVertices( fnodes );
    m_secplot[i].build();
  }
}

void MeshPlotter::needleField(uint ifield, int mode, float scale)
{
  if (not m_pmx)
    return;

  Indices visNodes;
  for (uint i=0; i<m_secplot.size(); ++i)
    m_secplot[i].visibleNodes(visNodes);

  if ((not visNodes.empty()) and (ifield != NotFound)) {
    if (m_pmx->v2eMap().size() != m_pmx->nnodes())
      m_pmx->fixate();
    m_hhplot.plotField(*m_pmx, ifield, visNodes, mode, scale);
  } else {
    m_hhplot.clear();
  }
}

void MeshPlotter::build(bool dynamicDraw)
{
  for (uint i=0; i<m_secplot.size(); ++i)
    m_secplot[i].build(dynamicDraw);
  m_hhplot.build();
  m_slplot.build(dynamicDraw);
}

void MeshPlotter::draw() const
{
  if (not m_visible)
    return;

  for (uint i=0; i<m_secplot.size(); ++i)
    m_secplot[i].draw();

  m_fpplot.draw();
  m_hhplot.draw();
  m_slplot.draw();
}

uint MeshPlotter::nearestElement(const Vct3f &p) const
{
  if (m_etree.ntriangles() > 0) {
    uint itri = m_etree.nearestTriangle(p);
    if (itri != NotFound)
      return m_etree.globalElement(itri);
    else
      return NotFound;
  } else {
    return NotFound;
  }
}

void MeshPlotter::updateNodeTree()
{
  const int ns = m_secplot.size();

  // build point tree from scratch
  m_visibleNodes.clear();
  for (int i=0; i<ns; ++i)
    m_secplot[i].visibleNodes(m_visibleNodes);

  const int np = m_visibleNodes.size();
  if (np > 0) {
    PointList<3,float> pts(np);
    for (int i=0; i<np; ++i)
      pts[i] = Vct3f( m_pmx->node(m_visibleNodes[i]) );
    uint leafNodeCount = 4;
    if (pts.size() > 8*1024*1024)
      leafNodeCount = 16;
    m_ptree.allocate(pts, false, leafNodeCount);
    m_ptree.sort();
  }
}

void MeshPlotter::updateElementTree()
{
  Wallclock clk;
  clk.start();

  const int ns = m_secplot.size();

  // build element search tree
  size_t ne = 0;
  MxTriTree::SubsetArray sba( ns );
  for (int i=0; i<ns; ++i) {
    sba[i].isection = i;
    m_secplot[i].visibleElements( sba[i].elementList );
    ne += sba[i].elementList.size();
  }

  uint leafElemCount = (ne < 8*1024*1024) ? 4 : 16;
  m_etree = MxTriTree( leafElemCount );
  m_etree.build(*m_pmx, sba);

  clk.stop();
  cout << "updateElementTree: " << clk.elapsed() << endl;
}

bool MeshPlotter::vboSupported()
{
  return GLEW_VERSION_1_5;
}
