
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
 
#ifndef SCOPE_MESHPLOTTER_H
#define SCOPE_MESHPLOTTER_H

#include "sectionplotter.h"
#include "pathplotter.h"
#include "hedgehogplotter.h"
#include "streamlineplotter.h"
#include <genua/mxelementtree.h>
#include <genua/ndpointtree.h>
#include <boost/shared_ptr.hpp>

/** Mesh display manager.
 *
 * MeshPlotter owns a number of SectionPlotter objects which are responsible
 * for drawing components of the mesh. In addition, it stores node and element
 * search trees which allow efficient mouse-based picking.
 *
 * Note: Must call tree update separately whenever element or node visibility
 * is changed.
 *
 * \sa SectionPlotter, PathPlotter, StreamlinePlotter, HedgehogPlotter
 */
class MeshPlotter
{
public:

  /// undefined plotter
  MeshPlotter();

  /// load a new mesh from file
  MxMeshPtr load(const std::string &fname);

  /// load STL file with merge option
  MxMeshPtr loadStl(const std::string &fname, double featureAngle=rad(44.0),
                    double mergeThreshold=1e-12);

  /// add fields from file to current mesh; return true if possible
  bool addFields(const std::string &fname);

  /// assign a mesh to plot
  void assign(MxMeshPtr pmx);

  /// re-create sections after mesh was changed by third party
  void rebuildSections();

  /// eliminate an entire section
  void eraseSection(uint isec);

  /// add an element group which maps a section
  uint addMappedBoco(uint isec);

  /// eliminate an element group
  void eraseBoco(uint iboco);

  /// access mesh to plot
  MxMeshPtr pmesh() const {return m_pmx;}

  /// access plotter for section k
  SectionPlotter & section(uint k) {
    assert(k < m_secplot.size());
    return m_secplot[k];
  }

  /// access flight path plotter
  PathPlotter & path() {
    return m_fpplot;
  }

  /// access vector field plotter
  HedgehogPlotter & hedgehog() {
    return m_hhplot;
  }

  /// access streamline plotter
  StreamlinePlotter & streamlines() {
    return m_slplot;
  }

  /// whether anything in this mesh can be visible
  bool visible() const {return m_visible;}

  /// show/hide entire mesh
  void visible(bool flag) {m_visible = flag;}

  /// update node search tree
  void updateNodeTree();

  /// update element search tree
  void updateElementTree();

  /// extend bounding box by all visible sections
  void boundingBox(float plo[], float phi[]);

  /// lower corner of current bounding box
  const Vct3f & lowCorner() const {return m_bblo;}

  /// lower corner of current bounding box
  const Vct3f & highCorner() const {return m_bbhi;}

  /// set element visibility in terms of BCs/element groups
  void bocoVisible(uint ibc, bool flag);

  /// check whether boco was marked visible or not
  bool bocoVisible(uint ibc) const {
    assert(ibc < m_bcVisible.size());
    return m_bcVisible[ibc];
  }

  /// set solid colors from sections
  void sectionColors();

  /// set solid colors from bocos
  void bocoColors();

  /// mark volume elements sliced by plane p as visible
  void cutMesh(const Plane &pln);

  /// enable volume elements which (e.g.) fulfill a quality criterion
  void displayVolumeElements(const Indices &gix, bool flag=true);

  /// mark all volume elements as invisible
  void clearVolumeElements();

  /// set center of gravity for flight path display
  void rotCenter(const Vct3 & c) { m_cog = c; }

  /// center of gravity for flight path display
  const Vct3 & rotCenter() const {return m_cog;}

  /// current position of CoG during simulation
  const Vct3 & currentCoG() const {return m_curcog;}

  /// current angle of attack during simulation
  Real currentAlpha() const {return m_curalpha;}

  /// current sideslip angle during simulation
  Real currentBeta() const {return m_curbeta;}

  /// determine color limits from spread factor
  void colorLimits(uint ifield, float &blue, float &red, float spread = 0.0f,
                   int vfm = 0) const;

  /// set vertex colors from field k
  void fieldColors(uint ifield, float blue, float red,
                   int vfm = 0);

  /// prepare for single-mode displacement animation
  void prepareSingleMode(uint ifield, Real scale=1.0);

  /// apply prepared single mode deformation
  void animateSingleMode(Real adisp);

  /// apply deformation to visible nodes, rebuild display
  void deformNodes(uint ifield, Real scale=1.0);

  /// evaluate deformation in modal subspace at (relative) time t
  bool ipolDeformation(uint idef, Real time, Real scale=1.0);

  /// determine node locations at given time for trajectory itj
  bool ipolTrajectory(uint idef, Real time,
                      Real defScale=1.0, Real rbScale=1.0);

  /// enable display of flight path
  PathPlotter & flightPath(uint idef, Real rbScale=1.0);

  /// use nodes of the undeformed geometry
  void undeformedGeometry();

  /// assign vector field for needle display
  void needleField(uint ifield, int mode, float scale);

  /// find index of nearest node
  uint nearestNode(const Vct3f &p) const {
    if (m_ptree.npoints() == m_visibleNodes.size()) {
      uint nn = m_ptree.nearest(p);
      return (nn < m_visibleNodes.size()) ? m_visibleNodes[nn] : NotFound;
    } else
      return NotFound;
  }

  /// find global index of nearest element
  uint nearestElement(const Vct3f &p) const;

  /// pass updated configuration to OpenGL
  void build(bool dynamicDraw = false);

  /// draw all sections
  void draw() const;

  /// whether VBO drawing is in use of not
  static bool vboSupported();

private:

  /// mesh to plot
  MxMeshPtr m_pmx;

  /// section display elements
  SectionPlotterArray m_secplot;

  /// keep track of which bocos were shown/hidden
  std::vector<bool> m_bcVisible;

  /// global indices of nodes visible at the time of search tree construction
  Indices m_visibleNodes;

  /// tree for node location queries
  NDPointTree<3,float> m_ptree;

  /// tree for element location queries
  MxTriTree m_etree;

  /// vector field visualization using hedgehog plot
  HedgehogPlotter m_hhplot;

  /// flight path display (if enabled)
  PathPlotter m_fpplot;

  /// surface streamlines (if enabled)
  StreamlinePlotter m_slplot;

  /// current rigid-body rotation matrix
  Mtx33 m_rbrot;

  /// center of rotation for rigid-body transformations, undeformed coordinates
  Vct3 m_cog;

  /// current position of CoG during trajectory simulation
  Vct3 m_curcog;

  /// bounding box dimensions
  Vct3f m_bblo, m_bbhi;

  /// last deformation factors applied in displaced mesh animation
  Real m_lastDispA, m_lastDispB;

  /// current angle of attack and sideslip angle
  Real m_curalpha, m_curbeta;

  /// allows to hide the entire mesh
  bool m_visible;
};

#endif // MESHPLOTTER_H
