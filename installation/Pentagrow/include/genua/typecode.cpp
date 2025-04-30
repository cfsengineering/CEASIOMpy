
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
 
#include "typecode.h"
#include "xmlelement.h"

const char *TypeCode::keylist[] = { "None", "Int8", "UInt8", "Int16", "UInt16",
                                    "Int32", "UInt32", "Int64", "UInt64",
                                    "Float16", "Float32", "Float64",
                                    "Complex64", "Complex128", "Str8"};

const char *TypeCode::toString() const
{
  if (ivalue > 0 and ivalue < nkeys())
    return keylist[ivalue];
  else
    return keylist[0];
}

TypeCode TypeCode::fromString(const std::string &s)
{
  for (int i=0; i<nkeys(); ++i) {
    if (keylist[i] == s)
      return TypeCode(i);
  }
  return TypeCode();
}

bool TypeCode::fromXmlBlock(const XmlElement &xe, size_t nval, char *ptr)
{
  assert(ptr != 0);
  switch (ivalue) {
  case None:
    return false;
  case Int8:
    xe.fetch(nval, (int8_t*) ptr);
    return true;
  case UInt8:
    xe.fetch(nval, (uint8_t*) ptr);
    return true;
  case Int16:
    xe.fetch(nval, (int16_t*) ptr);
    return true;
  case UInt16:
    xe.fetch(nval, (uint16_t*) ptr);
    return true;
  case Int32:
    xe.fetch(nval, (int32_t*) ptr);
    return true;
  case UInt32:
    xe.fetch(nval, (uint32_t*) ptr);
    return true;
  case Int64:
     xe.fetch(nval, (int64_t*) ptr);
    return true;
  case UInt64:
    xe.fetch(nval, (uint64_t*) ptr);
    return true;
  case Float16:
    return false;
  case Float32:
    xe.fetch(nval, (float*) ptr);
    return true;
  case Float64:
    xe.fetch(nval, (double*) ptr);
    return true;
  case Complex64:
    xe.fetch(nval, (std::complex<float>*) ptr);
    return true;
  case Complex128:
    xe.fetch(nval, (std::complex<double>*) ptr);
    return true;
  case Str8:
    assert(nval == xe.text().size());
    memcpy(ptr, xe.text().data(), std::min(nval, xe.text().size()));
    return true;
  default:
    return false;
  }
  return false;
}

bool TypeCode::toXmlBlock(XmlElement &xe, size_t nval,
                          const char *ptr, bool share) const
{
  assert(ptr != 0);
  switch (ivalue) {
  case None:
    return false;
  case Int8:
    xe.asBinary(nval, (const int8_t*) ptr, share);
    return true;
  case UInt8:
    xe.asBinary(nval, (const uint8_t*) ptr, share);
    return true;
  case Int16:
    xe.asBinary(nval, (const int16_t*) ptr, share);
    return true;
  case UInt16:
    xe.asBinary(nval, (const uint16_t*) ptr, share);
    return true;
  case Int32:
    xe.asBinary(nval, (const int32_t*) ptr, share);
    return true;
  case UInt32:
    xe.asBinary(nval, (const uint32_t*) ptr, share);
    return true;
  case Int64:
     xe.asBinary(nval, (const int64_t*) ptr, share);
    return true;
  case UInt64:
    xe.asBinary(nval, (const uint64_t*) ptr, share);
    return true;
  case Float16:
    return false;
  case Float32:
    xe.asBinary(nval, (const float*) ptr, share);
    return true;
  case Float64:
     xe.asBinary(nval, (const double*) ptr, share);
    return true;
  case Complex64:
    xe.asBinary(nval, (const std::complex<float>*) ptr, share);
    return true;
  case Complex128:
     xe.asBinary(nval, (const std::complex<double>*) ptr, share);
    return true;
  case Str8:
    xe.text(ptr, nval);
    return true;
  default:
    return false;
  }
  return false;
}
