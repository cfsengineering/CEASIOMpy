
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
 
#ifndef SURF_DCFACESET_H
#define SURF_DCFACESET_H

#include "dcface.h"
#include <vector>

#ifdef _MSC_VER
#undef near
#endif 

#ifdef HAVE_JUDY

#include <genua/judymap.h>

/** Ordered set of triangles for use in DelaunayCore.
 *
 * This container allows to access faces efficiently by index and at the
 * same time keeps a map of Morton codes for the triangle centers in order
 * to allow efficient queries for triangles near a given point in space.
 *
 * The mapping of Morton codes to face indices is implemented using a Judy
 * array when available; otherwise, a std::map is used instead.
 *
 * \ingroup meshgen
 * \sa JudyArray, DcFace
 */
class DcIndexMap
{
public:

  typedef JudyArray<size_t> map_type;
  typedef JudyArray<size_t>::iterator iterator;

  /// replace face at idx with new one with zcode
  void insert(size_t zcode, uint idx) {
    m_jmap.insert(zcode, size_t(idx));
  }

  /// erase a face from map
  bool erase(size_t zcode) {
    return m_jmap.erase(zcode);
  }

  /// iterator to first index
  iterator begin() const {return m_jmap.begin();}

  /// iterator to invalid iterator
  iterator end() const {return m_jmap.end();}

  /// locate an entry, return end() if not found
  iterator find(size_t zcode) const {
    return m_jmap.find(zcode);
  }

  /// return iterator to face with zcode equal or larger than zcode
  iterator lower(size_t zcode) const {
    return m_jmap.lower_bound(zcode);
  }

  /// return iterator to face with zcode equal or smaller than zcode
  iterator upper(size_t zcode) const {
    return m_jmap.upper_bound(zcode);
  }

  /// find a valid iterator near zcode, unless map is empty
  iterator near(size_t zcode) const {
    iterator pos = lower(zcode);
    if (pos != end())
      return pos;
    else if (pos != begin())
      --pos;
    return pos;
  }

  /// return triangle index for a given iterator
  uint triangle(iterator pos) const {
    return *pos;
  }

  /// clear all data
  void clear() {
    m_jmap.clear();
  }

private:

  /// map Morton code to array index
  JudyArray<size_t> m_jmap;
};

#else

#include <map>

class DcIndexMap
{
public:

  typedef std::map<size_t, uint> map_type;
  typedef map_type::const_iterator iterator;

  /// replace face at idx with new one with zcode
  void insert(size_t zcode, uint idx) {
    m_zmap[zcode] = idx;
  }

  /// erase a face from map
  bool erase(size_t zcode) {
    return (m_zmap.erase(zcode) == 1);
  }

  /// iterator to first index
  iterator begin() const {return m_zmap.begin();}

  /// end/invalid iterator
  iterator end() const {return m_zmap.end();}

  /// find a valid iterator near zcode, unless map is empty
  iterator near(size_t zcode) const {
    iterator pos = lower(zcode);
    if (pos != end())
      return pos;
    else if (pos != begin())
      --pos;
    return pos;
  }

  /// return iterator to face with zcode equal or larger than zcode
  iterator lower(size_t zcode) const {
    return m_zmap.lower_bound(zcode);
  }

  /// return iterator to face with zcode equal or smaller than zcode
  iterator upper(size_t zcode) const {
    return m_zmap.upper_bound(zcode);
  }

  /// return triangle index for a given iterator
  uint triangle(iterator pos) const {
    return pos->second;
  }

  /// clear all data
  void clear() {
    m_zmap.clear();
  }

private:

  /// map Morton code to array index
  map_type m_zmap;
};

#endif

#endif // DCFACESET_H
