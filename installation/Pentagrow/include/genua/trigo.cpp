//
// project:      genua
// file:         trigo.cpp
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// trigonometric utilities

#include "point.h"
#include "trigo.h"

//Real solid_angle(const PointList<3> & pts, uint ictr,
//                 Indices & iring)
//{
//  assert(iring.size() > 2);
//
//  // determine mean normal
//  assert(iring.size()%3 == 0);
//  Vct3 nz;
//  const int ntri = iring.size() / 3;
//  for (int i=0; i<ntri; ++i) {
//    const uint *vi = &iring[3*i];
//    Vct3 fn = cross( pts[vi[1]]-pts[vi[0]], pts[vi[2]]-pts[vi[0]] );
//    nz += fn.normalized();
//  }
//  normalize(nz);
//
////  // ensure that the mean normal will yield positive partial
////  // solid angle contributions
////  for (int i=0; i<ntri; ++i) {
////    const uint *vi = &iring[3*i];
////    Vct3 fn = cross( pts[vi[1]]-pts[vi[0]], pts[vi[2]]-pts[vi[0]] );
////    normalize(fn);
////    Real fdz = dot(nz, fn);
////    if (fdz < 0.0) {
////      nz -= 1.25*fdz*fn;
////      normalize(nz);
////    } else if (fdz < gmepsilon) {
////      nz += 1e-3 * fn;
////      normalize(nz);
////    }
////  }
//
//  // add solid angle contributions from facets
//  Vct3 a, b;
//  Real omega = 0.0;
//  for (int i=0; i<ntri; ++i) {
//    const uint *vi = &iring[3*i];
//    if (ictr == vi[0]) {
//      a = pts[vi[1]] - pts[vi[0]];
//      b = pts[vi[2]] - pts[vi[0]];
//    } else if (ictr == vi[1]) {
//      a = pts[vi[2]] - pts[vi[1]];
//      b = pts[vi[0]] - pts[vi[1]];
//    } else if (ictr == vi[2]) {
//      a = pts[vi[0]] - pts[vi[2]];
//      b = pts[vi[1]] - pts[vi[2]];
//    }
//    omega += solid_angle(nz, a, b);
//  }
//
//  return omega;
//}

//
//namespace detail {
//
//  class atan2_cmp {
//  public:
//    atan2_cmp(const PointList<3> & p, const Vct3 & o,
//              const Vct3 & x, const Vct3 & y) : pts(p), org(o), nx(x), ny(y) {}
//
//    bool operator() (uint a, uint b) const {
//      return phi(a) < phi(b);
//    }
//
//    Real phi(uint a) const {
//      Real xa = dot(pts[a] - org, nx);
//      Real ya = dot(pts[a] - org, ny);
//      Real aphi = atan2(ya, xa);
//      return (aphi >= 0.0) ? aphi : aphi + 2*M_PI;
//    }
//
//  private:
//    const PointList<3> & pts;
//    const Vct3 & org;
//    const Vct3 & nx;
//    const Vct3 & ny;
//  };
//
//}
//
//Real solid_angle(const PointList<3> & pts, uint ictr,
//                 Indices & iring)
//{
//  int n = iring.size();
//  assert(n > 2);
//
//  // determine mean normal
//  assert(n%3 == 0);
//  Vct3 nz;
//  const int ntri = iring.size() / 3;
//  for (int i=0; i<ntri; ++i) {
//    const uint *vi = &iring[3*i];
//    Vct3 fn = cross( pts[vi[1]]-pts[vi[0]], pts[vi[2]]-pts[vi[0]] );
//    nz += fn.normalized();
//  }
//  normalize(nz);
//
//  // ensure that the mean normal will yield positive partial
//  // solid angle contributions
//
//  // define a cartesian coordinate system
//  const Vct3 & ctr( pts[ictr] );
//  uint ia(0);
//  while (iring[ia] == ictr)
//    ++ia;
//  const Vct3 & a( pts[iring[ia]] );
//  nx = a - ctr;
//  normalize(nx);
//  ny = cross(nz,nx);
//  normalize(ny);
//
//  // remove all references to center point from ring
//  Indices::iterator last;
//  last = std::remove(iring.begin(),
//                     iring.end(), ictr);
//
//  // sort vertices in consistent direction
//  detail::atan2_cmp cmp(pts, ctr, nx, ny);
//  std::sort(iring.begin(), last, cmp);
//
//  // remove duplicates
//  last = std::unique(iring.begin(), last);
//  n = std::distance(iring.begin(), last);
//
//  // add solid angle contributions from facets
//  Real omega = 0.0;
//  for (int i=0; i<n; ++i) {
//    uint ia = iring[i];
//    uint ib = iring[(i+1)%n];
//    omega += solid_angle(nz, pts[ia] - ctr, pts[ib] - ctr);
//  }
//
//  return omega;
//}
