
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
 
#ifndef GENUA_PRIMITIVES_H
#define GENUA_PRIMITIVES_H

#include "smatrix.h"
#include "smallqr.h"

namespace detail
{

template <typename FloatType>
inline FloatType lparm(const SVector<3,FloatType> & pt,
                       const SVector<3,FloatType> & p1,
                       const SVector<3,FloatType> & p2)
{
  SVector<3,FloatType> lnv(p2 - p1), dst(pt - p1);
  return clamp(dot(lnv,dst)/sq(lnv), FloatType(0), FloatType(1));
}

template <typename FloatType>
inline void mt_cross(FloatType dest[],
                     const FloatType v1[], const FloatType v2[])
{
  dest[0]=v1[1]*v2[2]-v1[2]*v2[1];
  dest[1]=v1[2]*v2[0]-v1[0]*v2[2];
  dest[2]=v1[0]*v2[1]-v1[1]*v2[0];
}

template <typename FloatType>
inline FloatType mt_dot(const FloatType v1[], const FloatType v2[])
{
  return (v1[0]*v2[0]+v1[1]*v2[1]+v1[2]*v2[2]);
}

template <typename FloatType>
inline void mt_sub(FloatType dest[],
                   const FloatType v1[], const FloatType v2[])
{
  dest[0]=v1[0]-v2[0];
  dest[1]=v1[1]-v2[1];
  dest[2]=v1[2]-v2[2];
}

template <typename FloatType>
inline int volume_sign(const FloatType p1[], const FloatType p2[],
                       const FloatType p3[], const FloatType p4[])
{
  FloatType a[3], b[3], c[3], t[3];
  mt_sub(a, p1, p4);
  mt_sub(b, p2, p4);
  mt_sub(c, p3, p4);
  mt_cross(t, b, c);
  FloatType v = mt_dot(a, t);
  if (v < 0)
    return -1;
  else if (v > 0)
    return 1;
  else
    return 0;
}

} // detail

/** Parameters that minimize the distance between two segments.
 *
 * For two line segments a and b in ND-space, compute the line parameters
 * which minimize the distance between the segments. Returns true if the
 * point of least distance lies within [0,1] for both segments.
 *
 * \ingroup geometry
 */
template <typename FloatType, uint ND>
inline bool qr_segment_nearest(const SVector<ND,FloatType> sa[],
                               const SVector<ND,FloatType> sb[],
                               SVector<2,FloatType> &tab)
{
  SMatrix<ND,2,FloatType> A;
  SVector<ND,FloatType> b;
  A.assignColumn(0, sa[1]-sa[0]);
  A.assignColumn(1, sb[0]-sb[1]);
  b = sb[0] - sa[0];
  bool qrok = qrlls<ND,2>(A.pointer(), b.pointer());
  if (qrok) {
    tab[0] = b[0];
    tab[1] = b[1];
    return (b[0] >= 0) and (b[0] <= 1) and (b[1] >= 0) and (b[1] <= 1);
  } else {
    tab = FloatType(0.5f);
    return true;
  }
}

template <typename FloatType>
inline FloatType qr_tri_edge_edge(const SVector<3,FloatType> atri[],
                                  const SVector<3,FloatType> btri[],
                                  SVector<3,FloatType> &c,
                                  FloatType sqlimit = FloatType(0))
{
  SVector<3,FloatType> sa[2], sb[2], pa, pb;
  SVector<2,FloatType> tab;
  FloatType dst, mindst = std::numeric_limits<FloatType>::max();
  for (int ka=0; ka<3; ++ka) {
    sa[0] = atri[ka];
    sa[1] = atri[(ka+1)%3];
    for (int kb=0; kb<3; ++kb) {
      sb[0] = btri[kb];
      sb[1] = btri[(kb+1)%3];
      qr_segment_nearest(sa, sb, tab);
      pa = sa[0] + clamp(tab[0], FloatType(0), FloatType(1))*(sa[1] - sa[0]);
      pb = sb[0] + clamp(tab[1], FloatType(0), FloatType(1))*(sb[1] - sb[0]);
      dst = sq(pb - pa);
      if (dst < mindst) {
        mindst = dst;
        c = FloatType(0.5f)*(pa + pb);
        if (dst <= sqlimit)
          return dst;
      }
    }
  }
  return mindst;
}


/** Projection of a point onto a triangle.
 *
 * Uses numerically stable, but expensive QR-factorization to determine the
 * barycentric coordinates (u,v) of the point on tri closest to p. Returns
 * false if the problem is ill-posed, eg. for a degenerate triangle with
 * identical vertices, or if the point projection is outside the triangle
 * boundaries.
 *
 * \ingroup geometry
 * \sa adp_project_point
 */
template <typename FloatType>
bool qr_project_point(const SVector<3,FloatType> tri[],
                      const SVector<3,FloatType> &p,
                      SVector<2,FloatType> & uv)
{  
  SMatrix<3,2,FloatType> A;
  SVector<3,FloatType> r;
  for (int i=0; i<3; ++i) {
    A(i,0) = tri[1][i] - tri[0][i];
    A(i,1) = tri[2][i] - tri[0][i];
    r[i] = p[i] - tri[0][i];
  }
  bool flag = qrlls<3,2>(A.pointer(), r.pointer());
  uv[0] = r[0];
  uv[1] = r[1];
  FloatType wp = 1.0 - uv[0] - uv[1];
  flag &= (uv[0] >= 0.0);
  flag &= (uv[1] >= 0.0);
  flag &= (wp >= 0.0);
  return flag;
}

/** Minimum distance of a point from triangle.
 *
 * Returns the squared distance of p from tri. Projects p onto tri; if the
 * projection is inside the triangle, returns the distance from p. Otherwise,
 * computes the distance from the nearest triangle edge.
 *
 * \ingroup geometry
 * \sa adp_sqdistance
 */
template <typename FloatType>
FloatType qr_sqdistance(const SVector<3,FloatType> tri[],
                        const SVector<3,FloatType> &p)
{
  SVector<2,FloatType> uv;
  bool inside = qr_project_point(tri, p, uv);
  FloatType w = 1 - uv[0] - uv[1];
  FloatType best = std::numeric_limits<FloatType>::max();

  if (inside) {

    best = sq(p - w*tri[0] - uv[0]*tri[1] - uv[1]*tri[2]);

  } else {

    FloatType lp, dl;

    // project on line tri[0] - tri[2]
    if (uv[0] <= 0) {
      lp = detail::lparm(p, tri[0], tri[2]);
      dl = sq(p - (1-lp)*tri[0] - lp*tri[2]);
      best = std::min(best, dl);
    }

    // project on line tri[0] - tri[1]
    if (uv[1] <= 0) {
      lp = detail::lparm(p, tri[0], tri[1]);
      dl = sq(p - (1-lp)*tri[0] - lp*tri[1]);
      best = std::min(best, dl);
    }

    // project on line tri[1] - tri[2]
    if (w <= 0) {
      lp = detail::lparm(p, tri[1], tri[2]);
      dl = sq(p - (1-lp)*tri[1] - lp*tri[2]);
      best = std::min(best, dl);
    }
  }

  return best;
}

/** Minimum distance between two triangles.
 *
 *  Tests the squared distance of all points in t1 against t2 and vice versa.
 *  Returns prematurely if any distance found smaller than the threshold value
 *  passed as argument.
 *
 * \ingroup geometry
 * \sa qr_sqdistance
 */
template <typename FloatType>
FloatType qr_tritri_sqdistance(const SVector<3,FloatType> t1[],
                               const SVector<3,FloatType> t2[],
                               FloatType sqlimit = FloatType(0))
{
  FloatType minsqd( std::numeric_limits<FloatType>::max() );

  for (int i=0; i<3; ++i) {
    minsqd = std::min(minsqd, qr_sqdistance(t1, t2[i]));
    if (minsqd <= sqlimit)
      return minsqd;
  }

  for (int i=0; i<3; ++i) {
    minsqd = std::min(minsqd, qr_sqdistance(t2, t1[i]));
    if (minsqd <= sqlimit)
      return minsqd;
  }

  SVector<3,FloatType> dmy;
  FloatType eed = qr_tri_edge_edge(t1, t2, dmy, sqlimit);
  return std::min(minsqd, eed);
}

/** Project point on triangle.
 *
 * This function does exactly the same as qr_project_point(), but tries to
 * compute the solution from the normal equations, which is a much less stable
 * problem. If that fails, switches to the QR algorithm. Do not use this
 * version if cancellation errors are a concern.
 *
 * \ingroup geometry
 * \sa qr_project_point
 */
template <typename FloatType>
bool adp_project_point(const SVector<3,FloatType> tri[],
                       const SVector<3,FloatType> &p,
                       SVector<2,FloatType> & uv)
{
  SVector<3,FloatType> du(tri[1] - tri[0]), dv(tri[2] - tri[0]);
  FloatType a00 = dot(du,du);
  FloatType a01 = dot(du,dv);
  FloatType a11 = dot(dv,dv);

  FloatType det = a00*a11 - sq(a01);
  const FloatType eps = std::numeric_limits<FloatType>::epsilon();
  if (std::fabs(det) < eps)
    return qr_project_point(tri, p, uv);

  SVector<3,FloatType> r(p - tri[0]);
  FloatType b0 = dot(du,r);
  FloatType b1 = dot(dv,r);

  FloatType idet = FloatType(1) / det;
  uv[0] = (b0*a11 - b1*a01) * idet;
  uv[1] = (a00*b1 - a01*b0) * idet;

  FloatType wp = 1.0 - uv[0] - uv[1];
  bool flag = true;
  flag &= (uv[0] >= 0.0);
  flag &= (uv[1] >= 0.0);
  flag &= (wp >= 0.0);
  return flag;
}

/** Minimum distance of a point from triangle.
 *
 * Returns the squared distance of p from tri, by means of the solution of the
 * normal equations when possible, otherwise using qr_sqdistance.
 *
 * \ingroup geometry
 * \sa qr_sqdistance
 */
template <typename FloatType>
FloatType adp_sqdistance(const SVector<3,FloatType> tri[],
                         const SVector<3,FloatType> &p)
{
  SVector<2,FloatType> uv;
  bool inside = adp_project_point(tri, p, uv);

  FloatType w = 1 - uv[0] - uv[1];
  FloatType best = std::numeric_limits<FloatType>::max();

  if (inside) {
    best = sq(p - w*tri[0] - uv[0]*tri[1] - uv[1]*tri[2]);
  } else {

    FloatType lp, dl;

    // project on line tri[0] - tri[2]
    if (uv[0] <= 0) {
      lp = detail::lparm(p, tri[0], tri[2]);
      dl = sq(p - (1-lp)*tri[0] - lp*tri[2]);
      best = std::min(best, dl);
    }

    // project on line tri[0] - tri[1]
    if (uv[1] <= 0) {
      lp = detail::lparm(p, tri[0], tri[1]);
      dl = sq(p - (1-lp)*tri[0] - lp*tri[1]);
      best = std::min(best, dl);
    }

    // project on line tri[1] - tri[2]
    if (w <= 0) {
      lp = detail::lparm(p, tri[1], tri[2]);
      dl = sq(p - (1-lp)*tri[1] - lp*tri[2]);
      best = std::min(best, dl);
    }
  }

  return best;
}

/** Line-triangle intersection computation (Möller-Trumbore)
 *
 * The boolean template argument determines whether intersections outside the
 * line parameter range are rejected (segment-triangle test) or not
 * (ray-triangle test). Due to the early exit conditions, settings this to
 * 'true' is faster, but not always what you need.
 *
 * Tomas Möller and Ben Trumbore: "Fast, Minimum Storage Ray-Triangle
 * Intersection", journal of graphics, gpu, and game tools, 2(1),21-28,1997
 *
 * \ingroup geometry
 *
 */
template <bool test_in_line, typename FloatType>
bool mt_line_triangle(const FloatType lineOrigin[3],
                      const FloatType lineDirection[3],
                      const FloatType tri0[3],
                      const FloatType tri1[3],
                      const FloatType tri2[3],
                      FloatType &t, FloatType &u, FloatType &v)
{
  FloatType edge1[3], edge2[3], tvec[3], pvec[3], qvec[3];
  FloatType det,inv_det;
  //const FloatType mt_epsilon(0.000001f);
  const FloatType mt_epsilon = 2*std::numeric_limits<FloatType>::epsilon();

  /* find vectors for two edges sharing vert0 */
  detail::mt_sub(edge1, tri1, tri0);
  detail::mt_sub(edge2, tri2, tri0);

  /* begin calculating determinant - also used to calculate U parameter */
  detail::mt_cross(pvec, lineDirection, edge2);

  /* if determinant is near zero, ray lies in plane of triangle */
  det = detail::mt_dot(edge1, pvec);

  if (std::fabs(det) < mt_epsilon)
    return false;
  inv_det = 1.0f / det;

  /* calculate distance from vert0 to ray origin */
  detail::mt_sub(tvec, lineOrigin, tri0);

  /* calculate U parameter and test bounds */
  u = detail::mt_dot(tvec, pvec) * inv_det;
  if (u < 0.0f || u > 1.0f)
    return false;

  /* prepare to test V parameter */
  detail::mt_cross(qvec, tvec, edge1);

  /* calculate V parameter and test bounds */
  v = detail::mt_dot(lineDirection, qvec) * inv_det;
  if (v < 0.0f || u + v > 1.0f)
    return false;

  /* calculate t, ray intersects triangle */
  t = detail::mt_dot(edge2, qvec) * inv_det;
  if (test_in_line && (t < 0.0f || t > 1.0f))
    return false;

  return true;
}

/** Pure triangle-line intersection test.
 *
 * This function checks for triangle-line intersection and does not actually
 * compute the intersection point; returns only an intersection indication.
 *
 * \ingroup geometry
 *
 */
template <bool test_in_line, typename FloatType>
bool mt_line_triangle(const FloatType lineOrigin[3],
                      const FloatType lineDirection[3],
                      const FloatType tri0[3],
                      const FloatType tri1[3],
                      const FloatType tri2[3] )
{
  FloatType edge1[3], edge2[3], tvec[3], pvec[3], qvec[3];
  FloatType det,inv_det,u,v,t;
  //const FloatType mt_epsilon(0.000001f);
  const FloatType mt_epsilon = 2*std::numeric_limits<FloatType>::epsilon();

  /* find vectors for two edges sharing vert0 */
  detail::mt_sub(edge1, tri1, tri0);
  detail::mt_sub(edge2, tri2, tri0);

  /* begin calculating determinant - also used to calculate U parameter */
  detail::mt_cross(pvec, lineDirection, edge2);

  /* if determinant is near zero, ray lies in plane of triangle */
  det = detail::mt_dot(edge1, pvec);

  if (std::fabs(det) < mt_epsilon)
    return false;
  inv_det = 1.0 / det;

  /* calculate distance from vert0 to ray origin */
  detail::mt_sub(tvec, lineOrigin, tri0);

  /* calculate U parameter and test bounds */
  u = detail::mt_dot(tvec, pvec) * inv_det;
  if (u < 0.0 || u > 1.0)
    return false;

  /* prepare to test V parameter */
  detail::mt_cross(qvec, tvec, edge1);

  /* calculate V parameter and test bounds */
  v = detail::mt_dot(lineDirection, qvec) * inv_det;
  if (v < 0.0 || u + v > 1.0)
    return false;

  /* calculate t, ray intersects triangle */
  t = detail::mt_dot(edge2, qvec) * inv_det;
  if (test_in_line && (t < 0.0 || t > 1.0))
    return false;

  return true;
}

///** Test one line against multiple triangles at once.
// *
// */
//template <bool test_in_line, class SimdType>
//int mt_line_ntriangles(const SimdType lineOrigin[3],
//const SimdType lineDirection[3],
//const SimdType tri0[3],
//const SimdType tri1[3],
//const SimdType tri2[3])
//{
//  SimdType edge1[3], edge2[3], tvec[3], pvec[3], qvec[3];
//  SimdType det, inv_det, u, v, t;
//  const SimdType mt_epsilon(0.000001f);
//  const SimdType zero;
//  zero ^= zero;

//  // mask[i] is set if triangle i does not intersect line
//  SimdType disjointMask;
//  disjointMask ^= disjointMask;  // zero out, all may intersect

//  // signbit mask for a mask with all bits set
//  const int N = SimdType::width();
//  const int allDisjoint = (1 << N) - 1;

//  /* find vectors for two edges sharing vert0 */
//  detail::mt_sub(edge1, tri1, tri0);
//  detail::mt_sub(edge2, tri2, tri0);

//  /* begin calculating determinant - also used to calculate U parameter */
//  detail::mt_cross(pvec, lineDirection, edge2);

//  /* if determinant is near zero, ray lies in plane of triangle */
//  det = detail::mt_dot(edge1, pvec);

//  if (test_in_line) {

//    disjointMask |= ((det > -mt_epsilon) & (det < mt_epsilon));
//    if (disjointMask.signbits() == allDisjoint)
//      return 0;

//    /* calculate distance from vert0 to ray origin */
//    detail::mt_sub(tvec, lineOrigin, tri0);

//    /* calculate U parameter and test bounds */
//    u = detail::mt_dot(tvec, pvec);
//    disjointMask |= ((u < zero) | (u > det));
//    if (disjointMask.signbits() == allDisjoint)
//      return 0;

//    /* prepare to test V parameter */
//    detail::mt_cross(qvec, tvec, edge1);

//    /* calculate V parameter and test bounds */
//    v = detail::mt_dot(lineDirection, qvec);
//    disjointMask |= ((v < 0.0) | ((u + v) > det));
//    if (disjointMask.signbits() == allDisjoint)
//      return 0;

//    //    /* calculate t, scale parameters, ray intersects triangle */
//    //    t = detail::mt_dot(edge2, qvec);
//    //    inv_det = SimdType(1.0f) / det;
//    //    t *= inv_det;
//    //    u *= inv_det;
//    //    v *= inv_det;

//  } else {                   /* the non-culling branch */

//    disjointMask |= ((det > -mt_epsilon) & (det < mt_epsilon));
//    if (disjointMask.signbits() == allDisjoint)
//      return 0;
//    inv_det = SimdType(1.0f) / det;

//    /* calculate distance from vert0 to ray origin */
//    detail::mt_sub(tvec, lineOrigin, tri0);

//    /* calculate U parameter and test bounds */
//    u = detail::mt_dot(tvec, pvec) * inv_det;
//    disjointMask |= ((u < zero) | (u > SimdType(1.0f)));
//    if (disjointMask.signbits() == allDisjoint)
//      return 0;

//    /* prepare to test V parameter */
//    detail::mt_cross(qvec, tvec, edge1);

//    /* calculate V parameter and test bounds */
//    v = detail::mt_dot(lineDirection, qvec) * inv_det;
//    disjointMask |= ((v < zero) | ((u + v) > SimdType(1.0f)));
//    if (disjointMask.signbits() == allDisjoint)
//      return 0;

//    //    /* calculate t, ray intersects triangle */
//    //    t = detail::mt_dot(edge2, qvec) * inv_det;
//  }

//  return (disjointMask.signbits() ^ allDisjoint);
//}

/** Alternative line-triangle intersection test.
 *
 * This is an alternative test which, according to the comparison paper below,
 * is faster than the Möller-Trumbore function. Profiling shows that that is
 * not the case today.
 *
 * Rafael J. Segura and Francisco R. Feito:
 * "ALGORITHMS TO TEST RAY-TRIANGLE INTERSECTION -- COMPARATIVE STUDY"
 *
 * \ingroup geometry
 * \sa mt_line_triangle
 */
template <typename FloatType>
bool segura_line_triangle(const FloatType lineP1[], const FloatType lineP2[],
                          const FloatType triP1[], const FloatType triP2[],
                          const FloatType triP3[])
{
  int i = detail::volume_sign(lineP1, lineP2, triP1, triP3);
  int j = detail::volume_sign(lineP1, lineP2, triP2, triP3);
  int k = detail::volume_sign(lineP1, lineP2, triP1, triP2);

  if (((i==0)&&(j==0))||// Intersects in C
      ((i==0)&&(k==0))||// Intersects in A
      ((j==0)&&(k==0))) // Intersects in B
    return true;
  if ((i==0) && (i==k)) // Intersects in AC
    return true;
  if ((j==0) && (i==k)) // Intersects in BC
    return true;
  if ((k==0) && (i==j)) // Intersects in AB
    return true;
  if ((i==j)&&(j==k)) // Intersects inside
    return true;

  return false;  // Does not intersect
}

/** Estimate local curvature using two triangles sharing an edge.
 *
 * The signed reciprocal radius of curvature is estimated from the normal
 * vectors of two triangles by postulating that these normals are parallel to
 * the radius of a circumscribed cylinder. A positive curvature indicates that
 * the surface is convex in the sense that the vector from the centerline of
 * the cylinder is parallel to the normal vector of triangle (p[0], p[1], p[2]).
 *
 *  \param p Array of four points which make up two triangles which share the
 *           edge p[0] - p[1]. Hence, p[2] and p[3] belong to different
 *           triangles.
 *  \return signed reciprocal radius of curvature
 */
template <typename FloatType>
FloatType estimate_curvature(const SVector<3,FloatType> p[])
{
  const FloatType third(1.0/3.0);
  const SVector<3,FloatType> &src(p[0]);
  const SVector<3,FloatType> &trg(p[1]);
  const SVector<3,FloatType> &left(p[2]);
  const SVector<3,FloatType> &right(p[3]);
  SVector<3,FloatType> e = trg - src;
  assert(dot(e,e) > 0);
  SVector<3,FloatType> fnleft = cross(e, left-src);
  assert(dot(fnleft,fnleft) > 0);
  SVector<3,FloatType> fnright = cross(right-src, e);
  assert(dot(fnright,fnright) > 0);
  SVector<3,FloatType> midleft = (src + trg + left) * third;
  SVector<3,FloatType> midright = (src + trg + right) * third;

  // create lines L1(s) := midleft + s*fnleft,  L2(t) := midright + t*fnright
  // then find (s,t) which minimize |L1 - L2| = |A*[s,t] - b|
  SMatrix<3,2,FloatType> A;
  A.assignColumn(0,  fnleft);
  A.assignColumn(1, -fnright);

  SVector<3,FloatType> b( midright - midleft);
  bool nonparallel = qrlls<3,2>(A, b);
  if (nonparallel) {
    SVector<3,FloatType> d( src - (midleft + b[0]*fnleft) );
    d -= (dot(d,e)/dot(e,e)) * e;
    return -sign(dot(d,fnleft)) / norm(d);
  }

  // vectors parallel, no curvature
  return FloatType(0);
}

#endif // PRIMITIVES_H
