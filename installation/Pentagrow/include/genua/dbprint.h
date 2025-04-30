
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
 
#ifndef GENUA_DBPRINT_H
#define GENUA_DBPRINT_H

#ifdef NDEBUG

#include <mutex>

namespace detail {
  extern std::mutex g_dbprint_guard;
  struct sink { template<typename ...Args> sink(Args const & ... ) {} };
}

template<typename FirstType, typename... MoreTypes>
void dbprint(const FirstType& a1, MoreTypes... as)
{
  detail::sink { a1, as ... };
}

#else

#include <mutex>
#include <string>
#include <iostream>
#include <sstream>

namespace detail {
  extern std::mutex g_dbprint_guard;

  template <typename T1>
  void dbappend_arg(std::stringstream &ss, T1 &a1)
  {
    ss << ' ' << a1;
  }

  template <typename T1, typename ...Args>
  void dbappend_arg(std::stringstream &ss, T1 &a1, Args... as)
  {
    detail::dbappend_arg(ss, a1);
    detail::dbappend_arg(ss, as...);
  }

}

/// print everything to cerr
template<typename FirstType, typename... MoreTypes>
void dbprint(const FirstType& a1, MoreTypes... as)
{
  std::stringstream ss;
  detail::dbappend_arg(ss, a1, as...);
  detail::g_dbprint_guard.lock();
  std::cerr << ss.str() << std::endl;
  detail::g_dbprint_guard.unlock();
}

#endif

#endif // DBPRINT_H
