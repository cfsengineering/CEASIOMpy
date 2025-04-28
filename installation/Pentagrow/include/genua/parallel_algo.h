
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
 
#ifndef GENUA_PARALLEL_ALGO_H
#define GENUA_PARALLEL_ALGO_H

#include "parallel_loop.h"

#if defined(HAVE_TBB)

#include <tbb/parallel_sort.h>
#include <tbb/parallel_for_each.h>
#include <tbb/parallel_for.h>

namespace parallel
{

template <typename Iterator>
void sort(Iterator begin, Iterator end)
{
  tbb::parallel_sort(begin, end);
}

template <typename Iterator, typename Compare>
void sort(Iterator begin, Iterator end, const Compare &c)
{
  tbb::parallel_sort(begin, end, c);
}

template <typename Iterator, typename Functor>
void for_each(Iterator begin, Iterator end, const Functor &f)
{
  tbb::parallel_for_each(begin, end, f);
}

}

// #elif (__GNUC__ >= 4) && (__GNUC_MINOR__ >= 3) && defined(_OPENMP)

// GNU stdlibc++ has a parallel mode for gcc >= 4.3, which uses OpenMP

// #include <parallel/algorithm>
// #include <parallel/numeric>

// #define HAVE_PARALLEL_LIBCXX

// namespace parallel {

// using __gnu_parallel::for_each;
// using __gnu_parallel::sort;

// }

/*

#define accumulate		__gnu_parallel::accumulate
#define adjacent_difference		__gnu_parallel::adjacent_difference
#define inner_product		__gnu_parallel::inner_product
#define partial_sum		__gnu_parallel::partial_sum
#define adjacent_find		__gnu_parallel::adjacent_find
#define count		__gnu_parallel::count
#define count_if		__gnu_parallel::count_if
#define equal		__gnu_parallel::equal
#define find		__gnu_parallel::find
#define find_if		__gnu_parallel::find_if
#define find_first_of		__gnu_parallel::find_first_of
#define for_each		__gnu_parallel::for_each
#define generate		__gnu_parallel::generate
#define generate_n		__gnu_parallel::generate_n
#define lexicographical_compare		__gnu_parallel::lexicographical_compare
#define mismatch		__gnu_parallel::mismatch
#define search		__gnu_parallel::search
#define search_n		__gnu_parallel::search_n
#define transform		__gnu_parallel::transform
#define replace		__gnu_parallel::replace
#define replace_if		__gnu_parallel::replace_if
#define max_element		__gnu_parallel::max_element
#define merge		__gnu_parallel::merge
#define min_element		__gnu_parallel::min_element
#define nth_element		__gnu_parallel::nth_element
#define partial_sort		__gnu_parallel::partial_sort
#define partition		__gnu_parallel::partition
#define random_shuffle		__gnu_parallel::random_shuffle
#define set_union		__gnu_parallel::set_union
#define set_intersection		__gnu_parallel::set_intersection
#define set_symmetric_difference		__gnu_parallel::set_symmetric_difference
#define set_difference		__gnu_parallel::set_difference
#define sort		__gnu_parallel::sort
#define stable_sort		__gnu_parallel::stable_sort
#define unique_copy		__gnu_parallel::unique_copy

*/

//#elif HAVE_PPL

//#include <ppl.h>

//#define parallel_sort concurrency::parallel_sort
//#define parallel_for_each concurrency::parallel_for_each

#else // no TBB, no PPL, no GNU parallel mode libstdc++

#define HAVE_GENUA_PARALLEL_ALGO

#include "taskgroup.h"
#include <iterator>
#include <algorithm>

namespace parallel
{

namespace detail {

enum { PSortRecursionLimit = 16 };
enum { PSortSerialThreshold = 1024 };

template<typename ValueType, typename Compare>
inline const ValueType& median3(const ValueType& a, const ValueType& b,
                               const ValueType& c, Compare cmp)
{
  if (cmp(a, b))
    if (cmp(b, c))
      return b;
    else if (cmp(a, c))
      return c;
    else
      return a;
  else if (cmp(a, c))
    return a;
  else if (cmp(b, c))
    return c;
  else
    return b;
}

// not much better than 3-way median

template <typename Iterator, typename Compare>
inline typename std::iterator_traits<Iterator>::value_type
median9(Iterator begin, Iterator end, Compare cmp)
{
  typedef typename std::iterator_traits<Iterator>::value_type ValueType;
  typedef typename std::iterator_traits<Iterator>::difference_type SizeType;
  SizeType step = std::distance(begin, end) / 8;
  Iterator pos(begin);
  const ValueType & a = median3( *pos, *(pos + step),
                                 *(pos + 2*step), cmp );
  const ValueType & b = median3( *(pos + 3*step), *(pos + 4*step),
                                 *(pos + 5*step), cmp );
  const ValueType & c = median3( *(pos + 6*step), *(pos + 7*step),
                                 *(end - 1), cmp );
  return median3(a, b, c, cmp);

//  ValueType samples[9];
//  for (int i=0; i<9; ++i) {
//    samples[i] = *begin;
//    begin += step - 1;
//  }
//  std::sort(samples, samples+9, cmp);
//  return samples[4];
}


template <typename ValueType, typename Compare>
struct PivotPred
{
  PivotPred(const Compare &c, const ValueType &x) : cmp(c), m(x) {}
  bool operator() (const ValueType & a) const {
    return cmp(a,m);
  }
  const Compare & cmp;
  ValueType m;
};

template <typename Iterator, typename Compare>
inline Iterator split_range(Iterator begin, Iterator end, const Compare & cmp)
{
  typedef typename std::iterator_traits<Iterator>::value_type ValueType;
  typedef typename std::iterator_traits<Iterator>::difference_type SizeType;

  SizeType len = std::distance(begin, end);
  Iterator mid(begin + len/2), last(end - 1);
  PivotPred<ValueType,Compare> pred( cmp, median3(*begin, *mid, *last, cmp) );
  return std::partition(begin, end, pred);
}

template <typename Iterator, typename Compare>
struct SortTask
{
  typedef void result_type;
  typedef SortTask<Iterator,Compare>        TaskType;

#ifdef GENUA_MSVC
  // plain vanilla iterators are not trivially assignable in VS 2013 (!!!)
  // so we need to use a mutex instead of atomics ... sigh.
  typedef WorkStack<TaskType>               SortStack;
#else
  typedef boost::lockfree::stack<TaskType>  LfStack;
  typedef LockfreePool<LfStack>             SortStack;
#endif

  SortTask() {}

  SortTask(SortStack *pstack, const Compare *pcmp,
           Iterator begin, Iterator end)
    : m_stack(pstack), m_cmp(pcmp),
      m_begin(begin), m_end(end), depth( detail::PSortRecursionLimit ) {}

  SortTask(const SortTask *parent, Iterator begin, Iterator end)
    : m_stack(parent->m_stack), m_cmp(parent->m_cmp),
      m_begin(begin), m_end(end), depth(parent->depth) {}

  void operator() () {
    const intptr_t threshold = detail::PSortSerialThreshold;
    --depth;
    if (std::distance(m_begin, m_end) <= threshold or depth <= 0) {
      std::sort(m_begin, m_end, *m_cmp);
    } else {
      Iterator pivot = split_range(m_begin, m_end, *m_cmp);
      SortTask leftTask( this, m_begin, pivot );
      SortTask rightTask( this, pivot, m_end);

      bool leftSubmitted = m_stack->submit( leftTask );
      if ( not leftSubmitted )
        leftTask();
      if (leftSubmitted) {
        rightTask();
      } else {
        if (not m_stack->submit(rightTask))
          rightTask();
      }

    }
  }

  SortStack *m_stack;
  const Compare *m_cmp;
  Iterator m_begin, m_end;
  int depth;
};

template <typename Iterator, typename Functor>
class IterationAdaptor
{
public:

  /// construct adaptor
  IterationAdaptor(const Functor &f, Iterator begin)
    : m_fun(f), m_begin(begin) {}

  /// adapt fun(Iterator pos) for use as in fun(int a, int b)
  void operator() (int a, int b) {
    Iterator cur(m_begin), last(m_begin);
    std::advance(cur, a);
    std::advance(last, b);
    for (; cur != last; ++cur)
      m_fun(*cur);
  }

private:

  /// copy of functor
  Functor m_fun;

  /// first iterator
  Iterator m_begin;
};


} // detail

template <typename Iterator, typename Compare>
inline void genua_sort(Iterator begin, Iterator end, const Compare & cmp)
{
  typedef detail::SortTask<Iterator,Compare> TaskType;
  typedef typename TaskType::SortStack StackType;

  StackType stack(512);
  stack.submit( TaskType(&stack, &cmp, begin, end) );
  stack.spawn( boost::thread::hardware_concurrency() );
  stack.join();
}

/** Parallel Quicksort.
 *
 * \ingroup concurrency
 */
template <typename Iterator, typename Compare>
void sort(Iterator begin, Iterator end, const Compare & cmp)
{
  genua_sort(begin, end, cmp);
}

template <typename Iterator>
void sort(Iterator begin, Iterator end)
{
  typedef typename std::iterator_traits<Iterator>::value_type value_type;
  genua_sort(begin, end, std::less<value_type>());
}

/** Parallel Foreach.
 *
 * \ingroup concurrency
 */
template <typename Iterator, typename Functor>
void for_each(Iterator begin, Iterator end, Functor f)
{
  detail::IterationAdaptor<Iterator,Functor> itap(f, begin);
  int n = std::distance(begin, end);
  assert(n >= 0);
  block_loop(itap, 0, n);
}

} // namespace parallel

#endif




#endif // PARALLEL_ALGO_H
