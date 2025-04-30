
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
 #ifndef GENUA_LOOPTASK_H
#define GENUA_LOOPTASK_H

#include "threadpool.h"

/** Task for parallel loops.

  The LoopTask template is used for simple loop-based parallelism, normally
  together with the ParLoop container below. A simple implementation would
  derive from LoopTask, templatized on the reduction variable, and implement
  only ThreadTask::work() and ThreadTask::reduce(), where begin() and end()
  can be used to obtain iteration limits and reduction() gives access to the
  shared reduction variable (if any).

  */
template <class RedType>
class LoopTask : public ThreadTask
{
  public:
    
    /// construct task
    LoopTask() : ThreadTask(), rglob(0), ibegin(0), iend(0) {}
    
    /// destroy
    virtual ~LoopTask() {}
    
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
    
    /// set reduction variable 
    void assign(RedType *rv) {rglob = rv;}
    
  protected:
    
    /// first index in range
    int begin() const {return ibegin;}
    
    /// last+1 index in range 
    int end() const {return iend;}
    
    /// access global reduction variable 
    RedType & reduction() { 
      assert(rglob != 0);
      return *rglob;
    }
    
  protected:
    
    /// private copy to work on
    RedType rpriv;
    
    /// reduction variable to store result 
    RedType *rglob;
    
    /// index range to process
    int ibegin, iend;
};

/** Parallel loop construct.

  ParLoop is a task container which simplifies parallel loop constructs using
  a shared (e.g. application-wide) thread pool. ParLoop is templatized on the
  reduction variable and takes ownership of the assigned task objects. 

  Normally, the user appends newly created tasks and then calls process(&r,n)
  with a pointer to the reduction variable and the loop count. If process is
  called without setting reduction variables, undefined behaviour results.

  */
template <class RedType>
class ParLoop
{
  public:
    
    typedef LoopTask<RedType> LpTask;
    typedef std::vector<LpTask*> LpTaskArray;
    
    /// create a new loop task manager 
    ParLoop(ThreadPool & pool) : tp(pool) {}
    
    /// destroy tasks 
    virtual ~ParLoop() {
      tcp.dispose();
//       const uint nt(tset.size());
//       for (uint i=0; i<nt; ++i)
//         delete tset[i];
    }
    
    /// number of tasks 
    uint ntask() const {return tset.size();}
    
    /// add a new task and transfer ownership 
    void append(LpTask *lt) {
      tset.push_back(lt);
      tcp.push(lt);
    }
    
    /// set index ranges for all tasks 
    void assign(uint i1, uint i2) {
      const uint nt(tset.size());
      for (uint i=0; i<nt; ++i) 
        tset[i]->setRange(i, nt, i1, i2);
    } 
    
    /// set index ranges for all tasks 
    void assign(RedType *rv, uint i1, uint i2) {
      const uint nt(tset.size());
      for (uint i=0; i<nt; ++i) {
        tset[i]->assign(rv);
        tset[i]->setRange(i, nt, i1, i2);
      }
    } 
    
    /// process tasks in parallel, reduce  
    void process() {
      tp.process(&tcp);
    }
    
    /// process tasks in parallel, do not reduce  
    void nrprocess() {
      tp.nrprocess(&tcp);
    }
    
    /// set range and process tasks in parallel, reduce 
    void process(RedType *rv, uint n) {
      assign(rv, 0u, n);
      tp.process(&tcp);
    }
  
    /// set range and process tasks in parallel, no reduction 
    void nrprocess(RedType *rv, uint n) {
      assign(rv, 0u, n);
      tp.process(&tcp);
    }
    
    /// set range and process tasks in parallel, no reduction 
    void nrprocess(uint n) {
      assign(0u, n);
      tp.process(&tcp);
    }
    
    /// clear out all tasks
    void clear() {
      tcp.dispose();
      tset.clear();
    }
    
  private:
    
    /// thread pool to use
    ThreadPool & tp;
    
    /// internal task container to manage processing 
    TaskContainer tcp;
    
    /// owns loop tasks
    LpTaskArray tset;
};

#endif
