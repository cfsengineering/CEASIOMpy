
/* Copyright (C) 2019 David Eller <david@larosterna.com>
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

#ifndef GENUA_HAVELHEROUT_H
#define GENUA_HAVELHEROUT_H

#include "defines.h"
#include <svector.h>

/** Triangle-ray intersection according to Havel & Herout
 *
 * Adapted from the paper:
 * J. Havel and A. Herout: "Yet Faster Ray-Triangle Intersection.",
 * IEEE Transactions on Visualization and Computer Graphics, 16(3),
 * May-June 2010, doi: 10.1109/TVCG.2009.73
 *
 * \ingroup geometry
 */
template <typename FloatType>
class HavelHerout
{

  /// precompute once from a triangle
  void prep(const SVector<3,FloatType> &v0, const SVector<3,FloatType> &v1,
            const SVector<3,FloatType> &v2)
  {
    SVector<3,FloatType> e1(v1 - v0);
    SVector<3,FloatType> e2(v2 - v0);
    m_n0 = cross(e1, e2);
    m_d0 = dot(m_n0, v0);
    FloatType insq = 1.0f / dot(m_n0, m_n0);
    m_n1 = cross(e2, m_n0) * insq;
    m_d1 = -dot(m_n1, v0);
    m_n2 = cross(m_n0, e1) * insq;
    m_d2 = -dot(m_n2, v0);
  }

  /// test ray (org, dir) against precomputed triangle, return line parameter
  FloatType intersect(const SVector<3,FloatType> &org,
                      const SVector<3,FloatType> &dir,
                      SVector<2,FloatType> &uv) const
  {
    FloatType det = dot(m_n0, dir);
    FloatType dett = m_d0 - dot(org, m_n0);
    SVector<3,FloatType> wr = (org*det) + (dir*dett);
    uv[0] = dot(wr, m_n1) + det * m_d1;
    uv[1] = dot(wr, m_n2) + det * m_d2;
    auto pdet0 = HavelHerout::floatAsInt(det - uv[0] - uv[1]);
    auto pdetu = HavelHerout::floatAsInt(uv[0]);
    auto pdetv = HavelHerout::floatAsInt(uv[1]);
    pdet0 = pdet0 ^ pdetu;
    pdet0 = pdet0 | (pdetu ^ pdetv);
    if (pdet0 & 0x80000000)
      return NotFloat;

    FloatType rdet = 1.0f / det;
    uv[0] *= rdet;
    uv[1] *= rdet;
    return (dett * rdet);
  }

private:

  /// return binary representation of float as int
  static int32_t floatAsInt(float a) {
    union {float f; int32_t i;} u;
    u.f = a;
    return u.i;
  }

  /// return binary representation of float as int
  static int64_t floatAsInt(double a) {
    union {double f; int64_t i;} u;
    u.f = a;
    return u.i;
  }

private:

  /// pre-computed data
  SVector<3,FloatType> m_n0;

  /// pre-computed data
  FloatType m_d0;

  /// pre-computed data
  SVector<3,FloatType> m_n1;

  /// pre-computed data
  FloatType m_d1;

  /// pre-computed data
  SVector<3,FloatType> m_n2;

  /// pre-computed data
  FloatType m_d2;
};

#endif // HAVELHEROUT_H
