
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
 
#ifndef SCOPE_HEDGEHOGPLOTTER_H
#define SCOPE_HEDGEHOGPLOTTER_H

#include "forward.h"
#include <genua/point.h>
#include <genua/color.h>

/** Display vector data as a collection of simple lines.
 *
 * \sa PlotController
 */
class HedgehogPlotter
{
public:

  enum LineScaling { EqualLength, ByMagnitude, LocalLength };

  /// empty plotter
  HedgehogPlotter() : m_lineColor(0.0f, 0.3f, 1.0f),
    m_idl(NotFound), m_vbo(NotFound) {}

  /// release OpenGL resources
  ~HedgehogPlotter();

  /// compute nodal length scales
  void nodalLengths(const MxMesh &mx, const Indices &nodeList);

  /// assign a vector field (accumulative)
  void plotField(const MxMesh &mx, uint ifield, const Indices &nodeList,
                 int scaling = EqualLength, float scaleFactor = 1.0f);

  /// draw normal vectors for surface element section (accumulative)
  void plotNormals(const MxMesh &mx, uint isection);

  /// number of lines currently sheduled to be drawn
  uint nlines() const {return (m_vtx.size()/2);}

  /// setup drawing buffers
  void build(bool dynamicDraw = false);

  /// issue OpenGL drawing commands
  void draw() const;

  /// clear plot
  void clear();

private:

  /// line points
  PointList<3,float> m_vtx;

  /// local (nodal) length scale
  DVector<float> m_nodalLength;

  /// color to use for line display
  Color m_lineColor;

  /// display list index (if applicable)
  uint m_idl;

  /// vertex buffer index (if applicable)
  uint m_vbo;
};

#endif // HEDGEHOGPLOTTER_H
