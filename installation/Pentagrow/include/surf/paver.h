
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
 

#ifndef SURF_PAVER_H
#define SURF_PAVER_H

#include <genua/point.h>
#include "surface.h"

/** Generates a triangular mesh by rows.
 *
 * \ingroup meshgen
 * \sa InitMesh, CascadeMesh
 */
class Paver
{
  public:

    /// create a paver for surface s
    Paver(const Surface & s) : srf(s), loffset(0), hoffset(0) {}

    /// append a single row of vertices, mesh
    void nextRow(const PointList<2> & row);

    /// append a single row of vertices, mesh
    void nextVRow(Real v, const Vector & up);

    /// generate a fan as the last row
    void fan(const Vct2 & ctr);

    /// access result
    const PointList<2> & vertices() const {return ppt;}

    /// access result
    const Indices & triangles() const {return itriangles;}

    /// convenience interface
    void exportMesh(TriMesh &msh);

    /// clear stored mesh
    void clear() {ppt.clear(); itriangles.clear();}

  private:

    /// compute tangent to paving front
    bool pickLow(uint ilo, uint ihi) const;

    /// evaluate parameter space vertex
    Vct3 eval(uint k) const {
      return srf.eval(ppt[k][0], ppt[k][1]);
    }

  private:

    /// surface to pave
    const Surface & srf;

    /// parameter space points
    PointList<2> ppt;

    /// triangle indices into ppt
    Indices itriangles;

    /// offset pointer
    uint loffset, hoffset;
};

#endif // PAVER_H
