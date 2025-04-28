
/* Copyright (C) 2019 David Eller <david@larosterna.com>
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

#ifndef GENUA_SPAN_H
#define GENUA_SPAN_H

#include "defines.h"
#include <limits>
#include <boost/static_assert.hpp>

#define DynamicSpanExtent std::numeric_limits<size_t>::max()

/** Encapsulation of pointer and size.
 *
 *  Used for compiler testing.
 *
 * \ingroup utility
 */
template <class T, size_t Extent = DynamicSpanExtent>
class Span
{
public:

  explicit Span(T *ptr) : m_ptr(ptr), m_size(Extent) {
    BOOST_STATIC_ASSERT(Extent != DynamicSpanExtent);
  }

  Span(T *ptr, size_t n) : m_ptr(ptr), m_size(n) {
    BOOST_STATIC_ASSERT(Extent == DynamicSpanExtent);
  }

  template <class Iterator>
  Span(Iterator first, Iterator last) {
    assert((Extent == DynamicSpanExtent) or (std::distance(first, last) == Extent));
    m_ptr = std::addressof(*first);
    m_size = last - first;
  }

  size_t size() const {
    return (Extent == DynamicSpanExtent) ? m_size : Extent;
  }

  bool empty() const {
    return (Extent == DynamicSpanExtent) ? (m_size == 0) : (m_ptr == nullptr);
  }

  T *data() {
#ifndef PERMIT_NULL_SPANDATA
    assert(m_ptr != nullptr);
#endif
    return m_ptr;
  }

  const T *data() const {
#ifndef PERMIT_NULL_SPANDATA
    assert(m_ptr != nullptr);
#endif
    return m_ptr;
  }

  const T& operator[] (size_t idx) const {
    assert(idx < size());
    return m_ptr[idx];
  }

  T& operator[] (size_t idx) {
    assert(idx < size());
    return m_ptr[idx];
  }

  bool isDynamic() const {return (Extent == DynamicSpanExtent);}

  bool isStatic() const {return (Extent != DynamicSpanExtent);}

private:

  /// pointed to
  T *m_ptr = nullptr;

  /// size, if dynamic
  size_t m_size = 0;
};

#endif // SPAN_H
