
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
 
#ifndef GENUA_STRUTILS_H
#define GENUA_STRUTILS_H

#include <cstdlib>
#include <cstring>
#include <vector>
#include <string>
#include <sstream>

#include "defines.h"

/// split string into token
StringArray split(const std::string & s, const std::string & sep = " ");

/// strip whitespace
std::string strip(const std::string & s, const std::string & wsp = " \n\t\r");

/// remove comments from line
std::string strip_comments(const std::string & s, const std::string & cmtid = "#");

/// return filename part of a full path
std::string path2filename(const std::string &s);

/// append filename suffix
std::string append_suffix(const std::string & fname, const std::string & sfx);

/// determine filename suffix
std::string filename_suffix(const std::string & fname);

/// strip last suffix from filename
std::string strip_suffix(const std::string & fname);

/// return whether the file exists
bool file_exists(const std::string &fname);

/// return contents of entire file as string
std::string file_contents(const std::string &fname);

/// convert line string to doubles
std::vector<double> lineToDouble(const std::string & line);

/// convert line string to ints
std::vector<int> lineToInt(const std::string & line);

namespace internal {

// string -> something

template <typename Convertible>
struct string_extractor {
  inline bool apply(const std::string &s, Convertible &c) const {
    std::stringstream ss;
    ss << s;
    ss >> c;
    return !ss.fail();
  }
};

template <>
struct string_extractor<double> {
  inline bool apply(const std::string &s, double &c) const {
    const char *pos = s.c_str();
    char *tail;
    c = genua_strtod(pos, &tail);
    return pos != tail;
  }
};

template <>
struct string_extractor<float> {
  inline bool apply(const std::string &s, float &c) const {
    const char *pos = s.c_str();
    char *tail;
    c = (float) genua_strtod(pos, &tail);
    return pos != tail;
  }
};

template <>
struct string_extractor<int> {
  inline bool apply(const std::string &s, int &c) const {
    const char *pos = s.c_str();
    char *tail;
    c = (int) genua_strtol(pos, &tail, 10);
    return pos != tail;
  }
};

template <>
struct string_extractor<uint> {
  inline bool apply(const std::string &s, uint &c) const {
    const char *pos = s.c_str();
    char *tail;
    c = (int) genua_strtoul(pos, &tail, 10);
    return pos != tail;
  }
};

template <>
struct string_extractor<bool> {
  inline bool apply(const std::string &s, bool &c) const {
    const char *pos = s.c_str();
    if ( strstr(pos, "true") )
      c = true;
    else if ( strstr(pos, "false") )
      c = false;
    else
      return false;
    return true;
  }
};

// something -> string

template <typename Convertible>
struct string_generator {
  inline std::string apply(const Convertible &c) const {
    std::stringstream ss;
    ss << c;
    return ss.str();
  }
};

template <>
struct string_generator<double> {
  inline std::string apply(const double & x)
  {
    std::stringstream sst;
    sst.precision(15);
    sst << x;
    return sst.str();
  }
};


template <>
struct string_generator<float> {
  inline std::string apply(const float & x)
  {
    std::stringstream sst;
    sst.precision(7);
    sst << x;
    return sst.str();
  }
};

template <>
struct string_generator<bool> {
  inline std::string apply(const bool & b)
  {
    if (b)
      return "true";
    else
      return "false";
  }
};

}

/// Get 'something' from String.
template <class Sth>
bool fromString(const std::string & s, Sth & obj)
{
  internal::string_extractor<Sth> extractor;
  return extractor.apply(s, obj);
}

template <class Sth>
bool fromString(const std::string & s, std::vector<Sth> & obj)
{
  std::stringstream ss(s);
  while (!ss.fail()) {
    Sth v;
    ss >> v;
    obj.push_back(v);
  }
  return true;
}

template <class Sth>
inline std::string str(const Sth & obj)
{
  internal::string_generator<Sth> gen;
  return gen.apply(obj);
}

// Replacements of standard library functions for Vistual Studio <= 2010

#if defined(_MSC_VER) && (_MSC_VER < 1600)

namespace std {

#undef DECLARE_TO_STRING
#define DECLARE_TO_STRING(fmt, type) \
  inline std::string to_string(type x) \
{ \
  char tmp[64]; \
  memset(tmp, 0, sizeof(tmp)); \
  sprintf(tmp, fmt, x); \
  return std::string(tmp); \
}

DECLARE_TO_STRING("%d", int)
DECLARE_TO_STRING("%u", unsigned int)
DECLARE_TO_STRING("%ld", long)
DECLARE_TO_STRING("%lu", unsigned long)
DECLARE_TO_STRING("%lld", long long)
DECLARE_TO_STRING("%llu", unsigned long long)
DECLARE_TO_STRING("%f", float)
DECLARE_TO_STRING("%f", double)
DECLARE_TO_STRING("%Lf", long double)

#undef DECLARE_TO_STRING

// no, we can't use the function names used  in the C standard
// because we are f*cking MSFT
#define strtoll _strtoi64

inline int stoi(const string &s, size_t *idx=0, int base=10)
{
  char *tail;
  const char *head = s.c_str();
  int v = strtol(head, &tail, base);
  if (idx != 0)
    *idx = tail - head;
  return v;
}

inline long long stoll(const string &s, size_t *idx=0, int base=10)
{
  char *tail;
  const char *head = s.c_str();
  long long v = strtoll(head, &tail, base);
  if (idx != 0)
    *idx = tail - head;
  return v;
}

inline double stod(const string &s, size_t *idx=0)
{
  char *tail;
  const char *head = s.c_str();
  double v = strtod(head, &tail);
  if (idx != 0)
    *idx = tail - head;
  return v;
}

} // namespace std

#endif

std::string format_time(double sec, int secprec=1);

inline long Int(const std::string & s) {
  return atol(s.c_str());
}

inline double Float(const std::string & s) {
  return atof(s.c_str());
}

/// convert number to nastran string
std::string nstr(Real x);

/// to lower case 
inline std::string toLower(const std::string & a)
{
  std::string b(a);
  const std::string::size_type n = b.size();
  for (std::string::size_type i=0; i<n; ++i)
    b[i] = static_cast<char>( tolower(b[i]) );
  return b;
}

#ifdef _MSC_VER

std::wstring utf8ToWide(const std::string &u8s);

inline std::wstring asPath(const std::string &u8name)
{
  return utf8ToWide(u8name);
}

#else

inline std::string asPath(const std::string &s)
{
  return s;
}

#endif

#endif

