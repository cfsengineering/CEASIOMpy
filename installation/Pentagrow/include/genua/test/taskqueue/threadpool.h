#ifndef THREADPOOL_H
#define THREADPOOL_H

#include <boost/thread.hpp>
#include <boost/container/vector.hpp>
#include <boost/lockfree/queue.hpp>
#include <boost/lockfree/stack.hpp>
#include <boost/atomic.hpp>

#include <vector>

/** Handles a group of threads.
 *
 *  ThreadGroup is meant as a base class for work queues/stacks, which performs
 *  handling of thread creation and joining.
 *
 *  \ingroup Concurrency
 *  \sa LockfreePool
 */
class ThreadGroup : public boost::noncopyable
{
public:

  /// create thread container, optionally spawn threads
  ThreadGroup(int startThreads = 0) {
    if (startThreads > 0)
      spawn(startThreads);
  }

  /// join all threads, then destroy container
  virtual ~ThreadGroup() {
    join();
  }

  /// start n (default: hw threads) new threads which call overloaded method work()
  virtual void spawn(int n = -1) {
    if (n <= 0)
      n = boost::thread::hardware_concurrency();
    m_workers.resize(n);
    for (int i=0; i<n; ++i)
      m_workers[i] = boost::thread( &ThreadGroup::work, this );
  }


  virtual void join() {
    for (size_t i=0; i<m_workers.size(); ++i) {
      if (m_workers[i].joinable())
        m_workers[i].join();
    }
  }

protected:

  /// overload this function with the processing loop used by threads
  virtual void work() = 0;

private:

  /// joinable threads
  boost::container::vector<boost::thread> m_workers;
};

template <class Container>
class LockfreePool : public ThreadGroup
{
public:

  typedef typename Container::value_type TaskType;

  LockfreePool(int reserved) : ThreadGroup(0),
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


protected:

  void work() {
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
    } while ( (m_pending.load() > 0) or (m_working.load() > 0) );
  }

private:

  /// container for tasks objects
  Container m_tasks;

  /// number of currently working (as opposed to waiting) threads
  boost::atomic<int> m_working;

  /// number of pending (submitted but not completed) tasks
  boost::atomic<int> m_pending;
};

template <class TaskType>
class WorkStack : public ThreadGroup
{
public:

  /// create blocking stack and reserve space for tasks
  WorkStack(size_t reserved = 64) : ThreadGroup(0), m_pending(0) {
    m_tasks.reserve(reserved);
  }

  /// submit a task and wake up one thread
  bool submit(const TaskType &t) {
    ++m_pending;
    boost::unique_lock<boost::mutex> lock(m_mutex);
    m_tasks.push_back(t);
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

  /// fetch one task, return false if none available
  bool pop(TaskType & t) {
    boost::unique_lock<boost::mutex> lock(m_mutex);
    if (not m_tasks.empty()) {
      t = m_tasks.back();
      m_tasks.pop_back();
      return true;
    } else {
      return false;
    }
  }

  /// thread work function
  void work() {
    do {

      TaskType task;
      if ( pop(task) ) {
        task();
        if ( --m_pending == 0 and m_tasks.empty())
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

    } while ( m_pending.load() > 0 );
  }

  /// wait condition
  bool notQuiteDone() const {
    return (m_tasks.empty() and (m_pending.load() > 0));
  }

private:

  /// container for tasks objects
  std::vector<TaskType> m_tasks;

  /// mutex for stack access
  boost::mutex m_mutex;

  /// condition which indicates that new work is available
  boost::condition_variable m_workpending;

  /// number of pending (submitted but not completed) tasks
  boost::atomic<int> m_pending;
};

#endif // THREADPOOL_H
