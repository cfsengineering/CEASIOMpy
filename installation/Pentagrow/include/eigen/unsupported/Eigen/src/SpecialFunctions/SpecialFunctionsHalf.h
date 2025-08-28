// This file is part of eeigen, a lightweight C++ template library
// for linear algebra.
//
// This Source Code Form is subject to the terms of the Mozilla
// Public License v. 2.0. If a copy of the MPL was not distributed
// with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

#ifndef EIGEN_SPECIALFUNCTIONS_HALF_H
#define EIGEN_SPECIALFUNCTIONS_HALF_H

namespace eeigen {
namespace numext {

#if EIGEN_HAS_C99_MATH
template<> EIGEN_STRONG_INLINE EIGEN_DEVICE_FUNC eeigen::half lgamma(const eeigen::half& a) {
  return eeigen::half(eeigen::numext::lgamma(static_cast<float>(a)));
}
template<> EIGEN_STRONG_INLINE EIGEN_DEVICE_FUNC eeigen::half digamma(const eeigen::half& a) {
  return eeigen::half(eeigen::numext::digamma(static_cast<float>(a)));
}
template<> EIGEN_STRONG_INLINE EIGEN_DEVICE_FUNC eeigen::half zeta(const eeigen::half& x, const eeigen::half& q) {
  return eeigen::half(eeigen::numext::zeta(static_cast<float>(x), static_cast<float>(q)));
}
template<> EIGEN_STRONG_INLINE EIGEN_DEVICE_FUNC eeigen::half polygamma(const eeigen::half& n, const eeigen::half& x) {
  return eeigen::half(eeigen::numext::polygamma(static_cast<float>(n), static_cast<float>(x)));
}
template<> EIGEN_STRONG_INLINE EIGEN_DEVICE_FUNC eeigen::half erf(const eeigen::half& a) {
  return eeigen::half(eeigen::numext::erf(static_cast<float>(a)));
}
template<> EIGEN_STRONG_INLINE EIGEN_DEVICE_FUNC eeigen::half erfc(const eeigen::half& a) {
  return eeigen::half(eeigen::numext::erfc(static_cast<float>(a)));
}
template<> EIGEN_STRONG_INLINE EIGEN_DEVICE_FUNC eeigen::half igamma(const eeigen::half& a, const eeigen::half& x) {
  return eeigen::half(eeigen::numext::igamma(static_cast<float>(a), static_cast<float>(x)));
}
template<> EIGEN_STRONG_INLINE EIGEN_DEVICE_FUNC eeigen::half igammac(const eeigen::half& a, const eeigen::half& x) {
  return eeigen::half(eeigen::numext::igammac(static_cast<float>(a), static_cast<float>(x)));
}
template<> EIGEN_STRONG_INLINE EIGEN_DEVICE_FUNC eeigen::half betainc(const eeigen::half& a, const eeigen::half& b, const eeigen::half& x) {
  return eeigen::half(eeigen::numext::betainc(static_cast<float>(a), static_cast<float>(b), static_cast<float>(x)));
}
#endif

}  // end namespace numext
}  // end namespace eeigen

#endif  // EIGEN_SPECIALFUNCTIONS_HALF_H
