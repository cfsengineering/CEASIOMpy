
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       macaddress.cpp
 * begin:      January 2009
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Determine MAC address of primary ethernet interface 
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#include "macaddress.h"

#if defined(__linux)

#include "macaddress.h"
#include "linux_macaddress.cpp"

#elif defined(__APPLE__)

// link to -framework CoreFoundation -framework IOKit

#include "macaddress.h"
#include "macosx_macaddress.cpp"

#elif defined(_WIN32)

// link to -lIPHlpApi

#include "macaddress.h"
#include "win_macaddress.cpp"

#else

#error "MAC addresses can not be determined on this OS."

#endif
