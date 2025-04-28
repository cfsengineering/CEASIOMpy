
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
 
#ifndef SURF_STEP_H
#define SURF_STEP_H

#include <genua/dmatrix.h>
#include <iostream>
#include <vector>
#include <string>

#ifdef _MSC_VER
#undef pascal
#endif

class StepFileLine;
class StepListRep;
typedef unsigned int       StepID;

typedef std::vector<StepID>    StepIDArray;
typedef DMatrix<StepID>        StepIDMatrix;
typedef std::vector<double>    StepRealArray;
typedef DMatrix<double>        StepRealMatrix;
typedef std::vector<int>          StepIntArray;
typedef DMatrix<int>              StepIntMatrix;
typedef std::vector<std::string>  StepStringArray;

/** Base class for enumeration types in STEP AP203.
 *
 * \ingroup interop
 * \sa StepFile
 */
class StepEnum
{
  public:
    static bool read(StepFileLine & line, int lval, const char *stringrep[], int & val);
};

/** Base class of SELECT types in STEP AP203.

  \ingroup interop
  \sa StepFile
*/
class StepSelect
{
public:

  /// enumeration to indicate the content type (primitive or entity)
  enum ValueType {NotSet, Real, Integer, EntityId, String};

  /// default: invalid object
  StepSelect() : m_id(NotFound), type(StepSelect::NotSet), keyIndex(-1) {}

  /// determine whether object was defined or not
  bool valid() const {return (type != NotSet);}

protected:

  /// extract a SELECT value from line, called by child class
  bool read(StepFileLine & line, int lval, const char *stringrep[]);

  /// write if defined
  void write(std::ostream & os, const char *stringrep[]) const;

private:

  /// determine content type and parse string
  bool parse(const char *key, StepFileLine & line);

  /// static table with names of AP203 typedefs
  static const char *typedefNames[];

  /// static table with AP203 typedefs
  static const ValueType typedefMap[];

public:

  /// string content, set only if type == String
  std::string m_string;

  /// real-valued content, set only if type == Real
  double m_real;

  /// int-valued content, set only if type == Integer
  int m_int;

  /// entity content, set only if type == EntityId
  StepID m_id;

  /// content type indication
  ValueType type;

  /// key index
  int keyIndex;
};

/** Base class of LOGICAL types in STEP AP203.

  \ingroup interop
  \sa StepFile
*/
class StepLogical : public StepEnum
{
  public:
    typedef enum { False, True, Undefined } Code;
  public:
    
    bool read(StepFileLine & line) {
      int iv = 0;
      bool ok = StepEnum::read(line, 3, stringrep, iv);
      value = (StepLogical::Code) iv;
      return ok;
    }
    
    void write(std::ostream & os) const {
      int i = (int) value;
      assert(i < 3);
      os << stringrep[i];
    }
    
    bool operator== (const StepLogical & a) const {
      return value == a.value;
    }
    
    bool operator!= (const StepLogical & a) const {
      return value != a.value;
    }
    
    bool operator== (const StepLogical::Code & a) const {
      return value == a;
    }
    
    bool operator!= (const StepLogical::Code & a) const {
      return value != a;
    }
    
  public:
    StepLogical::Code value;
  private:
    static const char *stringrep[];
};

#endif
