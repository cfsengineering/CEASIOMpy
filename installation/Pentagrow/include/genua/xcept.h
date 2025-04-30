
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
 
#ifndef GENUA_XCEPT_H
#define GENUA_XCEPT_H

#include <string>
#include <stdexcept>

/** Exception base class.

  Base of all exceptions thrown in this library. It can be
  thrown with a string and (optionally) and int as arguments
  and sets a message string accordingly. Any main program
  should catch this exception type as in
  
  \verbatim
    try
     {
       ... use smesh library ...
     }
    catch (Error & xcp)
     {
       cout << xcp.getMsg();
       exit(-1);
     }
  \endverbatim

  A GUI application can perhaps pop up a message box instead of the
  terminal notification (which would be invisible to the user).
  Since all exceptions are derived from Error, the above catch{} block
  handles all of them.


  \ingroup utility
*/
class Error : public std::runtime_error
{
public:

  /// empty constructor: do nothing
  Error() : std::runtime_error("Unspecified error.") {}

  /// print error message and quit
  Error(const std::string &s);

  /// error message plus integer
  Error(const std::string &s, int i);

  /// error message as std::string
  std::string swhat() const {return std::string(what());}

  /// access error code (translations...)
  int code() const {return m_ecode;}

  /// access stack backtrace (Linux only)
  const std::string & backtrace() const {return m_btrace;}

private:

  /// error code
  int m_ecode;

  /// stack backtrace, on Linux and in debugging mode only
  std::string m_btrace;
};

#endif
