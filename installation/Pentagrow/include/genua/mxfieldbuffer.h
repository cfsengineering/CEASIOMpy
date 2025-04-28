
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
 
#ifndef GENUA_MXFIELDBUFFER_H
#define GENUA_MXFIELDBUFFER_H

#include "blob.h"
#include "svector.h"
#include "dvector.h"
#include "xmlelement.h"
#include <limits>

/** Abstraction for runtime-typed, sparse storage in MxMeshField.
 *
 * This class handles conversion of types between storage data (which may be
 * at lower precision to save space) and in-memory representation, as well as
 * the mapping of values for sparse arrays.
 *
 * This is a low-level class for use inside MxMeshField.
 *
 * \ingroup mesh
 * \sa MxMeshField, Blob
 */
class MxFieldBuffer
{
public:

  typedef double QuFloat;
  typedef int16_t QuInt;
  typedef uint32_t IdxType;
  typedef std::vector<IdxType> IndexArray;

#ifndef _MSC_VER
  static const IdxType npos = std::numeric_limits<IdxType>::max();
#else
  // MSVC doesn't recognize it's own constants; change this when changing IdxType
  static const IdxType npos = UINT_MAX;
#endif

  /// create empty buffer; quantization can only be set on construction
  MxFieldBuffer(bool quant = false)
    : m_lda(1), m_qoffset(0.0), m_qscale(0.0),
      m_quantType(TypeCode::None), m_quantized(quant) {}

  /// create buffer to store quantized data with fixed saturation limits
  MxFieldBuffer(double lowSat, double hiSat)
    : m_lda(1), m_quantType(TypeCode::None), m_quantized(true)
  {
    m_qoffset = 0.5*(lowSat + hiSat);
    m_qscale = 0.5*std::fabs(hiSat - lowSat) / std::numeric_limits<QuInt>::max();
  }

  /// copy construction
  MxFieldBuffer(const MxFieldBuffer &a) = default;

  /// move construction
  MxFieldBuffer(MxFieldBuffer &&a) { *this = std::move(a); }

  /// default copy assignment
  MxFieldBuffer &operator= (const MxFieldBuffer &a) = default;

  /// move assignment
  MxFieldBuffer &operator= (MxFieldBuffer &&a) {
    if (this != &a) {
      m_blob = std::move(a.m_blob);
      m_idx = std::move(a.m_idx);
      m_lda = a.m_lda;
      m_qoffset = a.m_qoffset;
      m_qscale = a.m_qscale;
      m_quantType = std::move(a.m_quantType);
      m_quantized = a.m_quantized;
    }
    return *this;
  }

  /// whether field is sparse
  bool isSparse() const {return (not m_idx.empty());}

  /// whether field is dense
  bool isDense() const {return (m_idx.empty());}

  /// true if array stored quantized as 16-bit int
  bool quantized() const {return m_quantized;}

  /// quantization offset used
  QuFloat quantOffset() const {return m_qoffset;}

  /// quantization scale used
  QuFloat quantScale() const {return m_qscale;}

  /// access sparse index array
  const IndexArray & sparsity() const {return m_idx;}

  /// number of scalars (not bytes) contained in binary data block
  size_t size() const {return m_blob.size();}

  /// data type represented
  TypeCode typeCode() const {
    return quantized() ? m_quantType : m_blob.typeCode();
  }

  /// leading dimension
  size_t dimension() const {return m_lda;}

  /// assign a dense array
  template <typename ValueType>
  void assign(TypeCode storageType, IdxType nval,
              const ValueType x[], IdxType ldim = 1, bool share = false)
  {
    m_lda = ldim;
    if (quantized()) {
      this->encode(nval*m_lda, x);
    } else {
      m_blob.assign(storageType, nval*m_lda, x, share);
    }
    m_idx = IndexArray();
  }

  /// assign a sparse array
  template <typename ValueType, typename IndexType>
  void assign(TypeCode storageType, IdxType nval, const IndexType idx[],
              const ValueType x[], IdxType ldim = 1, bool share = false)
  {
    m_lda = ldim;
    m_idx.clear();
    m_idx.resize( nval );
    std::copy(idx, idx+nval, m_idx.begin());
    if (quantized())
      this->encode( nval*m_lda, x );
    else
      m_blob.assign(storageType, nval*m_lda, x, share);
  }

  /// retrieve a single scalar value (for lda == 1) at global index i
  template <typename DstType>
  void extract(IdxType i, DstType &x) const {
    assert(m_lda == 1);
    IdxType k = m_idx.empty() ? i : indexOf(i);
    assert(k < m_blob.size() or k == npos);
    if (k != npos) {
      if (quantized())
        this->decode(1, m_blob.as<QuInt>(k), &x);
      else
        m_blob.extract(k, x);
    } else {
      x = DstType(0);
    }
  }

  /// retrieve a short vector of dimension N (when lda == N) at global index i
  template <typename DstType, uint N>
  void extract(IdxType i, SVector<N,DstType> &x) const {
    assert(m_lda == N);
    IdxType k = m_idx.empty() ? i : indexOf(i);
    assert(k < m_blob.size() or k == npos);
    if (k != npos) {
      if (quantized())
        this->decode(N, m_blob.as<QuInt>(k*N), x.pointer());
      else
        m_blob.extract<N>(k*N, x.pointer());
    } else {
      x = DstType(0);
    }
  }

  /// access a short vector of dimension N (when lda == N) at global index i
  template <typename DstType, uint N>
  void inject(IdxType i, const SVector<N,DstType> &x) {
    assert(m_lda == N);
    IdxType k = m_idx.empty() ? i : indexOf(i);
    assert(k < m_blob.size() or k == npos);
    if (k != npos) {
      if (quantized())
        this->encode(N, x.pointer(), m_blob.as<QuInt>(k*N));
      else
        m_blob.inject<N>(k*N, x.pointer());
    } else {
      x = DstType(0);
    }
  }

  /// copy entire block, x must have correct (outer, indexed) size if sparse
  template <typename DstType>
  void extract(DstType x[]) const {
    assert(m_lda == 1);
    if (isDense()) {
      if (quantized())
        this->decode( m_blob.size(), x );
      else
        m_blob.extract(x);
    } else {
      const IdxType ns = m_idx.size();
      DVector<DstType> tmp( ns );
      if (quantized())
        this->decode( ns, &tmp[0] );
      else
        m_blob.extract( &tmp[0] );
      for (IdxType i=0; i<ns; ++i)
        x[m_idx[i]] = tmp[i];
    }
  }

  /// copy into point list
  template <int N, typename DstType>
  void extract(IdxType nvec, SVector<N,DstType> x[]) const {
    assert(N == m_lda);
    if (isDense()) {
      assert(m_lda*nvec == m_blob.size());
      if (quantized())
        this->decode( nvec*N, x[0].pointer() );
      else
        m_blob.extract( x[0].pointer() );
    } else {
      const IdxType ns = m_idx.size();
      DVector<DstType> tmp( N*ns );
      if (quantized())
        this->decode(N*ns, &tmp[0]);
      else
        m_blob.extract( &tmp[0] );
      for (IdxType i=0; i<ns; ++i)
        for (IdxType k=0; k<m_lda; ++k)
          x[m_idx[i]][k] = tmp[i*m_lda+k];
    }
  }

  /// indexed extraction
  template <typename DstType>
  void extract(const Indices &idx, DstType x[]) const {
    assert(m_lda == 1);
    const size_t nx = idx.size();
    if ( isDense() ) {
      if (not quantized()) {
        m_blob.extract(idx.size(), &idx[0], x);
      } else {
        for (size_t j=0; j<nx; ++j)
          this->decode(1, m_blob.as<QuInt>(idx[j]), &x[j]);
      }
    } else {  // sparse
      if (not quantized()) {
        for (size_t j=0; j<nx; ++j) {
          IdxType k = indexOf(idx[j]);
          if (k != npos)
            m_blob.extract(k, x[j]);
          else
            x[j] = 0;
        }
      } else {
        for (size_t j=0; j<nx; ++j) {
          IdxType k = indexOf(idx[j]);
          if (k != npos)
            this->decode(1, m_blob.as<DstType>(k), &x[j]);
          else
            x[j] = 0;
        }
      }
    }
  }

  /// create XML representation
  XmlElement toXml(bool share) const;

  /// recover from XML representation
  bool fromXml(const XmlElement &xe);

  /// swap contents with a
  void swap(MxFieldBuffer &a) {
    m_blob.swap(a.m_blob);
    m_idx.swap(a.m_idx);
    std::swap(m_lda, a.m_lda);
    std::swap(m_qoffset, a.m_qoffset);
    std::swap(m_qscale, a.m_qscale);
    std::swap(m_quantType, a.m_quantType);
    std::swap(m_quantized, a.m_quantized);
  }

private:

  /// return local index for global index i
  IdxType indexOf(IdxType i) const {
    IndexArray::const_iterator pos;
    pos = std::lower_bound(m_idx.begin(), m_idx.end(), i);
    return (pos != m_idx.end() and *pos == i) ?
          std::distance(m_idx.begin(), pos) : npos;
  }

  /// determine encoding parameter
  template <typename FloatType>
  void qrange(size_t n, const FloatType x[]) {
    // use saturation levels passed in constructor if applicable
    if (m_qscale != 0.0)
      return;
    FloatType xmin = std::numeric_limits<FloatType>::max();
    FloatType xmax = -xmin;
    for (size_t i=0; i<n; ++i) {
      FloatType xi = x[i];
      xmin = std::min(xmin, xi);
      xmax = std::max(xmax, xi);
    }
    m_qoffset = 0.5*(xmin + xmax);
    m_qscale = 0.5*(xmax - xmin) / (std::numeric_limits<QuInt>::max());
  }

  /// encode floating-point array
  template <typename FloatType>
  void encode(size_t n, const FloatType x[], QuInt y[]) const {
    const FloatType iscl = FloatType(1.0) / m_qscale;
    const FloatType offs = FloatType(m_qoffset);
    for (size_t i=0; i<n; ++i)
      y[i] = QuInt( (x[i] - offs) * iscl );
  }

  /// encode array and store internally
  template <typename FloatType>
  void encode(size_t n, const FloatType x[]) {
    DVector<QuInt> qv(n);
    this->qrange(n, x);
    this->encode(n, x, qv.pointer());
    m_blob.assign(create_typecode<QuInt>(), qv.size(), qv.pointer(), false);
    m_quantType = create_typecode<FloatType>();
    assert( m_quantType.isReal() );
  }

  /// decode floating-point array
  template <typename FloatType>
  void decode(size_t n, const QuInt y[], FloatType x[]) const {
    const FloatType scl = FloatType(m_qscale);
    const FloatType offs = FloatType(m_qoffset);
    for (size_t i=0; i<n; ++i)
      x[i] = y[i]*scl + offs;
  }

  /// decode floating-point values from internal, encoded storage
  template <typename FloatType>
  void decode(size_t n, FloatType x[]) const {
    assert(n < m_blob.size());
    this->decode(n, m_blob.as<QuInt>(0), x);
  }

private:

  /// raw data
  Blob m_blob;

  /// indices of stored values (if sparse)
  IndexArray m_idx;

  /// leading array dimension for n-dim data fields
  IdxType m_lda;

  /// quantization parameters
  QuFloat m_qoffset, m_qscale;

  /// quantized float type (for reference, not used in computations)
  TypeCode m_quantType;

  /// flag indicating whether data is quantized
  bool m_quantized;
};

#endif // MXFIELDBUFFER_H
