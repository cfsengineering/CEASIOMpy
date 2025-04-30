
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
 
#ifndef GENUA_SPLINEFITTER_H
#define GENUA_SPLINEFITTER_H

#include "defines.h"
#include "forward.h"
#include "point.h"

class SplineFitter
{
public:

  typedef NDArray<3,Real> Array3D;

  /// compute control points cp such that spl.eval(up(i)) = b(i,:)
  template <int ND>
  void fitCubicCurve(const SplineBasis &basis, const Vector &up,
                     const PointList<ND> &b, PointList<ND> &cp) const
  {
    size_t np = b.size();
    Matrix mb, mcp;
    mb.allocate(np, ND);
    for (size_t i=0; i<np; ++i)
      for (int k=0; k<ND; ++k)
        mb(i,k) = b[i][k];
    mcp.allocate(np, ND);
    fitCubicCurve(basis, up, mb, mcp);
    if (cp.size() != np)
      cp.resize(np);
    for (size_t i=0; i<np; ++i)
      for (int k=0; k<ND; ++k)
        cp[i][k] = mcp(i,k);
  }

  /// compute control points cp such that spl.eval(up(i)) = b(i,:)
  void fitCubicCurve(const SplineBasis &basis, const Vector &up,
                     const Vector &b, Vector &cp) const;

  /// compute control points cp such that spl.eval(up(i)) = b(i,:)
  void fitCubicCurve(const SplineBasis &basis, const Vector &up,
                     const Matrix &b, Matrix &cp) const;

  /// compute control points cp such that spl.eval(up(i)) = b(i,:)
  void fitBicubicSurface(const SplineBasis &ubasis, const Vector &up,
                         const SplineBasis &vbasis, const Vector &vp,
                         const Array3D &b, Array3D &cp) const;

};

#endif // SPLINEFITTER_H
