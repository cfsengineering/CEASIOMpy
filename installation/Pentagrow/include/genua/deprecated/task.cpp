
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       task.h
 * begin:      Jan 2003, major changes fall 2005
 * copyright:  (c) 2005 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * tasks for multithreaded processing
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#include "task.h"

using namespace std;

// ------------ parallel task with reduction ------------------------------

// default implementations for reduction are left empty since ReductionTask
// base class intentionally does not hold any data

void ReductionTask::reduce(Real &) const
{}

void ReductionTask::reduce(Vector &) const
{}

void ReductionTask::reduce(CpxVector &) const
{}

void ReductionTask::reduce(Real *) const
{}

void ReductionTask::reduce(Complex *) const
{}

void ReductionTask::indexRange(uint from, uint to, uint & begin, uint & end) const
{
  assert(ntr != 0);
  begin = from + id*(to-from)/ntr;
  if (id+1 < ntr)
    end = from + (id+1)*(to-from)/ntr;
  else
    end = to;
}

// ------------ processing thread ------------------------------------------

void TaskProcessor::run()
{
  assert(tq != 0);
  TaskPtr t = tq->popTask();
  while (t) {
    t->work();
    t = tq->popTask();
  }
  return;
}

void RTaskProcessor::run()
{
  assert(tq != 0);
  assert(ntr > 0);
  assert(id < ntr);
  RTaskPtr t = tq->popTask();
  while (t) {
    //cout << "Thread " << id << " picked up job" << endl;
    t->setThreadId(id, ntr);
    t->work();
    t = tq->popTask();
  }
  //cout << "Thread " << id << " exiting: TQ empty" << endl;
  return;
}

// -------------- task queue -------------------------------------------------

TaskQueue::TaskQueue(const TaskList & t) : jdone(0)
{
  tasks.resize(t.size());
  std::copy(t.begin(), t.end(), tasks.begin());
}

uint TaskQueue::process(uint nthread)
{
  // serial processing 
  if (nthread < 2) {
    TaskPtr t = popTask();
    while (t) {
      t->work();
      t = popTask();
    }
  }

  // multithreaded processing
  else {

    // create processing threads
    threads.resize(nthread);
    for (uint i=0; i<nthread; ++i) 
      threads[i] = TaskProcessor(this);

    // start working
    for (uint i=0; i<nthread; ++i)
      threads[i].start();

    // wait until all threads have finished
    for (uint i=0; i<nthread; ++i) {
      if (threads[i].defined())
        threads[i].join();
    }
  }

  return jdone;
}

// -------------- queue for reduction tasks -----------------------------------------

RTaskQueue::RTaskQueue(const RTaskList & t) : jdone(0)
{
  tasks.resize(t.size());
  std::copy(t.begin(), t.end(), tasks.begin());
}

uint RTaskQueue::process(uint nthread)
{
  // serial processing 
  if (nthread < 2) {
    RTaskPtr t = popTask();
    while (t) {
      t->work();
      t = popTask();
    }
  }

  // multithreaded processing
  else {

    // create processing threads
    threads.resize(nthread);
    for (uint i=0; i<nthread; ++i)
      threads[i] = RTaskProcessor(this, i, nthread);

    // start working
    for (uint i=0; i<nthread; ++i)
      threads[i].start();

    // wait until all threads have finished
    for (uint i=0; i<nthread; ++i)
      threads[i].join();
    
    // cout << "TQ processing completed. size: " << size() << " processed: " << jdone << endl;
  }

  return jdone;
}

void RTaskQueue::reduce(Real & r)
{
  for (uint i=0; i<rqueue.size(); ++i)
    rqueue[i]->reduce(r);
  rqueue.clear();
  return;
}

void RTaskQueue::reduce(Vector & r)
{
  for (uint i=0; i<rqueue.size(); ++i)
    rqueue[i]->reduce(r);
  rqueue.clear();
  return;
}

void RTaskQueue::reduce(CpxVector & r)
{
  for (uint i=0; i<rqueue.size(); ++i)
    rqueue[i]->reduce(r);
  rqueue.clear();
  return;
}

void RTaskQueue::reduce(Real *r)
{
  for (uint i=0; i<rqueue.size(); ++i)
    rqueue[i]->reduce(r);
  rqueue.clear();
  return;
}

void RTaskQueue::reduce(Complex *r)
{
  for (uint i=0; i<rqueue.size(); ++i)
    rqueue[i]->reduce(r);
  rqueue.clear();
  return;
}

