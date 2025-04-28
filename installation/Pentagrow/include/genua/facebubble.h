
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
 
#ifndef GENUA_FACEBUBBLE_H
#define GENUA_FACEBUBBLE_H

#include "edgecurve.h"

/** Cap surface.

  This class defines a bicubic interpolation surface over a triangular face.
  It requires (on creation time) that the Triangulation belonging to the
  face passed as constructor exists and defines vertex normals in a meaningfull
  manner. The interpolation surface which then can be evaluated by
  FaceBubble::eval() in the usual area coordinates $(xi,eta)$ interpolates
  triangle vertices and vertex normals exactly. Cap surfaces over two
  neighbouring faces will meet in their common edge curve. However, the
  surface derivative across edge curves may not be continuous.

  FaceBubbles are used by mesh adaption algorithms to approximate points
  between mesh vertices. FaceBubble objects are sized at 144 bytes;
  The surface evaluation member function should have acceptable speed
  (optimized).

  \deprecated

  \ingroup mesh
  \sa Triangulation
  */
class FaceBubble
{
  public:
  
    /// construct over given face of triangulation srf
    FaceBubble(const Face & f);
    
    /// evaluate surface at triangle coordinates (u,v)
    Vct3 eval(Real xi, Real eta) const;
  
  private:

    /// vertex and normal coordinates
    Vct3 pt1, pt2, pt3, vn1, vn2, vn3;
};

#endif

