
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

#ifndef GENUA_FORKJOINGROUP_H
#define GENUA_FORKJOINGROUP_H

#include "taskgroup.h"
#include "lockedqueue.h"
#include <boost/lockfree/stack.hpp>

namespace detail {

template <class TaskType>
class TaskCounter : public ThreadGroup
{
public:

  /// initialize counters
  TaskCounter() : ThreadGroup(0), m_working(0), m_pending(0) {}

  /// number of jobs submitted but not yet processed (snapshot value)
  intptr_t loadfactor() const {return m_pending.load(std::memory_order_relaxed);}

protected:

  /// entry point for newly created threads
  template <class Container>
  void parallelDo(Container &jobs) {
    do {
      TaskType task;
      if ( jobs.pop(task) ) {
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

protected:

  /// number of currently working (as opposed to waiting) threads
  std::atomic<intptr_t> m_working;

  /// number of pending (submitted but not completed) tasks
  std::atomic<intptr_t> m_pending;
};

template <class TaskType, class Context = int>
class ContextThreadGroup : public ThreadGroup
{
public:

  /// initialize counters
  ContextThreadGroup() : ThreadGroup(0), m_working(0), m_pending(0) {}

  /// number of jobs submitted but not yet processed (snapshot value)
  intptr_t loadfactor() const {return m_pending.load(std::memory_order_relaxed);}

protected:

  /// process tasks which may add more tasks to container
  template <class Container>
  void parallelDo(int threadIndex, Container &jobs, Context *result = nullptr)
  {
    Context ctx(threadIndex);
    do {
      TaskType task;
      if ( jobs.pop(task) ) {
        ++m_working;
        task(ctx);
        --m_pending;
        --m_working;
      } else {
        boost::this_thread::yield();
      }
      if (m_earlyexit)
        return;
    } while ( (m_pending.load() > 0) or (m_working.load() > 0) );

    // reduction step
    if (result != nullptr)
      *result += ctx;
  }

protected:

  /// number of currently working (as opposed to waiting) threads
  std::atomic<intptr_t> m_working;

  /// number of pending (submitted but not completed) tasks
  std::atomic<intptr_t> m_pending;
};

}

/** Isomorphic fork-join multithreading (stack and queue).
 *
 * The ForkJoin containers are used according to the following pattern:
 *
 * \verbatim
 * class Task
 * {
 * public:
 *  void operator() () {
 *    ...
 *    m_queue->push( Task(...) );
 *  }
 * private:
 *  ForkJoinQueue<Task> *m_queue;
 * };
 * ...
 * Task root_task;
 * ...
 * ForkJoinQueue<Task> queue;
 * queue.push( root_task );
 * queue.forkJoin();
 * \endverbatim
 *
 * where we assume that root_task will later on produce more work and push()
 * that to the same queue. This is mostly useful for tree-based algorithms
 * or recursion, where the amount of work is unknown at the start. One initial
 * task must be submitted before threads are forked, otherwise join() will
 * return immediately.
 *
 * \ingroup concurrency
 * \sa ThreadGroup, LockedQueue
 */
template <class TaskType>
class ForkJoinQueue : public detail::TaskCounter<TaskType>
{
private:

  typedef detail::TaskCounter<TaskType> Base;

public:

  /// initialize counters
  ForkJoinQueue() : Base() {}

  /// reserve storage capacity ahead of submittal
  void reserve(size_t capacity) {
    m_tasks.reserve(capacity);
  }

  /// wait for the lock to become available, then submit a new task
  template <class Arg>
  bool push(Arg &&a) {
    ++(Base::m_pending);
    m_tasks.push_back( std::forward<Arg>(a) );
    return true;
  }

  /// submit a task only if the lock is open (does not content the mutex)
  template <class Arg>
  bool try_push(Arg &&a) {
    ++(Base::m_pending);
    bool submitted = m_tasks.try_push_back( std::forward<Arg>(a) );
    if ( submitted ) {
      return true;
    } else {
      --(Base::m_pending);
      return false;
    }
  }

  /// Maintain a healthy task queue.
  /// If the current number of tasks waiting for execution is less than
  /// targetLoad per worker thread, then wait for the lock to be released and
  /// really push the task. Otherwise, if there are less than 4*targetLoad
  /// tasks waiting per worker, then only test the lock and push only if open
  /// anyway.
  template <class Arg>
  bool push_if(Arg &&a, int targetLoad = 4) {
    assert(targetLoad > 0);
    const intptr_t nthreads = ThreadGroup::nworker();
    const intptr_t queueLength = Base::loadfactor();
    const intptr_t desiredLength = targetLoad*nthreads;
    if ( queueLength < desiredLength ) {
      return push( std::forward<Arg>(a) );
    } else if ( queueLength < 4*desiredLength ) {
      return try_push( std::forward<Arg>(a) );
    }
    return false;
  }

  /// wait for the lock to become available, then submit multiple new tasks
  template <class Iterator>
  bool insert(Iterator first, Iterator last) {
    Base::m_pending += std::distance(first, last);
    m_tasks.insert(first, last);
    return true;
  }

  /// wait for the lock to become available, then submit a new task to the front
  template <class Arg>
  bool enqueue(Arg &&a) {
    ++(Base::m_pending);
    m_tasks.push_front( std::forward<Arg>(a) );
    return true;
  }

protected:

  /// drain the task container, then exit
  void work(int) { Base::parallelDo(m_tasks); }

private:

  /// mutex-protected std::deque
  LockedQueue<TaskType> m_tasks;
};

/** Isomorphic fork-join multithreading (stack).
 *
 * Similar to the slightly more flexible ForkJoinQueue, this container only
 * permits to push tasks deterministically to the top of the queue, where
 * they will be popped off first (LIFO). The underlying container is a
 * boost::lockfree::stack which requires that the task type (template argument)
 * has trivial constructors and destructors. If they have not, use a
 * ForkJoinQueue instead.
 *
 * The lockfree container is probably faster at pushing and popping tasks, at
 * least if they are very small (a few pointers). Therefore, use ForkJoinStack
 * if you need to make the work stack fairly tall in order to balance work.
 *
 * \ingroup concurrency
 * \sa ThreadGroup, ForkJoinQueue, boost::lockfree::stack
 */
template <class TaskType>
class ForkJoinStack : public detail::TaskCounter<TaskType>
{
private:

  typedef detail::TaskCounter<TaskType> Base;

public:

  /// initialize counters
  ForkJoinStack() : Base() {}

  /// reserve storage capacity ahead of submittal
  void reserve(size_t capacity) {
    m_tasks.reserve(capacity);
  }

  /// submit a new task (may spuriously fail)
  bool push(const TaskType &task) {
    ++(Base::m_pending);
    bool submitted = m_tasks.push( task );
    if ( submitted ) {
      return true;
    } else {
      --(Base::m_pending);
      return false;
    }
  }

  /// Maintain a healthy task queue.
  /// If the current number of tasks waiting for execution is less than
  /// targetLoad per worker thread, push task; should the queue be longer,
  /// run the task directly in the calling thread instead.
  bool push_if(const TaskType &task, int targetLoad = 16) {
    assert(targetLoad > 0);
    const intptr_t nthreads = ThreadGroup::nworker();
    const intptr_t queueLength = Base::loadfactor();
    const intptr_t desiredLength = targetLoad*nthreads;
    if ( queueLength < desiredLength )
      return push( task );

    return false;
  }

protected:

  /// drain the task container, then exit
  void work(int) { Base::parallelDo(m_tasks); }

private:

  /// container for tasks objects
  boost::lockfree::stack<TaskType> m_tasks;
};

/** Isomorphic multithreading using thread-specific context.
 *
 * This version of a task queue is used when each parallel task needs to access
 * some heavy data structure that therefore should only exist once per thread
 * (instead of once per task). The result of the parallel tasks are then merged
 * by each thread (not task) when the task queue has been drained.
 *
 * \ingroup concurrency
 * \sa ThreadGroup, LockedQueue
 */
template <class TaskType, class Context>
class CtxForkJoinQueue : public detail::ContextThreadGroup<TaskType, Context>
{
private:

  typedef detail::ContextThreadGroup<TaskType, Context> Base;

public:

  /// initialize counters, assign pointer to global context
  CtxForkJoinQueue(Context *ctx = nullptr) : Base(), m_ctx(ctx) {}

  /// reserve storage capacity ahead of submittal
  void reserve(size_t capacity) {
    m_tasks.reserve(capacity);
  }

  /// wait for the lock to become available, then submit a new task
  template <class Arg>
  bool push(Arg && task) {
    ++(Base::m_pending);
    m_tasks.push_back( std::forward(task) );
    return true;
  }

  /// submit a task only if the lock is open (does not contend the mutex)
  template <class Arg>
  bool try_push(Arg && task) {
    ++(Base::m_pending);
    bool submitted = m_tasks.try_push_back( std::forward(task) );
    if ( submitted ) {
      return true;
    } else {
      --(Base::m_pending);
      return false;
    }
  }

  /// Maintain a healthy task queue.
  /// If the current number of tasks waiting for execution is less than
  /// targetLoad per worker thread, then wait for the lock to be released and
  /// really push the task. Otherwise, if there are less than 4*targetLoad
  /// tasks waiting per worker, then only test the lock and push only if open
  /// anyway.
  template <class Arg>
  bool push_if(Arg &&task, int targetLoad = 4) {
    assert(targetLoad > 0);
    const intptr_t nthreads = ThreadGroup::nworker();
    const intptr_t queueLength = Base::loadfactor();
    const intptr_t desiredLength = targetLoad*nthreads;
    if ( queueLength < desiredLength ) {
      return push( std::forward(task) );
    } else if ( queueLength < 4*desiredLength ) {
      return try_push( std::forward(task) );
    }
    return false;
  }

  /// wait for the lock to become available, then submit multiple new tasks
  template <class Iterator>
  bool insert(Iterator first, Iterator last) {
    Base::m_pending += std::distance(first, last);
    m_tasks.insert(first, last);
    return true;
  }

  /// wait for the lock to become available, then enqueue a new task
  template <class Arg>
  bool enqueue(Arg && task) {
    ++(Base::m_pending);
    m_tasks.push_front( std::forward(task) );
    return true;
  }

protected:

  /// drain the task container, then exit
  void work(int threadIndex) { Base::parallelDo(threadIndex, m_tasks, m_ctx); }

private:

  /// mutex-protected std::deque
  LockedQueue<TaskType> m_tasks;

  /// reduction context
  Context *m_ctx = nullptr;
};

#endif // FORKJOINGROUP_H
