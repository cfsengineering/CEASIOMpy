
/* Copyright (C) 2017 David Eller <david@larosterna.com>
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

#ifndef GENUA_IOUTIL_H
#define GENUA_IOUTIL_H

#include "forward.h"
#include <fstream>

namespace detail {

/// return size of binary file in bytes
size_t filesize(const std::string &fname);

/// assign contents of a file to string
size_t file_as_string(const std::string &fname, std::string &contents);

/// return contents of a file as string
std::string file_as_string(const std::string &fname);

}

/** Redirect std::clog
 *
 *
 *
 */
class LogRedirector
{
public:

  /// start redirection to named file
  LogRedirector(const std::string &fname);

  /// redirection reversed on destruction
  ~LogRedirector();

private:

  /// clog output will be redirected here
  std::ofstream m_logf;

  /// stores the original clog buffer
  std::streambuf *m_rdbuf;
};

#endif // IOUTIL_H
