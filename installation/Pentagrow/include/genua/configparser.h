
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
 
#ifndef GENUA_CONFIGPARSER_H
#define GENUA_CONFIGPARSER_H

#include <string>
#include <map>

#include "defines.h"
#include "svector.h"
#include "xmlelement.h"

/** Configuration Parser.

  ConfigParser stores a set of key-value string pairs, which it usually reads
  from a simple configuration file, typically of the form
  \verbatim
    BgColor = black
    FgColor = green
    MaxTemp = 17.0
    MinTemp = 15.5

    # switch acoustic siren on/off
    AcousticWarn = yes
    Origin = 0.4 2.3 -5.6
  \endverbatim
  where the separator sign "=" and the comment sign "#" can be configured
  to be any string in order to read existing files.

  If any key appears multiple times, only the last occurance is relevant.
  Assignments are processed line by line, so that multi-line statements will
  be truncated to their first line.

  \ingroup utility
  */
class ConfigParser
{
  public:

    typedef std::map<std::string, std::string> KeyMap;
    typedef KeyMap::iterator iterator;
    typedef KeyMap::const_iterator const_iterator;

    /// empty construction
    ConfigParser() : sep("="), csign("#") {}

    /// construct with filename (instantly read)
    ConfigParser(const std::string & fname);

    /// set separator sign
    void setSeparator(const std::string & sp)
      {sep = sp;}

    /// set comment sign
    void setCommentSign(const std::string & cs)
      {csign = cs;}

    /// iterator access
    iterator begin() {return kv.begin();}

    /// iterator access
    iterator end() {return kv.end();}

    /// iterator access
    const_iterator begin() const {return kv.begin();}

    /// iterator access
    const_iterator end() const {return kv.end();}

    /// read from stream
    std::istream & read(std::istream & is);

    /// write to stream
    std::ostream & write(std::ostream & os) const;

    /// const access
    const std::string & operator[] (const std::string & key) const;

    /// write access
    std::string & operator[] (const std::string & key)
      {return kv[key];}

    /// for convenience: access plus conversion
    double getFloat(const std::string & key) const
      {return atof((*this)[key].c_str());}

    /// if key is available, return its value as float, else dval
    double getFloat(const std::string & key, double dval) const;

    /// for convenience: access plus conversion
    int getInt(const std::string & key) const
      {return atoi((*this)[key].c_str());}

    /// if key is available, return its value as int, else dval
    int getInt(const std::string & key, int dval) const;    
      
    /// for convenience: access plus conversion
    bool getBool(const std::string & key) const;

    /// if key is available, return its value as bool, else dval
    bool getBool(const std::string & key, bool dval) const;

    /// interprets value as vector; format example: XyPosition = 0.3 4.8 
    Vct2 getVct2(const std::string & key) const;

    /// read vector or return default if key not present
    Vct2 getVct2(const std::string & key, const Vct2 & dval) const;
    
    /// interprets value as vector; format example: XyzPosition = 0.3 4.8 0.9
    Vct3 getVct3(const std::string & key) const;

    /// read vector or return default if key not present
    Vct3 getVct3(const std::string & key, const Vct3 & dval) const;

    /// fetch a range of values, permitting specification of first:step:last
    template <class Sequence>
    bool getRange(const std::string &key, Sequence &rng) const
    {
      typedef typename Sequence::value_type Element;
      KeyMap::const_iterator itr = kv.find(key);
      if (itr == kv.end())
        return false;

      const std::string & val( itr->second );
      Element first(0), step(1), last(0);
      std::string::size_type p1 = val.find_first_of(':');
      std::string::size_type p2 = val.find_last_of(':');
      if (p1 != std::string::npos) {
        fromString( val.substr(0, p1), first );
        if (p2 != p1) {
          fromString( val.substr(p1+1, p2-p1), step );
          fromString( val.substr(p2+1), last );
        } else {
          fromString( val.substr(p1+1), last );
        }
        for ( ; first <= last; first += step )
          rng.push_back(first);
      } else {
        std::stringstream ss;
        ss << val;
        while (ss >> first)
          rng.push_back(first);
      }

      return true;
    }

    /// retrieve string key, or default value
    std::string value(const std::string &key, const std::string &def) const {
      if (hasKey(key))
        return (*this)[key];
      else
        return def;
    }

    /// look for key
    bool hasKey(const std::string & key) const;
    
    /// erase key-value pair 
    void erase(const std::string & key);

    /// convert key/value mapping to XML
    XmlElement toXml(const std::string &cfgname = "") const;

    /// recover key/value map from XML
    void fromXml(const XmlElement & xe);

  private:

    /// stores key/value pairs
    KeyMap kv;

    /// separator and comment sign
    std::string sep, csign;
};

#endif

