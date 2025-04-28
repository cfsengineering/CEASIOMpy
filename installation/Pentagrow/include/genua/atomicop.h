
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

#ifndef GENUA_ATOMICOP_H
#define GENUA_ATOMICOP_H

//#include "bitfiddle.h"
#include "defines.h"
#include "svector.h"
#include <boost/static_assert.hpp>
#include <atomic>

namespace detail {

template <typename ValueType>
struct AtomicUpdater
{
  template <class BinOp>
  void update(ValueType &x, BinOp op, ValueType dx) const {
    BOOST_STATIC_ASSERT(sizeof(ValueType) <= 16);
    std::atomic<ValueType> *p = reinterpret_cast<std::atomic<ValueType>*>(&x);
    ValueType xold, xnew;
    do {
      xold = p->load(std::memory_order_acquire);
      xnew = op(xold, dx);
    } while (not p->compare_exchange_weak(xold, xnew,
                                          std::memory_order_release,
                                          std::memory_order_relaxed));
  }

  void add(ValueType &x, ValueType dx) const {
    auto op = [=](ValueType a, ValueType b) {return a+b;};
    this->update(x, op, dx);
  }

  void minval(ValueType &x, ValueType y) const {
    auto op = [=](ValueType a, ValueType b) {return std::min(a,b);};
    this->update(x, op, y);
  }

  void maxval(ValueType &x, ValueType y) const {
    auto op = [=](ValueType a, ValueType b) {return std::max(a,b);};
    this->update(x, op, y);
  }

}; // AtomicUpdater

// should not be needed: 64b atomics should be available everywhere
//
//template <>
//struct AtomicUpdater< std::complex<float> >
//{
//  void add(std::complex<float> &x, std::complex<float> dx) const {
//    AtomicUpdater<float> fup;
//    float *px = reinterpret_cast<float*>(&x);
//    fup.add( px[0], dx.real() );
//    fup.add( px[1], dx.imag() );
//  }
//};

template <>
struct AtomicUpdater< std::complex<double> >
{
  void add(std::complex<double> &x, std::complex<double> dx) const {
    AtomicUpdater<double> fup;
    double *p = reinterpret_cast<double*>(&x);
    fup.add(p[0], dx.real());
    fup.add(p[1], dx.imag());
  }
};

#undef DECL_SVECTOR_UPDATER
#define DECL_SVECTOR_UPDATER(Type, M) \
  template <> \
  struct AtomicUpdater< SVector<M,Type> > { \
  template <class BinOp> \
    void update(SVector<M,Type> &x, BinOp op, SVector<M,Type> dx) const { \
      AtomicUpdater<Type> fup; \
      for (uint k=0; k<M; ++k) \
        fup.update(x[k], op, dx[k]); \
    } \
    void add(SVector<M,Type> &x, SVector<M,Type> dx) const { \
      AtomicUpdater<Type> fup; \
      for (uint k=0; k<M; ++k) \
        fup.add(x[k], dx[k]); \
    } \
  };

DECL_SVECTOR_UPDATER(float, 2)
DECL_SVECTOR_UPDATER(float, 3)
DECL_SVECTOR_UPDATER(float, 4)

DECL_SVECTOR_UPDATER(double, 2)
DECL_SVECTOR_UPDATER(double, 3)
DECL_SVECTOR_UPDATER(double, 4)

#undef DECL_SVECTOR_UPDATER

} // namespace detail

template <typename ValueType>
typename std::enable_if<!std::is_integral<ValueType>::value>::type
atomic_add(ValueType &x, ValueType dx)
{
  detail::AtomicUpdater<ValueType> up;
  up.add(x, dx);
}

template <typename ValueType>
typename std::enable_if<std::is_integral<ValueType>::value>::type
atomic_add(ValueType &x, ValueType dx)
{
  std::atomic<ValueType> *p = reinterpret_cast<std::atomic<ValueType>*>(&x);
  *p += dx;
}

template <typename ValueType>
void atomic_min(ValueType &x, ValueType y)
{
  detail::AtomicUpdater<ValueType> up;
  up.minval(x, y);
}

template <typename ValueType>
void atomic_max(ValueType &x, ValueType y)
{
  detail::AtomicUpdater<ValueType> up;
  up.maxval(x, y);
}

#ifdef _OPENMP

namespace detail {

template <typename ValueType>
struct omp_update_helper {
  static void add(ValueType &x, const ValueType &dx) {
    atomic_add(x, dx);
  }
};

#undef DECLARE_HELPER
#define DECLARE_HELPER(TYPE) \
  template <> \
  struct omp_update_helper< TYPE > { \
    static void add(TYPE &x, const TYPE &dx) { \
      DEFPRAGMA(omp atomic) \
      x += dx; \
    } \
  }; \

DECLARE_HELPER(float)
DECLARE_HELPER(double)
DECLARE_HELPER(int)
DECLARE_HELPER(unsigned)
#if defined(_M_X64) || defined(_LP64)
DECLARE_HELPER(size_t)
#endif
DECLARE_HELPER(int64_t)

#undef DECLARE_HELPER

template <>
struct omp_update_helper<std::complex<float> >
{
  static void add(std::complex<float>  &x, const std::complex<float> &dx)
  {
    float *px = (float *) &x;
#pragma omp atomic
    px[0] += dx.real();
#pragma omp atomic
    px[1] += dx.imag();
  }
};

template <>
struct omp_update_helper<std::complex<double> >
{
  static void add(std::complex<double> &x, const std::complex<double> &dx)
  {
    double *px = (double *) &x;
#pragma omp atomic
    px[0] += dx.real();
#pragma omp atomic
    px[1] += dx.imag();
  }
};

}

template <typename NumericType>
inline void omp_atomic_add(NumericType & x, const NumericType &dx)
{
  detail::omp_update_helper<NumericType> helper;
  helper.add(x, dx);
}

#else

template <typename NumericType>
inline void omp_atomic_add(NumericType & x, NumericType dx)
{
  atomic_add(x, dx);
}

#endif

#endif // ATOMICOP_H
