
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
 
#include "xcept.h"
#include "threadpool.h"

#ifndef USE_PTHREADS
#error "Compiling posix-thread version with USE_PTHREADS undefined."
#endif

void *threadpool_worker(void *ptr)
{
  ThreadPool & tp( *(static_cast<ThreadPool*>(ptr)) );
  tp.serve();
  return (void *) 0;
}
        
ThreadPool::ThreadPool(uint n) 
    : ptodo(0), nthreads(0), nidle(0), bterminate(false)
{
  start(n);
}
        
void ThreadPool::start(uint n)
{
  // set up attribute to use for worker threads
  pthread_attr_t attr;
  pthread_attr_init(&attr);
  pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
  
  // start worker threads
  nthreads = 0;
  nidle = 0;
  int stat;
  for (uint i=0; i<n; ++i) {
    pthread_t tmp;
    stat = pthread_create(&tmp, &attr, threadpool_worker, (void *) this);
    if (stat == EAGAIN)
      throw Error("pthread_create() - Too many threads.");
    else if (stat == EINVAL)
      throw Error("pthread_create() - Invalid attributes.");
    else if (stat == ENOMEM)
      throw Error("pthread_create() - Out of memory: Decrease stack size.");
    ++nthreads;
  }  
  
  // destroy attributes
  pthread_attr_destroy(&attr);
}

void ThreadPool::die() {
  cdone.lock();
  --nthreads;

  // if this is the last thread to finish, signal cdone so that the
  // destructor knows it may destroy sync objects. if not, make sure to
  // wake up any lagging worker threads
  if (nthreads == 0)
    cdone.signal();
  else
    cwork.signal();

  cdone.unlock();
}

ThreadPool::~ThreadPool()
{
  if (nthreads > 0) {
    bterminate = true;
    cwork.broadcast();
    cdone.lock();
    while (nthreads > 0) 
      cdone.wait();
    cdone.unlock();
  }
}

