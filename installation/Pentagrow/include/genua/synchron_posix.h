
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
 
#ifndef GENUA_SYNCHRON_POSIX_H
#define GENUA_SYNCHRON_POSIX_H
    
#include <cstdlib>
#include <iostream>
#include <pthread.h>
#include <errno.h>
#include <semaphore.h>
#include "defines.h"

#ifndef NDEBUG
inline void _sync_check(int stat, const char *fname)
{
  if (stat == 0) {
    return;
  } else {
    std::cerr << "Synchronization operation failed in call to " << fname << std::endl;
    std::cerr << "Return status: ";
    switch (stat) {
      case EINVAL:
        std::cerr << "EINVAL: primitive not initialized.";
        break;
      case EDEADLK:
        std::cerr << "EDEADLK: calling thread already owns this lock.";
        break;
      case ENOMEM:
        std::cerr << "ENOMEM: lacking memory to initialize primitive.";
        break;
      case EPERM:
        std::cerr << "EPERM: calling thread does not own this primitive.";
        break;
      case EAGAIN:
        std::cerr << "EAGAIN: resources exceeded/too many recursive locks";
        break;
      case EBUSY:
        std::cerr << "EBUSY: primitive in use, cannot be destroyed.";
        break;
      case ENOSYS:
        std::cerr << "ENOSYS: not supported on this system.";
        break;
      case EINTR:
        std::cerr << "EINTR: call interrupted by signal handler.";
        break;
      default:
        std::cerr << stat << " (unknown error code) ";
        break;
    }
    std::cerr << std::endl;
    abort();
  }
}
#else
inline void _sync_check(int, const char *) {}
#endif

/** Mutex.
  
  A thin wrapper around the Mutex functionality of the pthread library. When 
  compiling with NDEBUG not defined, return codes are checked and the program is 
  aborted on error. With NDEBUG defined, return values of the pthread functions 
  are just forwarded.

  TODO : initialize with deadlock detection if NDEBUG is not defined.

  \ingroup concurrency
  */
class Mutex
{
  public:

    /// default initialization
    Mutex() {
      int stat = pthread_mutex_init(&mtx, 0);
      _sync_check(stat, "pthread_mutex_init");
    }

    /// destruction
    ~Mutex() {
      int stat = pthread_mutex_destroy(&mtx);
      _sync_check(stat, "pthread_mutex_destroy");
    }

    /// acquire lock
    int lock() {
      int stat = pthread_mutex_lock(&mtx);
      _sync_check(stat, " pthread_mutex_lock");
      return stat;
    }

    /// try to lock, return false if unsuccesful
    bool trylock() {
      int stat = pthread_mutex_trylock(&mtx);
      if (stat == 0)
        return true;
      else if (stat == EBUSY)
        return false;
      else {
        _sync_check(stat, " pthread_mutex_trylock");
        return false;
      }
    }

    /// release mutex
    int unlock() {
      int stat = pthread_mutex_unlock(&mtx);
      _sync_check(stat, " pthread_mutex_unlock");
      return stat;
    }

  private:

    /// pthread mutex
    pthread_mutex_t mtx;
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

/** Posix thread semaphore.
 *
 * \ingroup concurrency
 */
class Semaphore
{
  public:
    
    /// initialize semaphore
    Semaphore(int value) {
      int stat = sem_init(&s, 0, value);
      _sync_check( (stat != 0) ? (errno) : 0, "sem_init");
    }

    /// release resources
    ~Semaphore() {
      int stat = sem_destroy(&s);
      _sync_check( (stat != 0) ? (errno) : 0, "sem_destroy");
    }
    
    /// wait on semaphore (block, -1)
    void wait() {
      int stat = sem_wait(&s);
      _sync_check( (stat != 0) ? (errno) : 0, "sem_wait");
    }
    
    /// post semaphore (+1)
    void post() {
      int stat = sem_post(&s);
      _sync_check( (stat != 0) ? (errno) : 0, "sem_post");
    }
    
    /// read current value
    int value() {
      int stat, v(0);
      stat = sem_getvalue(&s, &v);
      _sync_check( (stat != 0) ? (errno) : 0, "sem_getvalue");
      return v;
    }
    
  private:
    
    /// pthread semaphore
    sem_t s;
};

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

    /// default initialization
    Condition() {
      int stat;
      stat = pthread_mutex_init(&mtx, 0);
      _sync_check(stat, "pthread_mutex_init");
      stat = pthread_cond_init(&cnd, 0);
      _sync_check(stat, "pthread_cond_init");
    }

    /// destruction
    ~Condition() {
       int stat;
       stat = pthread_cond_destroy(&cnd);
       _sync_check(stat, "pthread_cond_destroy");
       stat = pthread_mutex_destroy(&mtx);
       _sync_check(stat, "pthread_mutex_destroy");
    }

    /// test if p is true. if not, wait. (tests only once)
    void wait(bool p) {
      lock();
      if (not p)
        wait();
      unlock();
    }
    
    /// wait for predicate p to become true (will re-check on wakeup)
    template <class Predicate>
    void wait(Predicate p) {
      lock();
      while (not p())
        wait();
      unlock();
    }
    
    /// signal one waiting thread to wake
    int signal() {
      int stat = pthread_cond_signal(&cnd);
      _sync_check(stat, "pthread_cond_signal");
      return stat;
    }

    /// broadcast to all threads waiting
    int broadcast() {
      int stat = pthread_cond_broadcast(&cnd);
      _sync_check(stat, "pthread_cond_broadcast");
      return stat;
    }

    /// wait for this condition (to be signalled)
    int wait() {
      int stat = pthread_cond_wait(&cnd, &mtx);
      _sync_check(stat, "pthread_cond_wait");
      return stat;
    }

    /// lock the associated Mutex
    int lock() {
      int stat = pthread_mutex_lock(&mtx);
      _sync_check(stat, "pthread_mutex_lock");
      return stat;
    }

    /// unlock the above
    int unlock() {
      int stat = pthread_mutex_unlock(&mtx);
      _sync_check(stat, "pthread_mutex_unlock");
      return stat;
    }

  private:

    /// Mutex for wait()
    pthread_mutex_t mtx;

    /// pthread Condition
    pthread_cond_t cnd;
};

/** Reuseable counting barrier.

  A blocking barrier, which can be used to make threads wait at certain
  points until all threads (of that group) have arrived at the same
  point. The threads just call Barrier::wait() when arriving at the
  synchronization point, whereupon they are blocked. When the n'th
  thread arrives at last, all waiting threads are woken up and resume.

  \ingroup concurrency
  */
class Barrier
{
  public:

    /// initialize with number of threads
    Barrier(uint nthreads = 1) : nt(nthreads), here(0) {}
    
    /// change the number of threads upon which to wait
    void resize(uint nthreads) {nt = nthreads;}

    /// called by a thread waiting at the Barrier
    void wait();

  private:

    /// total number of threads and of those come to Barrier
    uint nt, here;

    /// Condition to wait on
    Condition cnd;
};


#endif

