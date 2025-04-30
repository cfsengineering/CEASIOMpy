
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       synchron.cpp
 * begin:      Feb 2003
 * copyright:  (c) 2003 by david.eller@gmx.net
 * ------------------------------------------------------------------------
 * implementation of synchronization primitive wrappers
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#include <iostream>
#include <errno.h>
#include <stdlib.h>
#include "synchron.h"
       
using namespace std;


// ---------------------- Barrier ---------------------------------

void Barrier::wait()
{
  cnd.lock();
  here++;
  if (here < nt)
    cnd.wait();
  else {
    here = 0;
    cnd.broadcast();
  }
  cnd.unlock();
}




