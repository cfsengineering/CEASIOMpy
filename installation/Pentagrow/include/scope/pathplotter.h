
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
 
#ifndef SCOPE_PATHPLOTTER_H
#define SCOPE_PATHPLOTTER_H

#include <genua/point.h>
#include <genua/color.h>

/** Draws a flight path.
 *
 */
class PathPlotter
{
public:

  /// create empty plotter, will not display anything
  PathPlotter() : m_idl(NotFound) {
    std::fill(m_vbo, m_vbo+NBuf, NotFound);
  }

  /// release OpenGL resources
  ~PathPlotter();

  /// flight path visibility
  bool visible() const {return m_visible;}

  /// flight path visibility
  void visible(bool flag) {m_visible = flag;}

  /// define geometry to draw
  void assign(const MxMesh &msh, uint idef, const Vct3 &cog,
              Real width, Real scale=1.0);

  /// draw flight path
  void draw() const;

  /// clear out data
  void clear();

private:

  /// compile display list
  void compileList();

private:

  /// indices for vertex buffers
  enum VboIdx {BVtx=0, BNrm=1, NBuf};

  /// vertices and normals for flight path
  PointList<3,float> m_vfpath, m_nfpath;

  /// solid color to use for flight path
  Color m_fpcolor;

  /// display list index
  uint m_idl;

  /// VBO indices
  uint m_vbo[NBuf];

  /// whether the path should be drawn at all
  bool m_visible;
};

#endif // PATHPLOTTER_H
