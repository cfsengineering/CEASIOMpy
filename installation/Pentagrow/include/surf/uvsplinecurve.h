
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
 
#ifndef SURF_UVSPLINECURVE_H
#define SURF_UVSPLINECURVE_H

#include "forward.h"
#include "abstractuvcurve.h"
#include <genua/splinebasis.h>
#include <genua/lu.h>
#include <genua/xcept.h>

/** Parameter-space spline curve with compile-time degree.
 *
 * A template class used for the implementation of linear and cubic
 * parameter space curves.
 *
 * \ingroup geometry
 * \sa UvPolyline, UvCubicCurve
 */
template <int P>
class UvSplineCurve : public AbstractUvCurve
{
public:

  /// forwarding initialization
  UvSplineCurve(SurfacePtr psf = SurfacePtr())
    : AbstractUvCurve(psf), m_evalReverse(false) {}

  /// contruct so that points are interpolated exactly
  const Vector & interpolate(const PointList<2> &pts)
  {
    assert(pts.size() > P);

    // generate arclength parametrization
    const int np = pts.size();
    m_ipp.resize(np);
    for (int i=1; i<np; ++i)
      m_ipp[i] = m_ipp[i-1] + norm(pts[i] - pts[i-1]);
    m_ipp /= m_ipp.back();
    m_ipp.front() = 0.0;
    m_ipp.back() = 1.0;
    this->interpolate(m_ipp, pts);
    return m_ipp;
  }

  /// contruct so that points are interpolated exactly
  const Vector & interpolate(const Vector &u, const PointList<2> &pts)
  {
    assert(pts.size() > P);
    assert(u.size() == pts.size());
    m_ipp = u;
    m_basis.init(P, m_ipp);

    // bandwidth
    const int np = pts.size();
    const int ku(P), kl(P);

    // setup system of equations
    SVector<P+1> b;
    Matrix bcf(2*kl+ku+1, np), rm(np, 2);
    for (int i=0; i<np; i++) {
      rm(i,0) = pts[i][0];
      rm(i,1) = pts[i][1];
      int span = m_basis.eval(m_ipp[i], b);
      for (int j=0; j<P+1; j++) {
        int col = span-P+j;
        int row = kl+ku+i-col;
        bcf(row, col) = b[j];
      }
    }

    // solve for new control points
    int stat = banded_lu_solve(kl, ku, bcf, rm);
    if (stat != 0)
      throw Error("Lapack: LU solve failed in "
                  "UvSplineCurve::interpolate(), INFO = "+str(stat));

    m_uvc.resize(np);
    for (int i=0; i<np; ++i)
      m_uvc[i] = Vct2( rm(i,0), rm(i,1) );
    return m_ipp;
  }

  /// reverse direction
  void reverse() {
    m_evalReverse = (not m_evalReverse);
  }

  /// evaluate in (u,v) space
  Vct2 uveval(Real tp) const {
    SVector<P+1> b;
    Vct2 q;
    Real t = m_evalReverse ? (1.0 - tp) : tp;
    uint span = m_basis.eval(t, b);
    for (uint i=0; i<P+1; ++i)
      q += b[i] * m_uvc[ span-P+i ];
    q[0] = clamp(q[0], 0.0, 1.0);
    q[1] = clamp(q[1], 0.0, 1.0);
    return q;
  }

  /// evaluate derivative in (u,v) space
  Vct2 uvderive(Real tp, uint k) const {
    Vct2 qd;
    Matrix fu(k+1, P+1);
    Real t = m_evalReverse ? (1.0 - tp) : tp;
    Real sgn = m_evalReverse ? -1.0 : 1.0;
    uint span = m_basis.derive(t, k, fu);
    for (uint i=0; i<P+1; ++i)
      qd += sgn * fu(k,i) * m_uvc[ span-P+i ];
    return qd;
  }

  /// evaluate point and first derivative in (u,v) space
  void uvtgline(Real tp, Vct2 &q, Vct2 &dq) const {
    SMatrix<2,P+1> b;
    Real t = m_evalReverse ? (1.0 - tp) : tp;
    Real sgn = m_evalReverse ? -1.0 : 1.0;
    uint span = m_basis.derive(t, b);
    q = 0.0;
    dq = 0.0;
    for (uint i=0; i<P+1; ++i) {
      const Vct2 & cp( m_uvc[ span-P+i ] );
      q += b(0,i) * cp;
      dq += sgn * b(1,i) * cp;
    }
    q[0] = clamp(q[0], 0.0, 1.0);
    q[1] = clamp(q[1], 0.0, 1.0);
  }

protected:

  /// split curve at u, assign right/high part to chi
  void splitSpline(Real u, UvSplineCurve<P> &chi) {
    m_basis.split(u, m_uvc, chi.m_basis, chi.m_uvc);
  }

protected:

  /// spline basis
  SplineBasis m_basis;

  /// control points in (u,v) space
  PointList<2> m_uvc;

  /// parameterization of the interpolated points
  Vector m_ipp;

  /// direction flag
  bool m_evalReverse;
};

#endif // UVSPLINECURVE_H
