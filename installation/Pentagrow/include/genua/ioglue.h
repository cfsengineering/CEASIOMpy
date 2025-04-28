
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
 
#ifndef GENUA_IOGLUE_H
#define GENUA_IOGLUE_H

/// \file ioglue.h
/// \deprecated
/// kept for legacy code which once upon a time expected the nowide library
/// to be wired in for handling of UTF-8 filenames. no longer needed

#include "strutils.h"

//#if defined(_WIN32) && !defined(GENUA_NARROW_IO)

//#include <iostream>

//#include <boost/nowide/fstream.hpp>
//#include <boost/nowide/iostream.hpp>

//using std::ostream;
//using std::istream;

//using boost::nowide::fstream;
//using boost::nowide::ofstream;
//using boost::nowide::ifstream;

//using boost::nowide::cout;
//using boost::nowide::cerr;
//using boost::nowide::cin;
//using boost::nowide::clog;

//using std::endl;

//#else

#include <fstream>
#include <iostream>

using std::ostream;
using std::istream;

using std::fstream;
using std::ifstream;
using std::ofstream;

using std::cout;
using std::cerr;
using std::clog;
using std::cin;

using std::endl;

//#endif

#endif // IOGLUE_H
