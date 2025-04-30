
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
 
#ifndef GENUA_THREADPOOL_BOOST_H
#define GENUA_THREADPOOL_BOOST_H

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
      if (c.size() > 0)
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
      cdone.wait( boost::bind(&ThreadPool::pworkdone, this) );

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
      cdone.wait( boost::bind(&ThreadPool::pworkdone, this) );

      todo.reset();
      ptodo = 0;
    }
    
  private:
    
    /// process next item or wait if necessary (called by work thread)
    void serve() {
      do {
        idle();
        cwork.wait( boost::bind(&ThreadPool::workavailable, this) );
        wakeup();
        if (bterminate) 
          break;
        if (ptodo != 0) 
          ptodo->work();
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
    
    /// all parallel work completed?
    bool pworkdone() const {
      assert(ptodo != 0);
      return (ptodo->alldone()) and (nidle == nthreads);
    }
    
    /// parallel work available
    bool workavailable() const {
      bool havework = (ptodo != 0) and (not ptodo->alldone());
      return havework or bterminate;
    }
    
    /// all threads terminated?
    bool alldead() const {return nthreads == 0;}
    
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
};

#endif

