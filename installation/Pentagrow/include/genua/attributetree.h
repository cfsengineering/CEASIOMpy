
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
 
#ifndef GENUA_ATTRIBUTETREE_H
#define GENUA_ATTRIBUTETREE_H

#include "forward.h"
#include "strutils.h"
#include <exception>
#include <string>
#include <utility>
#include <vector>

/** Base class for objects which support hierarchical attribute sets.
 *
 */
class AttributeTree
{
public:

  typedef std::string KeyType;
  typedef std::string ValueType;
  typedef std::pair<KeyType, ValueType> Attribute;
  typedef std::vector<Attribute> AttributeArray;

  /// construct with name
  AttributeTree(const std::string &s = "") : m_nodename(s) {}

  /// access node name
  const std::string & name() const {return m_nodename;}

  /// change node name
  void rename(const std::string &s) {m_nodename = s;}

  /// test whether node has a particular attribute
  bool contains(const KeyType &key) const {return index(key) != NotFound;}

  /// retrieve an attribute value from string
  template <class ReturnValue>
  ReturnValue get(const KeyType &key, const ReturnValue &defaultValue) const {
    uint idx = index(key);
    if (idx != NotFound) {
      ReturnValue x;
      fromString(m_attr[idx].second, x);
      return x;
    }
    return defaultValue;
  }

  /// retrieve an attribute value from string
  template <class ReturnValue>
  ReturnValue get(const KeyType &key) const {
    ReturnValue x;
    uint idx = index(key);
    if (idx != NotFound)
      fromString(m_attr[idx].second, x);
    else
      throw std::runtime_error("No such key in attribute list: "+key);
    return x;
  }

  /// set key/value pair
  template <class Type>
  uint set(const KeyType &key, const Type &t) {
    AttributeArray::iterator pos;
    auto cmp = [&](const Attribute &a, const KeyType &b) {return a.first < b;};
    pos = std::lower_bound( m_attr.begin(), m_attr.end(), key, cmp);
    if (pos != m_attr.end() and pos->first == key)
      pos->second = str(t);
    else
      m_attr.insert(pos, std::make_pair(key, str(t)));
    return std::distance(m_attr.begin(), pos);
  }

protected:

  /// return index of attribute or NotFound
  uint index(const KeyType &key) const;

protected:

  /// node name
  std::string m_nodename;

  /// sorted attribute set
  AttributeArray m_attr;

  /// child elements
  AttributeTreeArray m_children;
};

#endif // ATTRIBUTETREE_H
