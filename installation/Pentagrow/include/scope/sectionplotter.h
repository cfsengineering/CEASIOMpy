
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
 
#ifndef SCOPE_SECTIONPLOTTER_H
#define SCOPE_SECTIONPLOTTER_H

#include "forward.h"
#include "plotprimitives.h"
#include "hedgehogplotter.h"
#include <genua/cgmesh.h>

/** Object responsible for drawing one mesh section.
 *
 * SectionPlotter encapsulates the OpenGL display functionility for a single
 * mesh section. Both node-based indexed elements and isolated elements
 * (for visualization of element groups and element-based properties) are
 * supported.
 *
 * \sa PlotController, MeshPlotter
 */
class SectionPlotter : public CgMesh
{
public:

  struct ElementColor {
    ElementColor() : color(0.5f, 0.5f, 0.5f, 1.0f), gelix(0) {}
    Color color;
    uint gelix;
    bool operator< (const ElementColor &a) const {return gelix < a.gelix;}
    bool operator< (uint a) const {return gelix < a;}
    bool operator== (const ElementColor &a) const {return gelix == a.gelix;}
    bool operator== (uint a) const {return gelix == a;}
  };

  typedef std::vector<ElementColor> ElementColorArray;

  /// up to this element count, volume element sections are processed fully
  const static size_t maxShowVolElements = 1024*1024;

  /// undefined plotter
  SectionPlotter();

  /// deallocate GL resources
  ~SectionPlotter();

  /// build buffers or display lists
  void assign(MxMeshPtr pmx, uint isec);

  /// change section index only (needed to allow to erase sections)
  void index(uint isec) {m_isec = isec;}

  /// compile display lists or transfer vertex buffers
  void build(bool dynamicDraw = false);

  /// draw using OpenGL
  void draw() const;

  /// visibility flag
  bool showEdges() const {return m_showEdges;}

  /// make edges visible
  void showEdges(bool flag);

  /// visibility flag
  bool showElements() const {return m_showElements;}

  /// make all elements visible
  void showElements(bool flag);

  /// mark global elements in subset as visible (call build when true returned)
  bool showElements(const Indices & gix, bool flag);

  /// normal visibility flag
  bool showNormals() const {return m_showNormals;}

  /// set normal visibility
  void showNormals(bool flag);

  /// mark all elements as (in-)visible, individually
  void markAllElements(bool flag);

  /// mark elements sliced by plane as visible
  bool cutVolumeElements(const std::vector<bool> & nodesBelowPlane);

  /// make the entire section visible
  void visible(bool flag) {
    showElements(flag);
    showEdges(flag);
  }

  /// test if either elements or edges are visible
  bool visible() const {
    return (showEdges() or showElements());
  }

  /// toggle visibility
  void toggleVisible() {
    bool vis = m_showEdges or m_showElements;
    visible(not vis);
  }

  /// number of triangles drawn
  size_t nVisibleTriangles() const {
    return m_showElements ? CgMesh::ntriangles() : 0;
  }

  /// number of edges drawn
  size_t nVisibleEdges() const {
    return m_showEdges ? (m_edges.size() / 2) : 0;
  }

  /// set a solid color for all vertices
  void solidColor(const Color &c);

  /// update vertex color array from field
  void updateColors(const MxMeshField &field, float blueLimit, float redLimit);

  /// update vertex color array from condensed field
  void updateColors(const DVector<float> &cf, float blueLimit, float redLimit);

  /// set element-wise colors
  bool updateColors(const ElementColorArray &ecl);

  /// reset vertex positions to undeformed configuration
  void resetUndeformed();

  /// fetch mesh vertices (needed for animated deformation)
  void updateVertices(const PointList<3,float> &pts);

  /// set deformation basis for single mode deformation from global field
  void setDeformationBasis(uint ifield, float scale);

  /// set deformation basis for two-mode deformation from global fields
  void setDeformationBasis(const PointList<3,float> &gadef,
                           const PointList<3,float> &gbdef);

  /// deform current vertex set by single stored local deformation basis
  void basisDeform(float dxa);

  /// deform current vertex set by two stored local deformation basis
  void basisDeform(float dxa, float dxb);

  /// accumulate visible vertices in set
  void visibleNodes(Indices & idx) const;

  /// list of local element indices which are actually visible
  void visibleElements(Indices &idx) const;

  /// clear mesh and index sets
  void clear();

private:

  /// assemble set of triangles from surface/line element sections
  //void assignSurface();

  /// assemble set of triangles from volume element sections
  //void assignVolume();

  /// mark volume elements which share boundary nodes
  void markBoundaryVolumes();

  /// fill arrays of plot primitives and sort
  void gatherPrimitives(bool useMask = false);

  /// extract the set of triangles and edges to draw and map to local vertices
  void mapVisible(bool shareVertices = true);

  /// decompose volume elements into triangles
  int triangleMap(int map[]) const;

  /// draw triangle and line primitives
  void drawElements();

  /// draw element edges
  void drawEdges();

  /// compile display lists
  void compileLists();

  /// copy buffers to GPU
  void transferBuffers(bool dynamicDraw = false);

  /// update just the buffer of deformed vertices
  void transferDisplaced();

  /// render used current vertex buffer objects
  void renderBuffers() const;

  /// swap buffers for vertices and deformed vertices
  void swapDisplacedVertexBuffer() {
    std::swap(m_vbo[BVtx], m_vbo[BDef]);
  }

private:

  /// indices for vertex buffers
  enum VboIdx {BVtx=0, BNrm=1, BClr=2, BTri=3, BEdg=4, BLns=5, BDef=6, NBuf};

  /// type of elements in this section
  enum SectionCategory {LineElements, SurfaceElements, VolumeElements};

  /// associated mesh
  MxMeshPtr m_pmx;

  /// triangles to draw for all section elements
  PlotTriangleArray m_ptri;

  /// edges to draw for all elements
  PlotEdgeArray m_pedg;

  /// plotter for normal vectors (if requested)
  HedgehogPlotter m_hhp;

  /// local vertex arrays used for mesh deformation
  PointList<3,float> m_vdefa, m_vdefb;

  /// indices of local vertex indices in global mesh set
  Indices m_gnix;

  /// indices of global elements belonging to triangles
  Indices m_gelix;

  /// flags which indicate which local elements to display
  std::vector<bool> m_useElement;

  /// vertex indices for element edges
  Indices m_edges;

  /// element category
  SectionCategory m_cat;

  /// section index
  uint m_isec;

  /// index of first display list, used if VBO rendering not supported
  uint m_idl;

  /// VBO object handles
  uint m_vbo[NBuf];

  /// display flags
  bool m_showElements, m_showEdges, m_showNormals;

  /// indicates whether triangles where split for element-wise coloring
  bool m_splitElements;

  /// set to true once gatherPrimitives has been called
  bool m_havePrimitives;

  /// true one BDef buffer allocated
  bool m_bdefAllocated;

  /// fixed colors for edges
  static Color s_edgeColor;

  /// color for line elements
  static Color s_lineColor;
};

typedef std::vector<SectionPlotter> SectionPlotterArray;

inline bool operator< (uint a , const SectionPlotter::ElementColor &b)
{
  return a < b.gelix;
}

//inline bool operator< (const SectionPlotter::ElementColor &a, uint b)
//{
//  return a.gelix < b;
//}

inline bool operator== (uint a , const SectionPlotter::ElementColor &b)
{
  return a == b.gelix;
}

//inline bool operator== (const SectionPlotter::ElementColor &a, uint b)
//{
//  return a.gelix == b;
//}

#endif // SECTIONPLOTTER_H
