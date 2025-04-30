
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
 
#ifndef GENUA_TRIGO_H
#define GENUA_TRIGO_H

#include "defines.h"

template <uint N, class Type> class PointList;

#ifdef HAVE_ACML
#include <acml_mv.h>
#endif

#ifdef __ICC
#include <mathimf.h>
#endif

template <class NumType>
inline NumType deg(NumType a)
{
  return a * 180./M_PI;
}

template <class NumType>
inline NumType rad(NumType a)
{
  return a * M_PI/180.;
}

inline void sincosine(double phi, double & sinphi, double & cosphi)
{
#ifdef HAVE_ACML
  fastsincos(phi, &sinphi, &cosphi);
#elif defined(GENUA_LINUX) || defined(__ICC)
  sincos(phi, &sinphi, &cosphi);
#else
  sinphi = sin(phi);
  cosphi = cos(phi);
#endif
}

inline void sincosine(float phi, float & sinphi, float & cosphi)
{
#ifdef HAVE_ACML
  fastsincosf(phi, &sinphi, &cosphi);
#elif defined(GENUA_LINUX) || defined(__ICC)
  sincosf(phi, &sinphi, &cosphi);
#else
  sinphi = sinf(phi);
  cosphi = cosf(phi);
#endif
}

template <class VectorType>
inline typename VectorType::value_type
cosarg(const VectorType & a, const VectorType & b)
{
  // cosine of enclosed angle between a and b
  assert(a.size() == b.size());
  typename VectorType::value_type dt(0.0), nma(0.0), nmb(0.0), lsq, cphi;
  const int n(a.size());
  for (int i=0; i<n; ++i) {
    dt += a[i]*b[i];
    nma += a[i]*a[i];
    nmb += b[i]*b[i];
  }

  // catch division by zero which occurs when a or b are zero length
  lsq = nma*nmb;
  if (lsq == 0)
    return 1;

  cphi = dt/std::sqrt(lsq);

  if (std::fabs(cphi) <= 1)
    return cphi;
  else
    return sign(cphi);
}

template <class VectorType>
inline typename VectorType::value_type
sinarg(const VectorType & a, const VectorType & b)
{
  // sine of enclosed angle between a and b
  assert(a.size() == b.size());
  typename VectorType::value_type dt(0.0), nma(0.0), nmb(0.0), sphi;
  const int n(a.size());
  for (int i=0; i<n; i++) {
    dt += a[i]*b[i];
    nma += a[i]*a[i];
    nmb += b[i]*b[i];
  }
  sphi = 1 - sq(dt)/(nma*nmb);

  if (sphi > 0)
    return std::sqrt(sphi);
  else
    return 0.0;
}

template <class VectorType>
inline typename VectorType::value_type
arg(const VectorType & a, const VectorType & b)
{
  // enclosed angle between a and b
  return std::acos(cosarg(a,b));
}

template <class VectorType>
inline typename VectorType::value_type
arg(const VectorType &xax, const VectorType &yax, const VectorType &b)
{
  // signed angle between xax and b using atan2
  assert(xax.size() == b.size());
  assert(yax.size() == b.size());
  typedef typename VectorType::value_type value_type;
  value_type dtx(0), dty(0), nmx(0), nmy(0), nmb(0);
  const int n(b.size());
  for (int i=0; i<n; i++) {
    dtx += xax[i]*b[i];
    dty += yax[i]*b[i];
    nmx += xax[i]*xax[i];
    nmy += yax[i]*yax[i];
    nmb += b[i]*b[i];
  }

  value_type sphi, cphi;
  sphi = std::sqrt( std::max(value_type(0), 1 - sq(dty)/(nmy*nmb)) );
  cphi = clamp(dtx/std::sqrt(nmx*nmb), value_type(-1), value_type(1));

  return std::atan2(sphi, cphi);
}

template <class VectorType>
inline typename VectorType::value_type
cot(const VectorType & a, const VectorType & b)
{
  // cotangent of the angle enclosed by a,b
  assert(a.size() == b.size());
  typename VectorType::value_type aa(0.0), bb(0.0), ab(0.0), c;
  for (uint i=0; i<a.size(); ++i) {
    aa += a[i]*a[i];
    ab += a[i]*b[i];
    bb += b[i]*b[i];
  }
  c = aa*bb - sq(ab);
  return ab/std::sqrt(c);
}

template <class VectorType>
inline typename VectorType::value_type
solid_angle(const VectorType & a, const VectorType & b, const VectorType & c)
{
  typename VectorType::value_type la, lb, lc, t1, t2, t3, t4;
  la = norm(a);
  lb = norm(b);
  lc = norm(c);
  t1 = dot(a, cross(b,c));
  t2 = dot(a,b) * lc;
  t3 = dot(a,c) * lb;
  t4 = dot(b,c) * la;
  return 2.0*std::atan2(t1, la*lb*lc + t2 + t3 + t4);
}

#endif
