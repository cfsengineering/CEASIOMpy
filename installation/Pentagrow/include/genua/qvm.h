#ifndef GENUA_QVM_H
#define GENUA_QVM_H

#include "defines.h"
#include "svector.h"
#include <boost/qvm/quat_traits.hpp>
#include <boost/qvm/quat_operations.hpp>

namespace boost {
namespace qvm {

/// Allows to use an SVector<4,...> with boost::qvm
template <typename FloatType>
struct quat_traits< SVector<4,FloatType> > {
  typedef FloatType scalar_type;
  template <int I>
  static inline scalar_type read_element( SVector<4,FloatType> const & q )
  {
    return q[I];
  }
  template <int I>
  static inline scalar_type & write_element(SVector<4,FloatType> & q ) {
    return q[I];
  }
};

}
}

/// Return a quaternion for the rotation sequence Rx-Ry-Rz (x-y'-z'').
template <typename FloatType>
SVector<4,FloatType> rxyz2quat(FloatType rx, FloatType ry, FloatType rz)
{
  SVector<4,FloatType> a;
  boost::qvm::set_rotx(a, rx);
  boost::qvm::rotate_y(a, ry);
  boost::qvm::rotate_z(a, rz);
  return a;
}

/** Shortest-path spherical linear interpolation (SLERP).
 *
 * Interpolate between rotation ra and rb, both expressed as angles for the
 * rotation sequence Rx-Ry-Rz (x-y'-z'') at parameter 0 <= s <= 1. The result
 * is returned in the array rs containing the angular representation (Rx-Ry-Rz)
 * of the interpolated rotation. Note that the angles in rs are not necessarily
 * bounded by the values in ra and rb.
 *
 * \ingroup geometry
 */
template <typename FloatType>
void rxyz_slerp(const FloatType ra[], const FloatType rb[],
                FloatType s, FloatType rs[])
{
  assert(s >= 0 and s <= 1);

  int nchanges = 0;
  for (int k=0; k<3; ++k)
    nchanges += (ra[k] != rb[k]);

  // no point in going through all the algebra if trivial
  bool endPoint = (s == 0) or (s == 1);

  // SLERPing to/from pitch = 90 deg could possibly generate wild angles
  // because for the target (a+x, PI/2, b+x) for any x may be generated
  // theoretically - needs checking.
  // bool gimbalLock = fabsf( fabsf(ra[1]) - 0.5*M_PI ) < 0.01f;

  bool doSlerp = (not endPoint) and (nchanges > 1);
  if (doSlerp) {
    SVector<4,FloatType> qa = rxyz2quat(ra[0], ra[1], ra[2]);
    SVector<4,FloatType> qb = rxyz2quat(rb[0], rb[1], rb[2]);
    SVector<4,FloatType> qs;

    // take the short way
    if (boost::qvm::dot(qa, qb) > 0)
      qs = boost::qvm::slerp(qa, qb, s);
    else
      qs = boost::qvm::slerp(qa, -qb, s);

    rs[0] = std::atan2( 2*(qs[0]*qs[1] + qs[2]*qs[3]), 1 - 2*(sq(qs[1]) + sq(qs[2])) );
    rs[1] = std::asin( clamp(2*(qs[0]*qs[2] - qs[3]*qs[1]), -1.0f, 1.0f) );
    rs[2] = std::atan2( 2*(qs[0]*qs[3] + qs[1]*qs[2]), 1 - 2*(sq(qs[2]) + sq(qs[3])) );
  } else {
    // fall-back to linear interpolation for edge cases
    for (int k=0; k<3; ++k)
      rs[k] = (1.0f - s)*ra[k] + s*rb[k];
  }
}

#endif // QVM_H
