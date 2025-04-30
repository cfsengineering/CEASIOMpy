
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
 
#ifndef DCPLANEGEOMETRY_H
#define DCPLANEGEOMETRY_H

#include "dcgeometry.h"
#include <genua/point.h>

/** Plane geometry for use with DelaunayCore
 *
 * The simplest form of geometry representation is defined in a plane only.
 *
 * \ingroup meshgen
 * \sa DelaunayCore
 */
class DcPlaneGeometry : public DcGeometry
{
public:

  /// empty geometry for fixed coordinate range
  DcPlaneGeometry(Real qmin, Real qmax) : DcGeometry(qmin, qmax) {}

  /// sort points in polar order with respect to edge pe
  void sortPolar(const DcEdge *pe, Indices & c) const;

  /// compute circumcenter of triangle vi
  Vct2 circumCenter(const uint *vi) const {
    return circumCenter(m_st, vi);
  }

  /// compute circumcenter of triangle vi
  static Vct2 circumCenter(const PointList<2> &pts, const uint *vi);

private:

};

#endif // DCPLANEGEOMETRY_H
