
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       thread.h
 * begin:      Jan 2003
 * copyright:  (c) 2003 by david.eller@gmx.net
 * ------------------------------------------------------------------------
 * C++ wrapper for pthread
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#ifndef _GENUA_THREAD_H
#define _GENUA_THREAD_H

#include <vector>
#include <pthread.h>
#include <boost/shared_ptr.hpp>

#include "defines.h"
#include "synchron.h"

// system-dependent machinery to define and test for 'undefined' pthread_t
#if defined(GENUA_WIN32)
inline void _set_pthread_undef(pthread_t & t) { t.p = 0; }
inline bool _is_pthread_undef(const pthread_t & t) { return t.p == 0; }
#elif defined(GENUA_MACOSX)
inline void _set_pthread_undef(pthread_t & t) { t = (pthread_t) 0; }
inline bool _is_pthread_undef(const pthread_t & t) { return t == (pthread_t) 0; }
#else
inline void _set_pthread_undef(pthread_t & t) { t = 0; }
inline bool _is_pthread_undef(const pthread_t & t) { return int(t) == 0; }
#endif


/** Wrapper for posix threads.

  This is a thin wrapper encapsulating some of the Posix thread functionality
  (pthread_*). As the passing around of void pointers for functions and
  arguments is considered too error-prone, the function to be executed by
  the thread must be implemented in the run() method of a child class.

  If the wrapper is compiled with the NDEBUG macro defined, virtually no
  overhead is added, since the calls to pthread library functions will likely
  be inlined; the methods start() and join() then just return the error codes
  of pthread_create and pthread_join. Otherwise, error codes are checked and
  the program will be aborted if an unrecoverable error is detected.

  */
class ThreadBase
{
  public:

    /// initialize empty thread (not create!)
    ThreadBase() { _set_pthread_undef(thr); }

    /// virtual destructor
    virtual ~ThreadBase() {}

    /// equality
    bool operator== (const ThreadBase & a) const {
      if (pthread_equal(thr, a.thr) == 0)
        return false;
      else
        return true;
    }

    /// overload this function in derived classes
    virtual void run() = 0;
    
    /// creates new joinable thread and lets it execute run()
    int start();

    /// wait for this thread to complete
    int join();

  protected:

    /// thread id
    pthread_t thr;
};
typedef boost::shared_ptr<ThreadBase> ThreadPtr;

/** Group of inhomogeneous threads.
  */
// class ThreadPool
// {
//   public:
// 
//     /// create a new pool
//     ThreadPool() {}
// 
//     /// access
//     ThreadPtr operator[] (uint i) {
//       assert(i<thv.size());
//       return thv[i];
//     }
//     
//     /// append a thread pointer
//     uint append(ThreadPtr p) {
//       thv.push_back(p);
//       return thv.size();
//     }
// 
//     /// assign to barrier and start
//     void start();
// 
//     /// join all threads
//     void join() {
//       for (uint i=0; i<thv.size(); i++)
//         thv[i]->join();
//     }
// 
//     // run at most 'limit' threads at a time, join finally
//     void runGroups(uint limit);
// 
//     /// accumulation/reduction
//     void accumulate(Real & r) const {
//       for (uint i=0; i<thv.size(); ++i)
//         thv[i]->accumulate(r);
//     }
//   
//   private:
// 
//     typedef std::vector<ThreadPtr> thread_vector;
// 
//     /// stores reference-counted pointers to threads
//     thread_vector thv;
// 
//     /// common barrier
//     Barrier wall;
// };

#endif

