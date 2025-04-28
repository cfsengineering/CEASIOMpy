
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
 
#ifndef GENUA_TASKSYSTEM_H
#define GENUA_TASKSYSTEM_H

// NOTE
// Including this file anywhere breaks compilation with MSVC 2013
// First compiler error is "identifier HRESULT undefined" in concrt.h

#include "defines.h"
#include <mutex>
#include <deque>
#include <vector>
#include <functional>
#include <atomic>
#include <thread>
#include <condition_variable>

/** Simple task queue. (C++11)
 *
 * A first-in, first-out queue based on a mutex-protected std::deque. In order
 * to avoid contention on the single mutex, this queue is best employed in a
 * context where it is possible to *optionally* enqueue work. An example would
 * be an application where additional work can be performed whenever the
 * try_push() method returns false (i.e. the task could not be enqueued).
 *
 * In order to avoid unnecessary copies, prefer push(std::move(...)) whenever
 * possible.
 *
 * \b Note: This will likely not perform well with many small on systems with
 * a global memory allocation lock (e.g. Win XP).
 *
 * \ingroup concurrency
 * \sa TaskSystem, parallel::invoke
 */
class FunctionQueue
{
  typedef std::unique_lock<std::mutex> UniqueLock;

public:

  /// attempt to fetch a new task from queue, return true if that succeeded
  bool try_pop(std::function<void()> &x)
  {
    UniqueLock lock(m_mutex, std::try_to_lock);
    if ((not lock) or m_queue.empty())
      return false;
    x = std::move(m_queue.front());
    m_queue.pop_front();
    return true;
  }

  /// attempt to append a new task to the queue, return success
  template<typename F>
  bool try_push(F&& f) {
    {
      UniqueLock lock(m_mutex, std::try_to_lock);
      if (not lock)
        return false;
      m_queue.emplace_back(std::forward<F>(f));
    }
    m_ready.notify_one();
    return true;
  }

  /// mark all work as completed, i.e. no more tasks will be pushed
  void done();

  /// retrieve a new task, blocks until one is available or all done
  bool pop(std::function<void()>& x);

  /// append a new task; blocks until queue is available
  template<typename F>
  void push(F&& f) {
    {
      UniqueLock lock(m_mutex);
      m_queue.emplace_back(std::forward<F>(f));
    }
    m_ready.notify_one();
  }

  /// estimate (!) number of jobs in the queue
  size_t loadfactor() const {return m_queue.size();}

  /// lock, then clear out all tasks, but do not set 'done' flag
  void clear();

private:

  /// task queue protected by mutex
  std::deque<std::function<void()> > m_queue;

  /// guards the task queue
  std::mutex m_mutex;

  /// notifies threads waiting in pop()
  std::condition_variable m_ready;

  /// true if no more tasks will be appended
  bool m_done = false;
};

/** Task-stealing thread pool. (C++11)
 *
 * This is a relatively simple task scheduler which creates one thread and one
 * FunctionQueue per hardware thread, which start looking for work on creation.
 * Since FunctionQueue stores objects of type std::function, each task creation
 * typically implies at least one heap allocation in order to erase the type;
 * furthermore, the compiler will not be able to inline the task bodies into
 * the scheduler due to the indirect calls.
 *
 * However, since the enqueing and fetching of task objects is performed with
 * very little lock contention, this scheduler should be more suitable for
 * problems which generate very many (thousands) tasks or where a very dynamic
 * behavior (e.g. tasks creating variable numbers of new tasks of uneven cost).
 *
 * When the task type for a specific problem is fixed and POD and the number of
 * parallel jobs is known to be moderate, WorkStack or LockfreePool may be
 * preferable.
 *
 * \ingroup concurrency
 * \sa FunctionQueue, parallel::invoke
 */
class TaskScheduler
{
public:

  /// setup task system with one thread per logical processor core
  TaskScheduler();

  /// mark all tasks as completed and join worker threads
  ~TaskScheduler();

  /** Schedule f for asynchronuous execution.
   *
   *  1. Start the 'next' task queue, one past the one last tried
   *  2. Attempt to enqueue there; if it doesn't work (locked), go to the next
   *  3. Try each queue once if it still didn't succeed
   *  4. Only if all else fails, wait until queue tried first becomes unlocked
   *
   *  Any successfull push in any of the queues will notify one waiting
   *  thread (if there is any sleeping).
   */
  template <typename F>
  void enqueue(F&& f) {
    auto i = m_qindex++;
    for (uint n = 0; n < m_ncores; ++n) {
      if (m_queues[(i + n) % m_ncores].try_push(std::forward<F>(f)))
        return;
    }
    m_queues[i % m_ncores].push(std::forward<F>(f));
  }

  /// returns the approximate (!) number of jobs waiting to be processed
  size_t loadfactor() const {
    size_t n = 0;
    for (const FunctionQueue &q : m_queues)
      n += q.loadfactor();
    return n;
  }

  /// erase all remaining unfinished tasks (running tasks are not touched)
  void sweep();

  /// access the (centralized) system task pool
  static TaskScheduler &pool() {return s_pool;}

private:

  /** Execute the next task in line.
   *
   * This is the function called by thread i; it first tries to pop off a new
   * task from queue i. If that queue is locked or empty, cycle through the
   * other queues a few times trying to steal a task there. If even that fails,
   * waits for notification on queue i.
   *
   * \todo Will only wake up when queue i is notified - hmm.
   */
  void run(unsigned i);

private:

  /// number of threads and queues - must be a constant
  const uint m_ncores = std::thread::hardware_concurrency();

  /// holds the index of the task queue to feed next (mod m_count)
  std::atomic<uint> m_qindex;

  /// m_count threads, one per logical core
  std::vector<std::thread> m_threads;

  /// one task queue per thread
  std::vector<FunctionQueue> m_queues = std::vector<FunctionQueue>(m_ncores);

  /// global system pool
  static TaskScheduler s_pool;
};

/** Mechanism to wait for completion of a set of tasks.
 *
 *
 * \todo
 * - Investigate task object lifetime implications
 *
 * \ingroup experimental
 * \sa TaskScheduler
 */
class TaskContext
{
  typedef std::unique_lock<std::mutex> UniqueLock;

public:

  /// create a new context
  TaskContext() : m_enqeued(0) {}

  /// create a new context with it's own scheduler
  TaskContext(TaskScheduler &s) : m_enqeued(0), m_scheduler(s) {}

  /// enqueue a task for execution and run when resources available
  template <typename F>
  void enqueue(F&& f) {
    this->submit(1);
    m_scheduler.enqueue( [&](){ f(); this->completed(); } );
  }

  /// wait until all submitted tasks are completed
  void wait();

private:

  /// register that n more tasks will be committed to the queue
  void submit(uint n=1) { m_enqeued += n; }

  /// register one task as completed
  void completed() {
    assert(m_enqeued > 0);
    --m_enqeued;
    if ( 0 == m_enqeued.load(std::memory_order_acquire) )
      m_completed.notify_all();
  }

private:

  /// number of tasks in queue but not completed
  std::atomic<uint> m_enqeued;

  /// thread pool to use
  TaskScheduler &m_scheduler = TaskScheduler::pool();

  /// notified when all tasks completed
  std::condition_variable m_completed;

  /// mutex to protect cv
  std::mutex m_mutex;
};

namespace parallel {

/** Enqueue tasks and return immediately.
 *
 * parallell::enqueue submits jobs for parallel execution in the default
 * system task queue and return directly without waiting for the tasks to
 * complete. In order to allow for the caller to wait for completion, the
 * TaskCounter c is incremented correspondingly. A typical usage pattern
 * will involve tasks which decrement the task counter before terminating.
 *
 * \ingroup experimental
 * \sa TaskScheduler, TaskCounter, parallel::invoke
 */
template <class F1, class F2>
inline void enqueue(TaskContext &c, F1 &&g1, F2 &&g2)
{
  c.enqueue( std::forward<F1>(g1) );
  c.enqueue( std::forward<F2>(g2) );
}

template <class F1, class F2, class F3>
inline void enqueue(TaskContext &c, F1 &&g1, F2 &&g2, F3 &&g3)
{
  c.enqueue( std::forward<F1>(g1) );
  c.enqueue( std::forward<F2>(g2) );
  c.enqueue( std::forward<F3>(g3) );
}

template <class F1, class F2, class F3, class F4>
inline void enqueue(TaskContext &c, F1 &&g1, F2 &&g2, F3 &&g3, F4 &&g4)
{
  c.enqueue( std::forward<F1>(g1) );
  c.enqueue( std::forward<F2>(g2) );
  c.enqueue( std::forward<F3>(g3) );
  c.enqueue( std::forward<F4>(g4) );
}

// TODO : Variadic template version for more args

/** Execute tasks in parallel, return when all have finished.
 *
 * Unlike parallel::enqueue, parallel::invoke does not return before all
 * tasks passed as arguments have been processed. For consistency with other
 * implementations such as TBB, the last task in the argument list will be
 * executed by the calling thread and all other tasks send to the system
 * thread pool.
 *
 * \ingroup experimental
 * \sa TaskScheduler, TaskCounter, parallel::enqueue
 */
template <class F1, class F2>
inline void invoke(F1 &&g1, F2 &&g2)
{
  TaskContext c;
  c.enqueue( std::forward<F1>(g1) );
  g2();
  c.wait();
}

template <class F1, class F2, class F3>
inline void invoke(F1 &&g1, F2 &&g2, F3 &&g3)
{
  TaskContext c;
  c.enqueue( std::forward<F1>(g1) );
  c.enqueue( std::forward<F2>(g2) );
  g3();
  c.wait();
}

template <class F1, class F2, class F3, class F4>
inline void invoke(F1 &&g1, F2 &&g2, F3 &&g3, F4 &&g4)
{
  TaskContext c;
  c.enqueue( std::forward<F1>(g1) );
  c.enqueue( std::forward<F2>(g2) );
  c.enqueue( std::forward<F3>(g3) );
  g4();
  c.wait();
}

// TODO : Variadic template version for more args

}

#endif // TASKSYSTEM_H

