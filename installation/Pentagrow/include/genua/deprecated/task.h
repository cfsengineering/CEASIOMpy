
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       task.h
 * begin:      Jan 2003, major changes fall 2005
 * copyright:  (c) 2005 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Deprecated implementation of task-parallel processing
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#ifndef _GENUA_TASK_H
#define _GENUA_TASK_H

#include <deque>
#include <boost/shared_ptr.hpp>
#include "thread.h"
#include "synchron.h"
#include "dvector.h"
#include "threadtask.h"

typedef std::vector<TaskPtr> TaskList;

/** Task for multithreaded processing.

  Derive from this class to define a task which requires a serial
  reduction step after parallel work has been performed.
 */
class ReductionTask
{
  public:

    /// empty contruction
    ReductionTask() : id(0), ntr(0) {}
    
    /// virtual destructor
    virtual ~ReductionTask() {}

    /// implement this method to perform the parallel work
    virtual void work() = 0;
    
    /// implement this to perform a scalar reduction
    virtual void reduce(Real & r) const;

    /// implement this to perform a vector reduction
    virtual void reduce(Vector & r) const;
    
    /// implement this to perform a vector reduction
    virtual void reduce(CpxVector & r) const;
    
    /// implement this to perform a vector reduction
    virtual void reduce(Real *r) const;
    
    /// implement this to perform a vector reduction
    virtual void reduce(Complex *r) const;

    /// called by processing thread to set identity
    void setThreadId(uint tid, uint nt) {
      id = tid;
      ntr = nt;
    }
    
    /// utility function to determine index range
    void indexRange(uint from, uint to, uint & begin, uint & end) const;
    
  protected:

    /// thread id out of ntr processes this task
    uint id, ntr;
};

typedef boost::shared_ptr<ReductionTask> RTaskPtr;
typedef std::vector<RTaskPtr> RTaskList;

// forward declaration
class TaskQueue;
class RTaskQueue;

/** Processing thread.

  A thread which pops tasks from the queue and runs them. The thread
  function returns as soon as it encounters an empty queue.

  */
class TaskProcessor : public ThreadBase
{
  public:

    /// undefined processor (no queue ref)
    TaskProcessor() : ThreadBase(), tq(0) {}
    
    /// a processor can only exist within a queue
    TaskProcessor(TaskQueue *tqe) : ThreadBase(), tq(tqe) {}

    /// is defined?
    bool defined() {return tq != 0;}
    
    /// start processing tasks, exit if no tasks left
    void run();
    
  private:

    /// reference to queue
    TaskQueue *tq;
};

/** Processing thread for reduction tasks.

  Does the same as TaskProcessor, but for reduction tasks.

 */
class RTaskProcessor : public ThreadBase
{
  public:

    /// undefined processor (no queue ref)
    RTaskProcessor() : tq(0), id(0), ntr(0) {}
    
    /// a processor can only exist within a queue
    RTaskProcessor(RTaskQueue *tqe, uint tid, uint nt) : tq(tqe), id(tid), ntr(nt) {}

    /// start processing tasks, exit if no tasks left
    void run();
    
  private:

    /// reference to queue
    RTaskQueue *tq;

    /// thread id and number of threads created
    uint id, ntr;
};

/** Process many tasks with few threads.

  A TaskQueue is filled with tasks which can be processed in parallel using
  fewer threads than tasks. New tasks can be added even after process() has
  been called, but only from one of the running tasks themselves. If you add
  more tasks by calling pushTask() from another thread which is not one of
  the queue processors, the task may not be processed at all.

  */
class TaskQueue
{
  public:

    /// create empty queue
    TaskQueue() :jdone(0) {}

    /// create filled queue
    TaskQueue(const TaskList & t);

    /// virtual destructor
    virtual ~TaskQueue() {}
    
    /// process all tasks, return the number of jobs processed
    virtual uint process(uint nthread);

    /// add task to queue
    uint pushTask(TaskPtr t) {
      uint n;
      tqguard.lock();
      n = tasks.size();
      tasks.push_back(t);
      tqguard.unlock();
      return n;
    }

    /// convenience function: take ownership of task pointer
    uint pushTask(ThreadTask *tp) {
      return pushTask(TaskPtr(tp));
    }
    
    /// fetch a task from queue (may return null if queue empty)
    TaskPtr popTask() {
      TaskPtr t;
      tqguard.lock();
      if (not tasks.empty()) {
        t = tasks.front();
        tasks.pop_front();
        ++jdone;
      }
      tqguard.unlock();
      return t;      
    }

    /// number of current tasks
    uint size() const {return tasks.size();}

    /// number of scheduled processing threads
    uint nthreads() const {return threads.size();}
    
  private:

    /// worker threads
    std::vector<TaskProcessor> threads;
    
    /// jobs for threads
    std::deque<TaskPtr> tasks;

    /// queue access lock
    Mutex tqguard;

    /// count tasks performed
    uint jdone;
};

/** Process tasks which require serial reduction step

  A TaskQueue is filled with tasks which can be processed in parallel using
  fewer threads than tasks. New tasks can be added even after process() has
  been called, but only from one of the running tasks themselves. If you add
  more tasks by calling pushTask() from another thread which is not one of
  the queue processors, the task may not be processed at all.

 */
class RTaskQueue
{
  public:

    /// create empty queue
    RTaskQueue() :jdone(0) {}

    /// create filled queue
    RTaskQueue(const RTaskList & t);

    /// virtual destructor
    virtual ~RTaskQueue() {}
    
    /// process all tasks, return the number of jobs processed
    virtual uint process(uint nthread);

    /// add task to queue
    uint pushTask(RTaskPtr t) {
      uint n;
      tqguard.lock();
      n = tasks.size();
      tasks.push_back(t);
      tqguard.unlock();
      return n;
    }

    /// convenience function: take ownership of task pointer
    uint pushTask(ReductionTask *tp) {
      return pushTask(RTaskPtr(tp));
    }
    
    /// fetch a task from queue (may return null if queue empty)
    RTaskPtr popTask() {
      RTaskPtr t;
      tqguard.lock();
      if (not tasks.empty()) {
        t = tasks.front();

        // put task immediately into reduction queue
        // which will be processed later in serial
        rqueue.push_back(t);
        
        tasks.pop_front();
        ++jdone;
      }
      tqguard.unlock();
      return t;
    }

    /// number of current tasks
    uint size() const {return tasks.size();}

    /// number of scheduled processing threads
    uint nthreads() const {return threads.size();}

    /// perform scalar reduction
    void reduce(Real & r);

    /// perform vector reduction
    void reduce(Vector & r);
    
    /// perform vector reduction
    void reduce(CpxVector & r);
    
    /// perform vector reduction
    void reduce(Real *r);
    
    /// perform vector reduction
    void reduce(Complex *r);
    
  private:

    /// worker threads
    std::vector<RTaskProcessor> threads;
    
    /// jobs for threads
    std::deque<RTaskPtr> tasks, rqueue;

    /// queue access lock
    Mutex tqguard;

    /// count tasks performed
    uint jdone;
};

#endif

