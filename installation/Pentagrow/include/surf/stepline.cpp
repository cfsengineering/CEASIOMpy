
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
 
#include "stepline.h"
#include <cstring>
#include <climits>
#include <algorithm>

// debug
#include <iostream>
using namespace std;

static inline const char *proceed_next(const char *s)
{
  if (s == 0)
    return s;
  while (*s != '\0' and (isspace(*s) or *s == ','))
    ++s;
  return s;
}

uint StepFileLine::entityId()
{
  if (cursor == 0 or *cursor == '\0')
    return NotFound;

  const char *pos = strchr(cursor, '#');
  if (pos == 0 or *pos == '\0')
    return NotFound;

  ++pos;
  char *tail;
  uint id = genua_strtol(pos, &tail, 10);
  if (tail == pos)
    return NotFound;

  cursor = strchr(tail, '(');
  ++cursor;

  return id;
}

bool StepFileLine::skipAttr()
{
  if (*cursor == ',')
    ++cursor;
  while (*cursor != ',' and *cursor != '\0')
    ++cursor;
  if (*cursor == ',')
    ++cursor;
  return true;
}

const char *StepFileLine::entityType()
{
  const char *s = strchr(cursor, '=');
  if (s == 0)
    return 0;

  cursor = s+1;
  return cursor;
}

uint StepFileLine::entityType(std::string & etype)
{
  etype.clear();
  const char *s = strchr(cursor, '#');
  if (s == 0)
    return NotFound;

  ++s;
  char *tail;
  uint eid = genua_strtol(s, &tail, 10);
  if (tail == s)
    return NotFound;

  const char *beg = strchr(tail, '=');
  if (beg == 0)
    return eid;

  ++beg;
  while (isspace(*beg))
    ++beg;

  const char *end = strchr(beg, '(');
  if (end == 0)
    return eid;

  int n = end-beg;
  if (n > 0) {
    etype.resize(n);
    etype.assign(beg, n);
  }

  // let cursor point to character following '('
  cursor = end+1;

  // skip space
  while (isspace(*cursor))
    ++cursor;

  return eid;
}

bool StepFileLine::parseId(StepID & x)
{
  char *tail;
  const char *pos = strchr(cursor, '#');
  if (pos == 0)
    return false;

  cursor = pos+1;
  x = genua_strtol(cursor, &tail, 10);
  if (tail == cursor)
    return false;
  else
    cursor = tail;

  // skip space and comma
  while (isspace(*cursor) or *cursor == ',')
    ++cursor;

  return true;
}

bool StepFileLine::parseInt(int & x)
{
  char *tail;
  x = genua_strtol(cursor, &tail, 10);
  if (tail == cursor)
    return false;
  else
    cursor = tail;

  // skip space and comma
  while (isspace(*cursor) or *cursor == ',')
    ++cursor;

  return true;
}

bool StepFileLine::parseBool(bool & x)
{
  const char *s = strchr(cursor, '.');
  if (s == 0)
    return false;

  ++s;
  x = (*s == 'T');

  // skip space and comma
  cursor = s+2;
  while (isspace(*cursor) or *cursor == ',')
    ++cursor;

  return true;
}

bool StepFileLine::parseFloat(double & x)
{
  char *tail;
  x = genua_strtod(cursor, &tail);
  if (tail == cursor)
    return false;
  else
    cursor = tail;

  // skip space and comma
  while (isspace(*cursor) or *cursor == ',')
    ++cursor;

  return true;
}

bool StepFileLine::parseString(std::string & attr)
{
  const char *beg = strchr(cursor, '\'');
  if (beg == 0)
    return false;

  const char *end = strchr(beg+1, '\'');
  if (end == 0)
    return false;

  // make end point to character past apostrophe
  ++end;

  // size including apostrophes
  const int n = end-beg;
  if (n > 2) {
    attr.resize(n-2);
    attr.assign(beg+1, n-2);
  } else {
    attr.clear();
  }

  // move cursor past last apostrophe
  cursor = end;

  // skip space and comma
  while (isspace(*cursor) or *cursor == ',')
    ++cursor;

  return true;
}

bool StepFileLine::parseEnum(const char **beg, const char **end)
{
  const char *pbeg = strchr(cursor, '.');
  if (pbeg == 0)
    return false;

  const char *pend = strchr(pbeg+1, '.');
  if (pend == 0)
    return false;

  *beg = pbeg;
  *end = pend+1;

  // move cursor past last dot
  cursor = pend+1;

  // skip space and comma
  while (isspace(*cursor) or *cursor == ',')
    ++cursor;

  return true;
}

bool StepFileLine::parseSelect(const char **beg, const char **end)
{
  // a select looks like
  // PARAMETER_VALUE(1.0)
  // so it must begin with a type name
  const char *s = cursor;
  while ( (not isalpha(*s)) and *s != '\0')
    ++s;
  if (*s == '\0')
    return false;

  *beg = s;

  // its contents can contain alphanumeric characters
  // and underscore and are terminated by '('
  s = strchr(s, '(');
  if (s == 0)
    return false;

  *end = s;

  // move cursor one past '(' in preparation for reading the
  // SELECT value between parantheses
  cursor = s + 1;

  return true;
}

bool StepFileLine::parseIdArray(StepIDArray & x)
{
  StepListRep list = nextList();
  if (not list.valid())
    return false;
  x.resize(list.nelements());
  bool ok = list.parseIds(&x[0]);
  cursor = proceed_next(list.end()+1);
  return ok;
}

bool StepFileLine::parseIntArray(StepIntArray & x)
{
  StepListRep list = nextList();
  if (not list.valid())
    return false;
  x.resize(list.nelements());
  bool ok = list.parseInts(&x[0]);
  cursor = proceed_next(list.end()+1);
  return ok;
}

bool StepFileLine::parseFloatArray(StepRealArray & x)
{
  StepListRep list = nextList();
  if (not list.valid())
    return false;
  x.resize(list.nelements());
  bool ok = list.parseFloats(&x[0]);
  cursor = proceed_next(list.end()+1);
  return ok;
}

bool StepFileLine::parseStringArray(StepStringArray & x)
{
  StepListRep list = nextList();
  if (not list.valid())
    return false;
  x.resize(list.nelements());
  bool ok = list.parseStrings(&x[0]);
  cursor = proceed_next(list.end()+1);
  return ok;
}

bool StepFileLine::parseIDMatrix(StepIDMatrix & x)
{
  StepListRep list = nextList();
  uint ncol = list.nChildLists();
  uint nval = list.nelements();
  uint nrow = nval / ncol;
  x.resize(nrow, ncol);
  bool stat = list.parseIds(x.pointer());
  cursor = proceed_next(list.end()+1);
  return stat;
}

bool StepFileLine::parseFloatMatrix(StepRealMatrix & x)
{
  StepListRep list = nextList();
  uint ncol = list.nChildLists();
  uint nval = list.nelements();
  uint nrow = nval / ncol;
  x.resize(nrow, ncol);
  bool stat = list.parseFloats(x.pointer());
  cursor = proceed_next(list.end()+1);
  return stat;
}

void StepFileLine::writeAttr(std::ostream & os, const StepIntArray & x)
{
  const int n = x.size();
  if (n == 0) {
    os << '$';
  } else {
    os << '(';
    for (int i=0; i<n-1; ++i)
      os << x[i] << ',';
    os << x.back() << ')';
  }
}

void StepFileLine::writeAttr(std::ostream & os, const StepRealArray & x)
{
  const int n = x.size();
  if (n == 0) {
    os << '$';
  } else {
    os << '(';
    for (int i=0; i<n-1; ++i)
      os << x[i] << ',';
    os << x.back() << ')';
  }
}

void StepFileLine::writeAttr(std::ostream & os, const StepIDArray & x)
{
  const int n = x.size();
  if (n == 0) {
    os << '$';
  } else {
    os << '(';
    for (int i=0; i<n-1; ++i)
      os << '#' << x[i] << ',';
    os <<  '#' << x.back() << ')';
  }
}

void StepFileLine::writeAttr(std::ostream & os, const StepStringArray & x)
{
  const int n = x.size();
  if (n == 0) {
    os << '$';
  } else {
    os << '(';
    for (int i=0; i<n; ++i) {
      if (i > 0)
        os << ',';
      os << '\'' << x[i] << '\'';
    }
    os << ')';
  }
}

void StepFileLine::writeAttr(std::ostream & os, const StepIDMatrix & x)
{
  const int nc = x.ncols();
  const int nr = x.nrows();
  os << '(';
  for (int j=0; j<nc-1; ++j) {
    os << '(';
    for (int i=0; i<nr; ++i)
      os << '#' << x(i,j) << ',';
    os << "),";
  }
  os << '(';
  for (int i=0; i<nr; ++i)
    os << '#' << x(i,nc-1) << ',';
  os << "))";
}

void StepFileLine::writeAttr(std::ostream & os, const StepRealMatrix & x)
{
  const int nc = x.ncols();
  const int nr = x.nrows();
  os << '(';
  for (int j=0; j<nc-1; ++j) {
    os << '(';
    for (int i=0; i<nr; ++i)
      os << x(i,j) << ',';
    os << "),";
  }
  os << '(';
  for (int i=0; i<nr; ++i)
    os << x(i,nc-1) << ',';
  os << "))";
}



