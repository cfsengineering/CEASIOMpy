
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

#ifndef GENUA_SCALARSPLINE_H
#define GENUA_SCALARSPLINE_H

#include "defines.h"
#include "lu.h"
#include "splinebasis.h"

/** Simple cubic spline in one variable.
 *
 * This class provides a compact interface to the general spline interpolation
 * functionality provided by SplineBasis.
 *
 * Uses LAPACK routine DGBSV where available, otherwise the sparse LU solver
 * from the eeigen library.
 *
 * \ingroup utility
 * \sa SplineBasis
 */
template <typename Scalar>
class ScalarSplineTpl
{

public:
  /// undefined spline
  ScalarSplineTpl() : toff(0.0), itrange(1.0) {}

  /// evaluate spline
  Scalar eval(Real t) const
  {
    t = (t - toff) * itrange;
    Vct4 b;
    Scalar v(0.0);
    int span = bas.eval(t, b);
    for (int i = 0; i < 4; ++i)
      v += b[i] * cp[span - 3 + i];
    return v;
  }

  /// derive spline
  Scalar derive(Real t, uint k) const
  {
    assert(k < 4);
    Scalar v(0.0);
    if (k == 0)
    {
      v = eval(t);
    }
    else if (k == 1)
    {
      t = (t - toff) * itrange;
      SMatrix<2, 4> b;
      uint span = bas.derive(t, b);
      for (uint i = 0; i < 4; ++i)
        v += b(1, i) * cp[span - 3 + i];
      v *= itrange;
    }
    else if (k == 2)
    {
      t = (t - toff) * itrange;
      SMatrix<3, 4> b;
      uint span = bas.derive(t, b);
      for (uint i = 0; i < 4; ++i)
        v += b(2, i) * cp[span - 3 + i];
      v *= sq(itrange);
    }
    else if (k == 3)
    {
      t = (t - toff) * itrange;
      SMatrix<4, 4> b;
      uint span = bas.derive(t, b);
      for (uint i = 0; i < 4; ++i)
        v += b(3, i) * cp[span - 3 + i];
      v *= cb(itrange);
    }
    return v;
  }

  /// interpolate points p
  void interpolate(const Vector &u, const DVector<Scalar> &p)
  {
    assert(u.size() == p.size());

    // construct linear system to solve
    const int ku(3), kl(3), n(p.size());

    // normalize parameter values
    toff = u.front();
    itrange = 1.0 / (u.back() - u.front());
    Vector t(u);
    if (toff != 0.0 or itrange != 1.0)
    {
      for (int i = 0; i < n; ++i)
        t[i] = (u[i] - toff) * itrange;
    }

    // setup basis
    bas.init(3, t);

    // setup system of equations
    Vct4 b;
    cp.resize(n);
    DMatrix<Scalar> bcf(2 * kl + ku + 1, n);
    for (int i = 0; i < n; ++i)
    {
      cp[i] = p[i];
      int span = bas.eval(t[i], b);
      for (int j = 0; j < 4; ++j)
      {
        int col = span - 3 + j;
        int row = kl + ku + i - col;
        bcf(row, col) = b[j];
      }
    }

    // solve for control points
    int stat = banded_lu_solve(kl, ku, bcf, cp);
    if (stat != 0)
      throw Error("LU solve failed in ScalarSpline::interpolate().");
  }

private:
  /// cubic spline basis
  SplineBasis bas;

  /// control points
  DVector<Scalar> cp;

  /// parameter value boundaries
  Real toff, itrange;
};

typedef ScalarSplineTpl<Real> ScalarSpline;
typedef ScalarSplineTpl<Complex> CpxSpline;

#endif
