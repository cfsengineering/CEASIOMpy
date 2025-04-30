
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
 

#ifndef SURF_STEPLISTREP_H
#define SURF_STEPLISTREP_H

#include "step.h"
#include <genua/defines.h>

/** A list in a STEP file line.

  */
class StepListRep
{
public:

  /// identify list
  StepListRep(const char *s);

  /// determine whether list was identified
  bool valid() const {return last != 0;}

  /// first character of the list '('
  const char *begin() const {return first;}

  /// last character of the list ')'
  const char *end() const {return last;}

  /// number of child lists contained
  uint nChildLists() const;

  /// number of commas in list
  uint nComma() const;

  /// number of list elements
  uint nelements() const {return nComma() + 1;}

  /// extract list of entity ids
  bool parseIds(StepID val[]) const;

  /// extract list of integers
  bool parseInts(int val[]) const;

  /// extract list of strings
  bool parseStrings(std::string val[]) const;

  /// extract list of floating-point values, unknown length
  bool parseFloats(double val[]) const;

  /// extract fixed-size list of floating-point values
  template <int N>
  bool parseFloats(double val[]) const {
    char *tail;
    const char *s = first + 1;
    for (int i=0; i < N; ++i) {
      while (*s == ',' or isspace(*s))
        ++s;
      val[i] = genua_strtod(s, &tail);
      if (tail == s)
        return false;
      s = tail;
    }
    return true;
  }

  /// extract fixed-size list of floating-point values
  template <int N>
  bool parseInts(int val[]) const {
    char *tail;
    const char *s = first + 1;
    for (int i=0; i < N; ++i) {
      while (*s == ',' or isspace(*s))
        ++s;
      val[i] = genua_strtol(s, &tail, 10);
      if (tail == s)
        return false;
      s = tail;
    }
    return true;
  }

  /// extract fixed-size list of floating-point values
  template <int N>
  bool parseIds(StepID val[]) const {
    char *tail;
    const char *s = first + 1;
    for (int i=0; i < N; ++i) {
      while (*s == ',' or isspace(*s))
        ++s;
      val[i] = genua_strtol(s, &tail, 10);
      if (tail == s)
        return false;
      s = tail;
    }
    return true;
  }

private:

  /// first character of list
  const char *first;

  /// points to last character (closing char)
  const char *last;
};

#endif // STEPLISTREP_H
