#ifndef LOCKEDWORKQUEUE_H
#define LOCKEDWORKQUEUE_H

#include <genua/synchron.h>

#include <boost/thread.hpp>
#include <boost/container/vector.hpp>
#include <boost/bind.hpp>
#include <boost/atomic.hpp>

#include <deque>

// Does not work yet.

class LockedWorkQueue
{
public:

  LockedWorkQueue(int nthreads = -1)
    : m_idle(0), m_submitted(0), m_completed(0), m_shutdown(false)
  {
    if (nthreads <= 0)
      nthreads = boost::thread::hardware_concurrency();
    m_workers.resize(nthreads);
    for (int i=0; i<nthreads; ++i)
      m_workers[i] = boost::thread( boost::bind(&LockedWorkQueue::work, this) );
  }

  ~LockedWorkQueue() {
    join();
  }

  /// number of worker threads
  int nthread() const {return m_workers.size();}

  /// append a single task
  void append(const boost::function<void()> &f) {
    m_jobs.lock();
    m_queue.push_back( f );
    m_jobs.unlock();
    ++m_submitted;
  }

  /// notify all threads that new work is available
  void notify() {
    m_jobs.broadcast();
  }

  /// join all worker threads
  void join() {
    m_shutdown = true;
    m_jobs.broadcast();
    for (size_t i=0; i<m_workers.size(); ++i) {
      if (m_workers[i].joinable())
        m_workers[i].join();
    }
  }

  /// wait until end of work signalled
  void wait() {
    if (allWorkDone())
      return;
    m_done.wait( boost::bind(&LockedWorkQueue::allWorkDone, this) );
  }

private:

  /// function for worker threads to execute
  void work() {
    while (not m_shutdown) {
      m_jobs.lock();
      if (not m_queue.empty()) {
        boost::function<void()> task( m_queue.front() );
        m_queue.pop_front();
        m_jobs.unlock();
        task();
        ++m_completed;
      } else if (m_shutdown) {
        m_jobs.unlock();
        m_done.broadcast();
        return;
      } else {
        m_jobs.unlock();
        ++m_idle;
        m_done.broadcast();
        m_jobs.wait( boost::bind(&LockedWorkQueue::workAvailable, this) );
        --m_idle;
      }
    }
  }

  /// test whether there is any work to be done
  bool workAvailable() const {
    return (not m_queue.empty()) or m_shutdown;
  }

  /// whether all work has been completed
  bool allWorkDone() const {
    return m_queue.empty() and (nthread() == m_idle.load());
  }

private:

  /// queue
  std::deque<boost::function<void()> > m_queue;

  /// worker threads
  boost::container::vector<boost::thread> m_workers;

  /// condition variable for task queue
  Condition m_jobs;

  /// condition variable for completed work
  Condition m_done;

  /// counts
  boost::atomic<int> m_idle, m_submitted, m_completed;

  /// whether to shutdown worker threads
  bool m_shutdown;
};

template <class RangeFunctor, typename IntegerType>
inline void locked_loop(const RangeFunctor & f,
                          IntegerType begin, IntegerType end,
                          IntegerType chunk = 1)
{
  LockedWorkQueue wq;

  IntegerType ntask, n = end - begin;
  ntask = n/chunk + 1;
  IntegerType a(0), b(chunk);
  for (IntegerType i=0; i<ntask; ++i) {
    wq.append( boost::bind(f, a, b) );
    a += chunk;
    b = std::min(a+chunk, end);
  }
  wq.notify();
  wq.wait();
}

#endif // LOCKEDWORKQUEUE_H
