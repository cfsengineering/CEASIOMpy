
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       taskqueue.h
 * begin:      May 2007
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * updated task queue for multithreaded processing
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */
 
#ifndef _GENUA_TASKQUEUE_H
#define _GENUA_TASKQUEUE_H

#include <deque>
#include "synchron.h"
#include "threadtask.h"

/** Queue for tasks to be executed asynchronously.

  BasicTaskQueue starts n worker threads on construction and keeps them alive 
  during the lifetime of the object. New tasks can be added at any time, even
  if the queue is currently processed. 

  After appending jobs, process() is called to start parallel processing of the
  task items. Process() is useful since it returns only after all work items
  have been completed.

  */
class BasicTaskQueue
{
  public:
  
    /// create a new queue, start n threads
    BasicTaskQueue(uint n);
  
    /// terminate worker threads
    ~BasicTaskQueue();
    
    /// true if nothing to do
    bool empty() const {return todo.empty();}
    
    /// number of jobs in queue
    uint size() const {return todo.size();}
    
    /// number of worker threads
    uint nworker() const {return nthreads;}
    
    /// add a new job, take ownership 
    void append(ThreadTask *tp, bool runnow = false) {
      append(TaskPtr(tp), runnow);
    }
    
    /// add a new job 
    void append(const TaskPtr & tp, bool runnow = false) {
      cwork.lock();
      todo.push_back(tp);
      cwork.unlock();
      if ( (bprocessing or runnow) and (nidle > 0) )
        cwork.signal();
    }
    
    /// process tasks currently in queue
    void process() {
      if (todo.empty())
        return;
      
      if (nthreads == 0) {
        const uint ntask(todo.size());
        for (uint i=0; i<ntask; ++i) {
          todo[i]->work();
          todo[i]->reduce();
        }
        todo.clear();
      } else {
        bprocessing = true;
        cwork.broadcast();
        cdone.lock();
        while (not empty())
          cdone.wait();
        cdone.unlock();
        bprocessing = false;
        
        const uint nr(qdone.size());
        for (uint i=0; i<nr; ++i)
          qdone[i]->reduce();
        qdone.clear();
      }
    }
    
    /// process next item or wait if necessary (called by work thread)
    void serve() {
      TaskPtr task;
      do {
        cwork.lock();
        while (todo.empty()) {
          idle();
          cwork.wait();
          wakeup();
          if (bterminate) {
            cwork.unlock();
            die();
            return;
          }
        }
        if (not todo.empty()) {
          task = todo.front();
          todo.pop_front();
        } else {
          task.reset();
        }
        cwork.unlock();
        if (task) {
          task->work();
          cdone.lock();
          qdone.push_back(task);
          cdone.unlock();
        }
      } while (not bterminate);
      die();
    }
    
  private:
    
    /// cannot initialize without workers
    BasicTaskQueue() {}
    
    /// increment idle count
    void idle() {
      cdone.lock();
      ++nidle;
      cdone.unlock();
      if (nidle == nthreads and todo.empty())
        cdone.signal();
    }
    
    /// decrement idle count
    void wakeup() {
      cdone.lock();
      --nidle;
      cdone.unlock();
    }
    
    /// terminate thread 
    void die() {
      cdone.lock();
      --nthreads;
      cdone.unlock();
      
      // if this is the last thread to finish, signal cdone so that the
      // destructor knows it may destroy sync objects. if not, make sure to
      // wake up any lagging work threads
      if (nthreads == 0) 
        cdone.signal();
      else
        cwork.signal();
    }
    
  private:
    
    /// job queues
    TaskDeque todo, qdone;
    
    /// condition on which idle threads will wait
    Condition cwork;
    
    /// condition signalled when work completed
    Condition cdone;
    
    /// number of running and idle threads
    uint nthreads, nidle;
    
    /// set to true when threads should exit
    bool bterminate, bprocessing;
};

#endif

