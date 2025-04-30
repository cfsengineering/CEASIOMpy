#ifndef PARLOOP_H
#define PARLOOP_H

#include <boost/thread.hpp>
#include <boost/atomic.hpp>
#include <boost/bind.hpp>
#include <boost/container/vector.hpp>

namespace detail {

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

private:

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

}

template <class RangeFunctor, typename IntegerType>
void parallel_loop1(RangeFunctor &f,
                    IntegerType begin, IntegerType end, IntegerType chunk=0)
{
  IntegerType nthread = boost::thread::hardware_concurrency();
  if (chunk == 0)
    chunk = std::max(IntegerType(1), (end - begin) / (16*nthread));

  detail::Looper<RangeFunctor, IntegerType> looper(begin, end, chunk);
  looper.process(f, nthread);
}

#endif // PARLOOP_H
