
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
 
#ifndef SUMO_CGMESHPAINTER_H
#define SUMO_CGMESHPAINTER_H

#include "forward.h"
#include <genua/transformation.h>
#include <genua/color.h>

/** Helper object to draw CgMesh object.

  CgPainter implements OpenGL drawing for CgMesh objects. It allows to define
  a single solid color for the entire surface and one for feature lines. Lines
  and polygons can be drawn selectively.

  \sa CgInstancePainter
  */
class CgPainter
{
public:

  /// create empty painter
  CgPainter();

  /// destroy buffers
  ~CgPainter();

  /// initialize once OpenGL has been initialized
  void init();

  /// change polygon color
  void polygonColor(const Color & c) {m_pgcolor = c;}

  /// change line color
  void lineColor(const Color & c) {m_lncolor = c;}

  /// toggle drawing of triangles
  void drawPolygons(bool flag) {m_drawpg = flag;}

  /// toggle drawing of lines
  void drawLines(bool flag) {m_drawln = flag;}

  /// assign mesh to draw
  void attach(CgMeshPtr cgr);

  /// build OpenGL representation
  void build();

  /// issue OpenGL drawing commands
  void draw() const;

  /// extend bounding box to include this mesh
  void boundingBox(const Mtx44f & m, Vct3f & lo, Vct3f & hi) const;

private:

  /// generate display list
  void compileList();

  /// move vertex buffer contents to GPU
  void copyBuffers();

private:

  /// mesh to paint
  CgMeshPtr m_cgr;

  /// colors to use for all triangles, lines
  Color m_pgcolor, m_lncolor;

  /// number of triangle and line vertices
  uint m_ntrivx, m_nlinevx;

  /// buffers and lists
  uint m_vbo[4], m_idl;

  /// whether to draw polygons and lines
  bool m_drawpg, m_drawln;
};

/** Helper class to support instancing.

  CgInstancePainter keeps a reference to a mesh painter along with a
  transformation matrix. The purpose is to support drawing instanced geometry
  as represented by a Product class object (libsurf).

  \sa CgPainter
  */
class CgInstancePainter
{
public:

  /// create instance from mesh painter and node
  CgInstancePainter(CgPainterPtr painter, ProductTreePtr pnode)
    : m_node(pnode), m_painter(painter) {}

  /// add child node
  void appendChild(CgInstancePainterPtr cgp);

  /// number of child node painters
  uint nchildren() const {return m_siblings.size();}

  /// execute drawing commands
  void draw() const;

  /// determine bounding box considering transformation
  void boundingBox(const Mtx44f & dtf, Vct3f & lo, Vct3f & hi) const;

  /// delete siblings, reset everything
  void clear();

private:

  /// product node
  ProductTreePtr m_node;

  /// pointer to mesh painter
  CgPainterPtr m_painter;

  /// child nodes draw under dependent transformation
  CgInstancePainterArray m_siblings;
};

#endif // CGMESHPAINTER_H
