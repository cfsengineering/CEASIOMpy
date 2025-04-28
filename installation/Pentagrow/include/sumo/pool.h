
/* ------------------------------------------------------------------------
 * file:       pool.h
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * application-wide thread pool
 * ------------------------------------------------------------------------ */

#ifndef SUMO_POOL_H
#define SUMO_POOL_H

class ThreadPool;

class SumoPool
{
  public:

    /// initialize pool 
    static void start(int n);

    /// close down
    static void close();

    /// access reference
    static ThreadPool & pool() {assert(tp != 0); return *tp;}
    
  private:

    /// collection of worker threads
    static ThreadPool *tp;
};

  

#endif
