
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
 
#ifndef GENUA_CGMESH_H
#define GENUA_CGMESH_H

#include "forward.h"
#include "cgstrip.h"
#include "xmlelement.h"
#include "smatrix.h"
#include "point.h"
#include "color.h"

class TriMesh;

/** Mesh container for visualization.

  CgMesh stores a triangle mesh in a format suitable for efficient
  rendering using OpenGL. It is much less useful for anything else.

  Compared to MxMesh and TriMesh, this class uses single-precision floating
  point data in order to save space.

  \todo Rewrite the color handling stuff for 3DXML import.

  \ingroup geometry
  \sa CgStrip, Color
  */
class CgMesh
{
public:

  enum CheckStatus { Valid = 0, RefInvalidVertex = 1, RefInvalidNormal = 2 };

  /// empty mesh
  CgMesh() : m_tristrips(true), m_trifans(true), m_lnstrips(false), m_itag(0) {}

  /// common case: transfer ownership from vertex and index sets
  CgMesh(PointList3f &&points, Indices &&tris)
    : m_vtx( std::move(points) ), m_triangles( std::move(tris) ) {}

  /// common case: transfer ownership from vertex and index sets
  CgMesh(PointList3f &&points, Indices &&tris, Indices &&lns)
    : m_vtx( std::move(points) ), m_triangles( std::move(tris) ),
      m_lines( std::move(lns) ) {}

  /// virtual destructor
  virtual ~CgMesh() {}

  /// change id tag
  void tag(int t) {m_itag = t;}

  /// retrieve id tag
  int tag() const {return m_itag;}

  /// total number of triangles to render
  uint ntriangles() const;

  /// vertex indices of triangle i of non-stripped triangles
  const uint *triVertices(uint i) const {
    assert(3*i+2 < m_triangles.size());
    return &m_triangles[3*i];
  }

  /// number of lines to render
  uint nlines() const;

  /// access vertices
  const PointList<3,float> & vertices() const {return m_vtx;}

  /// access vertices; note that changing indexing will invalidate elements
  PointList<3,float> & vertices() {return m_vtx;}

  /// access normals
  const PointList<3,float> & normals() const {return m_nrm;}

  /// access normals
  PointList<3,float> & normals() {return m_nrm;}

  /// access normals
  const ColorArray & colors() const {return m_vtxcol;}

  /// access normals
  ColorArray & colors() {return m_vtxcol;}

  /// access triangles stored as elements (not strips)
  const Indices &triangles() const {return m_triangles;}

  /// access triangles stored as elements (not strips)
  Indices &triangles() {return m_triangles;}

  /// access lines stored as elements (not strips)
  const Indices &lines() const {return m_lines;}

  /// access lines stored as elements (not strips)
  Indices &lines() {return m_lines;}

  /// access single vertex
  const Vct3f & vertex(uint vix) const {return m_vtx[vix];}

  /// access single normal
  const Vct3f & normal(uint vix) const {return m_nrm[vix];}

  /// append vertex and normal, return index
  uint append(const Vct3f &v, const Vct3f &n) {
    m_vtx.push_back(v);
    m_nrm.push_back(n);
    return m_vtx.size()-1;
  }

  /// append vertex, normal, and color return index
  uint append(const Vct3f &v, const Vct3f &n, const Color &c) {
    m_vtx.push_back(v);
    m_nrm.push_back(n);
    m_vtxcol.push_back(c);
    return m_vtx.size()-1;
  }

  /// access color for one vertex
  const Color & color(uint vix) const {
    assert(vix < m_vtxcol.size());
    return m_vtxcol[vix];
  }

  /// set color for one vertex
  Color & color(uint vix) {
    assert(vix < m_vtxcol.size());
    return m_vtxcol[vix];
  }

  /// make color array match vertex array size and set default
  void fitColorBuffer(const Color & dfc);

  /// transform coordinates explicitly
  void transform(const SMatrix<4,4,float> & t);

  /// extend bounding box to include this mesh
  void boundingBox(float plo[], float phi[]) const;

  /// compute mean edge length 
  float meanEdgeLength() const;

  /// compute mean triangle area
  float meanTriangleArea() const;

  /// import triangle mesh with nv 3D vertices and normals and nt triangles
  template <class FloatType, class IntType>
  void importMesh(int nv, const FloatType *pvtx, const FloatType *pnrm,
                  int nt, const IntType *ptri)
  {
    clearMesh();
    if (nv <= 0 or nt <= 0)
      return;
    m_vtx.resize(nv);
    std::copy(pvtx, pvtx+3*nv, m_vtx.pointer());
    m_triangles.resize(3*nt);
    std::copy(ptri, ptri+3*nt, m_triangles.begin());
    if (pnrm != 0) {
      m_nrm.resize(nv);
      std::copy(pnrm, pnrm+3*nv, m_nrm.pointer());
    } else {
      estimateNormals();
    }
  }

  /// import triangle mesh
  template <class FloatType, class IntType>
  void importMesh(const PointList<3,FloatType> &vtx,
                  const PointList<3,FloatType> &nrm,
                  const std::vector<IntType> &tri)
  {
    int ntri = tri.size()/3;
    if (nrm.size() == vtx.size())
      importMesh(vtx.size(), vtx.pointer(), nrm.pointer(), ntri, &tri[0]);
    else
      importMesh(vtx.size(), vtx.pointer(), (const FloatType *) 0,
                 ntri, &tri[0]);
  }

  /// import from TriMesh (does not compute strips)
  void importMesh(const TriMesh & tm);

  /// export to TriMesh
  void exportMesh(TriMesh & tm) const;

  /// reserve space for known number of vertices and primitives
  void reserve(size_t nvert, size_t ntriangles, size_t nlines) {
    m_vtx.reserve(nvert);
    m_nrm.reserve(nvert);
    m_triangles.reserve(3*ntriangles);
    m_lines.reserve(2*nlines);
  }

  /// merge in another CgMesh
  void merge(const CgMesh & msub);

  /// merge in another CgMesh while applying transformation
  void merge(const CgMesh & msub, const Mtx44f & tsub);

  /// merge with multiple other meshes, do not use normals and lines
  void mergeTriangles(size_t nm, const PointList3f mv[], const Indices mt[]);

  /// merge with other mesh, do not use normals and lines
  void mergeTriangles(const CgMesh &msub);

  /// append a single vertex (best to reserve() first)
  template <typename VertexType>
  size_t appendVertex(const VertexType &v) {
    m_vtx.push_back( Vct3f(v) );
    return m_vtx.size()-1;
  }

  /// append a number of triangles
  void appendTriangles(const Indices &tri) {
    m_triangles.insert(m_triangles.end(), tri.begin(), tri.end());
  }

  /// replace triangles
  void replaceTriangles(const Indices &tri) {
    m_triangles = tri;
  }

  /** Generate a triangle fan to draw a circle with radius r
        centered at ctr and normal to cn, approximated with nt triangles */
  void appendCircle(const Vct3f & ctr, const Vct3f & cn,
                    float r, int nt=16);

  /** Generate lines to draw a coordinate-aligned cross centered
      at ctr and with edge lengths s */
  void appendCross(const Vct3f & ctr, float s);

  /// append a single line segment
  void appendLine(const Vct3f & p1, const Vct3f & p2);

  /// append a single polyline
  void appendLine(const PointList<3,float> & pts);

  /// append a single line segment, indexed into vertex buffer
  void appendLine(uint a, uint b) {
    m_lines.push_back(a);
    m_lines.push_back(b);
  }

  /// append multiple line segments (not a polyline!)
  void appendLines(const Indices & lns) {
    m_lines.insert(m_lines.end(), lns.begin(), lns.end());
  }

  /// append multiple line segments (not a polyline!)
  void appendLines(const PointList<3,float> & pts);

  /// remove a range of line elements
  void removeLines(size_t lbegin, size_t lend);

  /// convert everything to indexed triangles
  void toTriangles(Indices & tri) const;

  /// convert all line elements to simple indexed lines
  void toLines(Indices & lns) const;

  /// expand strips and fans to plain triangles
  void expandStrips();

  /// draw each triangle separately with its own normal
  void splitTriangles();

  /// extract lines that do not reference triangle vertices
  void freeLines(PointList3f &plines) const;

  /// apply a new vertex order to lines and triangles
  void reorderElements(const Indices &perm);

  /// remove unreferenced vertices (expands strips as well)
  uint dropUnusedVertices(Indices *pvm = 0);

  /// split mesh to identify sharp edges (merges vertices as well)
  void detectEdges(float mergeTol, float minAngle);

  /// drop ill-defined triangles with zero area after node merging
  void dropInvalidTriangles(float mergetol);

  /// split each triangle into 4 new ones by inserting mid-edge nodes
  void quadRefine();

  /// flip triangles to achieve a consistent normal orientation
  void repairNormals();

  /// determine area center from triangles
  Vct3f areaCenter() const;

  /// check whether elements references invalid vertices or normals
  int checkValidity() const;

  /// size in memory (for information only)
  float megabytes() const;

  /// clear mesh
  void clearMesh();

  /// swap contents
  void swap(CgMesh & a) {
    m_vtx.swap(a.m_vtx);
    m_nrm.swap(a.m_nrm);
    m_lvx.swap(a.m_lvx);
    m_tristrips.swap(a.m_tristrips);
    m_trifans.swap(a.m_trifans);
    m_lnstrips.swap(a.m_lnstrips);
    m_triangles.swap(a.m_triangles);
    m_lines.swap(a.m_lines);
    m_vtxcol.swap(a.m_vtxcol);
    std::swap(m_itag, a.m_itag);
  }

  /// import vertex colors from 3dxml?
  static void importColor(bool flag) {
    s_sigcolormode = flag ? CgMesh::ImportColor : CgMesh::IgnoreColor;
  }

  /// exclude faces of specified color when reading 3dxml
  static void excludeColor(const Color & c) {
    s_sigcolor = c;
    s_sigcolormode = CgMesh::ExcludeSigColor;
  }

  /// include faces of specified color when reading 3dxml
  static void includeColor(const Color & c) {
    s_sigcolor = c;
    s_sigcolormode = CgMesh::IncludeSigColor;
  }

  /// ignore colors (default)
  static void ignoreColor() {
    s_sigcolormode = CgMesh::IgnoreColor;
  }

  /// xml representation
  virtual XmlElement toXml(bool share = false) const;

  /// retrieve from xml representation
  virtual void fromXml(const XmlElement & xe);

protected:

  /// import 3DXML node 'PolygonalRepType'
  void importNode3Dxml(const XmlElement & xe);

  /// determine whether to read face node at all (based on signal color)
  bool testColorNode3Dxml(const XmlElement & xe, Color & faceCol) const;

  /// import all polygonal components of a whole 3DRep file
  void importFile3Dxml(const XmlElement & xe);

  /// distribute face color to affected vertices
  void setVertexColor(const Color & fc, const Indices & idx);
  
  /// estimate normal vectors from triangle vertices
  void estimateNormals();

protected:

  enum ColorImportMode {IgnoreColor, ImportColor,
                        ExcludeSigColor, IncludeSigColor} ;

  /// vertices and normals, polyline vertices
  PointList<3,float> m_vtx, m_nrm, m_lvx;

  /// triangle strips and fans
  CgStrip m_tristrips, m_trifans;

  /// line strips offset pointer
  CgStrip m_lnstrips;

  /// plain triangles and lines indexed into vtx
  Indices m_triangles, m_lines;

  /// vertex colors
  ColorArray m_vtxcol;

  /// integer id
  int m_itag;

  /// color which indicates that surface is to be excluded/included
  static Color s_sigcolor;

  /// signal color excluded or included?
  static ColorImportMode s_sigcolormode;
};

#endif

