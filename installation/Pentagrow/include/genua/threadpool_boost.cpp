
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
 
#include "threadpool.h"
#include "xcept.h"
#include <boost/bind.hpp>
#include <boost/thread/thread.hpp>

//// debug
//#include "synchron.h"
//#include <iostream>
//Mutex iomutex;
//// --

using namespace std;

ThreadPool::ThreadPool(uint n) 
    : ptodo(0), nthreads(0), nidle(0), bterminate(false)
{
  start(n);
}
        
void ThreadPool::start(uint n)
{
  bterminate = false;
  nidle = 0;
  nthreads = 0;
  for (uint i=0; i<n; ++i) {
    boost::thread ti(boost::bind(&ThreadPool::serve, this));
    ti.detach();
    nthreads++;
  }
}

void ThreadPool::die()
{
  cdone.lock();
    --nthreads;

  // if this is the last thread to finish, signal cdone so that the
  // destructor knows it may destroy sync objects. if not, make sure to
  // wake up any lagging worker threads
  if (nthreads == 0)
    cdone.signal();
  else
    cwork.signal();

  cdone.unlock();
}

ThreadPool::~ThreadPool()
{
  if (nthreads > 0) {
    bterminate = true;
    cwork.broadcast();
    cdone.wait( boost::bind(&ThreadPool::alldead, this) );
  }
}

