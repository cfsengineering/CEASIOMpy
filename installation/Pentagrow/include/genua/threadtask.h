
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
 
#ifndef GENUA_THREADTASK_H
#define GENUA_THREADTASK_H

#include <deque>
#include <boost/shared_ptr.hpp>

/** Task for multithreaded processing.

  Derive from this class to define a task to be performed in parallel.
  */
class ThreadTask
{
  public:

    /// virtual destructor
    virtual ~ThreadTask() {}

    /// implement this method to perform the parallel work
    virtual void work() = 0;
    
    /// optional reduction step to be performed in serial after work()
    virtual void reduce() {}
};

typedef boost::shared_ptr<ThreadTask> TaskPtr;
typedef std::deque<TaskPtr> TaskDeque;

/** Task which forwards to a function object.

  ForwardingTask is a template meant to enable the use of 
  boost::bind to compose thread tasks. Obviuously, this is
  only possible for tasks which do not perform reduction.

*/
template <class Functor>
class ForwardingTask : public ThreadTask
{
  public:
    
    /// copy functor on construction 
    ForwardingTask(Functor ftor) : f(ftor) {}
    
    /// forward to function object
    void work() { f(); }
    
  private:
    
    /// stores copy of the function object
    Functor f;
};

/** Thread task for iterations.

  IterationTask can be used to minimize the overhead of parallel processing
  in iterative methods, where the same operator is repeatedly called with 
  different arguments (e.g. b = op(x) is performed for different x and b).

  */
template <class VType>
class IterationTask : public ThreadTask
{
  public:
    
    /// construct task
    IterationTask() : ThreadTask(), px(0), pr(0), ibegin(0), iend(0) {}
    
    /// destroy
    virtual ~IterationTask() {}
    
    /// set iteration range
    void setRange(uint itask, uint ntask, uint n) {
      setRange(itask, ntask, 0, n);
    }
    
    /// set iteration range
    void setRange(uint itask, uint ntask, uint start, uint end) {
      uint npt = (end - start)/ntask;
      ibegin = start + itask*npt;
      if (itask < ntask-1)
        iend = start + (itask+1)*npt;
      else
        iend = end;
    }
    
    /// assign a new vector to multiplier
    void assign(const VType *x, VType *r) {
      px = x;
      pr = r;
    }
        
    /// first index in range
    int begin() const {return ibegin;}
    
    /// last+1 index in range 
    int end() const {return iend;}
    
    /// access current argument vector 
    const VType & argument() const {return *px;}
    
    /// access current result (global reduction) vector
    VType & result() const {return *pr;}
    
  protected:
    
    /// vector to multiply
    const VType *px;
    
    /// vector to reduce into
    VType *pr;
    
    /// index range to process
    int ibegin, iend;
};

/** Deprecated - use IterationTask or LoopTask instead. */
class RangeTask : public ThreadTask
{
  public:

    /// initialize task i of nt 
    RangeTask(uint nt, uint i) : ThreadTask(), id(i), ntask(nt) {}
    
    /// virtual destructor
    virtual ~RangeTask() {}

    /// implement this method to perform the parallel work
    virtual void work() = 0;
    
    /// optional reduction step to be performed in serial after work()
    virtual void reduce() {}
    
  protected:
    
    /// compute index range for loop parallelization
    void range(uint start, uint end, uint & ifirst, uint & ilast) const {
      uint npt = (end - start)/ntask;
      ifirst = start + id*npt;
      if (id < ntask-1)
        ilast = start + (id+1)*npt;
      else
        ilast = end;
    }
  
  private:
    
    /// do not allow empty initialization 
    RangeTask() {}
    
  protected:
    
    /// needed for index range to process
    uint id, ntask;
};

#endif
