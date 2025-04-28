
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
 
#ifndef SUMO_PRODUCTOVERLAY_H
#define SUMO_PRODUCTOVERLAY_H

#include "productpainter.h"
#include <surf/product.h>

class IgesFile;
class StepFile;
class FrameProjector;

/**
  */
class ProductOverlay
{
public:

  /// empty overlay object
  ProductOverlay() : m_visible(true) {}

  /// access current transformation
  const Trafo3d & currentTrafo() const {return m_painter.transformation();}

  /// toggle drawing of polygons
  void drawPolygons(bool flag) { m_painter.drawPolygons(flag); }

  /// toggle drawing of polygons
  void drawLines(bool flag) { m_painter.drawLines(flag); }

  /// change display transformation
  void applyTrafo(const Trafo3d & tf) {m_painter.transformation(tf);}

  /// move in IGES model to display
  void tesselate(const IgesFile & file);

  /// move in STEP model to display
  void tesselate(const StepFile & file);

  /// import multiple STL files
  void fromSTL(const StringArray & files);

  /// extract surfaces from mesh file
  void fromCGNS(const std::string &fname);

  /// extract surfaces from mesh file
  void fromBmsh(const std::string &bmsh);

  /// extract surfaces from MxMesh
  void fromMx(const MxMesh &mx);

  /// create OpenGL representation
  void build();

  /// issue OpenGL drawing commands
  void draw() const;

  /// extend bounding box (if visible)
  void extendBox(float lo[], float hi[]) const;

  /// visibility
  bool visible() const {return m_visible;}

  /// enable/disable display
  void visible(bool flag) {m_visible = flag;}

  /// (re-) build the frame projector
  void rebuildProjector(FrameProjector & fp) const;

  /// collect all surfaces into a global mesh
  void collectMesh(TriMesh & tm) const;

  /// create XML representation for stored product
  XmlElement toXml(bool share) const {return m_product.toXml(share);}

  /// load product from XML representation
  void fromXml(const XmlElement & xe);

  /// clear out all data
  void clear();

private:

  /// product imported from STL, IGES, STEP
  Product m_product;

  /// drawing object
  ProductPainter m_painter;

  /// global visibility flag
  bool m_visible;
};

#endif // PRODUCTOVERLAY_H
