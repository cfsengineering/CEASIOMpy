#ifndef SORT_H
#define SORT_H

#include "threadpool.h"

#include <iterator>
#include <algorithm>

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

/*  not much better than 3-way median

template <typename Iterator, typename Compare>
inline typename std::iterator_traits<Iterator>::value_type
median9(Iterator begin, Iterator end, Compare cmp)
{
  typedef typename std::iterator_traits<Iterator>::value_type ValueType;
  typedef typename std::iterator_traits<Iterator>::difference_type SizeType;
  SizeType step = std::distance(begin, end) / 8;
//  Iterator pos(begin);
//  const ValueType & a = median3( *pos, *(pos + step),
//                                 *(pos + 2*step), cmp );
//  const ValueType & b = median3( *(pos + 3*step), *(pos + 4*step),
//                                 *(pos + 5*step), cmp );
//  const ValueType & c = median3( *(pos + 6*step), *(pos + 7*step),
//                                 *(end - 1), cmp );
//  return median3(a, b, c, cmp);

  ValueType samples[9];
  for (int i=0; i<9; ++i) {
    samples[i] = *begin;
    begin += step - 1;
  }
  std::sort(samples, samples+9, cmp);
  return samples[4];
}

*/

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
  typedef boost::lockfree::stack<TaskType>  LfStack;
  // typedef WorkStack<TaskType>               SortStack;
  typedef LockfreePool<LfStack>             SortStack;

  SortTask() {}

  ~SortTask() {}

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
      // m_stack->submit(leftTask);
      // rightTask();


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

} // detail

template <typename Iterator, typename Compare>
inline void test_sort(Iterator begin, Iterator end, const Compare & cmp)
{
  typedef detail::SortTask<Iterator,Compare> TaskType;
  typedef typename TaskType::SortStack StackType;

  StackType stack(512);
  stack.submit( TaskType(&stack, &cmp, begin, end) );
  stack.spawn( boost::thread::hardware_concurrency() );
  stack.join();
}

#endif // SORT_H
