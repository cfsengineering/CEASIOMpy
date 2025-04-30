
/* ------------------------------------------------------------------------
 * file:       pool.h
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * application-wide thread pool
 * ------------------------------------------------------------------------ */

#include <genua/threadpool.h>
#include "pool.h"

ThreadPool *SumoPool::tp = 0;

void SumoPool::start(int n)
{
  if (tp != 0)
    delete tp;
  
  tp = new ThreadPool(n);
}

void SumoPool::close()
{
  delete tp;
  tp = 0;
}


