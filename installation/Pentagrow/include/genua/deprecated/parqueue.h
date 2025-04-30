
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       parqueue.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Minimum overhead queue for polymorphic tasks
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */
 
#ifndef _GENUA_PARQUEUE_H
#define _GENUA_PARQUEUE_H

#include "threadpool.h"

class ParQueue;

/** Thread task for recursive algorithms.

  Recursive algorithms often require that a parallel task creates a new
  subtask to be processed. This class provides a protected member to append a
  newly creates task to the currently active queue, which can be called by the
  implementation of ThreadTask::work().

  */
class RecursiveTask : public ThreadTask
{
  public:
    
    /// default construction 
    RecursiveTask() : ThreadTask(), tq(0) {}
    
    /// assign container to task
    void assign(ParQueue *q) {tq = q;}  
    
  protected:
    
    /// schedule new task for processing 
    void append(RecursiveTask *t) {
      tq->append(t);
    }
    
  private:
    
    /// pointer to queue
    ParQueue *tq;
};
    
/** Queue for recursive tasks.

  This is a simple task queue which is used for recursive algorithms where each 
  task may need to spawn new tasks to be processed in parallel. Note that 
  ParQueue takes ownership of all contained tasks, so that append() can only be 
  called with a new heap-allocated object.

  */
class ParQueue
{
  public:
    
    /// create a queue using pool p
    ParQueue(ThreadPool & p) : tp(p) {}
    
    /// destroy task objects 
    virtual ~ParQueue() {tcp.dispose();}
    
    /// append a new task object and take ownership 
    void append(RecursiveTask *t) {
      t->assign(this);
      tcp.push(t);
    }
    
    /// process and reduce 
    void process() {
      tp.process(&tcp);
    }
    
    /// process without reduction
    void nrprocess() {
      tp.nrprocess(&tcp);
    }
    
  private:
    
    /// thread pool to use
    ThreadPool & tp;
    
    /// task manager
    TaskContainer tcp;
};

#endif

