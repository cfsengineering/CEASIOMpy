
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
 
#ifndef GENUA_VIEWPTR_H
#define GENUA_VIEWPTR_H

#include "algo.h"
#include <memory>
#include <cassert>

namespace detail
{

template <class T>
class maybe_deleter {
public:

  maybe_deleter(bool leaveItAlive=false) 
    : m_leaveit(leaveItAlive) {}

  void operator() (T *ptr) const
  {
    // ask compiler to assume nothing needs to be done
    if ( hint_unlikely(not m_leaveit) )
      delete ptr;
  }
private:
  bool m_leaveit;
};

}

template <class T>
class ViewPointer
{
public:

  typedef detail::maybe_deleter<T> Deleter;
  typedef std::unique_ptr<T, Deleter> UniquePointer;

  /// empty, undefined
  ViewPointer() {}

  /// assign an existing pointer and a flag; delete ptr if not shared
  ViewPointer(T *ptr, bool shared)
    : m_upr( UniquePointer(ptr, Deleter(shared)) ) {}

  /// whether the content is not null
  bool empty() const { return m_upr == nullptr; }

  /// pointer to managed object
  T *get() const {return m_upr.get();}

  /// dereference
  T *operator-> () const {
    assert(m_upr != nullptr);
    return get();
  }

  /// dereference
  T &operator* () const {
    assert(m_upr != nullptr);
    return *get();
  }

  /// delete if not shared
  void reset() { m_upr.reset(); }

  /// replace with other content
  void reset(T *ptr, bool shared) {
    m_upr = UniquePointer(ptr, Deleter(shared));
  }

  /// swap with another one
  void swap(ViewPointer &other) {
    m_upr.swap(other.m_upr);
  }

private:

  /// lifetime manager
  UniquePointer m_upr;
};

template <class T>
bool operator== (const ViewPointer<T> &p, std::nullptr_t) 
{
  return p.empty();
}

template <class T>
bool operator!= (const ViewPointer<T> &p, std::nullptr_t) 
{
  return (not p.empty());
}

#endif // VIEWPTR_H

