/* Copyright (C) 2017 David Eller <david@larosterna.com>
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

#ifndef GENUA_UNROLL_H
#define GENUA_UNROLL_H

#include "defines.h"
#include "parallel_loop.h"

namespace internal {

template <uint N>
struct static_unroller
{
  template <class Functor>
  void apply(Functor f, size_t offset = 0u)
  {
    const uint M = N/2;
    const uint R = N - M;
    static_unroller<M> r1;
    r1.apply(f, offset);
    static_unroller<R> r2;
    r2.apply(f, offset+M);
  }
};

template <>
struct static_unroller<0u>
{
  template <class Functor>
  void apply(Functor /* f */, uint /* offset */) {}
};

template <>
struct static_unroller<1u>
{
  template <class Functor>
  void apply(Functor f, size_t offset = 0u) {
    f(offset);
  }
};

template <>
struct static_unroller<2u>
{
  template <class Functor>
  void apply(Functor f, size_t offset = 0u) {
    f(offset);
    f(offset+1);
  }
};

template <>
struct static_unroller<3u>
{
  template <class Functor>
  void apply(Functor f, size_t offset = 0u) {
    f(offset);
    f(offset+1);
    f(offset+2);
  }
};

template <>
struct static_unroller<4u>
{
  template <class Functor>
  void apply(Functor f, size_t offset = 0u) {
    f(offset);
    f(offset+1);
    f(offset+2);
    f(offset+3);
  }
};

template <uint P>
struct partial_unroller {

  template <class Functor>
  void apply(Functor f, size_t n) {
    const size_t nb = n/P;
    static_unroller<P> sr;
    for (size_t j=0; j<nb; ++j)
      sr.apply(f, j*P);
    for (size_t i=P*nb; i<n; ++i)
      f(i);
  }

  template <class Functor>
  void parallel_apply(Functor f, size_t n, size_t chunk = 0) {
    const size_t nb = n/P;
    static_unroller<P> sr;

    auto rf = [&](size_t a, size_t b) {
      for (size_t j=a; j<b; ++j)
        sr.apply(f, j*P);
    };
    parallel::block_loop(rf, 0, nb, chunk/P);
    for (size_t i=P*nb; i<n; ++i)
      f(i);
  }
};

} // end internal

template <uint N, class Functor>
void unrolled_loop(Functor f, size_t offset = 0)
{
  internal::static_unroller<N> r;
  r.apply(f, offset);
}

template <uint P, class Functor>
void partially_unrolled_loop(Functor f, size_t n)
{
  internal::partial_unroller<P> pur;
  pur.apply(f, n);
}

namespace parallel {

template <uint P, class Functor>
void partially_unrolled_loop(Functor f, size_t n, size_t chunk = 0)
{
  internal::partial_unroller<P> pur;
  pur.parallel_apply(f, n, chunk);
}

} // end parallel

#endif // UNROLL_H
