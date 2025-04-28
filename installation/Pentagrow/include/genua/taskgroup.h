
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

#ifndef GENUA_TASKGROUP_H
#define GENUA_TASKGROUP_H

// if compiler complains about missing overload for move(...)
// define BOOST_THREAD_USES_MOVE and BOOST_THREAD_VERSION >= 3

#include "defines.h"
#include <boost/thread.hpp>
#include <boost/container/vector.hpp>
#include <boost/lockfree/queue.hpp>
#include <boost/lockfree/stack.hpp>

#include <vector>
#include <deque>
#include <atomic>
#include <mutex>

/** Handles a group of threads (boost, C++98)
 *
 * ThreadGroup is meant as a base class for work queues/stacks, which performs
 * handling of thread creation and joining.
 *
 * Classes ThreadGroup, LockfreePool and WorkStack are implemented for parallel
 * processing of task objects with value-semantics. They are therefore most
 * applicable in data-parallel settings or for recursive tree algorithms where
 * all tasks have the same type and can be copied cheaply (bunch of pointers).
 *
 * Implementation predates support for C++ 2011: due to the need to declare
 * the task containers with task type names, they are not particularly
 * convenient for use with lambdas or for a system-wide central task queue
 * similar to GCD.
 *
 * On the other hand, inspection of assembly output shows that the compiler is
 * usually able to inline small task functions inside the run() method of
 * LockfreePool or WorkStack, provided it can see the task implementation. This
 * may help to reduce indirection overhead (indirect function calls) for
 * fine-grained tasks.
 *
 * \ingroup concurrency
 * \sa LockfreePool, WorkStack
 */
class ThreadGroup : public boost::noncopyable
{
public:

  /// create thread container, optionally spawn threads
  ThreadGroup(int startThreads = 0) : m_earlyexit(false) {
    if (startThreads > 0)
      spawn(startThreads);
  }

  /// join all threads, then destroy container
  virtual ~ThreadGroup() {
    // ask remaining active workers to terminate early
    m_earlyexit = true;
    join();
  }

  /// start n (default: hw threads) new threads which call overloaded method work()
  virtual void spawn(int n = -1) {
    if (n <= 0)
      n = boost::thread::hardware_concurrency();
    m_workers.resize(n);
    for (int i=0; i<n; ++i)
      m_workers[i] = boost::thread( &ThreadGroup::work, this, i );
  }

  /// wait for all threads to finish
  virtual void join() {
    for (size_t i=0; i<m_workers.size(); ++i) {
      if (m_workers[i].joinable())
        m_workers[i].join();
    }
  }

  /// spawn threads and wait until all have completed their work
  void forkJoin(int n = -1) {
    this->spawn(n);
    this->join();
  }

  /// set the termination flag
  void requestInterruption(bool flag) {m_earlyexit = flag;}

  /// number of threads created
  size_t nworker() const {return m_workers.size();}

protected:

  /// overload this function with the processing loop used by threads
  virtual void work(int i) = 0;

protected:

  /// early exit flag; if this is set, then worker threads should exit
  std::atomic<bool> m_earlyexit;

private:

  /// joinable threads
  boost::container::vector<boost::thread> m_workers;
};

/** Lock-free task container.
 *
 * This is a primitive and rather limited lock-free container wrapper which only
 * stores POD tasks of a single type. It would typically be instantiated with a
 * lock-free boost container, which also means that the task objects to be
 * stored need to be POD.
 *
 * The restrictions of the lockfree container template argument make this
 * class useful mostly for specialized usages within libraries, such as for
 * low-overhead parallel sorting or recursive algorithms.
 *
 * \ingroup concurrency
 * \sa ThreadGroup, WorkStack
 */
template <class Container>
class LockfreePool : public ThreadGroup
{
public:

  typedef typename Container::value_type TaskType;

  LockfreePool(int reserved = 32) : ThreadGroup(0),
    m_tasks(reserved), m_working(0), m_pending(0) {}

  /// reserve storage capacity ahead of submittal
  void reserve(size_t capacity) {
    m_tasks.reserve(capacity);
  }

  /// submit a task (thread-safe, lockfree) and increment pending work count
  bool submit(const TaskType &task) {
    ++m_pending;
    bool submitted = m_tasks.push( task );
    if ( submitted ) {
      return true;
    } else {
      --m_pending;
      return false;
    }
  }

  /// submit only if load is low
  bool submit_if(const TaskType &task, int targetLoad = 16) {
    const int desiredLength = targetLoad * nworker();
    if ( loadfactor() < desiredLength )
      return submit(task);
    return false;
  }

  /// number of submitted jobs
  int loadfactor() const {return m_pending;}

protected:

  void work(int) {
    do {
      TaskType task;
      if ( m_tasks.pop(task) ) {
        ++m_working;
        task();
        --m_pending;
        --m_working;
      } else {
        boost::this_thread::yield();
      }
      if (m_earlyexit)
        return;
    } while ( (m_pending.load() > 0) or (m_working.load() > 0) );
  }

private:

  /// container for tasks objects
  Container m_tasks;

  /// number of currently working (as opposed to waiting) threads
  std::atomic<int> m_working;

  /// number of pending (submitted but not completed) tasks
  std::atomic<int> m_pending;
};

/** Last-in, first-out task stack.
 *
 * This is a synchronized stack (using std::vector) with an attached
 * ThreadGroup. Use this task container if the algorithm benefits from
 * temporal locality issues, that is, when you want tasks to be executed in a
 * LIFO manner. Many tree-based or recursive algorithms benefit from this type
 * of locality because the topmost (last) tasks typically work on data which is
 * close to the memory block processed by the last task.
 *
 * \todo Implement corresponing FIFO queue.
 *
 * \ingroup concurrency
 * \sa ThreadGroup
 */
template <class TaskType>
class WorkStack : public ThreadGroup
{
public:

  /// create blocking stack and reserve space for tasks
  WorkStack(size_t /* reserved = 64 */) : ThreadGroup(0), m_pending(0), m_popped(0) {
    // m_tasks.reserve(reserved);
  }

  /// submit a task and wake up one thread
  bool submit(const TaskType &t) {
    ++m_pending;
    boost::unique_lock<boost::mutex> lock(m_mutex);
    m_tasks.push_back(t);
    m_workpending.notify_one();
    return true;
  }

  //  /// submit a task and wake up one thread
  //  bool submit(TaskType &&t) {
  //    ++m_pending;
  //    boost::unique_lock<boost::mutex> lock(m_mutex);
  //    m_tasks.push_back(std::move(t));
  //    m_workpending.notify_one();
  //    return true;
  //  }

  /// common pattern: submit two jobs (tree recursion)
  bool submit(const TaskType &a, const TaskType &b) {
    m_pending += 2;
    boost::unique_lock<boost::mutex> lock(m_mutex);
    m_tasks.push_back(a);
    m_tasks.push_back(b);
    m_workpending.notify_all();
    return true;
  }

  /// common pattern: submit two jobs (tree recursion)
  bool submit(TaskType &&a, TaskType &&b) {
    m_pending += 2;
    boost::unique_lock<boost::mutex> lock(m_mutex);
    m_tasks.push_back(std::move(a));
    m_tasks.push_back(std::move(b));
    m_workpending.notify_all();
    return true;
  }

  /// submit many tasks at once, only lock one time
  bool submit(size_t n, const TaskType t[]) {
    m_pending += n;
    boost::unique_lock<boost::mutex> lock(m_mutex);
    m_tasks.insert( m_tasks.end(), t, t+n );
    if (n > 1)
      m_workpending.notify_all();
    else
      m_workpending.notify_one();
    return true;
  }

  /// wakeup all waiting threads
  void wakeup() {
    boost::unique_lock<boost::mutex> lock(m_mutex);
    m_workpending.notify_all();
  }

  /// joining threads requires wakeup
  void join() {
    wakeup();
    ThreadGroup::join();
  }

protected:

  //  /// fetch one task, return false if none available
  //  bool pop(TaskType & t) {
  //    boost::unique_lock<boost::mutex> lock(m_mutex);
  //    if (not m_tasks.empty()) {
  //      t = std::move( m_tasks.back() );
  //      m_tasks.pop_back();
  //      return true;
  //    } else {
  //      return false;
  //    }
  //  }

  /// index-based task retrieval, only works without reallocation!
  uint pop() {
    // boost::unique_lock<boost::mutex> lock(m_mutex);
    if (m_popped.load() < m_tasks.size()) {
      return m_popped.fetch_add(1);
    } else {
      return NotFound;
    }
  }

  /// thread work function
  void work(int) {

    do {

      // this requires that iterators remain valid
      uint itask = pop();
      uint ntask = m_tasks.size();
      if ( itask < ntask ) {
        m_tasks[itask]();
        --m_pending;
        if ( (m_pending.load() <= 0) and empty() )
          wakeup();
      } else {

        boost::this_thread::yield();

        // thing is, the stack may be empty, but there could be some other
        // threads still working on the last tasks (m_pending > 0) which,
        // then, may add additional work to the stack
        boost::unique_lock<boost::mutex> lock(m_mutex);
        while ( notQuiteDone() )
          m_workpending.wait( lock );
      }

      if (m_earlyexit)
        return;

    } while ( m_pending.load() > 0 );
  }

  /// wait condition: task container drained, but someone still working
  bool notQuiteDone() const {
    return (empty() and (m_pending.load() > 0));
  }

  /// no tasks left
  bool empty() const {
    return m_tasks.size() <= m_popped;
  }

private:

  /// container for tasks objects
  std::deque<TaskType> m_tasks;

  /// mutex for stack access
  boost::mutex m_mutex;

  /// condition which indicates that new work is available
  boost::condition_variable m_workpending;

  /// number of pending (submitted but not completed) tasks
  std::atomic<int> m_pending;

  /// number of tasks popped off until now
  std::atomic<int> m_popped;
};

#endif // TASKGROUP_H
