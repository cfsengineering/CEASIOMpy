
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
 
#ifndef GENUA_SPARSITYCOUNTER_H
#define GENUA_SPARSITYCOUNTER_H

#include "defines.h"
#include <boost/unordered/unordered_set.hpp>

class ConnectMap;

namespace detail
{

  class SparseCoordinate
  {
  public:

    // undefined coordinate
    SparseCoordinate() {}

    // initialize
    SparseCoordinate(uint r, uint c) : row(r), col(c) {}

    // equality
    bool operator== (const SparseCoordinate & x) const {
      return ((row == x.row) and (col == x.col));
    }

    // inequality
    bool operator!= (const SparseCoordinate & x) const {
      return ((row != x.row) or (col != x.col));
    }

    // comparison, for use in ordered sets
    bool operator< (const SparseCoordinate & x) const {
      if (row < x.row)
        return true;
      else if (row > x.row)
        return false;
      else
        return col < x.col;
    }

    // row and column indices
    uint row, col;
  };

  // hash function for SparseCoordinate, extends boost::hash_value
  inline std::size_t hash_value(const SparseCoordinate & x) {
    size_t seed = x.row;
    boost::hash_combine(seed, x.col);
    return seed;
  }

}

/** Sparsity pattern counter based on hash table.

  Sparsity Counter can be used to assemble the nonzero pattern of a
  sparse matrix from irregular input data, for instance when the sparsity
  pattern is determined by a numerical criterion instead of a purely
  topological relationship. The sparsity pattern is stored in an
  boost::unordered_set, which is most likely rather inefficient for
  access in numerical algorithms. Therefore, this object is normally
  only used in the construction phase of the sparse matrix nonzero
  pattern, which is then stored efficiently in a ConnectMap.

  \todo Evaluate whether the use of ordered (std::set) containers is more
  efficient, as it eliminates the need for the sorting step in
  ConnectMap::assign().

  \sa ConnectMap
  */
class SparsityCounter
{
public:

  typedef boost::unordered_set<detail::SparseCoordinate> CoordSet;
  typedef CoordSet::const_iterator const_iterator;

  /// empty counter
  SparsityCounter() {}

  /// number of entries registered
  size_t size() const {return coord.size();}

  /// access stored coordinates
  const_iterator begin() const {return coord.cbegin();}

  /// access stored coordinates
  const_iterator end() const {return coord.cend();}

  /// append coordinate value to set
  void append(uint row, uint col) {
    coord.insert( detail::SparseCoordinate(row, col) );
  }

  /// append multiple values for the same row
  void append(uint row, uint n, const uint cols[]) {
    for (uint i=0; i<n; ++i)
      coord.insert( detail::SparseCoordinate(row, cols[i]) );
  }

  /// append a full map
  void append(const ConnectMap & map);

  /// merge with another counter
  void merge(const SparsityCounter & a) {
    coord.insert(a.begin(), a.end());
  }

  /// remove contents
  void clear() {coord.clear();}

private:

  /// unique storage for coordinates
  CoordSet coord;
};

template <int lg2n>
class BucketMap
{
public:

  enum {NB = (1 << lg2n)};

  typedef detail::SparseCoordinate    Coordinate;
  typedef std::vector<Coordinate>     Bucket;
  typedef Bucket::const_iterator      const_iterator;
  typedef Bucket::iterator            iterator;

  /// number of coordinates stored
  uint size() const {
    uint s = 0;
    for (int i=0; i<NB; ++i)
      s += buckets[i].size();
    return s;
  }

  /// number of buckets used
  uint nbuckets() const {return NB;}

  /// determine bucket index for row r
  uint ibucket(uint r) const {return r - ((r >> lg2n) << lg2n);}

  /// access bucket for row r
  const Bucket & bucket(uint r) const {return buckets[ibucket(r)];}

  /// access bucket for row r
  Bucket & bucket(uint r) {return buckets[ibucket(r)];}

  /// iterate over bucket ib
  const_iterator begin(uint ib) const {return buckets[ib].begin();}

  /// iterate over bucket ib
  const_iterator end(uint ib) const {return buckets[ib].end();}

  /// iterate over entries for row r
  const_iterator beginRow(uint r) const {
    const Bucket & b( bucket(r) );
    return std::lower_bound(b.begin(), b.end(), Coordinate(r,0));
  }

  /// iterate over entries for row r
  const_iterator endRow(uint r) const {
    const Bucket & b( bucket(r) );
    return std::upper_bound(b.begin(), b.end(), Coordinate(r,NotFound));
  }

  /// insert a coordinate
  void append(uint row, uint col) {
    Bucket & b( bucket(row) );
    Coordinate c(row,col);
    iterator pos = std::lower_bound(b.begin(), b.end(), c);
    if (pos == b.end() or *pos != c)
      b.insert(pos, c);
  }

  /// merge with another bucket map
  void merge(const BucketMap<lg2n> & other) {
//#pragma omp parallel for
    for (int i=0; i<NB; ++i) {
      Bucket tmp( buckets[i] );
      tmp.insert(tmp.end(),
                 other.buckets[i].begin(),
                 other.buckets[i].end());
      std::sort(tmp.begin(), tmp.end());
      iterator last = std::unique(tmp.begin(), tmp.end());
      buckets[i] = Bucket(tmp.begin(), last);
    }
  }

  /// clear all contents
  void clear() {
    for (int i=0; i<NB; ++i)
      buckets[i].clear();
  }

private:

  /// buckets
  Bucket buckets[NB];
};


#endif // SPARSITYCOUNTER_H
