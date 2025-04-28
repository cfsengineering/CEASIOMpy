
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
 
#ifndef GENUA_THEODORSEN_H
#define GENUA_THEODORSEN_H

#include <complex>
#include <boost/math/special_functions.hpp>
#include <cassert>

namespace detail
{

template <int N, typename FloatType>
std::complex<FloatType> hankel1(FloatType x)
{
  assert(x > 0);
  FloatType Jn = boost::math::cyl_bessel_j(N, x);
  FloatType Yn = boost::math::cyl_neumann(N, x);
  return std::complex<FloatType>(Jn, Yn);
}

template <int N, typename FloatType>
std::complex<FloatType> hankel2(FloatType x)
{
  assert(x > 0);
  FloatType Jn = boost::math::cyl_bessel_j(N, x);
  FloatType Yn = boost::math::cyl_neumann(N, x);
  return std::complex<FloatType>(Jn, -Yn);
}

} // namespace detail

/** Theodorsen's function.

  An implementation of Theodorsen's function using Bessel functions from
  the boost library.
  \f[
    C(k) = \frac{H_1^{(2)}(k)}{H_1^{(2)}(k) + i H_0^{(2)}(k)}
  \f]
  where the Hankel functions H can be expressed as linear combinations of
  the Bessel functions of the first and second kind according to
  \f[
    H_n^{2}(k) = J_n(k) - Y_n(k).
  \f]

  \param k Reduced frequency, real-valued
  \returns Complex value of Theodorsen's function C(k)

  \ingroup numerics
  */
template <typename FloatType>
std::complex<FloatType> theodorsen(FloatType k)
{
  assert(k >= 0);
  std::complex<FloatType> H0, H1, Ck(1, 0);
  if (k <= 0)
    return Ck;

  H0 = detail::hankel2<0>(k);
  H1 = detail::hankel2<1>(k);
  Ck = H1 / (H1 + std::complex<FloatType>(0,1)*H0 );
  return Ck;
}

#endif // THEODORSEN_H
