
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
 
#ifndef SURF_UVMAPPING_H
#define SURF_UVMAPPING_H

#include "forward.h"
#include <genua/splinebasis.h>
#include <genua/dmatrix.h>
#include <genua/smallqr.h>


/** Parameter-space mapping.

  UvMapping builds a transformation from surface parameter space (u,v) to a new
  space (s,t). The aim of the transformation is that a triangle which is
  well-spaed (in terms of edge-to-circumradius or angles) in (s,t) space is
  also well-shaped in the 3D space (x,y,z) <- S(u,v).

  \ingroup meshgen
  \sa UvMapDelaunay, DelaunayCore
*/
class UvMapping
{
public:

  /// undefined mapping
  UvMapping() {}

  /// initialized mapping
  UvMapping(const Surface & srf, const Vector & up, const Vector & vp);

  /// construct mapping for surface srf avaluated at given parameter grid
  void init(const Surface & srf, const Vector & up, const Vector & vp);

  /// determine min/max boundaries for t
  void boundaries(Real & tmin, Real & tmax) const;

  /// check whether mapping is initialized
  bool empty() const {return (m_ctp.size() == 0);}

  /// dump mapping to file (debugging)
  void dump(const std::string &fname) const;

  /// evaluate mapping t <- (u,v) while implicitly, s <- u
  Real eval(Real u, Real v) const {
    SVector<SDEG+1> bu, bv;
    const int uspan = m_ubas.eval(u, bu);
    const int vspan = m_vbas.eval(v, bv);
    Real t = 0.0;
    for (int i=0; i<SDEG+1; ++i)
      for (int j=0; j<SDEG+1; ++j)
        t += bu[i] * bv[j] * m_ctp( uspan+i-SDEG, vspan+j-SDEG );
    return t;
  }

  /// convenience interface
  Vct2 eval(const Vct2 & uv) const {
    Real s = uv[0];
    Real t = eval(uv[0], uv[1]);
    return Vct2(s, t);
  }

  /// evaluate derivatives of mapping t <- (u,v)
  Vct2 gradient(Real u, Real v) const {
    SMatrix<2,SDEG+1> bu, bv;
    const int uspan = m_ubas.derive(u, bu);
    const int vspan = m_vbas.derive(v, bv);
    Real tu(0.0), tv(0.0);
    for (int i=0; i<SDEG+1; ++i) {
      for (int j=0; j<SDEG+1; ++j) {
        Real c = m_ctp( uspan+i-SDEG, vspan+j-SDEG );
        tu += bu(1,i) * bv(0,j) * c;
        tv += bu(0,i) * bv(1,j) * c;
      }
    }
    return Vct2(tu,tv);
  }

  /// solve for step in uv for a given change in st
  Vct2 uvStep(const Vct2 & uv, const Vct2 & dst) const {
    Vct2 duv, g = gradient(uv[0], uv[1]);
    duv[0] = dst[0];
    duv[1] = (dst[1] - duv[0]*g[0]) / g[1];
    return duv;
  }

  /// compute (u,v) for known (s,t) without initial guess
  Vct2 invert(const Vct2 & st, Real tol = 1e-9) const;

  /// obtain an initial guess for the inverse mapping (s,t) -> (u,v)
  Vct2 lookup(const Vct2 &st) const;

  /// compute (u,v) for known (s,t) starting from a initial guess
  bool invert(const Vct2 & st, Vct2 & uv, Real tol = 1e-9) const;

  /// compute the mapping criteria from surface derivatives
  template <int ND>
  static Vct2 mappingCriteria(const SVector<ND> &Su, const SVector<ND> &Sv) {
    Real squ = sq(Su);
    Real sqv = sq(Sv);
    Real c1 = sqv / squ;  assert(c1 > 0);
    Real t1 = dot(Su,Sv);
    Real c2 = sq(t1) / (squ*sqv); assert(c2 < 1);
    Real cr1 = sign(t1) * sqrt(c2 / (1-c2));
    Real cr2 = sqrt(c1 / (1-c2));
    return Vct2( cr1, cr2 );
  }

  /// compute derivatives of surface coordinates S w.r.t. s,t
  void plane(const Surface &srf, Real u, Real v, Vct3 &Ss, Vct3 &St) const;

  /// clear data
  void clear();

private:

  /// down-sample map evaluation grid
  static void downSample(const Vector & upp, Vector & up);

  /// utility to generate sampling vector from knots
  static void upSample(const Vector &knots, Vector &p);

  /// solve least-squares problem, assumes spline bases are initialized
  void fitSpline(const Surface &srf);

  /// use dense QR from LAPACK for spline fitting
  bool denseFitSpline(const Surface &srf);

  /// use Tim Davis' sparse QR for spline fitting
  bool sparseFitSpline(const Surface &srf);

  /// generate a constant length-based mapping, ignore skew (fallback)
  bool lengthRatioMapping(const Surface &srf);

  /// generate the inverse mapping
  void buildLookupTable();

  /// lookup a value of t in column j, return interpolated v
  Real vlookup(Real t, uint jcol) const;

private:

  enum {SDEG = 2};

  /// spline basis for scalar 2D mapping
  SplineBasis m_ubas, m_vbas;

  /// control points for forward mapping (u,v) -> t
  Matrix m_ctp;

  /// support for inverse lookup : spacing in s/u (columns of m_tval)
  Vector m_ucol;

  /// support for inverse lookup : spacing in v (rows of m_tval)
  Vector m_vrow;

  /// values of t for inverse lookup (s,t) -> v
  Matrix m_tval;

  /// used to limit the number of evaluation points for map definition
  static uint s_max_neval;
};

#endif // UVMAPPING_H
