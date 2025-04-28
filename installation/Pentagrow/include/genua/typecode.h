
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

#ifndef GENUA_TYPECODE_H
#define GENUA_TYPECODE_H

#ifdef _MSC_VER
#pragma warning( disable : 4267 )
#endif

#include "forward.h"
#include "defines.h"
#include "enumobject.h"
#include <string>
#include <cstring>
#include <complex>
#include <algorithm>
#include <type_traits>

/** Integer type code.

  TypeCode is a single integer value containing a code which identifies a
  plain old data type. Its main purpose is to standardize the way binary data
  is tagged in files using integer or string code tags.

  */
class TypeCode : public EnumObject<15>
{
private:

  typedef EnumObject<15> BaseClass;

public:

  enum Code { None, Int8, UInt8, Int16, UInt16, Int32, UInt32,
              Int64, UInt64, Float16, Float32, Float64,
              Complex64, Complex128, Str8 };

  /// create undefined code object
  TypeCode() : ivalue(None) {}

  /// create a defined object
  TypeCode(int v) : ivalue(Code(v)) {}

  /// equivalence
  bool operator== (const TypeCode &c) const { return ivalue == c.ivalue; }

  /// equivalence
  bool operator!= (const TypeCode &c) const { return ivalue != c.ivalue; }

  /// string representation of current code value
  const char *toString() const;

  /// access value
  int value() const {return ivalue;}

  /// width of the type in bytes
  int width() const {return width(ivalue);}

  /// width of the type in bytes
  static int width(int code) {
    const int tb[] = {0, 1, 1, 2, 2, 4, 4, 8, 8, 2, 4, 8, 8, 16, 1};
    if (code > 0 and code < BaseClass::nkeys())
      return tb[code];
    else
      return 0;
  }

  /// create type code from string
  static TypeCode fromString(const std::string &s);

  /// type is real-valued, but not complex
  bool isReal() const {
    return (ivalue >= Float16 and ivalue <= Float64);
  }

  /// type is complex-valued
  bool isComplex() const {
    return (ivalue >= Complex64 and ivalue <= Complex128);
  }

  /// type is integer
  bool isInt() const {
    return (ivalue >= Int8 and ivalue <= UInt64);
  }

  /// type is string
  bool isString() const {
    return (ivalue == Str8);
  }

  /// tests if value conversion will succeed
  bool compatible(TypeCode a) const {
    if (isInt())
      return (a.isInt() or a.isReal());
    if (isReal())
      return (a.isInt() or a.isReal());
    if (isComplex())
      return (a.isReal() or a.isComplex());
    if (isString())
      return a.isString();
    return false;
  }

  /// generate type code at compile time
  template <typename PodType>
  static TypeCode of() {
    if (std::is_same<PodType, int8_t>::value)
      return TypeCode(TypeCode::Int8);
    else if (std::is_same<PodType, uint8_t>::value)
      return TypeCode(TypeCode::UInt8);
    else if (std::is_same<PodType, int16_t>::value)
      return TypeCode(TypeCode::Int16);
    else if (std::is_same<PodType, uint16_t>::value)
      return TypeCode(TypeCode::UInt16);
    else if (std::is_same<PodType, int32_t>::value)
      return TypeCode(TypeCode::Int32);
    else if (std::is_same<PodType, uint32_t>::value)
      return TypeCode(TypeCode::UInt32);
    else if (std::is_same<PodType, int64_t>::value)
      return TypeCode(TypeCode::Int64);
    else if (std::is_same<PodType, uint64_t>::value)
      return TypeCode(TypeCode::UInt64);
    else if (std::is_same<PodType, float>::value)
      return TypeCode(TypeCode::Float32);
    else if (std::is_same<PodType, double>::value)
      return TypeCode(TypeCode::Float64);
    else if (std::is_same<PodType, std::complex<float> >::value)
      return TypeCode(TypeCode::Complex64);
    else if (std::is_same<PodType, std::complex<double> >::value)
      return TypeCode(TypeCode::Complex128);

    return TypeCode(TypeCode::None);
  }

  /// convert from memory location to value
  template <typename ValueType>
  bool extract(const char *raw, ValueType & x) const {
    switch (ivalue) {
    case None:
      return false;
    case Int8:
      x = *( reinterpret_cast<const int8_t*>(raw)  );
      return true;
    case UInt8:
      x = *( reinterpret_cast<const uint8_t*>(raw)  );
      return true;
    case Int16:
      x = *( reinterpret_cast<const int16_t*>(raw)  );
      return true;
    case UInt16:
      x = *( reinterpret_cast<const uint16_t*>(raw)  );
      return true;
    case Int32:
      x = *( reinterpret_cast<const int32_t*>(raw)  );
      return true;
    case UInt32:
      x = *( reinterpret_cast<const uint32_t*>(raw)  );
      return true;
    case Int64:
      x = *( reinterpret_cast<const int64_t*>(raw)  );
      return true;
    case UInt64:
      x = *( reinterpret_cast<const uint64_t*>(raw)  );
      return true;
    case Float16:
      return false;
    case Float32:
      x = *( reinterpret_cast<const float*>(raw)  );
      return true;
    case Float64:
      x = *( reinterpret_cast<const double*>(raw)  );
      return true;
    case Complex64:
      x = *( reinterpret_cast<const std::complex<float>* >(raw)  );
      return true;
    case Complex128:
      x = *( reinterpret_cast<const std::complex<double>* >(raw)  );
      return true;
    default:
      return false;
    }
    return false;
  }

  /// copy with value conversion, assuming dst has enough space
  template <typename ValueType>
  bool extract(size_t nval, const char *raw, ValueType dst[]) const {
    switch (ivalue) {
    case None:
      return false;
    case Int8:
      return copyIfConvertible(nval, reinterpret_cast<const int8_t*>(raw), dst);
    case UInt8:
      return copyIfConvertible(nval, reinterpret_cast<const uint8_t*>(raw), dst);
    case Int16:
      return copyIfConvertible(nval, reinterpret_cast<const int16_t*>(raw), dst);
    case UInt16:
      return copyIfConvertible(nval, reinterpret_cast<const uint16_t*>(raw), dst);
    case Int32:
      return copyIfConvertible(nval, reinterpret_cast<const int32_t*>(raw), dst);
    case UInt32:
      return copyIfConvertible(nval, reinterpret_cast<const uint32_t*>(raw), dst);
    case Int64:
      return copyIfConvertible(nval, reinterpret_cast<const int64_t*>(raw), dst);
    case UInt64:
      return copyIfConvertible(nval, reinterpret_cast<const uint64_t*>(raw), dst);
    case Float16:
      return false;
    case Float32:
      return copyIfConvertible(nval, reinterpret_cast<const float*>(raw), dst);
    case Float64:
      return copyIfConvertible(nval, reinterpret_cast<const double*>(raw), dst);
    case Complex64:
    {
      const std::complex<float> *p = reinterpret_cast<const std::complex<float>*>(raw);
      if ( std::is_same<ValueType, std::complex<float> >::value ) {
        std::copy( p, p+nval, (std::complex<float> *) dst );
        return true;
      } else if (std::is_same<ValueType, std::complex<double> >::value) {
        std::copy( p, p+nval, (std::complex<double> *) dst );
        return true;
      } else
        return false;
    }
    case Complex128:
    {
      const std::complex<double> *p = reinterpret_cast<const std::complex<double>*>(raw);
      if ( std::is_same<ValueType, std::complex<float> >::value ) {
        std::copy( p, p+nval, (std::complex<float> *) dst );
        return true;
      } else if (std::is_same<ValueType, std::complex<double> >::value) {
        std::copy( p, p+nval, (std::complex<double> *) dst );
        return true;
      } else
        return false;
    }
    case Str8:
      return copyIfConvertible(nval, raw, dst);
    default:
      return false;
    }
    return false;
  }

  /// copy with value conversion, assuming dst has enough space
  template <typename IndexType, typename ValueType>
  bool extract(size_t nidx, const IndexType idx[],
               const char *raw, ValueType dst[]) const {
    switch (ivalue) {
    case None:
      return false;
    case Int8:
    {
      const int8_t *p = reinterpret_cast<const int8_t*>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case UInt8:
    {
      const uint8_t *p = reinterpret_cast<const uint8_t*>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case Int16:
    {
      const int16_t *p = reinterpret_cast<const int16_t*>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case UInt16:
    {
      const uint16_t *p = reinterpret_cast<const uint16_t*>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case Int32:
    {
      const int32_t *p = reinterpret_cast<const int32_t*>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case UInt32:
    {
      const uint32_t *p = reinterpret_cast<const uint32_t*>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case Int64:
    {
      const int64_t *p = reinterpret_cast<const int64_t*>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case UInt64:
    {
      const uint64_t *p = reinterpret_cast<const uint64_t*>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case Float16:
      return false;
    case Float32:
    {
      const float *p = reinterpret_cast<const float*>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case Float64:
    {
      const double *p = reinterpret_cast<const double*>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case Complex64:
    {
      const std::complex<float> *p;
      p = reinterpret_cast<const std::complex<float> *>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case Complex128:
    {
      const std::complex<double> *p;
      p = reinterpret_cast<const std::complex<double> *>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    case Str8:
    {
      assert( sizeof(ValueType) == sizeof(char) );
      const char *p;
      p = reinterpret_cast<const char *>(raw);
      for (size_t j=0; j<nidx; ++j)
        dst[j] = p[idx[j]];
      return true;
    }
    default:
      return false;
    }
    return false;
  }

  /// copy with value conversion, assuming dst has enough space
  template <typename ValueType>
  bool inject(size_t nval, const ValueType a[], char *dst) const {
    switch (ivalue) {
    case None:
      return false;
    case Int8:
    {
      int8_t *p = reinterpret_cast<int8_t*> (dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case UInt8:
    {
      uint8_t *p = reinterpret_cast<uint8_t*>(dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case Int16:
    {
      int16_t *p = reinterpret_cast<int16_t*>(dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case UInt16:
    {
      uint16_t *p = reinterpret_cast<uint16_t*>(dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case Int32:
    {
      int32_t *p = reinterpret_cast<int32_t*>(dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case UInt32:
    {
      uint32_t *p = reinterpret_cast<uint32_t*>(dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case Int64:
    {
      int64_t *p = reinterpret_cast<int64_t*>(dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case UInt64:
    {
      uint64_t *p = reinterpret_cast<uint64_t*>(dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case Float16:
      return false;
    case Float32:
    {
      float *p = reinterpret_cast<float*>(dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case Float64:
    {
      double *p = reinterpret_cast<double*>(dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case Complex64:
    {
      std::complex<float> *p = reinterpret_cast<std::complex<float>*>(dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case Complex128:
    {
      std::complex<double> *p = reinterpret_cast<std::complex<double>*>(dst);
      std::copy(a, a+nval, p);
      return true;
    }
    case Str8:
    {
      assert( sizeof(ValueType) == sizeof(char) );
      memcpy(dst, a, nval);
      return true;
    }
    default:
      return false;
    }
    return false;
  }

  /// create a data block in XML element
  bool toXmlBlock(XmlElement &xe, size_t nval,
                  const char *ptr, bool share) const;

  /// retrieve a data block from XML element
  bool fromXmlBlock(const XmlElement &xe, size_t nval, char *ptr);

  /// type conversion, general form
  template <typename SrcType, typename DstType>
  static DstType recast(const char *raw, size_t i) {
    union { const char *cp;
            const SrcType *sp; } u;
    u.cp = raw;
    return static_cast<DstType>( u.sp[i] );
  }

  /// type conversion, general form
  template <typename SrcType, typename DstType>
  static void copy(const char *raw, size_t nval, DstType *dst) {
    union { const char *cp;
            const SrcType *sp; } u;
    u.cp = raw;
    std::copy( u.sp, u.sp+nval, dst );
  }

  /// utility overload
  static bool fromString(const char *s, char **tail, int &value) {
    value = genua_strtol(s, tail, 10);
    return *tail != s;
  }

  /// utility overload
  static bool fromString(const char *s, char **tail, uint &value) {
    value = genua_strtoul(s, tail, 10);
    return *tail != s;
  }

  /// utility overload
  static bool fromString(const char *s, char **tail, int8_t &value) {
    value = (int8_t) genua_strtol(s, tail, 10);
    return *tail != s;
  }

  /// utility overload
  static bool fromString(const char *s, char **tail, uint8_t &value) {
    value = (uint8_t) genua_strtoul(s, tail, 10);
    return *tail != s;
  }

  /// utility overload
  static bool fromString(const char *s, char **tail, int16_t &value) {
    value = (int16_t) genua_strtol(s, tail, 10);
    return *tail != s;
  }

  /// utility overload
  static bool fromString(const char *s, char **tail, uint16_t &value) {
    value = (uint16_t) genua_strtoul(s, tail, 10);
    return *tail != s;
  }

  /// utility overload
  static bool fromString(const char *s, char **tail, int64_t &value) {
#ifdef _MSC_VER
    value = _strtoi64(s, tail, 10);
#else
    value = strtoll(s, tail, 10);
#endif
    return *tail != s;
  }

  /// utility overload
  static bool fromString(const char *s, char **tail, uint64_t &value) {
#ifdef _MSC_VER
    value = _strtoui64(s, tail, 10);
#else
    value = strtoull(s, tail, 10);
#endif
    return *tail != s;
  }

  /// utility overload
  static bool fromString(const char *s, char **tail, double &value) {
    value = genua_strtod(s, tail);
    return *tail != s;
  }

  /// utility overload
  static bool fromString(const char *s, char **tail, float &value) {
    value = genua_strtod(s, tail);
    return *tail != s;
  }

protected:

  template <typename SrcType, typename DstType>
  static bool copyIfConvertible(size_t n, const SrcType src[], DstType dst[]) {
    if ( std::is_convertible<SrcType, DstType>::value ) {
      std::copy(src, src+n, dst);
      return true;
    } else {
      return false;
    }
  }

private:

  /// integer code
  TypeCode::Code ivalue;

  /// type names
  static const char *keylist[];
};

// legacy code compatibility
template <class PodType>
inline TypeCode create_typecode()
{
  return TypeCode::of<PodType>();
}

#endif // TYPECODE_H
