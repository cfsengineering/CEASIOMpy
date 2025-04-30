
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
 
#ifndef GENUA_QUANTBUFFER_H
#define GENUA_QUANTBUFFER_H

#include "dvector.h"
#include "xmlelement.h"

/** Quantizes floating-point values using 16-bit integers.
 *
 * This is a helper class employed to store large floating-point datasets
 * using a fixed-range 16-bit integer representation. Use this kind of data
 * compression if the approximation error throughout the value range should
 * be constant, or if the data to compress has a known, limited range.
 *
 * \ingroup io
 * \sa MxFieldBuffer
 */
class QuantBuffer
{
public:

  typedef uint16_t CodeType;

  /// undefined buffer
  QuantBuffer() {}

  /// currently allocated size
  uint size() const {return m_qv.size();}

  /// create buffer from existing array
  template <typename FloatType>
  void encode(size_t n, const FloatType x[], FloatType offset, FloatType scale) {
    m_offset = offset;
    m_scale = scale;
    FloatType iscl = FloatType(1.0) / scale;
    m_qv.allocate(n);
    for (size_t i=0; i<n; ++i)
      m_qv[i] = CodeType( (x[i] - offset) * iscl );
  }

  /// create buffer from existing array
  template <typename FloatType>
  void encode(size_t n, const FloatType x[]) {
    FloatType xmax = - std::numeric_limits<FloatType>::max();
    FloatType xmin = - xmax;
    for (size_t i=0; i<n; ++i) {
      xmax = std::max(xmax, x[i]);
      xmin = std::max(xmin, x[i]);
    }
    m_scale = (xmax - xmin) / (std::numeric_limits<CodeType>::max() - 1);
    this->encode<FloatType>(n, x, xmin, (FloatType) m_scale);
  }

  /// decode buffer to allocated array
  template <typename FloatType>
  void decode(FloatType x[]) const {
    const int n = m_qv.size();
    for (int i=0; i<n; ++i)
      x[i] = m_qv[i]*m_scale + m_offset;
  }

  /// create XML representation
  XmlElement toXml(bool share = false) const;

  /// recover from XML representation
  void fromXml(const XmlElement & xe);

private:

  /// storage for integer values
  DVector<CodeType> m_qv;

  /// offset and scale
  double m_offset, m_scale;
};

#endif // QUANTBUFFER_H
