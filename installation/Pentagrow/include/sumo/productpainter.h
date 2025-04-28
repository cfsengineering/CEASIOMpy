
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
 
#ifndef SUMO_PRODUCTTREEPAINTER_H
#define SUMO_PRODUCTTREEPAINTER_H

#include "cgpainter.h"
#include <genua/transformation.h>
#include <boost/shared_ptr.hpp>
#include <map>

class Product;
class ProductTree;
typedef boost::shared_ptr<ProductTree> ProductTreePtr;

/** Helper used to draw complete product tree.


  */
class ProductPainter
{
public:

  /// empty painter
  ProductPainter();

  /// drawing transform for all nodes
  void transformation(const Trafo3d & tf);

  /// access transformation
  const Trafo3d & transformation() const;

  /// change display setting
  void drawPolygons(bool flag);

  /// change display setting
  void drawLines(bool flag);

  /// rebuild completely from tree
  void init(const Product & prod);

  /// create OpenGL representation
  void build();

  /// draw tree as configured
  void draw() const;

  /// return painter object for surface index
  CgPainterPtr painter(uint key);

  /// extend bounding box to include this mesh
  void boundingBox(Vct3f & lo, Vct3f & hi) const;

private:

  /// assemble instance painter tree
  void buildPainterTree(CgInstancePainterPtr ip, ProductTreePtr pnode);

private:

  typedef std::map<uint, CgPainterPtr> PainterMap;

  /// root node of the product tree
  ProductTreePtr m_root;

  /// stores one mesh renderer per surface object
  PainterMap m_painter;

  /// keep an instance renderer for each product tree node
  CgInstancePainterPtr m_rootpainter;

private:

  /// internal helper functor
  class PainterCreator {
  public:

    /// create functor with map to fill
    PainterCreator(PainterMap & map) : m_map(map), hue(19) {}

    /// called for each part/surface in product
    void operator() (uint key, const CgMeshPtr & cgr) {
      CgPainterPtr cgp(new CgPainter);
      cgp->attach(cgr);
      cgp->polygonColor( Color::hsvColor(hue, 100, 120) );
      // cgp->polygonColor( Color(0.5f, 0.5f, 0.5f) );
      m_map.insert( std::make_pair(key, cgp) );
      hue = (hue + 53) % 360;
    }

  private:

    /// reference to painter map stored in parent object
    PainterMap & m_map;

    /// color rotation
    int hue;
  };

};

#endif // PRODUCTTREEPAINTER_H
