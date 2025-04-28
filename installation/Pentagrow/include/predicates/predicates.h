
/* prototypes for functions in predicates.c */

#ifndef SURF_PREDICATES_H
#define SURF_PREDICATES_H

#if defined(__cplusplus)
extern "C" {
#endif

void jrsExactInit(void);

double jrsOrient2dfast(const double pa[], const double pb[], const double pc[]);

/// return positive value, if pa, pb, pc occur in counterclockwise order
double jrsOrient2d(const double pa[], const double pb[], const double pc[]);

double jrsOrient3dfast(const double pa[], const double pb[], const double pc[],
                       const double pd[]);

double jrsOrient3dExact(const double pa[], const double pb[], const double pc[],
                        const double pd[]);

/** Return a positive value if the point pd lies below the
    plane passing through pa, pb, and pc; "below" is defined so
    that pa, pb, and pc appear in counterclockwise order when
    viewed from above the plane.  Returns a negative value if
    pd lies above the plane.  Returns zero if the points are
    coplanar.  The result is also a rough approximation of six
    times the signed volume of the tetrahedron defined by the
    four points.
  */
double jrsOrient3d(const double pa[], const double pb[], const double pc[],
                   const double pd[]);

double jrsInCirclefast(const double pa[], const double pb[], const double pc[],
                       const double pd[]);

/** Return a positive value if pd is inside the circle (pa,pb,pc),
provided that (pa,pb,pc) are in counterclockwise order. zero if all four
points are on the circle. */
double jrsInCircle(const double pa[], const double pb[], const double pc[],
                   const double pd[]);

double jrsInSpherefast(const double pa[], const double pb[], const double pc[],
                       const double pd[], const double pe[]);

double jrsInSphere(const double pa[], const double pb[], const double pc[],
                   const double pd[], const double pe[]);

#if defined(__cplusplus)
}  // extern "C"
#endif

#ifdef __cplusplus

#include <genua/svector.h>

inline double jrsOrient2d(const Vct2 &a, const Vct2 &b, const Vct2 &c)
{
  return jrsOrient2d(a.pointer(), b.pointer(), c.pointer());
}

inline double jrsInCircle(const Vct2 &a, const Vct2 &b, const Vct2 &c,
                          const Vct2 &d)
{
  return jrsInCircle(a.pointer(), b.pointer(), c.pointer(), d.pointer());
}

inline double jrsOrient3d(const Vct3 &a, const Vct3 &b, const Vct3 &c,
                          const Vct3 &d)
{
  return jrsOrient3d(a.pointer(), b.pointer(), c.pointer(), d.pointer());
}

inline double jrsOrient3dExact(const Vct3 &a, const Vct3 &b, const Vct3 &c,
                               const Vct3 &d)
{
  return jrsOrient3dExact(a.pointer(), b.pointer(), c.pointer(), d.pointer());
}

inline double jrsInSphere(const Vct3 &a, const Vct3 &b, const Vct3 &c,
                          const Vct3 &d, const Vct3 &e)
{
  return jrsInSphere(a.pointer(), b.pointer(), c.pointer(), d.pointer(),
                     e.pointer());
}

#endif

#endif
