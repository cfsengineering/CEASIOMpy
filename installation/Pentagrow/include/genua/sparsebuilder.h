
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
 
#ifndef GENUA_SPARSEBUILDER_H
#define GENUA_SPARSEBUILDER_H

#include "defines.h"
#include "parallel_algo.h"
#include <vector>
#include <algorithm>

namespace detail {

// TODO: Modify to support block matrices (CsrMatrix with N > 1)

template <typename FloatType>
struct Triplet {

  Triplet() {}
  Triplet(uint r, uint c, FloatType v) : key(pack(r,c)), val(v) {}

  static uint64_t pack(uint r, uint c) {
    uint64_t wr(r), wc(c);
    return (wr << 32) | wc;
  }

  uint row() const {
    return (key >> 32);
  }

  uint col() const {
    return (key & uint64_t(0xffffffff));
  }

  bool invalid() const {
    return ((row() == NotFound) or (col() == NotFound));
  }

  bool valid() const {
    return (not invalid());
  }

  FloatType value() const {return val;}

  bool operator< (const Triplet &a) const {
    return (key < a.key);
  }

  uint64_t key;
  FloatType val;
};

}

/** Helper object for the assembly of sparse matrices
 *
 *  SparseBuilder is intended to be used as a helper object for the
 *  parallel assembly of large sparse matrices, in particular in the case where
 *  the iteration over the range of generating objects is expensive so that
 *  only one single pass is to be performed. Furthermore, when the number of
 *  (row, column, value) triplets which will be generated in the process is
 *  known in advance, then the assembly procedure can be parallelized because
 *  each element can access disjoint storage locations.
 *
 *  The drawback is that SparseBuilder requires more temporary memory than
 *  other techniques such as the two-pass approach in ConnectMap, because
 *  matrix values are stored along with the coordinate pair, while the two-
 *  pass procedure only stores redundant column indices.
 *
 *  \ingroup numerics
 *  \sa ConnectMap, CsrMatrix
 */
template <typename FloatType>
class SparseBuilder
{
public:

  typedef detail::Triplet<FloatType>                      Triplet;
  typedef typename std::vector<Triplet>::const_iterator   const_iterator;
  typedef typename std::vector<Triplet>::iterator         iterator;

  /// initialize and reserve space
  SparseBuilder(size_t n = 0) { m_triplets.reserve(n); }

  /// access triplet range
  const_iterator begin() const { return m_triplets.begin(); }

  /// access triplet range
  const_iterator end() const { return m_triplets.end(); }

  /// reserve space
  void reserve(size_t n) { m_triplets.reserve(n); }

  /// resize triplet array
  void resize(size_t n) { m_triplets.resize(n); }

  /// number of triplets present
  size_t size() const {return m_triplets.size();}

  /// access triplet i
  Triplet & operator[] (size_t i) { return m_triplets[i]; }

  /// access triplet i
  const Triplet & operator[] (size_t i) const { return m_triplets[i]; }

  /// set triplet at index i
  void assign(size_t i, uint r, uint c, FloatType v) {
    m_triplets[i] = Triplet(r, c, v);
  }

  /// append triplet
  void append(uint row, uint col, FloatType v) {
    m_triplets.emplace_back(row, col, v);
  }

  /// append MxN matrix of triplets (element assembly)
  template <int M, int N>
  void append(const uint row[], const uint col[], const FloatType v[]) {
    Triplet t[M*N];
    for (int j=0; j<N; ++j)
      for (int i=0; i<M; ++i)
        t[N*j+i] = Triplet(row[i], col[j], v[N*j+i]);
    m_triplets.insert(m_triplets.end(), t, t+(M*N));
  }

  /// merge with another builder
  void merge(const SparseBuilder &a) {
    m_triplets.insert(m_triplets.end(), a.begin(), a.end());
  }

  /// merge with sorted builder
  void mergeSorted(const SparseBuilder &a) {
    size_t mid = m_triplets.size();
    merge(a);
    std::inplace_merge(m_triplets.begin(),
                       m_triplets.begin()+mid, m_triplets.end());
  }

  /// sort in parallel, make unique
  void sort(bool inparallel) {

    if (m_triplets.empty())
      return;

    if (inparallel)
      parallel::sort(m_triplets.begin(), m_triplets.end());
    else
      std::sort(m_triplets.begin(), m_triplets.end());

    // skip to first valid triplet
    iterator first, result, last(m_triplets.end());
    first = result = m_triplets.begin();
    while (first != last and first->invalid())
      ++first;

    // keep valid triplets and merge those with identical keys
    while (++first != last) {
      if ( first->valid() ) {
        if ( result->key != first->key )
          *(++result) = *first;
        else  // duplicate key
          result->val += first->val;
      } // is valid
    }
    ++result;
    m_triplets.erase(result, last);
  }

  /// clear values
  void clear() { m_triplets.clear(); }

private:

  /// collection of triplets
  std::vector<Triplet> m_triplets;
};



#endif // SPARSEBUILDER_H
