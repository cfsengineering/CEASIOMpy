
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
 
#include "step.h"
#include "stepline.h"
#include <cstring>

using namespace std;

const char *StepLogical::stringrep[] = {".F.", ".T.", ".U."};

static bool find_key(const char *begin, const char *end, const char *key)
{
  const char *itr;
  for (itr = begin; itr != end; ++itr, ++key) {
    if (*key == '\0')
      return false;
    if (*itr != *key)
      return false;
  }
  return true;
}

// ----------------- StepEnum

bool StepEnum::read(StepFileLine & line, int lval,
                    const char *stringrep[], int & val)
{
  const char *beg, *end;
  bool ok = line.parseEnum(&beg, &end);
  if (not ok)
    return false;
  for (int i=0; i<lval; ++i) {
    if (find_key(beg, end, stringrep[i])) {
      val = i;
      return true;
    }
  }
  val = 0;
  return false;
}

// --------------------- StepSelect

// these are AP203 types which are mapped to primitive types
// SELECT uses this table to decide how to parse content

const char *StepSelect::typedefNames[] =
{
  "HOUR_IN_DAY",
  "TEXT",
  "DIMENSION_COUNT",
  "MONTH_IN_YEAR_NUMBER",
  "MINUTE_IN_HOUR",
  "POSITIVE_LENGTH_MEASURE",
  "SECOND_IN_MINUTE",
  "LABEL",
  "PLANE_ANGLE_MEASURE",
  "MASS_MEASURE",
  "POSITIVE_PLANE_ANGLE_MEASURE",
  "VOLUME_MEASURE",
  "CONTEXT_DEPENDENT_MEASURE",
  "DAY_IN_WEEK_NUMBER",
  "DAY_IN_MONTH_NUMBER",
  "WEEK_IN_YEAR_NUMBER",
  "YEAR_NUMBER",
  "SOLID_ANGLE_MEASURE",
  "LENGTH_MEASURE",
  "PARAMETER_VALUE",
  "AREA_MEASURE",
  "DAY_IN_YEAR_NUMBER",
  "DESCRIPTIVE_MEASURE",
  "IDENTIFIER"
};

const StepSelect::ValueType StepSelect::typedefMap[] =
{
  StepSelect::Integer, StepSelect::String, StepSelect::Integer,
  StepSelect::Integer, StepSelect::Integer, StepSelect::Real, StepSelect::Real,
  StepSelect::String, StepSelect::Real, StepSelect::Real, StepSelect::Real,
  StepSelect::Real, StepSelect::Real, StepSelect::Integer, StepSelect::Integer,
  StepSelect::Integer, StepSelect::Integer, StepSelect::Real, StepSelect::Real,
  StepSelect::Real, StepSelect::Real, StepSelect::Integer, StepSelect::String,
  StepSelect::String
};

bool StepSelect::parse(const char *key, StepFileLine & line)
{
  type = NotSet;

  // determine whether key is typedef'd to a POD type or an entity name
  const int ntypes = sizeof(typedefMap) / sizeof(typedefMap[0]);
  for (int i=0; i<ntypes; ++i) {
    if (strcmp(key, typedefNames[i]) == 0) {
      type = typedefMap[i];
      break;
    }
  }

  // not in typedef list, must be an entity name
  if (type == NotSet)
    type = EntityId;

  bool ok(true);
  switch (type) {
  case NotSet:
    ok = false;
  case Real:
    ok = line.parseFloat(m_real);
    break;
  case Integer:
    ok = line.parseInt(m_int);
    break;
  case EntityId:
    ok = line.parseId(m_id);
    break;
  case String:
    ok = line.parseString(m_string);
    break;
  default:
    ok = false;
  }

  const char *s = strchr( line.current(), ')' );
  if (s != 0) {
    while (*s != '\0' and (isspace(*s) or *s == ','))
      ++s;
    line.move(s);
  }

  return ok;
}

bool StepSelect::read(StepFileLine & line, int lval, const char *stringrep[])
{
  // a select of id type may just be specified as an id alone, w/o type name
  if ( line.parseId(m_id) ) {
    type = EntityId;
    return true;
  }

  // find key in subclass stringrep
  bool ok = true;
  const char *beg(0);
  const char *end(0);
  ok &= line.parseSelect(&beg, &end);

  keyIndex = -1;
  if (beg != 0 and end != 0) {
    for (int i=0; i<lval; ++i) {
      if (find_key(beg, end, stringrep[i])) {
        keyIndex = i;
        break;
      }
    }
  }

  // no valid key found in line
  if (keyIndex < 0)
    ok = false;

  // try to parse value depending on type
  if (ok)
    ok &= parse(stringrep[keyIndex], line);


  return ok;
}

void StepSelect::write(std::ostream & os, const char *stringrep[]) const
{
  if (type == NotSet) {
    os << '$';
    return;
  }

  if (keyIndex < 0 and type == EntityId) {
    os << '#' << m_id;
    return;
  }

  // mark as incorrectly processed
  if (keyIndex < 0) {
    os << "???";
    return;
  }

  os << stringrep[keyIndex] << '(';
  if (type == StepSelect::Real)
    os << m_real;
  else if (type == StepSelect::Integer)
    os << m_int;
  else if (type == StepSelect::EntityId)
    os << '#' << m_id;
  else if (type == StepSelect::String)
    os << '\'' << m_string << '\'';
  os << ')';
}
