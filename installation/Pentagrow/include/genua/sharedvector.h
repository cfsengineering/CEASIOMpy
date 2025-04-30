
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
 
#ifndef GENUA_SHAREDVECTOR_H
#define GENUA_SHAREDVECTOR_H

#include <vector>
#include <list>
#include <boost/shared_ptr.hpp>

/** Shared pointer to vector.

  Implements shared-object semantics for std::vector. An object of
  type SharedVector<> can be used in the same way as std::vector<>, but
  it can also be passed by value and copied cheaply as it only holds
  a reference-counted pointer to the underlying vector.

  All of the member functions should work as for std::vector. The only
  additional function detach() can be used to obtain a unique copy of the
  current object - use this if you want a real copy in order to modify the
  contents of the copy without changing the original.

  \ingroup utility
  */
template <class Type>
class SharedVector
{
  public:

    typedef typename std::vector<Type>::iterator iterator;
    typedef typename std::vector<Type>::const_iterator const_iterator;
    typedef typename std::vector<Type>::value_type value_type;
    typedef typename std::vector<Type>::reference reference;
    typedef typename std::vector<Type>::pointer pointer;

    /// empty construction
    SharedVector() : ptr(VectorPtr(new std::vector<Type>)) {}

    /// sized construction
    explicit SharedVector(size_t n) : ptr(VectorPtr(new std::vector<Type>(n))) {}

    /// sized construction
    SharedVector(size_t n, const Type & t)
          : ptr(VectorPtr(new std::vector<Type>(n,t))) {}

    /// mutable access
    Type & operator[] (size_t i) {
      assert(i < ptr->size());
      return (*ptr)[i];
    }

    /// const access
    const Type & operator[] (size_t i) const {
      assert(i < ptr->size());
      return (*ptr)[i];
    }

    iterator begin() {return ptr->begin();}
    const_iterator begin() const {return ptr->begin();}
    iterator end() {return ptr->end();}
    const_iterator end() const {return ptr->end();}

    void resize(size_t n) {ptr->resize(n);}
    void reserve(size_t n) {ptr->reserve(n);}
    size_t size() const {return ptr->size();}
    size_t capacity() const {return ptr->capacity();}
    void clear() {ptr->clear();}

    Type & front() {return ptr->front();}
    Type & back() {return ptr->back();}
    const Type & front() const {return ptr->front();}
    const Type & back() const {return ptr->back();}

    iterator insert(iterator pos, const Type & x) {
      return ptr->insert(pos,x);
    }
    template <class InputIterator>
    void insert(iterator pos, InputIterator first, InputIterator last) {
      ptr->insert(pos, first, last);
    }
    iterator erase(iterator pos) {return ptr->erase(pos);}
    iterator erase(iterator first, iterator last) {
      return ptr->erase(first,last);
    }
    void push_back(const Type & x) {ptr->push_back(x);}
    void pop_back() {ptr->pop_back();}
    void swap(SharedVector & v) {std::swap(ptr, v.ptr);}
    

    /// make *this a deep copy of the original
    void detach() {
      ptr = VectorPtr(new std::vector<Type>(*ptr));
    }        
  
  private:

    typedef boost::shared_ptr<std::vector<Type> > VectorPtr;
  
    /// shared pointer to vector object
    VectorPtr ptr;
};


#endif

