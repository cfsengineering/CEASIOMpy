
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       taskqueue.cpp
 * begin:      May 2007
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * updated task queue for multithreaded processing
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#include "taskqueue.h"

void *basic_threadqueue_worker(void *ptr)
{
  BasicTaskQueue & tq( *(static_cast<BasicTaskQueue*>(ptr)) );
  tq.serve();
  return (void *) 0;
}
    
// ---------------- BasicTaskQueue -----------------------------------------
    
BasicTaskQueue::BasicTaskQueue(uint n) : nthreads(0), nidle(0), 
                                         bterminate(false), bprocessing(false)
{
  // set up attribute to use for worker threads
  pthread_attr_t attr;
  pthread_attr_init(&attr);
  pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
  
  // start worker threads
  for (uint i=0; i<n; ++i) {
    ++nthreads;
    pthread_t tmp;
    pthread_create(&tmp, &attr, basic_threadqueue_worker, (void *) this);
  }  
  
  // destroy attributes
  pthread_attr_destroy(&attr);
}

BasicTaskQueue::~BasicTaskQueue()
{
  if (nthreads > 0) {
    cwork.lock();
    bterminate = true;
    cwork.unlock();
    cwork.broadcast();
    cdone.lock();
    while (nthreads > 0) 
      cdone.wait();
    cdone.unlock();
  }
}


