
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
 
#ifndef GENUA_MATRIXVIEW_H
#define GENUA_MATRIXVIEW_H

#include "defines.h"

// experiment with CRTP
template <class M, typename T>
class MatrixConcept
{
public:

  typedef T value_type;
  typedef value_type* iterator;
  typedef const value_type* const_iterator;

  iterator begin() { return self().pointer(); }
  const_iterator begin() const { return self().pointer(); }

  iterator end() { return begin() + self().size(); }
  const_iterator end() const { return begin() + self().size(); }

  value_type& operator() (size_t i, size_t j) {
    assert((i < self().nrows()) and (j < self().ncols()));
    value_type *p = self().pointer();
    const size_t ldi = self().ldim();
    return p[j*ldi+i];
  }

  const value_type& operator() (size_t i, size_t j) const {
    assert((i < self().nrows()) and (j < self().ncols()));
    const value_type *p = self().pointer();
    const size_t ldi = self().ldim();
    return p[j*ldi+i];
  }

  const value_type* colpointer(size_t j) const {
    assert(j < self().ncols());
    const value_type *p = self().pointer();
    const size_t ldi = self().ldim();
    return p + ldi*j;
  }

  value_type* colpointer(size_t j) {
    assert(j < self().ncols());
    value_type *p = self().pointer();
    const size_t ldi = self().ldim();
    return p + ldi*j;
  }

  value_type& operator[] (size_t k) {
    assert(k < self().size());
    value_type *p = self().pointer();
    return p[k];
  }

  const value_type& operator[] (size_t k) const {
    assert(k < self().size());
    value_type *p = self().pointer();
    return p[k];
  }

private:

  /// represent this as an instance of M
  M& self() {
    return *static_cast<M*>(this);
  }

  /// represent this as an instance of M
  const M& self() const {
    return *static_cast<const M*>(this);
  }

};

template <typename T>
class MatrixView : public MatrixConcept<MatrixView<T>, T>
{
public:

  typedef T value_type;

  MatrixView(T *base, size_t nr, size_t nc)
    : m_base(base), m_rows(nr), m_cols(nc) {}

  value_type *pointer() { return m_base; }
  const value_type *pointer() const { return m_base; }
  size_t nrows() const {return m_rows;}
  size_t ncols() const {return m_cols;}
  size_t size() const {return m_rows*m_cols;}
  size_t ldim() const {return m_rows;}

private:

  T *m_base;

  size_t m_rows, m_cols;
};

#endif // MATRIXVIEW_H

