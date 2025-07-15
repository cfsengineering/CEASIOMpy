
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

#include "configparser.h"
#include "ioglue.h"
#include "xcept.h"
#include "dvector.h"
#include "strutils.h"

#include <boost/regex.hpp>
#include <sstream>

using namespace boost;

using std::string;
using std::stringstream;

ConfigParser::ConfigParser(const std::string &fname) : sep("="), csign("#")
{
  // open file, read config
  ifstream in(asPath(fname).c_str());
  if (!in)
    throw Error("Could not open file " + fname);

  read(in);
  in.close();
}

const std::string &ConfigParser::operator[](const std::string &key) const
{
  // const access
  KeyMap::const_iterator itr = kv.find(key);
  if (itr == kv.end())
  {
    string msg("Valid keys: ");
    for (itr = kv.begin(); itr != kv.end(); itr++)
      msg += "'" + itr->first + "'\n";
    msg += "No such key: '" + key + "'";
    throw Error(msg);
  }

  return itr->second;
}

bool ConfigParser::hasKey(const std::string &key) const
{
  // check for availability
  KeyMap::const_iterator itr = kv.find(key);
  if (itr == kv.end())
    return false;
  else
    return true;
}

void ConfigParser::erase(const std::string &key)
{
  KeyMap::iterator itr = kv.find(key);
  if (itr != kv.end())
    kv.erase(itr);
}

bool ConfigParser::getBool(const std::string &key) const
{
  KeyMap::const_iterator itr = kv.find(key);
  if (itr == kv.end())
    throw Error("No such key: " + key);

  string val = strip(itr->second);
  if (val == "y" or val == "yes" or val == "true" or
      val == "Y" or val == "YES" or val == "TRUE")
    return true;
  else if (val == "n" or val == "no" or val == "false" or
           val == "N" or val == "NO" or val == "FALSE")
    return false;
  else
    throw Error("Key has no recognized boolean value: " + key + " : " + val);
}

double ConfigParser::getFloat(const std::string &key, double dval) const
{
  KeyMap::const_iterator itr = kv.find(key);
  if (itr == kv.end())
    return dval;
  else
    return atof(itr->second.c_str());
}

int ConfigParser::getInt(const std::string &key, int dval) const
{
  KeyMap::const_iterator itr = kv.find(key);
  if (itr == kv.end())
    return dval;
  else
    return atoi(itr->second.c_str());
}

bool ConfigParser::getBool(const std::string &key, bool dval) const
{
  KeyMap::const_iterator itr = kv.find(key);
  if (itr == kv.end())
  {
    return dval;
  }
  else
  {
    string val = strip(itr->second);
    cout << val << endl;
    if (val == "y" or val == "yes" or val == "true" or
        val == "Y" or val == "YES" or val == "TRUE")
      return true;
    else if (val == "n" or val == "no" or val == "false" or
             val == "N" or val == "NO" or val == "FALSE")
      return false;
    else
      throw Error("Key has no recognized boolean value: " + key + " : " + val);
  }
}

Vct2 ConfigParser::getVct2(const std::string &key) const
{
  // interpret value for key as blank-separated vector
  KeyMap::const_iterator itr = kv.find(key);
  if (itr == kv.end())
    throw Error("No such key: " + key);

  Vct2 v;
  string val = strip(itr->second);
  stringstream ssf(val);
  ssf >> v[0] >> v[1];
  return v;
}

Vct2 ConfigParser::getVct2(const std::string &key, const Vct2 &dval) const
{
  // interpret value for key as blank-separated vector
  KeyMap::const_iterator itr = kv.find(key);
  if (itr == kv.end())
    return dval;

  Vct2 v;
  string val = strip(itr->second);
  stringstream ssf(val);
  ssf >> v[0] >> v[1];
  return v;
}

Vct3 ConfigParser::getVct3(const std::string &key) const
{
  // interpret value for key as blank-separated vector
  KeyMap::const_iterator itr = kv.find(key);
  if (itr == kv.end())
    throw Error("No such key: " + key);

  Vct3 v;
  string val = strip(itr->second);
  stringstream ssf(val);
  ssf >> v[0] >> v[1] >> v[2];
  return v;
}

Vct3 ConfigParser::getVct3(const std::string &key, const Vct3 &dval) const
{
  // interpret value for key as blank-separated vector
  KeyMap::const_iterator itr = kv.find(key);
  if (itr == kv.end())
    return dval;

  Vct3 v;
  string val = strip(itr->second);
  stringstream ssf(val);
  ssf >> v[0] >> v[1] >> v[2];
  return v;
}

std::istream &ConfigParser::read(std::istream &is)
{
  // construct regular expression
  smatch found;
  regex rx("[[:blank:]]*(.+)[[:blank:]]*" + sep + "[[:blank:]]*(.+)[[:blank:]]*");

  // read from stream, pick up keys and values
  string ln;
  while (getline(is, ln))
  {
    ln = strip_comments(ln, csign);
    regex_match(ln, found, rx);

    if (found.size() == 3)
    {
      string key = strip(found[1].str());
      string val = strip(found[2].str());
      if ((not key.empty()) and (not val.empty()))
        kv[key] = val;
    }
  }

  return is;
}

std::ostream &ConfigParser::write(std::ostream &os) const
{
  // write to stream
  KeyMap::const_iterator itr;
  for (itr = kv.begin(); itr != kv.end(); itr++)
    os << "  " << itr->first << " " << sep << " " << itr->second << endl;

  return os;
}

XmlElement ConfigParser::toXml(const string &cfgname) const
{
  string cname("Configuration");
  if (not cfgname.empty())
    cname = cfgname;
  XmlElement xe(cname);
  xe["separator"] = sep;
  xe["comment-token"] = csign;

  KeyMap::const_iterator itr, last = kv.end();
  for (itr = kv.begin(); itr != last; ++itr)
  {
    XmlElement xi(itr->first);
    xi.text(itr->second);
    xe.append(xi);
  }
  return xe;
}

void ConfigParser::fromXml(const XmlElement &xe)
{
  kv.clear();
  sep = xe.attribute("separator", sep);
  csign = xe.attribute("comment-token", csign);
  XmlElement::const_iterator itr, last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr)
  {
    kv[itr->name()] = itr->text();
  }
}
