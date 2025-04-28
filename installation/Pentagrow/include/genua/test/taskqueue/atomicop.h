#ifndef GENUA_ATOMICOP_H
#define GENUA_ATOMICOP_H

#include <boost/static_assert.hpp>
#include <boost/type_traits/is_integral.hpp>
#include <boost/utility/enable_if.hpp>
#include <genua/defines.h>

namespace detail {

#if defined(GENUA_GCC) || defined(GENUA_CLANG)
#define GENUA_GNU_ATOMICS
#elif defined(GENUA_ICC) && defined(GENUA_POSIX)
#define GENUA_GNU_ATOMICS
#elif defined(GENUA_WIN32)
#define GENUA_MS_ATOMICS
#else
#error No compiler intrinsics for atomic operations detected.
#endif

#if defined(GENUA_GNU_ATOMICS)

template <typename PodType, typename IntType>
inline bool aliased_compare_and_swap(PodType *ptr,
                                     PodType oldval, PodType newval)
{
  union bitrep { PodType pval; IntType ival; };
  bitrep oldbits, newbits;
  oldbits.pval = oldval;
  newbits.pval = newval;
  IntType current = __sync_val_compare_and_swap(reinterpret_cast<IntType*>(ptr),
                                                oldbits.ival, newbits.ival);
  return (current == oldbits.ival);
}

template <typename IntType>
IntType atomic_add_int(IntType &x, IntType y)
{
  return __sync_fetch_and_add(&x, y);
}

template <typename IntType>
IntType atomic_and_int(IntType &x, IntType y)
{
  return __sync_fetch_and_and(&x, y);
}

template <typename IntType>
IntType atomic_or_int(IntType &x, IntType y)
{
  return __sync_fetch_and_or(&x, y);
}

template <typename IntType>
IntType atomic_xor_int(IntType &x, IntType y)
{
  return __sync_fetch_and_xor(&x, y);
}

#elif defined(GENUA_MS_ATOMICS)

#include <intrin.h>

inline short sync_compare_and_swap(short *ptr, short oldval, short newval)
{
  return _InterlockedCompareExchange16(ptr, newval, oldval);
}

inline short sync_compare_and_swap(long *ptr, long oldval, long newval)
{
  return _InterlockedCompareExchange(ptr, newval, oldval);
}

inline short sync_compare_and_swap(__int64 *ptr,
                                   __int64 oldval, __int64 newval)
{
  return _InterlockedCompareExchange64(ptr, newval, oldval);
}

template <typename PodType, typename IntType>
inline bool aliased_compare_and_swap(PodType *ptr,
                                     PodType oldval, PodType newval)
{
  union bitrep { PodType pval; IntType ival; };
  bitrep oldbits, newbits;
  oldbits.pval = oldval;
  newbits.pval = newval;
  IntType current = sync_compare_and_swap(reinterpret_cast<IntType*>(ptr),
                                          oldbits.ival, newbits.ival);
  return (current == oldbits.ival);
}

#undef DECLARE_INT_OP
#define DECLARE_INT_OP(opname, intrin, itype) \
inline itype opname(itype &x, itype y) { return intrin( &x, y ); }

DECLARE_INT_OP(atomic_add_int, _InterlockedExchangeAdd, long)

DECLARE_INT_OP(atomic_and_int, _InterlockedAnd, long)
DECLARE_INT_OP(atomic_and_int, _InterlockedAnd8, char)
DECLARE_INT_OP(atomic_and_int, _InterlockedAnd16, short)

DECLARE_INT_OP(atomic_or_int, _InterlockedOr, long)
DECLARE_INT_OP(atomic_or_int, _InterlockedOr8, char)
DECLARE_INT_OP(atomic_or_int, _InterlockedOr16, short)

DECLARE_INT_OP(atomic_xor_int, _InterlockedXor, long)
DECLARE_INT_OP(atomic_xor_int, _InterlockedXor8, char)
DECLARE_INT_OP(atomic_xor_int, _InterlockedXor16, short)

// strange - there should be intrinsics for these according to the doc,
// but any attempt to use them gives a C3861 "identifier not found" errors.

DECLARE_INT_OP(atomic_add_int, InterlockedExchangeAdd64, __int64)
DECLARE_INT_OP(atomic_and_int, InterlockedAnd64, __int64)
DECLARE_INT_OP(atomic_or_int, InterlockedOr64, __int64)
DECLARE_INT_OP(atomic_xor_int, InterlockedXor64, __int64)


#undef DECLARE_INT_OP

#endif // platform/compiler-specific intrinsics

template <typename PodType>
inline bool compare_and_swap(PodType *ptr,
                             PodType oldval, PodType newval)
{
  BOOST_STATIC_ASSERT( sizeof(PodType) <= 8 );
  if ( sizeof(PodType) == sizeof(int32_t) )
    return aliased_compare_and_swap<PodType,int32_t>(ptr, oldval, newval);
  else if ( sizeof(PodType) == sizeof(int64_t) )
    return aliased_compare_and_swap<PodType,int64_t>(ptr, oldval, newval);
  else if ( sizeof(PodType) == sizeof(int16_t) )
    return aliased_compare_and_swap<PodType,int16_t>(ptr, oldval, newval);
  else if ( sizeof(PodType) == sizeof(int8_t) )
    return aliased_compare_and_swap<PodType,int8_t>(ptr, oldval, newval);
}

} // namespace detail

// logical operations for integer types

template <typename IntType>
inline void atomic_and(IntType &x, IntType y)
{
  detail::atomic_and_int(x, y);
}

template <typename IntType>
inline void atomic_or(IntType &x, IntType y)
{
  detail::atomic_or_int(x, y);
}

template <typename IntType>
inline void atomic_xor(IntType &x, IntType y)
{
  detail::atomic_xor_int(x, y);
}

// other generic operations which make sense even for non-integral types

template <typename PodType>
inline void atomic_add(PodType &x, PodType y)
{
  PodType xnew, xold;
  do {
    xold = x;
    xnew = xold + y;
  } while ( not detail::compare_and_swap(&x, xold, xnew) );
}

template <typename PodType>
inline void atomic_min(PodType &x, PodType y)
{
  PodType xnew, xold;
  do {
    xold = x;
    xnew = std::min(xold, y);
  } while ( not detail::compare_and_swap(&x, xold, xnew) );
}

template <typename PodType>
inline void atomic_max(PodType &x, PodType y)
{
  PodType xnew, xold;
  do {
    xold = x;
    xnew = std::max(xold, y);
  } while ( not detail::compare_and_swap(&x, xold, xnew) );
}

template <typename BinaryOp, typename PodType>
inline void atomic_update(const BinaryOp &op, PodType &x, PodType y)
{
  PodType xnew, xold;
  do {
    xold = x;
    xnew = op(xold,y);
  } while ( not detail::compare_and_swap(&x, xold, xnew) );
}

// overloads for integral types

#undef DECLARE_INT_OP
#define DECLARE_INT_OP(opname, itype) \
  template <> \
  inline void atomic_ ## opname(itype &x, itype y) { detail::atomic_ ## opname ## _int(x, y); }

#if defined(GENUA_GNU_ATOMICS)

DECLARE_INT_OP( add, int8_t )
DECLARE_INT_OP( add, int16_t )
DECLARE_INT_OP( add, int32_t )
DECLARE_INT_OP( add, int64_t )

#elif defined(GENUA_MS_ATOMICS)

DECLARE_INT_OP( add, long )
DECLARE_INT_OP( add, __int64 )

#endif // platform-specific overloads

#undef DECLARE_INT_OP

#endif // ATOMICOP_H
