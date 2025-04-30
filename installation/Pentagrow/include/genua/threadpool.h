
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
 
#ifndef GENUA_THREADPOOL_H
#define GENUA_THREADPOOL_H

#include <boost/shared_ptr.hpp>
#include <boost/bind.hpp>
#include "defines.h"
#include "synchron.h"
#include "threadtask.h"

/** Container for thread tasks.

  A TaskContainer is needed to pass work to an existing thread pool for 
  processing. The container itself only holds pointers to tasks which 
  must be stored externally. Note that any tasks stored in a ThreadContainer
  must not be destroyed until ThreadPool::process() returned. 
  
  The TaskContainer/ThreadPool mechanism for multithreading is meant to be 
  an implementation with minimal overhead. 

 */
class TaskContainer
{
  public:
    
    /// create an empty container
    TaskContainer() : inext(0) {}
    
    /// add another task at the end (threadsafe)
    uint push(ThreadTask *tp) {
      uint idx;
      guard.lock();
      idx = tasks.size();
      tasks.push_back(tp);
      guard.unlock();
      return idx;
    }

    /// add two more tasks at the end (threadsafe)
    void push(ThreadTask *tp1, ThreadTask *tp2) {
      guard.lock();
      tasks.push_back(tp1);
      tasks.push_back(tp2);
      guard.unlock();
    }
    
    /// add another task at the end, use with boost::bind
    template <class Functor>
    void pushFunction(Functor f) {
      guard.lock();
      tasks.push_back( new ForwardingTask<Functor>(f) );
      guard.unlock();
    }
    
    /// use all tasks from the container 
    template <class TaskArray>
    void fill(TaskArray & a) {
      const uint n(a.size());
      guard.lock();
      tasks.resize(n);
      for (uint i=0; i<n; ++i)
        tasks[i] = &a[i];
      inext = 0;
      guard.unlock();
    }
    
    /// work on the next task in line, or return NotFound if all done
    uint work() {
      guard.lock();
      uint i = inext;
      inext = std::min(inext+1, size());
      guard.unlock();
      if (i < size()) {
        tasks[i]->work();
        return i;
      } else {
        return NotFound;
      }
    }
    
    /// true if all work done 
    bool alldone() const {
      return (tasks.empty() or (inext >= size()));
    }
    
    /// reset next task pointer to n 
    void reset(uint n = 0) {
      guard.lock();
      inext = n;
      guard.unlock();
    }
    
    /// number of tasks stored 
    uint size() const {return tasks.size();}
    
    /// access task at index i 
    ThreadTask & operator[] (uint i) {
      assert(i < tasks.size());
      return *tasks[i];
    }
    
    /// delete all contained tasks 
    void dispose() {
      const uint nt(tasks.size());
      for (uint i=0; i<nt; ++i)
        delete tasks[i];
      tasks.clear();
      inext = 0;
    }
    
    // debug: access pointer to next item 
    uint nextItem() const  {return inext;}
    
  private:
    
    typedef std::vector<ThreadTask*> TaskArray;
    
    /// contains pointers to thread tasks
    TaskArray tasks;
    
    /// access lock
    Mutex guard;
    
    /// points to next task to perform
    uint inext;
};

typedef boost::shared_ptr<TaskContainer> TaskContainerPtr;

#ifdef USE_PTHREADS
#include "threadpool_posix.h"
#else
#include "threadpool_boost.h"
#endif

#endif

