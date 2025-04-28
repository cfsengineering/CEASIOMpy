
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       threadpool.h
 * begin:      May 2007
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * reuseable thread task queue with minimal overhead, intended for
 * iterative solver where similar tasks are performed in each iteration
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */
 
#ifndef GENUA_THREADPOOL_POSIX_H
#define GENUA_THREADPOOL_POSIX_H

/** Group of threads.

  On construction, ThreadPool creates a number of threads which 
  immediately block while waiting for work. Parallel tasks are 
  processed by passing a TaskContainer to the process() member. 

  process() will not return unless all tasks in the container are
  completed.

  */
class ThreadPool
{
  public:
    
    /// create a new pool with n threads
    ThreadPool(uint n);
    
    /// terminate worker threads
    ~ThreadPool();
    
    /// number of worker threads
    uint nworker() const {return nthreads;}
    
    /// process a homogeneous set of tasks
    template <class TaskSet>
    void processArray(TaskSet & s) {
      TaskContainer c;
      c.fill(s);
      process(&c);
    }

    /// process a homogeneous set of tasks
    template <class TaskSet>
    void nrprocessArray(TaskSet & s) {
      TaskContainer c;
      c.fill(s);
      nrprocess(&c);
    }

    /// process all tasks in current queue, reduce and return when done
    void process(TaskContainer *pt) {
      if (pt == 0)
        return;
      if (pt->size() == 0)
        return;
      
      ptodo = pt;
      TaskContainer & todo(*ptodo);

      // wake up worker threads...
      cwork.broadcast();
      cdone.lock();

      // ...and wait until all parallel work finished
      while ( (not todo.alldone()) or (nidle != nthreads) )
        cdone.wait();
      cdone.unlock();

      // TODO: confirm that this works even for nthreads == 1
      // ..then, perform serial reduction
      const uint nr(todo.size());
      for (uint i=0; i<nr; ++i)
        todo[i].reduce();

      todo.reset();
      ptodo = 0;
    }
    
    /// process all tasks in current queue, do not reduce
    void nrprocess(TaskContainer *pt) {
      if (pt == 0)
        return;
      if (pt->size() == 0)
        return;
      
      ptodo = pt;
      TaskContainer & todo(*ptodo);
      
      // wake up worker threads...
      cwork.broadcast();
      cdone.lock();

      //...and wait until all parallel work finished
      while ( (not todo.alldone()) or (nidle != nthreads) )
        cdone.wait();
      cdone.unlock();

      todo.reset();
      ptodo = 0;
    }
    
  private:
    
    /// process next item or wait if necessary (called by work thread)
    void serve() {
      do {
        cwork.lock();
        while ((ptodo == 0) or ptodo->alldone()) {
          idle();
          cwork.wait();
          wakeup();
          if (bterminate) {
            cwork.unlock();
            die();
            return;
          }
        }
        cwork.unlock();
        if (ptodo != 0) {
          ptodo->work();
        }
      } while (not bterminate);
      die();
    }
    
    /// cannot initialize without workers
    ThreadPool() {}
    
    /// start n worker threads 
    void start(uint n);
    
    /// increment idle count
    void idle() {
      cdone.lock();
      ++nidle;
      cdone.unlock();
      if (nidle == nthreads and ptodo != 0 and ptodo->alldone())
        cdone.signal();
    }
    
    /// decrement idle count
    void wakeup() {
      cdone.lock();
      --nidle;
      cdone.unlock();
    }
    
    /// terminate thread 
    void die();
    
  private:
    
    /// pointer to task container currently processed 
    TaskContainer *ptodo;
    
    /// condition on which idle threads will wait
    Condition cwork;
    
    /// condition signalled when work completed
    Condition cdone;
    
    /// number of running and idle threads
    uint nthreads, nidle;
    
    /// set to true when threads should exit
    bool bterminate;
    
  friend void *threadpool_worker(void *ptr);
};

#endif

