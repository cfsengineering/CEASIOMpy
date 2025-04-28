
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       loopthread.h
 * begin:      Jan 2003
 * copyright:  (c) 2003 by david.eller@gmx.net
 * ------------------------------------------------------------------------
 * threads for loop parallelization
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#ifndef GENUA_LOOPTHREAD_H
#define GENUA_LOOPTHREAD_H

#include <boost/shared_ptr.hpp>
#include "dmatrix.h"
#include "thread.h"
#include "synchron.h"


/** Thread for loop parallelization.
 
  Thread class derived from ThreadBase, designed to simplify loop
  parallelization. LoopThreads would usually be created by the
  constructor of LoopThreadFlock, which also assigns each thread
  a reference for a common Barrier for loop synchronization. 

  Typically, the computations in the loop body are implemented in
  run() of a class derived from LoopThread. These computations may require
  reduction operations after completion of the loop, which are performed in
  reduce().

  Usage example:
  \verbatim
  class JacobiThread : public LoopThread {
  public:

  JacobiThread(Matrix & ma, Matrix & mb, uint nit) : LoopThread(), a(ma), b(mb), n(nit) {}

  void run() {
    nr = a.nrows();
    nc = a.ncols();
    first = firstIndex(1, nc-1);
    last = lastIndex(1, nc-1);
    for (uint iter=0; iter<n; ++iter) {
      for (uint j=first; j<last; ++j)
        for (uint i=1; i<nr-1; ++i)
          b(i,j) = 0.25*(a(i-1,j) + a(i+1,j) + a(i,j-1) + a(i,j+1));
      wait();
      for (uint j=first; j<last; ++j)
        for (uint i=1; i<nr-1; ++i)
          a(i,j) = 0.25*(b(i-1,j) + b(i+1,j) + b(i,j-1) + b(i,j+1));
      wait();
    }
  }

  void reduce(Matrix & r) const {
    for (uint j=first; j<last; ++j)
      for (uint i=1; i<nr-1; ++i)
        r(i,j) = -4*a(i,j) + a(i-1,j) + a(i+1,j) + a(i,j-1) + a(i,j+1);
  }

  private:
    Matrix & a;
    Matrix & b;
    uint n, nr, nc, first, last;
  };
  \endverbatim

  */
class LoopThread : public ThreadBase
{

public:

  /// initialize empty thread
  LoopThread() : ThreadBase(), wall(0), rlock(0) {}
  
  /// initialize named thread
  LoopThread(uint i, uint nt) : ThreadBase(), id(i), ntr(nt), wall(0), rlock(0) {}

  /// virtual destructor
  virtual ~LoopThread()
  {}

  /// overload this
  virtual void run() = 0;

  /// assign index and number of threads
  void rename(uint i, uint nt)
  {
    id=i;
    ntr=nt;
  }

  /// assign a barrier
  void assignBarrier(Barrier *bp)
  {
    wall = bp;
  }

  /// assign a loop resource mutex
  void assignLock(Mutex *m)
  {
    rlock = m;
  }

  /// wait at barrier (if defined)
  void wait()
  {
    if (wall != 0)
      wall->wait();
  }

  /// acquire lock on mutex belonging to loop
  void acquireLock()
  {
    if (rlock != 0)
      rlock->lock()
      ;
  }

  /// release lock on mutex belonging to loop
  void releaseLock()
  {
    if (rlock != 0)
      rlock->unlock();
  }

  /// compute first index for loop parallelization
  uint firstIndex(uint start, uint end) const
  {
    return start + id*(end-start)/ntr;
  }

  /// compute first index for loop parallelization
  uint lastIndex(uint start, uint end) const
  {
    if (id < ntr-1)
      return start + (id+1)*(end-start)/ntr;
    else
      return end;
  }

  /// reduction after loop completion
  virtual void reduce(Real &) const {}

  /// reduction after loop completion
  virtual void reduce(Vector &) const {}

  /// reduction after loop completion
  virtual void reduce(Matrix &) const {}

protected:

  /// integer thread id and number of loop threads created
  uint id, ntr;

  /// optionally used barrier
  Barrier *wall;

  /// optionally used mutex for synchronized access
  Mutex *rlock;
};

typedef boost::shared_ptr<LoopThread> LoopThreadPtr;

/** Group of LoopThreads.
 
  For groups of identical threads, i.e. with threads executing the same
  function in their run() method, this class provides a very simple
  container. It is mainly meant for data-parallel programming in the
  spawn/join style where a (dynamically determined) number of threads
  is created, all working on different "slices" of the data, but
  performing the same operations.

  Usage example:
  \verbatim
  uint niter, nthread;
  Matrix a, b, r;
  [...]
  // create 
  LoopThreadFlock<JacobiThread> jpack(nthread, a, b, niter);

  // perform loop iterations, assemble results after loop completion
  jpack.start();
  jpack.join();
  jpack.reduce(r);
  \endverbatim
 
 */
template <class thread_type>
class LoopThreadFlock
{
public:

  /// initialize a group of n threads (will not be started yet)
  LoopThreadFlock(uint nt = 0) : thv(nt)
  {}

  /// create nt threads with single-argument constructor
  template <class targ_type>
  LoopThreadFlock(uint nt, targ_type & arg)
  {
    for (uint i=0; i<nt; i++)
      thv.push_back( LoopThreadPtr(new thread_type(arg)) );
  }

  /// create nt threads with two-argument constructor
  template <class arg1, class arg2>
  LoopThreadFlock(uint nt, arg1 & first, arg2 & second)
  {
    for (uint i=0; i<nt; i++)
      thv.push_back( LoopThreadPtr(new thread_type(first, second)) );
  }

  /// create nt threads with three-argument constructor
  template <class arg1, class arg2, class arg3>
  LoopThreadFlock(uint nt, arg1 & first, arg2 & second, arg3 & third)
  {
    for (uint i=0; i<nt; i++)
      thv.push_back( LoopThreadPtr(new thread_type(first, second, third)) );
  }

  /// create nt threads with four-argument constructor
  template <class arg1, class arg2, class arg3, class arg4>
  LoopThreadFlock(uint nt, arg1 & first, arg2 & second, arg3 & third, arg4 & fourth)
  {
    for (uint i=0; i<nt; i++)
      thv.push_back( LoopThreadPtr(new thread_type(first, second, third, fourth)) );
  }

  /// create nt threads with five-argument constructor
  template <class arg1, class arg2, class arg3, class arg4, class arg5>
  LoopThreadFlock(uint nt, arg1 & first, arg2 & second, arg3 & third,
                  arg4 & fourth, arg5 & fifth)
  {
    for (uint i=0; i<nt; i++)
      thv.push_back( LoopThreadPtr(new thread_type(first, second, third, fourth, fifth)) );
  }

  /// create nt threads with six-argument constructor
  template <class arg1, class arg2, class arg3, class arg4, class arg5, class arg6>
  LoopThreadFlock(uint nt, arg1 & first, arg2 & second, arg3 & third,
                  arg4 & fourth, arg5 & fifth, arg6 & sixth)
  {
    for (uint i=0; i<nt; i++)
      thv.push_back( LoopThreadPtr(new thread_type(first, second, third, fourth, fifth, sixth)) );
  }

  /// start all threads
  void start()
  {
    wall.resize(thv.size());
    for (uint i=0; i<thv.size(); i++) {
      thv[i]->rename(i, thv.size());
      thv[i]->assignBarrier(&wall);
      thv[i]->assignLock(&rlock);
      thv[i]->start();
    }
  }

  /// join all threads
  void join()
  {
    for (uint i=0; i<thv.size(); i++)
      thv[i]->join();
  }

  /// access thread i
  LoopThreadPtr operator[] (uint i) const
  {
    assert(i < thv.size());
    return thv[i];
  }

   /// reduction after loop completion
  void reduce(Real & r) const {
    for (uint i=0; i<thv.size(); ++i)
      thv[i]->reduce(r);
  }

  /// reduction after loop completion
  void reduce(Vector & r) const  {
    for (uint i=0; i<thv.size(); ++i)
      thv[i]->reduce(r);
  }

  /// reduction after loop completion
  void reduce(Matrix & r) const  {
    for (uint i=0; i<thv.size(); ++i)
      thv[i]->reduce(r);
  }

private:

  /// stores thread objects
  std::vector<LoopThreadPtr> thv;

  /// Barrier for the whole flock
  Barrier wall;

  /// Mutex for common resources (reduction, etc.)
  Mutex rlock;
};

#endif
