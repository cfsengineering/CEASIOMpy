
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
 
#include "steplistrep.h"

StepListRep::StepListRep(const char *s) : first(0), last(0)
{
  if (s == 0)
    return;
  s = first = strchr(s, '(');
  if (s == 0)
    return;

  // keep track of depth
  int cdep(1);
  while (cdep > 0 and *s != '\0') {
    ++s;
    if (*s == '(')
      ++cdep;
    else if (*s == ')')
      --cdep;
  }

  if (*s == ')')
    last = s;
}

uint StepListRep::nChildLists() const
{
  if (valid())
    return std::count(begin(), end(), '(') - 1;
  else
    return 0;
}

uint StepListRep::nComma() const
{
  if (valid())
    return std::count(begin(), end(), ',');
  else
    return 0;
}

bool StepListRep::parseIds(StepID val[]) const
{
  if (not valid())
    return false;

  char *tail;
  const char *s = strchr(first, '#');
  int i = 0;
  while (s != 0 and s < last) {
    ++s;
    uint x = genua_strtol(s, &tail, 10);
    if (tail == s)
      return false;
    val[i++] = x;
    s = strchr(tail, '#');
  }

  return true;
}

bool StepListRep::parseInts(int val[]) const
{
  if (not valid())
    return false;

  char *tail;
  const char *s = first;
  int i = 0;
  while (s != 0 and s < last) {
    ++s;
    int x = genua_strtol(s, &tail, 10);
    if (tail == s)
      return false;
    val[i++] = x;
    s = strchr(tail, ',');
  }

  return true;
}

bool StepListRep::parseFloats(double val[]) const
{
  if (not valid())
    return false;

  char *tail;
  const char *s = first;
  int i = 0;
  while (s != 0 and s < last) {
    ++s;
    double x = genua_strtod(s, &tail);
    if (tail == s)
      return false;
    val[i++] = x;
    s = strchr(tail, ',');
  }

  return true;
}

bool StepListRep::parseStrings(std::string val[]) const
{
  if (not valid())
    return false;

  const char *s = first;
  int i = 0;
  while (s != 0 and s < last) {

    const char *beg = strchr(s, '\'');
    if (beg == 0)
      return false;

    const char *end = strchr(beg+1, '\'');
    if (end == 0)
      return false;

    // make end point to character past apostrophe
    ++end;

    // size including apostrophes
    const int n = end-beg;
    std::string & attr( val[i++] );
    if (n > 2) {
      attr.resize(n-2);
      attr.assign(beg+1, n-2);
    } else {
      attr.clear();
    }

    // move cursor past last apostrophe
    s = strchr(end, ',');
  }

  return true;
}
