#ifndef FASTWORKQUEUE_H
#define FASTWORKQUEUE_H

#include <boost/thread.hpp>
#include <boost/lockfree/queue.hpp>
#include <boost/container/vector.hpp>
#include <boost/bind.hpp>
#include <boost/atomic.hpp>


/** Work queue with minimal synchronization overhead.
 *
 * Requirements on Functor class:
 * - Default constructible
 * - Copy constructor
 * - Trivial destructor
 *
 */
template <class Functor>
class FastWorkQueue
{
public:

  /// create a work queue and start nthreads worker threads
  FastWorkQueue(int nthreads) : m_queue(1024), m_shutdown(false)
  {
    m_workers.resize(nthreads);
    for (int i=0; i<nthreads; ++i)
      m_workers[i] = boost::thread( boost::bind(&FastWorkQueue::work, this) );
  }

  /// halt all threads on destruction
  ~FastWorkQueue() {
    // important - need to join all workers before synchronization
    // variables which may be in use are destroyed.
    join();
  }

  /// number of threads configured
  int nthread() const {return m_workers.size();}

  /// enqueue a task, but do not start processing
  bool append(Functor f) {
    return m_queue.push( f );
  }

  /// join all worker threads
  void join() {
    m_shutdown = true;
    for (size_t i=0; i<m_workers.size(); ++i) {
      if (m_workers[i].joinable())
        m_workers[i].join();
    }
  }

private:

  /// serving function for worker threads
  void work() {

    do {

      // try to pop off a task w/o wait
      Functor task;
      while ( m_queue.pop(task) )
        task();

      // yield execution slice to next thread
      boost::this_thread::yield();

    } while (not m_shutdown);
  }

protected:

  typedef boost::lockfree::queue<Functor> LockfreeQueue;

  /// container for tasks to perform
  LockfreeQueue m_queue;

  /// worker threads stored in move-aware vector
  boost::container::vector< boost::thread > m_workers;

  /// flag indicating that worker threads should terminate
  bool m_shutdown;
};

namespace detail {

template <class RangeFunctor, typename IntegerType>
class LoopAdaptor
{
public:

  LoopAdaptor() {}

  LoopAdaptor(const RangeFunctor & f, IntegerType a, IntegerType b)
    : m_rf(f), m_begin(a), m_end(b) {}

  void operator() () {
    m_rf(m_begin, m_end);
  }

private:

  /// functor which defines f(a, b)
  RangeFunctor m_rf;

  /// range limits
  IntegerType m_begin, m_end;
};

}

template <class RangeFunctor, class IntegerType = int>
class LoopWorkQueue
    : protected FastWorkQueue<detail::LoopAdaptor<RangeFunctor, IntegerType> >
{
public:

  typedef detail::LoopAdaptor<RangeFunctor, IntegerType>  MappedFunctor;
  typedef FastWorkQueue<MappedFunctor>                    MappedQueue;

  /// construct thread pool with n threads
  LoopWorkQueue(int nthreads) : MappedQueue(nthreads) {}

  /// parallelize a loop with static chunk size
  bool loop(const RangeFunctor &f, IntegerType begin, IntegerType end,
            IntegerType chunk = 1)
  {
    IntegerType ntask, n = end - begin;
    if (chunk == 0) {
      ntask = std::min(n, 8*IntegerType(MappedQueue::nthread()));
      chunk = n/ntask;
    } else {
      ntask = n/chunk + 1;
    }

    IntegerType a(0), b(chunk);
    MappedQueue::m_queue.reserve( ntask );
    for (IntegerType i=0; i<ntask; ++i) {
      bool pushed = MappedQueue::append( MappedFunctor(f, a, b) );
      if (not pushed)
        return false;
      a += chunk;
      b = std::min(a+chunk, end);
    }

    return true;
  }

  /// wait for all threads to complete
  void finish() { MappedQueue::join(); }

};

template <class RangeFunctor, typename IntegerType>
inline bool parallel_loop(const RangeFunctor & f,
                          IntegerType begin, IntegerType end,
                          IntegerType chunk = 1)
{
  size_t nthread = boost::thread::hardware_concurrency();
  LoopWorkQueue<RangeFunctor,IntegerType> queue( nthread );
  bool submitted = queue.loop( f, begin, end, chunk );
  assert(submitted);
  if (submitted) {
    queue.finish();
  }
  return submitted;
}

#endif // FASTWORKQUEUE_H
