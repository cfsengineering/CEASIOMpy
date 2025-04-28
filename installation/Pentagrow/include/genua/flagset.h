
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
 
#ifndef GENUA_FLAGSET_H
#define GENUA_FLAGSET_H

#include "forward.h"

/** Keep track of how many have been tagged.
 *
 * FlagSet is just a wrapper around std::vector<bool> which keeps track of
 * how many elements have been set to true. Useful for queue- and graph-based
 * algorithms.
 *
 * \ingroup utility
 */
class FlagSet
{
public:

  /// create set of boolean flags
  FlagSet(size_t n, bool initial=false) : m_flags(n, initial) {
    m_nset = initial ? n : 0;
  }

  /// number of flags allocated
  size_t size() const {return m_flags.size();}

  /// set flag i to value, return whether value was changed
  bool set(size_t i, bool flag = true) {
    if (m_flags[i] == flag)
      return false;
    m_flags[i] = flag;
    m_nset += flag ? 1 : -1;
    return true;
  }

  /// test flag
  bool operator[] (size_t i) const {return m_flags[i];}

  /// number of flags set to true
  size_t nset() const {return m_nset;}

private:

  /// flags
  std::vector<bool> m_flags;

  /// number of flags set
  size_t m_nset;
};

#endif // FLAGSET_H
