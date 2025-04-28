
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

#ifndef GENUA_BLOB_H
#define GENUA_BLOB_H

#include "typecode.h"
#include "defines.h"
#include "dbprint.h"
#include <boost/shared_array.hpp>

/** Binary blob.

  Blob represents a chunk of memory which is either to be written to a
  binary file or has been retrieved from it. It provides an interface to
  access the raw binary data and convert it to a suitable in-memory
  representation.

  \b Example: A class holding computational results may hold double precision
  values in memory, but (perhaps optionally) store single precision floats to
  file in order to reduce disk space requirements and load/store times. Such a
  class would use intermediate Blob objects in order to manage the load/store
  and conversion operations transparently.

  \ingroup io
  \sa TypeCode, BinFileNode, XmlElement
  */
class Blob
{
public:

  /// create empty blob
  Blob() : m_nval(0) {}

  /// assign data to blob
  template <class PodType>
  Blob(size_t nval, const PodType a[], bool share) {
    assign(nval, a, share);
  }

  /// allocate memory only, do not move data in
  void allocate(TypeCode type, size_t nval) {
    m_code = type;
    m_nval = nval;
    m_block.reset( new char[m_nval*m_code.width()] );
  }

  /// reference or copy data into the block
  template <class PodType>
  void assign(size_t nval, const PodType a[], bool share) {
    m_nval = nval;
    m_code = create_typecode<PodType>();
    if (share) {
      m_block = boost::shared_array<char>( a, null_deleter() );
    } else {
      size_t nbyte = nval*sizeof(PodType);
      m_block = boost::shared_array<char>( new char[nbyte] );
      memcpy(m_block.get(), a, nbyte);
    }
  }

  /// reference or copy data into the block
  template <class PodType>
  void assign(TypeCode storageType, size_t nval, const PodType a[], bool share) {
    m_nval = nval;
    m_code = storageType;
    if (share and (storageType == create_typecode<PodType>())) {
      m_block = boost::shared_array<char>( (char *) a, null_deleter() );
    } else {
      if (share and (storageType != create_typecode<PodType>()))
        dbprint("Blob::assign() - Sharing requested for non-matching datatype.");
      size_t nbyte = nval*sizeof(PodType);
      m_block = boost::shared_array<char>( new char[nbyte] );
      if (storageType.width() == sizeof(PodType))
        memcpy(m_block.get(), a, nbyte);
      else
        inject(a);
    }
  }

  /// read specified block from binary file
  std::istream & read(TypeCode type, size_t nval, std::istream & in) {
    m_code = type;
    m_nval = nval;
    size_t nbyte = bytes();
    m_block.reset( new char[nbyte] );
    return in.read( m_block.get(), nbyte );
  }

  /// write block to binary file
  std::ostream & write(std::ostream & out) {
    assert(m_block);
    return out.write( m_block.get(), bytes() );
  }

  /// access raw pointer to memory block
  const char *pointer() const { assert(m_block); return m_block.get(); }

  /// access pointer for element i
  template <typename ValueType>
  const ValueType *as(size_t i) const {
    assert(i < size());
    union { const char *cp; const ValueType *vp; } u;
    u.cp = pointer();
    return &(u.vp[i]);
  }

  /// number of bytes stored in block
  size_t bytes() const { return m_nval*m_code.width(); }

  /// number of values (not bytes) stored
  size_t size() const { return m_nval; }

  /// access type string
  const char *typeString() const {return m_code.toString();}

  /// access type code
  TypeCode typeCode() const {return m_code;}

  /// access a single value, convert from stored type to ValueType
  template <typename ValueType>
  bool extract(size_t index, ValueType & x) const {
    assert(index < m_nval);
    const char *ptr = m_block.get() + index*m_code.width();
    return m_code.extract( ptr, x );
  }

  /// access a single value, convert from ValueType to stored type
  template <typename ValueType>
  bool inject(size_t index, const ValueType &x) {
    assert(index < m_nval);
    const char *ptr = m_block.get() + index*m_code.width();
    return m_code.inject(1, &x, ptr);
  }

  /// convert a fixed number of values, starting at index
  template <int N, typename ValueType>
  bool extract(size_t index, ValueType x[]) const {
    assert(index < m_nval);
    const char *ptr = m_block.get() + index*m_code.width();
    return m_code.extract( N, ptr, x );
  }

  /// convert a fixed number of values, starting at index
  template <int N, typename ValueType>
  bool inject(size_t index, const ValueType x[]) const {
    assert(index < m_nval);
    const char *ptr = m_block.get() + index*m_code.width();
    return m_code.inject( N, &x, ptr);
  }

  /// copy block contents to external array using C++ type conversion
  template <typename ValueType>
  bool extract(ValueType x[]) const {
    return m_code.extract( m_nval, m_block.get(), x );
  }

  /// copy contents from external array using C++ type conversion
  template <typename ValueType>
  bool inject(const ValueType x[]) {
    return m_code.inject( m_nval, x, m_block.get() );
  }

  /// indexed extraction
  template <typename IndexType, typename ValueType>
  bool extract(size_t n, const IndexType idx[], ValueType x[]) const {
    return m_code.extract(n, idx, m_block.get(), x);
  }

  /// create a data block in XML element
  bool toXmlBlock(XmlElement &xe, bool share) const;

  /// retrieve from data block in XML element
  bool fromXmlBlock(const XmlElement &xe);

  /// swap contents with a
  void swap(Blob &a) {
    m_block.swap( a.m_block );
    std::swap(m_nval, a.m_nval);
    std::swap(m_code, a.m_code);
  }

private:

  /// raw data, either copied or shared
  boost::shared_array<char> m_block;

  /// number of values (not bytes)
  size_t m_nval;

  /// type code
  TypeCode m_code;
};

#endif // BLOB_H
