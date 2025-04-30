
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       thread.cpp
 * begin:      Jan 2003
 * copyright:  (c) 2003 by david.eller@gmx.net
 * ------------------------------------------------------------------------
 * C++ wrapper for pthread
 * Are the error codes returned by the pthread_* functions portable?
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#include <iostream>
#include <errno.h>         // error codes
#include <cassert>

#include "xcept.h"
#include "thread.h"

using namespace std;
                
static void *thread_function_wrapper(void *arg)
{
  // provides a pthread-compatible function which invokes thread::run()
#ifndef NDEBUG
  try {
    ThreadBase *th = (ThreadBase *) arg;
    th->run();
    return (void *) 0;
  } catch (Error & xcp) {
    cerr << "Library thread threw exception:" << endl;
    cerr << xcp.what() << endl;
    abort();
  }  
#else
  ThreadBase *th = (ThreadBase *) arg;
  th->run();
  return (void *) 0;
#endif
}

// -------------------- ThreadBase

int ThreadBase::start()
{
  int stat;
  stat = pthread_create(&thr, 0, thread_function_wrapper, this);
  #ifndef NDEBUG
  if (stat == EAGAIN) 
    throw Error("Too many active threads.");
  #endif
  return stat;
}

int ThreadBase::join()
{
  if (_is_pthread_undef(thr))
    return 0;
  
  int stat;
  stat = pthread_join(thr, 0);
  #ifndef NDEBUG
  if (stat == ESRCH)
    throw Error("No such thread can be joined.");
  else if (stat == EINVAL)
    throw Error("Detached thread cannot be joined.");
  else if (stat == EDEADLK) 
    throw Error("Thread cannot join itself.");
  #endif
  return stat;
}

// // ----------- ThreadPool
// 
// void ThreadPool::start()
// {
//   // start threads
//   wall.resize(thv.size());
//   for (uint i=0; i<thv.size(); i++) {
//     thv[i]->rename(i, thv.size());
//     thv[i]->assign(wall);
//     thv[i]->start();
//   }
// }
// 
// void ThreadPool::runGroups(uint limit)
// {
//   // prepare threads
//   wall.resize(thv.size());
//   for (uint i=0; i<thv.size(); i++) {
//     thv[i]->rename(i, thv.size());
//     thv[i]->assign(wall);
//   }
// 
//   // start limit threads at a time, then join
//   uint groups = thv.size() / limit;
//   for (uint i=0; i<groups; ++i) {
//     for (uint j=0; j<limit; ++j)
//       thv[i*limit+j]->start();
//     for (uint j=0; j<limit; ++j)
//       thv[i*limit+j]->join();
//   }
// 
//   // run the last few
//   for (uint i=groups*limit; i<thv.size(); ++i)
//     thv[i]->start();
//   for (uint i=groups*limit; i<thv.size(); ++i)
//     thv[i]->join();
// }



