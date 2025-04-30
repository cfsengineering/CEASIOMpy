
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
 
#ifndef GENUA_PARALLEL_LOOP_H
#define GENUA_PARALLEL_LOOP_H

#include <boost/config.hpp>

#if 0 // defined(HAVE_TBB)

#include <tbb/parallel_for.h>

namespace detail {

/** Adaptor for TBB algorithms.
 *
 * This simple wrapper adapts a functor with the signature f(int a)
 * for use with TBB algorithms which require an argument of the form
 * tbb::blocked_range.
 *
 */
template <typename SimpleFunctor, typename IntegerType>
struct TbbSimpleAdaptor
{
  TbbSimpleAdaptor(SimpleFunctor &f) : m_prf(f) {}
  void operator()(const tbb::blocked_range<IntegerType> &r) const {
    for (IntegerType i = r.begin(); i != r.end(); ++i)
      m_prf(i);
  }
  mutable SimpleFunctor &m_prf;
};

/** Adaptor for TBB algorithms.
 *
 * This simple wrapper adapts a functor with the signature f(int a, int b)
 * for use with TBB algorithms which require an argument of the form
 * tbb::blocked_range.
 *
 */
template <typename RangeFunctor, typename IntegerType>
struct TbbRangeAdaptor : public RangeFunctor
{
  TbbRangeAdaptor(RangeFunctor &f) : m_prf(f) {}
  void operator()(const tbb::blocked_range<IntegerType> &r) const {
    m_prf(r.begin(), r.end());
  }
  mutable RangeFunctor &m_prf;
};

} // namespace detail

namespace parallel {

template <typename SimpleFunctor, typename IntegerType>
inline void plain_loop(SimpleFunctor &f, IntegerType begin,
                       IntegerType end, IntegerType chunk=1)
{
  detail::TbbSimpleAdaptor<SimpleFunctor,IntegerType> rap(f);
  tbb::parallel_for( tbb::blocked_range<IntegerType>(begin, end, chunk), rap );
}

template <typename RangeFunctor, typename IntegerType>
inline void block_loop(RangeFunctor &f, IntegerType begin,
                       IntegerType end, IntegerType chunk=1)
{
  // detail::TbbRangeAdaptor<RangeFunctor,IntegerType> rap(f);
  tbb::parallel_for( tbb::blocked_range<IntegerType>(begin, end, chunk),
                     detail::TbbRangeAdaptor<RangeFunctor,IntegerType>(f) );
}

}

//#elif HAVE_PPL

//#include <ppl.h>

//namespace detail
//{

//template <typename RangeFunctor, typename IntegerType>
//struct PplRangeAdaptor
//{
//  PplRangeAdaptor(RangeFunctor &f, IntegerType begin,
//                  IntegerType end, IntegerType chunk)
//    : m_prf(f), m_begin(begin), m_end(end), m_chunk(chunk) {}

//  void operator() (IntegerType i) {
//    IntegerType a = m_begin + i*m_chunk;
//    IntegerType b = std::min( a+m_chunk, m_end );
//    m_prf(a, b);
//  }

//  RangeFunctor &m_prf;
//  IntegerType m_begin, m_end, m_chunk;
//};

//} // namespace detail

//template <typename SimpleFunctor, typename IntegerType>
//inline void parallel_loop(SimpleFunctor &f, IntegerType begin,
//                          IntegerType end, IntegerType chunk=1)
//{
//  assert(end > begin);  // PPL restriction
//  if (chunk != 1) {
//    concurrency::simple_partitioner part(chunk);
//    concurrency::parallel_for( begin, end, f, part);
//  } else {
//    concurrency::parallel_for( begin, end, f);
//  }
//}

//template <typename RangeFunctor, typename IntegerType>
//inline void parallel_range(RangeFunctor &f, IntegerType begin,
//                           IntegerType end, IntegerType chunk=1)
//{
//  assert(end > begin);  // PPL restriction
//  detail::PplRangeAdaptor rap(f, begin, end, chunk);
//  IntegerType ntask = (end - begin) / chunk;
//  concurrency::parallel_for(IntegerType(0), ntask, rap);
//}

#else // HAVE_TBB

#include "taskgroup.h"
#include <boost/atomic.hpp>
#include <boost/bind.hpp>

namespace parallel
{

namespace detail {

template <typename SimpleFunctor, typename IntegerType>
struct LooperRangeAdaptor
{
  LooperRangeAdaptor(SimpleFunctor &f) : m_prf(f) {}

  void operator() (IntegerType a, IntegerType b) {
    IntegerType step = (a < b) ? 1 : -1;
    for (IntegerType j=a; j!=b; j+=step)
      m_prf(j);
  }

  SimpleFunctor &m_prf;
};

template <typename RangeFunctor, typename IntegerType>
class Looper
{
public:

  /// construct loop parallelization helper
  Looper(IntegerType begin, IntegerType end, IntegerType chunk) : m_itask(0),
    m_begin(begin), m_chunk(chunk), m_end(end)
  {
    m_ntask = (m_end - m_begin) / m_chunk + 1;
  }

  /// start threads and process
  void process(RangeFunctor &f, int nthreads) {
    boost::container::vector<boost::thread> workers(nthreads);
    for (int i=0; i<nthreads; ++i)
      workers[i] = boost::thread(&Looper::work, this, boost::ref(f));

    // wait for worker to finish
    for (int i=0; i<nthreads; ++i)
      workers[i].join();
  }

protected:

  /// thread worker function
  void work(RangeFunctor & f) {
    do {
      IntegerType i = m_itask.fetch_add(1);
      IntegerType a = m_begin + i*m_chunk;
      IntegerType b = std::min(a+m_chunk, m_end);
      f(a, b);
    } while (m_itask.load() < m_ntask);
  }

private:

  /// task counter
  boost::atomic<size_t> m_itask;

  /// total number of tasks to complete
  size_t m_ntask;

  /// interation space
  IntegerType m_begin, m_chunk, m_end;
};

} // namespace detail

/** Parallel blocked loop.
 *
 * This function template executes a functor which maps a blocked loop. In order
 * to use this mechanism, define a data-parallel loop inside a function object
 * (or lambda) of the following form:
 *
 * \verbatim
 * struct LoopFunction {
 * void operator() (int a, int b) const {
 *     for (int i=a; i<b; ++i)
 *        work_on(i);
 *   }
 * };
 * \endverbatim
 *
 * Prefer this form over a plain loop or parallel::for_each whenever the work in
 * a single iteration is too small to warrant creation of a task.
 * The same mechanism is also used to implement plain data-parallel loops on
 * platforms without OpenMP.
 *
 * \ingroup concurrency
 */
template <class RangeFunctor, typename IntegerType>
inline void block_loop(RangeFunctor &f,
                       IntegerType begin, IntegerType end, IntegerType chunk=0)
{
  IntegerType nthread = boost::thread::hardware_concurrency();
  if (chunk == 0)
    chunk = std::max(IntegerType(1), (end - begin) / (16*nthread));

  detail::Looper<RangeFunctor, IntegerType> looper(begin, end, chunk);
  looper.process(f, nthread);
}

// version for PARLOOP macros
template <class RangeFunctor, typename IntegerType>
inline void block_loop_r(IntegerType begin, IntegerType end,
                         IntegerType chunk, RangeFunctor f)
{
  block_loop(f, begin, end, chunk);
}

template <class SimpleFunctor, typename IntegerType>
inline void plain_loop(SimpleFunctor &f,
                       IntegerType begin, IntegerType end,
                       IntegerType chunk=0)
{
  detail::LooperRangeAdaptor<SimpleFunctor, IntegerType> rap(f);
  block_loop(rap, begin, end, chunk);
}

} // namespace parallel

#endif // no TBB

// macros used to simplify portable loop parallelization

#undef BEGIN_PARLOOP
#undef BEGIN_PARLOOP_CHUNK
#undef END_PARLOOP

#if defined(HAVE_NO_OPENMP)

#define BEGIN_PARLOOP(begin, end) \
  parallel::block_loop_r( (begin), (end), 0, [&](int a, int b) {

#define BEGIN_PARLOOP_CHUNK(begin, end, chunk) \
  parallel::block_loop_r( (begin), (end), (chunk), [&](int a, int b) {

#define END_PARLOOP         });
#define END_PARLOOP_CHUNK   });

#elif defined(_OPENMP) // OpenMP wrapped in macro

#ifndef _MSC_VER
#define DECL_OMP_PRAG(x) _Pragma(#x)
#else
#define DECL_OMP_PRAG(x) __pragma(x)
#endif

#define BEGIN_PARLOOP(begin, end) \
  { int a(begin), b(end); \
  DECL_OMP_PRAG(omp parallel for)

#define END_PARLOOP  }

#define BEGIN_PARLOOP_CHUNK(begin, end, chunk)  \
  { int a(begin), b(end); \
  DECL_OMP_PRAG(omp parallel for schedule(dynamic, (chunk)))

#define END_PARLOOP_CHUNK  }

#else

#define BEGIN_PARLOOP(begin, end)   { int a(begin), b(end);
#define END_PARLOOP }

#define BEGIN_PARLOOP_CHUNK(begin, end, chunk) { int a(begin), b(end);
#define END_PARLOOP_CHUNK }

#endif

// simple loop mechanism for parallel algorithms deep inside the libraries
// which are likely to be called by multithreaded calls higher up - use
// TBB where possible, else OpenMP and revert to low-level implementation
// only when neither alternative is feasible

#if defined(HAVE_TBB)

#include <tbb/parallel_for.h>

namespace parallel {

template <typename IntegerType, class Functor>
inline void loop(IntegerType a, IntegerType b, Functor f)
{
  tbb::parallel_for(a, b, f);
}

}

#elif !defined(HAVE_NO_OPENMP)

namespace parallel {

template <typename IntegerType, class Functor>
inline void loop(IntegerType a, IntegerType b, Functor f)
{
  intptr_t ai(a), bi(b);
#pragma omp parallel for
  for (intptr_t i=ai; i<bi; ++i)
    f(i);
}

}

#else

namespace parallel {

template <typename IntegerType, class Functor>
inline void loop(IntegerType a, IntegerType b, Functor f)
{
  IntegerType chunk = std::abs(b-a) / (4*boost::thread::hardware_concurrency());
  parallel::block_loop_r(a, b, chunk, f);
}

}

#endif // parallel backend


#endif // PARALLEL_LOOP_H
