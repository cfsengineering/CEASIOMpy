
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
 
#ifndef GENUA_SPARSE_H
#define GENUA_SPARSE_H

#include <vector>
#include <limits>
#include <iostream>

#include "forward.h"
#include "dmatrix.h"
#include "spvector.h"

/** Compressed-row matrix.

  Random access matrix class using compressed row storage. Provides acceptable
  performance for matrix-vector products, combined with low storage
  requirements (approximately 12bytes, maximum 18bytes per entry). Storage
  grows dynamically so that sparsity pattern need not be known in advance.

  Disadvantage: Insertion has linear complexity (linear with nonzero elements
  per row). This could be improved by using a binary heap to store the
  sparse row vectors.

  */
template <typename Type>
class SpMatrixT
{
  public:

    /// construction
    SpMatrixT(uint r=0, uint c=0) : rows(r), cols(c) {
      m.resize(r);
      for (uint i=0; i<r; ++i)
        m[i] = SpVectorT<Type>(c);
    }

    /// constant access
    Type operator() (uint r, uint c) const {
      assert(rows > r);
      assert(cols > c);
      return m[r][c];
    }

    /// mutable access
    Type & operator() (uint r, uint c) {
      assert(rows > r);
      assert(cols > c);
      return m[r][c];
    }

    /// row access
    const SpVectorT<Type> & row(uint i) const
      {return m[i];}

    /// row access
    SpVectorT<Type> & row(uint i)
      {return m[i];}

    /// dense vector multiply (B*a)
    DVector<Type> operator* (const DVector<Type> & a) const {
      assert(a.size() == cols);
      DVector<Type> r(rows);
      for (uint i=0; i<rows; i++)
        r[i] = m[i].dot(a);
      return r;
    }
    
    /// inplace dense vector multiply (r += B*a)
    void mult(const DVector<Type> & a, DVector<Type> & r) const {
      assert(a.size() == cols);
      assert(r.size() == rows);
      for (uint i=0; i<rows; i++)
        r[i] += m[i].dot(a);
    }
    
    /// transpose multiply (B^T * a)
    DVector<Type> trans_mult(const DVector<Type> & a) const {
      assert(a.size() == rows);
      DVector<Type> r(cols);
      for (uint i=0; i<m.size(); i++)
        m[i].axpy(a[i], r);
      return r;
    }

    /// inplace transpose multiply (r += B^T * a)
    void trans_mult(const DVector<Type> & a, DVector<Type> & r) const {
      assert(a.size() == rows);
      assert(r.size() == cols);
      for (uint i=0; i<m.size(); i++)
        m[i].axpy(a[i], r);
    }
    
    /// scale matrix
    SpMatrixT<Type> & operator *= (Type f) {
      for (uint i=0; i<m.size(); ++i)
        m[i].scale(f);
      return *this;
    }

    /// add another sparse matrix
    SpMatrixT<Type> & operator += (const SpMatrixT & s) {
      assert(nrows() == s.nrows());
      assert(ncols() == s.ncols());
      for (uint i=0; i<m.size(); ++i)
        m[i].add(s.row(i));
      return *this;
    }

    /// dense matrix multiply b += this * a
    void mult(const DMatrix<Type> & a, DMatrix<Type> & b) const {
      assert(a.nrows() == cols);
      assert(b.nrows() == rows);
      assert(b.ncols() == a.ncols());
      uint nz, cl, ncol(a.ncols());
      Type vl;
      for (uint i=0; i<rows; i++) {
        nz = m[i].nonzero();
        for (uint k=0; k<nz; k++) {
          cl = m[i].index(k);
          vl = m[i].value(k);
          for (uint j=0; j<ncol; j++)
            b(i,j) += vl*a(cl,j);
        }
      }
    }
    
    /// dense matrix multiply
    DMatrix<Type> operator* (const DMatrix<Type> & a) const {
      assert(a.nrows() == cols);
      DMatrix<Type> b(rows, a.ncols());
      mult(a, b);
      return b;
    }

    /// find a index, return position or NotFound 
    uint find(uint i, uint j) const {
      return m[i].find(j);
    }

    /// outer dimension
    uint nrows() const {return rows;}

    /// outer dimension
    uint ncols() const {return cols;}

    /// compute number of nonzero entries
    uint nonzero() const {
      uint sum(0);
      for (uint i=0; i<m.size(); i++)
        sum += m[i].nonzero();
      return sum;
    }

    /// compute memory consumption
    double megabytes() const {
      double mb(0.0);
      mb = 1e-6*sizeof(SpMatrixT<Type>);
      for (uint i=0; i<m.size(); ++i)
        mb += m[i].megabytes();
      return mb;
    }

    /// set all values to zero, but keep sparsity pattern
    void vzero() {
      const int n = m.size();
      for (int i=0; i<n; ++i)
        m[i].vzero();
    }
    
    /// erase contents, but keep size 
    void clear() {
      for (uint i=0; i<m.size(); ++i)
        m[i].clear();
    }

    /// shrink to fit
    void shrink() {
      const int nr(m.size());
      for (int i=0; i<nr; i++)
        m[i].shrink();
    }
    
    /// restrict to indices in keep
    void irestrict(const Indices & keep, SpMatrixT<Type> & rsm) const {
      assert(rows == cols);
      rsm = SpMatrixT<Type>(keep.size(), keep.size());
      for (uint i=0; i<keep.size(); ++i) {
        const SpVector & r(m[keep[i]]);
        r.irestrict(keep, rsm.row(i));
      }
    }
    
    /// cut off rows and columns beyond nr, nc (inplace)
    void irestrict(uint nr, uint nc) {
      assert(nr <= rows);
      assert(nc <= cols);
      for (uint i=0; i<nr; ++i)
        m[i].irestrict(nc);
      m.erase(m.begin()+nr, m.end());
      assert(m.size() == nr);
      rows = nr;
      cols = nc;
    }
    
    /// conversion to crs format to colind[nnz], rowptr[rows+1], nzval[nnz]
    void toCrs(uint *colind, uint *rowptr, Type *nzval) const {
      uint pos(0);
      for (uint i=0; i<rows; ++i) {
        const uint nz(m[i].nonzero());
        for (uint j=0; j<nz; ++j) {
          nzval[pos+j] = m[i].value(j);
          colind[pos+j] = m[i].index(j);
        }
        rowptr[i] = pos;
        pos += nz;
      }
      rowptr[rows] = pos;
    }
    
    /// conversion to ccs format, rowind[nnz], colptr[cols+1], nzval[nnz]
    void toCcs(uint *rowind, uint *colptr, Type *nzval) const {
      // count how many nonzeros there are in each column
      Indices cnz(cols);
      std::fill(cnz.begin(), cnz.end(), 0);
      for (uint i=0; i<rows; ++i) {
        const uint nz(m[i].nonzero());
        for (uint j=0; j<nz; ++j)
          cnz[m[i].index(j)]++;
      }
      colptr[0] = 0;
      for (uint i=1; i<=rows; ++i)
        colptr[i] = colptr[i-1] + cnz[i-1];
    
      // fill data structure row-by-row
      uint c, pos;
      std::fill(cnz.begin(), cnz.end(), 0);
      for (uint r=0; r<rows; ++r) {
        const uint nz(m[r].nonzero());
        for (uint j=0; j<nz; ++j) {
          c = m[r].index(j);
          pos = colptr[c] + cnz[c];
          nzval[pos] = m[r].value(j);
          rowind[pos] = r;
          cnz[c]++;
        }
      }
    }
    
    /// write in plain ascii format: irow, icol, value
    void write(std::ostream & os) const {
      os.precision(16);
      for (uint i=0; i<m.size(); ++i)
        for (uint j=0; j<m[i].nonzero(); ++j)
          os << i << " " << m[i].index(j) << " " << m[i].value(j) << std::endl;
    }

    /// read from plain ascii format: irow, icol, value
    void read(std::istream & is) {
      rows = cols = NotFound;
      uint r, c, rmax(0), cmax(0);
      Real val;
      while (is) {
        is >> r >> c >> val;
        if (r >= m.size()) {
          m.resize(r+1);
        }
        (*this)(r,c) = val;
        rmax = std::max(rmax,r);
        cmax = std::max(cmax,c);
      }
      rows = rmax+1;
      cols = cmax+1;
      for (uint i=0; i<rows; ++i)
        m[i].setOuterLength(cols);
    }

    /// write to binary stream
    void writeBin(std::ostream & os) const {
      os.write((const char*) &rows, sizeof(uint));
      os.write((const char*) &cols, sizeof(uint));
      for (uint i=0; i<m.size(); ++i)
        m[i].writeBin(os);
    }

    /// read from binary stream
    void readBin(std::istream & is) {
      is.read((char*) &rows, sizeof(uint));
      is.read((char*) &cols, sizeof(uint));
      m.resize(rows);
      for (uint i=0; i<m.size(); ++i) {
        m[i] = SpVector(cols);
        m[i].readBin(is);
      }
    }

    /// swap contents
    void swap(SpMatrixT<Type> & a) {
      std::swap(rows, a.rows);
      std::swap(cols, a.cols);
      m.swap(a.m);
    }
    
  private:

    /// outer dimensions
    uint rows, cols;

    /// compressed rows
    std::vector<SpVectorT<Type> > m;
};

// SpMatrixT operator*(Type s, const SpMatrixT & m);
// SpMatrixT operator*(const SpMatrixT & m, Type s);
// SpMatrixT operator+(const SpMatrixT & a, const SpMatrixT & b);




#endif

