
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
 
#ifndef GENUA_SPVECTOR_H
#define GENUA_SPVECTOR_H

#include <iostream>
#include "defines.h"
#include "dvector.h"
#include "dmatrix.h"

/** Sparse vector.

  SpVector contains an array of indices and an array of values with the
  same length. It is mainly used to implement the SpMatrix. Note that
  SpVector::size() returns the external length of the full vector
  including zero elements, not the number of non-zero elements.

  */
template <typename Type>
class SpVectorT
{
  public:

    /// construction
    SpVectorT(uint len=0) : n(len) {}
    
    /// initialized construction
    SpVectorT(uint nc, const Indices & ix, const DVector<Type> & v) :
      n(nc), idx(ix), val(v) {}

    /// modify outer length
    void setOuterLength(uint cols) {n = cols;}

     /// outer size
    uint size() const {return n;}

    /// nonzero elements
    uint nonzero() const {return idx.size();}

    /// allocate space for nnz nonzero entries  
    void allocate(uint nnz) {
      idx.resize(nnz);
      val.resize(nnz);
    }
    
    /// access column index
    uint index(uint i) const {
      assert(idx.size() > i);
      return idx[i];
    }

    /// access column index
    uint & index(uint i) {
      assert(idx.size() > i);
      return idx[i];
    }
    
    /// access value
    Type value(uint i) const {
      assert(val.size() > i);
      return val[i];
    }

    /// access value
    Type & value(uint i) {
      assert(val.size() > i);
      return val[i];
    }
    
    /// access all column indices 
    const Indices & indices() const {return idx;}
    
    /// access all values 
    const DVector<Type> & values() const {return val;}

    /// const access
    Type operator[] (uint i) const {
      assert(n > i);
      Indices::const_iterator pos;
      pos = std::lower_bound(idx.begin(), idx.end(), i);
      if (pos == idx.end() or *pos != i)
        return 0.0;
      else {
        uint dst = std::distance(idx.begin(), pos);
        return val[dst];
      }
    }

    /// mutable access
    Type & operator[] (uint i) {
      uint dst;
      Indices::iterator pos;
      pos = std::lower_bound(idx.begin(), idx.end(), i);
      dst = std::distance(idx.begin(), pos);
      if (pos == idx.end() or *pos != i) {
        idx.insert(pos, i);
        typename DVector<Type>::iterator vpos(val.begin());
        std::advance(vpos,dst);
        return *(val.insert(vpos, 0.0));
      }
      else
        return val[dst];
    }
    
    /// append an index/value pair (no checking!)
    void push_back(uint i, Type v) {
      idx.push_back(i);
      val.push_back(v);
    }

    /// add another sparse vector (fills)
    void add(const SpVectorT & v) {
      uint ix, ip, dst;
      Indices::iterator pos;
      typename DVector<Type>::iterator vpos;
      for (uint i=0; i<v.nonzero(); ++i) {
        ix = v.index(i);
        pos = std::lower_bound(idx.begin(), idx.end(), ix);
        dst = std::distance(idx.begin(), pos);
        if (pos == idx.end() or *pos != ix) {
          idx.insert(pos, ix);
          vpos = val.begin();
          std::advance(vpos, dst);
          val.insert(vpos, v.value(i));
        }
        else {
          ip = distance(idx.begin(), pos);
          val[ip] += v.value(i);
        }
      }
    }    

    /// scale
    void scale(Type f) {
      typename DVector<Type>::iterator itr;
      for (itr = val.begin(); itr != val.end(); ++itr)
        *itr *= f;
    }

    /// set all values to zero but keep column indices
    void vzero() {
      if (not val.empty())
        memset(&val[0], 0, val.size()*sizeof(Type));
    }

    /// dot product
    Type dot(const DVector<Type> & v) const {
      assert(v.size() == n);
      Type sum1(0.0), sum2(0.0), sum3(0.0), sum4(0.0);
      uint top = 4*(idx.size()/4);
      for (uint i=0; i<top; i+=4) {
        sum1 += val[i] * v[idx[i]];
        sum2 += val[i+1] * v[idx[i+1]];
        sum3 += val[i+2] * v[idx[i+2]];
        sum4 += val[i+3] * v[idx[i+3]];
      }
      sum1 += sum2 + sum3 + sum4;
      for (uint i=top; i<idx.size(); ++i)
        sum1 += val[i] * v[idx[i]];
      return sum1;
    }
    
    /// dot product with different type
    template <typename RType>
    RType xdot(const DVector<RType> & v) const {
      assert(v.size() == n);
      RType sum1(0.0), sum2(0.0), sum3(0.0), sum4(0.0);
      uint top = 4*(idx.size()/4);
      for (uint i=0; i<top; i+=4) {
        sum1 += val[i] * v[idx[i]];
        sum2 += val[i+1] * v[idx[i+1]];
        sum3 += val[i+2] * v[idx[i+2]];
        sum4 += val[i+3] * v[idx[i+3]];
      }
      sum1 += sum2 + sum3 + sum4;
      for (uint i=top; i<idx.size(); ++i)
        sum1 += val[i] * v[idx[i]];
      return sum1;
    }
    
//     // lower triangular dot product (deprecated)
//     Type lower_dot(uint k, const DVector<Type> & v) const {
//       assert(v.size() == n);
//       Type sum(0.0);
//       Indices::const_iterator pos;
//       pos = std::lower_bound(idx.begin(), idx.end(), k);
//       if (pos == idx.end())
//         return 0;
//       uint na = std::distance(idx.begin(), pos);
//       for (uint i=0; i<na; ++i)
//         sum += val[i] * v[idx[i]];
//       return sum;
//     }
    
//     // lower triangular dot product
//     Type lower_dot(uint k, const Matrix & m, uint col) const {
//       assert(m.nrows() == n);
//       Type sum(0.0);
//       Indices::const_iterator pos;
//       pos = std::lower_bound(idx.begin(), idx.end(), k);
//       if (pos == idx.end())
//         return 0;
//       uint na = std::distance(idx.begin(), pos);
//       for (uint i=0; i<na; ++i)
//         sum += val[i] * m(idx[i], col);
//       return sum;
//     }
    
    /// simplified lower triangular dot product
    Type ldot(int k, const DVector<Type> & v) const {
      assert(v.size() == n);
      assert(uint(k) < idx.size());
      Type sum(0.0);
      for (int i=0; i<k; ++i)
        sum += val[i] * v[idx[i]];
      return sum;
    }
    
    /// simplified lower triangular dot product
    Type ldot(int k, const Matrix & m, uint col) const {
      assert(m.nrows() == n);
      assert(uint(k) < idx.size());
      Type sum(0.0);
      for (int i=0; i<k; ++i)
        sum += val[i] * m(idx[i], col);
      return sum;
    }

//     // upper triangular dot product (deprecated)
//     Type upper_dot(uint k, const DVector<Type> & v) const {
//       assert(v.size() == n);
//       Type sum(0.0);
//       Indices::const_iterator pos;
//       pos = std::lower_bound(idx.begin(), idx.end(), k);
//       if (pos == idx.end())
//         return 0;
//       uint na = std::distance(idx.begin(), pos);
//       while (idx[na] <= k)
//         ++na;
//       for (uint i=na; i<idx.size(); ++i)
//         sum += val[i] * v[idx[i]];
//       return sum;
//     }
    
//     // upper triangular dot product
//     Type upper_dot(uint k, const Matrix & m, uint col) const {
//       assert(m.nrows() == n);
//       Type sum(0.0);
//       Indices::const_iterator pos;
//       pos = std::lower_bound(idx.begin(), idx.end(), k);
//       if (pos == idx.end())
//         return 0;
//       uint na = std::distance(idx.begin(), pos);
//       while (idx[na] <= k)
//         ++na;
//       for (uint i=na; i<idx.size(); ++i)
//         sum += val[i] * m(idx[i], col);
//       return sum;
//     }
    
    /// simplified upper triangular dot product
    Type udot(int k, const DVector<Type> & v) const {
      assert(v.size() == n);
      Type sum(0.0);
      int ni(idx.size());
      for (int i=k; i<ni; ++i)
        sum += val[i] * v[idx[i]];
      return sum;
    }
    
    /// simplified upper triangular dot product
    Type udot(int k, const Matrix & m, uint col) const {
      assert(m.nrows() == n);
      Type sum(0.0);
      int ni(idx.size());
      for (int i=k; i<ni; ++i)
        sum += val[i] * m(idx[i], col);
      return sum;
    }
    
    /// update a dense vector y += alfa*this
    void axpy(Type alfa, DVector<Type> & y) const {
      assert(y.size() == n);
      uint top = 4*(idx.size()/4);
      for (uint i=0; i<top; i+=4) {
        y[idx[i]] += alfa*val[i];
        y[idx[i+1]] += alfa*val[i+1];
        y[idx[i+2]] += alfa*val[i+2];
        y[idx[i+3]] += alfa*val[i+3];
      }
      for (uint i=top; i<idx.size(); ++i)
        y[idx[i]] += alfa*val[i];
    }

    /// find an index, return NotFound if not found, else position
    uint find(uint i) const {
      assert(i < n);
      Indices::const_iterator pos;
      pos = std::lower_bound(idx.begin(), idx.end(), i);
      if (pos == idx.end() or *pos != i)
        return NotFound;
      else
        return std::distance(idx.begin(), pos);
    }
    
    /// find the position that index i would take
    uint lower_bound(uint i) const {
      Indices::const_iterator pos;
      pos = std::lower_bound(idx.begin(), idx.end(), i);
      if (pos == idx.end())
        return NotFound;
      else
        return std::distance(idx.begin(), pos);
    }
    
    /// fill data from other sparse vector
    void copy(const SpVectorT<Type> & v) {
      idx = v.idx;
      val = v.val;
    }

    /// shift all column indices by constant
    void shiftColumns(int offset) {
      const uint nnz(idx.size());
      for (uint i=0; i<nnz; ++i)
        idx[i] += offset;
    }

    /// clear storage
    void clear() {
      idx.clear();
      val = DVector<Type>();
    }

    /// shrink to fit
    void shrink() {
      DVector<Type>(val).swap(val);
      Indices(idx).swap(idx);
    }
    
    /// copy to r with index restriction
    void irestrict(const Indices & keep, SpVectorT<Type> & r) const {
      r.clear();
      Indices::const_iterator pos;
      for (uint i=0; i<idx.size(); ++i) {
        uint oix = idx[i];
        pos = std::lower_bound(keep.begin(), keep.end(), oix);
        if (pos != keep.end() and *pos == oix) {
          uint ip = std::distance(keep.begin(), pos);
          r.idx.push_back(ip);
          r.val.push_back(val[i]);
        }
      }
    }
    
    /// keep only columns below nc
    void irestrict(uint nc) {
      n = nc;
      Indices::iterator pos = std::lower_bound(idx.begin(), idx.end(), nc);
      if (pos == idx.end())
        return;
      uint ipos = std::distance(idx.begin(), pos);
      idx.erase(pos, idx.end());
      val.erase(val.begin()+ipos, val.end());
    }
    
    /// compute memory used 
    double megabytes() const {
      double bts(0.0);
      bts  = sizeof(SpVectorT<Type>);
      bts += idx.capacity() * sizeof(Indices::value_type);
      bts += val.capacity() * sizeof(Type);
      return 1e-6*bts;
    }
    
    /// write to binary stream
    void writeBin(std::ostream & os) const {
      assert(idx.size() == val.size());
      uint nv = idx.size();
      os.write((const char*) &nv, sizeof(uint));
      os.write((const char*) &idx[0], nv*sizeof(Indices::value_type));
      os.write((const char*) val.pointer(), nv*sizeof(Type));
    }

    /// read from binary stream
    void readBin(std::istream & is) {
      uint nv;
      is.read((char*) &nv, sizeof(uint));
      idx.resize(nv);
      val.resize(nv);
      is.read((char*) &idx[0], nv*sizeof(Indices::value_type));
      is.read((char*) &val[0], nv*sizeof(Type));
    }

    /// swap contents
    void swap(SpVectorT<Type> & a) {
      std::swap(n, a.n);
      idx.swap(a.idx);
      val.swap(a.val);
    }

  private:

    /// outer length
    uint n;

    /// indices
    Indices idx;

    /// values
    DVector<Type> val;
};

typedef SpVectorT<Real> SpVector;
typedef SpVectorT<Complex> CpxSpVector;

#endif
