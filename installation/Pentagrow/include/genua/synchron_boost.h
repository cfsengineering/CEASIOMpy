
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
 
#ifndef GENUA_SYNCHRON_BOOST_H
#define GENUA_SYNCHRON_BOOST_H

#include "defines.h"
#include <mutex>
#include <condition_variable>

/** Mutex.
  
  Forwards to boost::thread::mutex. This class serves as a compatibility
  layer for existing code which used pthread_mutex_*
  
  As with all code in this file, it should inline completely.

  \ingroup concurrency
  */
class Mutex
{
  public:

    /// acquire lock
    void lock() { mtx.lock(); }

    /// try to lock, return false if unsuccesful
    bool trylock() { return mtx.try_lock(); }

    /// release mutex
    void unlock() { mtx.unlock(); }

  private:

    /// boost mutex
    std::mutex mtx;
};

/** Scoped lock 

  Acquires the mutex passed as argument on construction and releases the same
  on destruction. Useful to implement monitors.
  
  \ingroup concurrency
*/
class ScopedLock
{
  public:
    
    /// acquire mutex
    ScopedLock(Mutex & m) : mx(m) {mx.lock();}
    
    /// release mutex
    ~ScopedLock() {mx.unlock();}
        
  private:
    
    /// reference to mutex
    Mutex & mx;
};

/* boost::thread does not provide a semaphore */

/** Condition variable.

  A pthread Condition variable and its associated Mutex. The Mutex
  can be acquired/released with lock/unlock, while wait() can be used
  to wait on the variable to be signalled. Typical use to wait on a
  expression to become true:
  \verbatim
  Condition cnd;
  [...]
  // thread which relies on (p == true) 
  cnd.lock();
  while (not p)
    cnd.wait();        // releases lock while blocked, then reacquires
  cnd.unlock();
  [..]
  // thread which sets condition p
  cnd.lock()
  p = true;
  cnd.unlock()
  cnd.signal()    // or cnd.broadcast()
  \endverbatim

  \ingroup concurrency
  */
class Condition
{
  public:
    
    typedef std::unique_lock<std::mutex> UniqueLock;

    /// access mutex object
    std::mutex & mutex() {return mtx;}
    
    /// test if p is true. if not, wait. (tests only once)
    void wait(bool p) {
      UniqueLock lck(mtx);
      if (not p)
        cnd.wait(lck);
    }
    
    /// wait for predicate p to become true (will re-check on wakeup)
    template <class Predicate>
    void wait(Predicate p) {
      UniqueLock lck(mtx);
      while (not p()) {
        cnd.wait(lck);
      }
    }
    
    /// signal one waiting thread to wake
    void signal() {
      cnd.notify_one();
    }

    /// broadcast to all threads waiting
    void broadcast() {
      cnd.notify_all();
    }

    /// wait using externally provided lock
    void wait(UniqueLock & lck) {
      cnd.wait(lck);
    }

    /// lock the associated mutex
    void lock() {
      mtx.lock();
    }

    /// unlock the associated mutex
    void unlock() {
      mtx.unlock();
    }

  private:

    /// Mutex for wait()
    std::mutex mtx;

    /// boost condition variable 
    std::condition_variable cnd;
};

///** Reuseable counting barrier.

//  A blocking barrier, which can be used to make threads wait at certain
//  points until all threads (of that group) have arrived at the same
//  point. The threads just call Barrier::wait() when arriving at the
//  synchronization point, whereupon they are blocked. When the n'th
//  thread arrives at last, all waiting threads are woken up and resume.

//  This implementation just forwards to boost::barrier.

//  \ingroup concurrency
//  */
//class Barrier
//{
//  public:

//    /// initialize with number of threads
//    Barrier(uint nthreads = 1) : b(nthreads) {}
    
//    /// called by a thread waiting at the Barrier
//    void wait() {b.wait();}

//  private:

//    /// boost already has a barrier class
//    boost::barrier b;
//};


#endif

