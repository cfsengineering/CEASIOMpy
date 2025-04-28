
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
 
#include "xcept.h"
#include <sstream>

#if defined(GENUA_LINUX)
#include <execinfo.h>
#endif

using namespace std;

Error::Error(const string &s) : std::runtime_error(s), m_ecode(0)
{
#ifndef NDEBUG
#if defined(GENUA_LINUX)
  void *array[25];
  int nSize = backtrace(array, 25);
  char **symbols = backtrace_symbols(array, nSize);

  stringstream ss;
  ss << "Stack backtrace:" << endl;
  for (int i = 0; i < nSize; i++)
    ss << "#" << i << " " << symbols[i] << endl;

  m_btrace = ss.str();
  free(symbols);
#endif
#endif

#if defined(GENUA_XTERMINATE)
  abort();
#endif
}

Error::Error(const string &s, int i) : std::runtime_error(s), m_ecode(i)
{
#if defined(GENUA_XTERMINATE)
  abort();
#endif
}


