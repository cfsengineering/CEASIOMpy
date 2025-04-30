
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

#include "xcept.h"
#include "strutils.h"
#include "sparsitycounter.h"
#include "connectmap.h"
#include "dbprint.h"
#include "parallel_loop.h"
#include "ffanode.h"
#include <boost/config.hpp>
#include <numeric>

#ifdef HAVE_MTMETIS
#include <mtmetis.h>
#elif defined(HAVE_METIS)
extern "C" {
#include <metis.h>
}
#endif

#if defined(METIS_VER_MAJOR) and METIS_VER_MAJOR >= 5
#undef HAVE_METIS
#define HAVE_METIS METIS_VER_MAJOR
#endif

using namespace std;

static inline bool invalid_key(uint64_t key)
{
  uint64_t wr = (key >> 32);
  uint64_t wc = (key & uint64_t(0xffffffff));
  uint32_t r = (uint32_t) wr;
  uint32_t c = (uint32_t) wc;
  return (r == NotFound) or (c == NotFound);
}

static inline bool invalid_upper_key(uint64_t key)
{
  uint64_t wr = (key >> 32);
  uint64_t wc = (key & uint64_t(0xffffffff));
  uint32_t r = (uint32_t) wr;
  uint32_t c = (uint32_t) wc;
  return (r == NotFound) or (c == NotFound) or (r > c);
}

static inline bool invalid_lower_key(uint64_t key)
{
  uint64_t wr = (key >> 32);
  uint64_t wc = (key & uint64_t(0xffffffff));
  uint32_t r = (uint32_t) wr;
  uint32_t c = (uint32_t) wc;
  return (r == NotFound) or (c == NotFound) or (r < c);
}

static inline bool in_lower_triangle(uint i, uint j)
{
  return (i >= j);
}

static inline bool in_upper_triangle(uint i, uint j)
{
  return (i <= j);
}

size_t ConnectMap::dropInvalidPairs(Symmetry sym, size_t n, uint64_t sp[])
{
  switch (sym) {
  case Unsymmetric:
    return std::distance(sp, std::remove_if(sp, sp+n, invalid_key));
  case LowerTriangular:
    return std::distance(sp, std::remove_if(sp, sp+n, invalid_lower_key));
  case UpperTriangular:
    return std::distance(sp, std::remove_if(sp, sp+n, invalid_upper_key));
  }

  // never reached.
  return n;
}

void ConnectMap::generatePairs(const Indices &rowMap, const Indices &colMap,
                               uint rowOffset, uint colOffset,
                               ConnectMap::PairArray &pairs) const
{
  pairs.reserve( pairs.size() + icol.size() );
  const uint nr = size();
  for (uint i=0; i<nr; ++i) {
    const uint mi = rowMap.empty() ? i : rowMap[i];
    if (mi != NotFound) {
      const uint nc = size(mi);
      const uint *jc = first(mi);
      for (uint k=0; k<nc; ++k) {
        const uint mj = colMap.empty() ? jc[k] : colMap[jc[k]];
        if (mj != NotFound)
          pairs.push_back( this->packpair( mi+rowOffset, mj+colOffset ) );
      }
    }
  }
}

void ConnectMap::generatePairs(uint rowOffset, uint colOffset,
                               ConnectMap::PairArray &pairs) const
{
  pairs.reserve( pairs.size() + icol.size() );
  const uint nr = size();
  for (uint i=0; i<nr; ++i) {
    const uint nc = size(i);
    const uint *jc = first(i);
    for (uint k=0; k<nc; ++k)
      pairs.push_back( packpair( i+rowOffset, jc[k]+colOffset ) );
  }
}

void ConnectMap::assign(uint nrows, size_t npairs, const uint64_t sp[])
{
  irow.resize(nrows+1);
  irow[0] = 0;

  icol.resize(npairs);
  uint32_t r, c, k(0);
  for (size_t i=0; i<npairs; ++i) {
    unpackpair(sp[i], r, c);
    assert(r != NotFound and c != NotFound);
    assert(r < nrows);
    icol[i] = c;
    if (r != k) {
      assert(r > k);
      while (r > k) {
        ++k;
        assert(k < irow.size());
        irow[k] = i;
      }
    } // r != k
  } // i, npair

  // there may be empty rows following the last nonzero element
  ++k;
  while (k <= nrows)
    irow[k++] = npairs;
}

void ConnectMap::assign(const std::vector<Indices> & m) 
{
  clear();
  const uint nr(m.size());
  irow.resize(nr+1);
  irow[0] = 0;
  for (uint i=0; i<nr; ++i) {
    icol.insert(icol.end(), m[i].begin(), m[i].end());
    irow[i+1] = icol.size();
  }
  // Indices(icol).swap(icol);
  icol.shrink_to_fit();
}

void ConnectMap::assign(uint nr, const Indices & lmap) 
{
  assert(lmap.size() % 2 == 0);
  const uint n(lmap.size());
  const uint nnz(n/2);
  irow.resize(nr+1);
  icount.resize(nr);
  std::fill(icount.begin(), icount.end(), 0);
  for (uint i=0; i<nnz; ++i) {
    uint ir = lmap[2*i];
    assert(ir < nr);
    ++icount[ir];
  }
  
  irow[0] = 0;
  for (uint i=1; i<nr+1; ++i)
    irow[i] = irow[i-1] + icount[i-1];
  std::fill(icount.begin(), icount.end(), 0);
  
  icol.resize(nnz);
  for (uint i=0; i<nnz; ++i) {
    uint ir = lmap[2*i];
    uint k = lmap[2*i+1];
    icol[irow[ir] + icount[ir]] = k;
    ++icount[ir];
  }
  icount.clear();
}

void ConnectMap::assign(uint nr, const SparsityCounter & sc)
{
  // not a random-access iterator - cannot easily parallelize this
  SparsityCounter::const_iterator itr, last;
  last = sc.end();

  clear();
  beginCount(nr);
  for (itr = sc.begin(); itr != last; ++itr)
    incCount( itr->row );
  endCount();

  for (itr = sc.begin(); itr != last; ++itr)
    append(itr->row, itr->col);

  sort();
}

void ConnectMap::incCount(const ConnectMap & map, int rowOffset)
{
  const int nr = map.size();
  for (int i=0; i<nr; ++i)
    incCount(i+rowOffset, map.size(i));
}

void ConnectMap::incCount(const ConnectMap & spty, const Indices & rcmap)
{
  const int nr = spty.size();
  for (int i=0; i<nr; ++i)
    incCount(rcmap[i], spty.size(i));
}

void ConnectMap::endCount()
{
  const uint nr(icount.size());
  irow.resize(nr+1);
  irow[0] = 0;
  for (uint i=1; i<nr+1; ++i)
    irow[i] = irow[i-1] + icount[i-1];
  uint nnz = irow.back();
  icol.clear();
  icol.resize(nnz);
  std::fill(icount.begin(), icount.end(), 0);
}

void ConnectMap::allocate(uint nr, uint nc)
{
  clear();
  icol.resize(nr*nc);
  irow.resize(nr+1);
  for (uint i=0; i<nr+1; ++i)
    irow[i] = i*nc;
  icount.resize(nr);
  std::fill(icount.begin(), icount.end(), 0);
}

void ConnectMap::append(const ConnectMap & map, int rowOffset, int colOffset)
{
  const int nr = map.size();
  if (rowOffset == 0 and colOffset == 0) {
    for (int i=0; i<nr; ++i)
      append(i, map.size(i), map.first(i));
  } else {
    for (int i=0; i<nr; ++i) {
      const int ncol = map.size(i);
      const uint *jc = map.first(i);
      for (int j=0; j<ncol; ++j)
        append(i+rowOffset, jc[j]+colOffset);
    }
  }
}

void ConnectMap::append(const ConnectMap & spty, const Indices & rcmap)
{
  const int nr = spty.size();
  for (int i=0; i<nr; ++i) {
    const uint row = rcmap[i];
    const int nc = spty.size(i);
    const uint *jc = spty.first(i);
    for (int j=0; j<nc; ++j)
      append(row, rcmap[jc[j]]);
  }
}

void ConnectMap::compactify()
{
  // store sorted row lengths in trow
  const uint nr = size();
  Indices trow(nr+1);
  trow[0] = 0;

  assert(icount.size() == nr);

  // append() updates icount[i] to contain the number
  // of values in a row

  for (uint i=0; i<nr; ++i)
    trow[i+1] = trow[i] + icount[i];

  size_t nnz = trow.back();
  Indices tcol(nnz);
  for (uint i=0; i<nr; ++i) {
    Indices::const_iterator src = icol.begin() + irow[i];
    Indices::iterator dst = tcol.begin() + trow[i];
    const uint rlen = trow[i+1] - trow[i];
    std::copy(src, src+rlen, dst);
  }

  irow = std::move(trow);
  icol = std::move(tcol);
  icount = Indices();
}

uint ConnectMap::maxcolindex() const
{
  if (icol.empty())
    return 0;
  Indices::const_iterator pos;
  pos = std::max_element(icol.begin(), icol.end());
  return *pos;
}

uint ConnectMap::sharedColumns(uint i, uint j) const
{
  uint count = 0;
  const uint *itr1 = first(i);
  const uint *itr2 = first(j);
  const uint *last1 = itr1 + size(i);
  const uint *last2 = itr2 + size(j);
  while ((itr1 != last1) and (itr2 != last2)) {
    if (*itr1 < *itr2) {
      ++itr1;
    } else  {
      if (not (*itr2 < *itr1)) {
        ++itr1;
        ++count;
      }
      ++itr2;
    }
  }
  return count;
}

void ConnectMap::rowBlockPermutation(uint blockSize, Indices &perm) const
{
  const uint n = size();
  const uint nblock = (n%blockSize != 0) ? ((n/blockSize)+1) : (n/blockSize);
  perm.resize(n);
  std::vector<bool> taken(n, false);
  uint base = 0;

  // don't even consider blocking together a row with a very dense one
  const uint densityLimit = 4;
  for (uint i=0; i<nblock; ++i) {

    // pick the first available row
    for (uint j=base; j<n; ++j) {
      if (taken[i])
        ++base;
      else
        break;
    }
    assert(base < n);

    taken[base] = true;
    perm[i*nblock] = base;
    for (uint j=1; j<blockSize; ++j) {

      // last block may not be full
      if ( hint_unlikely(i*nblock+j >= n) )
        break;

      // first candidate is the next row not taken; this will be used if
      // it's either optimal or nothing better can be found
      uint best = base+1;
      for (uint k=base+1; k<n; ++k) {
        if (taken[k])
          ++best;
        else
          break;
      }

      // use it directly if there can't be a better one
      uint sopt = sharedColumns(base, best);
      if (sopt < size(base) and sopt < size(best)) {

        for (uint k=best+1; k<n; ++k) {
          if (taken[k])
            continue;
          if (size(k) > densityLimit*size(base))
            continue;
          uint s = sharedColumns(base, k);
          if (s > sopt) {
            sopt = s;
            best = k;
            if (sopt == size(base) or s == size(k))
              break;
          }
        }
      }

      taken[best] = true;
      perm[i*nblock+j] = best;
    }
  }
}

bool ConnectMap::metisPermutation(Indices &perm, Indices &iperm) const
{
#if defined(HAVE_METIS) || defined(HAVE_MTMETIS)

  // generate a symmetric map needed for metis
  const size_t n = size();
  ConnectMap sym;
  sym.beginCount(n);
  for (size_t i=0; i<n; ++i) {
    size_t ni = size(i);
    const uint *pcol = first(i);
    sym.incCount(i, ni);
    for (size_t j=0; j<ni; ++j)
      sym.incCount(pcol[j]);
  }
  sym.endCount();
  for (size_t i=0; i<n; ++i) {
    size_t ni = size(i);
    const uint *pcol = first(i);
    sym.append(i, ni, pcol);
    for (size_t j=0; j<ni; ++j)
      sym.append(pcol[j], i);
  }

  // specific modification for METIS: remove diagonal terms
  // as required for it's graph representation
  for (uint i=0; i<n; ++i) {
    uint *first = &(sym.icol[sym.irow[i]]);
    uint *last = first + sym.icount[i];
    std::replace(first, last, i, NotFound);
  }

  // compress() eliminates all references to NotFound
  sym.compress();

#if HAVE_MTMETIS

  // setup arguments for metis call
  mtmetis_vtx_t nvtxs = size();
  std::vector<mtmetis_adj_t> xadj;
  std::vector<mtmetis_vtx_t> adjncy;
  std::vector<mtmetis_pid_t> xperm(size());

  xadj.resize(sym.irow.size());
  std::copy(sym.irow.begin(), sym.irow.end(), xadj.begin());

  adjncy.resize(sym.icol.size());
  std::copy(sym.icol.begin(), sym.icol.end(), adjncy.begin());

  int stat;
  stat = mtmetis_nd(nvtxs, &xadj[0], &adjncy[0], nullptr, nullptr, &xperm[0]);
  if (stat != MTMETIS_SUCCESS)
    return false;

  iperm.assign(xperm.begin(), xperm.end());
  perm.resize(n);
  for (size_t i=0; i<n; ++i)
    perm[iperm[i]] = i;
  return true;

#elif HAVE_METIS >= 5

  // setup arguments for metis call
  idx_t nvtxs = size();
  std::vector<idx_t> xadj, adjncy;
  std::vector<idx_t> xperm(size()), ixperm(size());

  xadj.resize(sym.irow.size());
  std::copy(sym.irow.begin(), sym.irow.end(), xadj.begin());

  adjncy.resize(sym.icol.size());
  std::copy(sym.icol.begin(), sym.icol.end(), adjncy.begin());

  idx_t options[METIS_NOPTIONS];
  METIS_SetDefaultOptions(options);
  options[METIS_OPTION_NUMBERING] = 0;  // 0-based
#ifndef NDEBUG
  options[METIS_OPTION_DBGLVL] = METIS_DBG_INFO | METIS_DBG_CONTIGINFO;
#endif

  int stat;
  stat = METIS_NodeND(&nvtxs, &xadj[0], &adjncy[0], 0,
      options, &xperm[0], &ixperm[0]);
  if (stat != METIS_OK)
    return false;

  perm.assign(xperm.begin(), xperm.end());
  iperm.assign(ixperm.begin(), ixperm.end());
  return true;

#else // METIS 4

  // setup arguments for metis call
  int nvtxs = size();
  int numflag(0);
  int options[8];

  // use default settings for everything
  memset(options, 0, sizeof(options));

  //  options[0] = 1;   // no defaults
  //  options[1] = 3;   // SHEM
  //  options[2] = 1;   // edge-based region growing
  //  options[3] = 2;   // one-sided node FM refinement
  //  options[4] = 0;   // always = 0
  //  options[5] = 1;   // try to compress
  //  options[6] = 200; // move dense columns back
  //  options[7] = 3;   // introduce n separators per step

  std::vector<idxtype> xadj, adjncy;
  std::vector<idxtype> xperm(size()), ixperm(size());

  xadj.resize(sym.irow.size());
  std::copy(sym.irow.begin(), sym.irow.end(), xadj.begin());

  adjncy.resize(sym.icol.size());
  std::copy(sym.icol.begin(), sym.icol.end(), adjncy.begin());

  METIS_NodeND(&nvtxs, &xadj[0], &adjncy[0], &numflag,
      options, &xperm[0], &ixperm[0]);

  perm.assign(xperm.begin(), xperm.end());
  iperm.assign(ixperm.begin(), ixperm.end());
  return true;

#endif // MTMETIS, METIS4, METIS5

#else // no METIS
  (void) iperm;
  (void) perm;
  return false;
#endif
}

void ConnectMap::rowpermute(const Indices & rep)
{
  const uint nr(irow.size()-1);
  assert(rep.size() == nr);

  ConnectMap tmp;
  tmp.beginCount(nr);
  for (uint i=0; i<nr; ++i) {
    const uint repi = rep[i];
    uint rowlength = (repi != NotFound) ? this->size(repi) : 0;
    tmp.incCount(i, rowlength);
  }
  tmp.endCount();
  for (uint i=0; i<nr; ++i) {
    const uint repi = rep[i];
    if (repi != NotFound)
      tmp.append(i, this->size(repi), this->first(repi));
  }

  // no need to sort or compress because *this is sorted on entry
  irow = std::move(tmp.irow);
  icol = std::move(tmp.icol);
  icount.clear();
}

void ConnectMap::colpermute(const Indices &rep)
{
  const size_t n = icol.size();
  for (size_t i=0; i<n; ++i)
    icol[i] = rep[icol[i]];

  // replacement can introduce NotFound column indices which
  // are removed by compress()
  compress();
}

void ConnectMap::fillIn(const ConnectMap &amap, const ConnectMap &tmap,
                        std::vector<uint64_t> &f)
{
  // note: can be parallelized by rows using thread-private 'tf' which
  // must be merged at the end into global 'f'; each 'tf' is sorted
  // due to row-traversal

  // expect to generate at least 2*nnz new entries
  f.clear();
  f.reserve( 2*amap.nonzero() );

  const size_t n = amap.size();
  for (size_t i=0; i<n; ++i) {
    const_iterator ita, alast = amap.end(i);
    for (size_t j=0; j<n; ++j) {

      // skip entries which are already present in A
      if (binary_search(amap.begin(i), alast, j))
        continue;

      const_iterator itt, tlast = tmap.end(j);
      itt = tmap.begin(j);
      ita = amap.begin(i);

      // h-loop: if A(i,h)*A(h,j) != 0, add fill-in at (i,j)
      while ((itt != tlast) and (ita != alast)) {

        // looking left-up only, that's where fill-in is coming from
        if (*ita > j or *itt > i)
          break;

        if (*ita < *itt) {
          ++ita;
        } else if (*ita > *itt) {
          ++itt;
        } else {
          // h == *ita == *itt is present
          f.push_back( packpair(i,j) );
          break;
        }
      }
    }
  }

  // since we process by rows and add entries in increasing column order,
  // f is already sorted here
  assert(std::is_sorted(f.begin(), f.end()));
}

void ConnectMap::merge(const ConnectMap & a, const ConnectMap & b)
{
  assert(a.size() == b.size());
  const int na = a.size();
  const int nb = b.size();
  const int nr = max(na, nb);

  // count and allocate
  beginCount(nr);
  for (int i=0; i<na; ++i)
    incCount(i, a.size(i));
  for (int i=0; i<nb; ++i)
    incCount(i, b.size(i));
  endCount();

  // append data to rows
  // write in parallel to disjoint rows

#pragma omp parallel for
  for (int i=0; i<na; ++i)
    append(i, a.size(i), a.first(i));

#pragma omp parallel for
  for (int i=0; i<nb; ++i)
    append(i, b.size(i), b.first(i));

  compress();
}

void ConnectMap::catColumns(const ConnectMap &a, const ConnectMap &b, uint acol)
{
  const uint anr = a.size();
  assert(anr == b.size());

  clear();
  beginCount(anr);
  for (uint i=0; i<anr; ++i)
    incCount(i, a.size(i) + b.size(i));
  endCount();
  for (uint i=0; i<anr; ++i)
    append(i, a.size(i), a.first(i));
  append(b, 0, acol);

  // no need to sort again since a and b are sorted internally
  close();
}

void ConnectMap::catRows(const ConnectMap &a, const ConnectMap &b)
{
  clear();

  // simply concatenate column indices
  const size_t nza = a.icol.size();
  const size_t nzb = b.icol.size();
  icol.resize( nza + nzb );
  memcpy(&icol[0],   &(a.icol[0]), nza*sizeof(uint));
  memcpy(&icol[nza], &(b.icol[0]), nzb*sizeof(uint));

  // create row pointer array
  const size_t anr = a.size();
  const size_t bnr = b.size();
  irow.resize(anr + bnr + 1);
  memcpy(&irow[0], &(a.irow[0]), anr*sizeof(uint));

  const size_t nr = anr + bnr;
  for (size_t i=anr; i<nr+1; ++i)
    irow[i] = nza + b.irow[i-anr];
}

void ConnectMap::transpose(uint ncol, ConnectMap &mt) const
{
  const int nr = size();
  ConnectMap::const_iterator itr, ilast;

  mt.clear();
  mt.beginCount(ncol);
  for (int i=0; i<nr; ++i) {
    ilast = end(i);
    for (itr = begin(i); itr != ilast; ++itr)
      mt.incCount(*itr);
  }
  mt.endCount();

  for (int i=0; i<nr; ++i) {
    ilast = end(i);
    for (itr = begin(i); itr != ilast; ++itr)
      mt.append(*itr, i);
  }

  // the count is exact, appending is performed in order,
  // so that the result must be sorted at this stage
  // mt.compress();
  mt.close();
}

void ConnectMap::transpose(uint ncol)
{
  ConnectMap mt;
  transpose(ncol, mt);
  swap(mt);
}

float ConnectMap::megabytes() const
{
  float b;
  b  = sizeof(ConnectMap);
  b += static_cast<float>( (icol.capacity() + irow.capacity()
                            + icount.capacity()) * sizeof(uint) );
  return 1e-6f*b;
}

void ConnectMap::sort()
{
  const int nr = size();

  BEGIN_PARLOOP_CHUNK(0, nr, 256)
      for (int i=a; i<b; ++i) {
    Indices::iterator beg = icol.begin()+irow[i];
    Indices::iterator lst = icol.begin()+irow[i+1];
    std::sort(beg, lst);
  }
  END_PARLOOP
}

void ConnectMap::compress()
{
  // store sorted row lengths in trow
  const int nr = size();
  Indices trow(nr+1);
  trow[0] = 0;

  if ( int(icount.size()) == nr ) {

    // append() updates icount[i] to contain the number
    // of values in a row

    BEGIN_PARLOOP_CHUNK(0, nr, 256)
        for (int i=a; i<b; ++i) {
      Indices::iterator beg = icol.begin() + irow[i];
      Indices::iterator lst = beg + icount[i];
      std::sort(beg, lst);
      Indices::iterator unq = std::unique(beg, lst);
      while (unq > beg and *(unq - 1) == NotFound)
        --unq;
      trow[i+1] = std::distance(beg, unq);
    }
    END_PARLOOP_CHUNK

  } else {

    // if compress() is called outside of initializatin, icount is empty
    // but irow contains the correct offsets (before eliminating NotFounds)

    BEGIN_PARLOOP_CHUNK(0, nr, 256)
        for (int i=a; i<b; ++i) {
      Indices::iterator beg = icol.begin() + irow[i];
      Indices::iterator lst = icol.begin() + irow[i+1];
      std::sort(beg, lst);
      Indices::iterator unq = std::unique(beg, lst);
      while (unq > beg and *(unq - 1) == NotFound)
        --unq;
      trow[i+1] = std::distance(beg, unq);
    }
    END_PARLOOP_CHUNK

  }

  // construct offsets
  std::partial_sum(trow.begin(), trow.end(), trow.begin());
  
  // copy sorted rows in place (does not profit from parallelization)
  Indices tcol(trow.back());
  for (int i=0; i<nr; ++i) {
    Indices::const_iterator src = icol.begin() + irow[i];
    Indices::iterator dst = tcol.begin() + trow[i];
    uint rlen = trow[i+1] - trow[i];
    copy(src, src+rlen, dst);
  }
  
  tcol.swap(icol);
  irow.swap(trow);
  icount = Indices();
}

void ConnectMap::scotchify(ConnectMap & map) const
{
  const int n = size();
  map.beginCount(n);
  for (int i=0; i<n; ++i) {
    const int nc = size(i);
    for (int j=0; j<nc; ++j) {
      int jc = index(i,j);
      if (jc == i)
        continue;
      map.incCount(i);
      map.incCount(jc);
    }
  }
  map.endCount();

  for (int i=0; i<n; ++i) {
    const int nc = size(i);
    for (int j=0; j<nc; ++j) {
      int jc = index(i,j);
      if (jc == i)
        continue;
      map.append(i,jc);
      map.append(jc,i);
    }
  }
  map.compress();
}

bool ConnectMap::equalPattern(uint ri, uint rj) const
{
  if (size(ri) != size(rj))
    return false;
  else
    return std::equal(begin(ri), end(ri), begin(rj));
}

bool ConnectMap::equal(const ConnectMap & a) const
{
  if (size() != a.size())
    return false;
  if (nonzero() != a.nonzero())
    return false;
  if (not std::equal(irow.begin(), irow.end(), a.irow.begin()))
    return false;
  if (not std::equal(icol.begin(), icol.end(), a.icol.begin()))
    return false;
  else
    return true;
}

void ConnectMap::print(ostream &os)
{
  for (uint i=0; i<size(); ++i) {
    os << i << " :";
    for (const_iterator itr = begin(i); itr != end(i); ++itr)
      os << ' ' << *itr;
    os << endl;
  }
}

void ConnectMap::dropLowerTriangle(Indices & upperlix)
{
  ConnectMap m;
  const int n = size();
  m.beginCount(n);
  for (int i=0; i<n; ++i)
    m.incCount( i, size(i) );
  m.endCount();

  uint lix(0);
  upperlix.clear();
  upperlix.reserve( (nonzero() + n) / 2 );
  for (int i=0; i<n; ++i) {
    const int nc = size(i);
    const uint *jc = first(i);
    for (int j=0; j<nc; ++j) {
      uint kj = jc[j];
      if (kj >= (uint) i) {
        m.append(i, kj);
        upperlix.push_back(lix);
      }
      ++lix;
    }
  }
  m.compress();
  swap(m);
}

template <class Filter>
static void filtered_map(Filter f, const ConnectMap &org, ConnectMap &m)
{
  m.clear();
  const uint n = org.size();
  m.beginCount( n );
  for (uint i=0; i<n; ++i)
    m.incCount(i, org.size(i));
  m.endCount();
  for (uint i=0; i<n; ++i) {
    ConnectMap::const_iterator itr, last = org.end(i);
    for (itr = org.begin(i); itr != last; ++itr) {
      if ( f(i, *itr) )
        m.append(i, *itr);
    }
  }
  m.compress();
}

void ConnectMap::upperTriangle(ConnectMap &uptri) const
{
  filtered_map( in_upper_triangle, *this, uptri );
}

void ConnectMap::lowerTriangle(ConnectMap &lotri) const
{
  filtered_map( in_lower_triangle, *this, lotri );
}

uint ConnectMap::coloring(Indices &clr) const
{
  uint nc(0), c(0);
  const size_t n = size();
  clr.resize(n);
  std::fill(clr.begin(), clr.end(), 0);
  Indices rc;
  rc.reserve(64);
  for (size_t i=1; i<n; ++i) {
    c = 0;
    rc.clear();
    const uint nk = size(i);
    const uint *pcol = first(i);
    for (uint k=0; k<nk; ++k)
      rc.push_back(clr[pcol[k]]);
    std::sort(rc.begin(), rc.end());
    for (uint k=0; k<nk; ++k) {
      if (c == rc[k])
        ++c;
    }
    clr[i] = c;
    nc = std::max(nc, c);
  }
  return nc+1;
}

XmlElement ConnectMap::toXml(bool shared) const
{
  XmlElement xc("ColumnIndex");
  xc["count"] = str(icol.size());
  xc.asBinary(icol.size(), &icol[0], shared);
  
  XmlElement xr("RowPointer");
  xr["count"] = str(irow.size());
  xr.asBinary(irow.size(), &irow[0], shared);

  XmlElement xe("ConnectMap");
  xe.append(std::move(xr));
  xe.append(std::move(xc));
  return xe;
}

void ConnectMap::fromXml(const XmlElement & xe)
{
  if (xe.name() != "ConnectMap")
    throw Error("Incompatible XML representation for ConnectMap: "+xe.name());
  
  icount = Indices();
  XmlElement::const_iterator ite, ilast;
  ilast = xe.end();
  for (ite = xe.begin(); ite != ilast; ++ite) {
    const string & s = ite->name();
    if (s == "ColumnIndex") {
      icol.resize( Int(ite->attribute("count")) );
      ite->fetch(icol.size(), &icol[0]);
    } else if (s == "RowPointer") {
      irow.resize( Int(ite->attribute("count")) );
      ite->fetch(irow.size(), &irow[0]);
    }
  }
}

FFANodePtr ConnectMap::toFFA() const
{
  FFANodePtr root = boost::make_shared<FFANode>("sparsity");
  int32_t nnz = nonzero();
  int32_t nrow = size();
  root->append("nnz", nnz);
  root->append("nrow", nrow);

  {
    const size_t n = irow.size();
    std::vector<int> rowPtr(n);
    for (size_t i=0; i<n; ++i)
      rowPtr[i] = irow[i] + 1;
    root->append("row_pointer", n, 1, &rowPtr[0]);
  }

  {
    const size_t n = icol.size();
    std::vector<int> colIdx(n);
    for (size_t i=0; i<n; ++i)
      colIdx[i] = icol[i] + 1;
    root->append("column_index", n, 1, &colIdx[0]);
  }

  return root;
}

bool ConnectMap::fromFFA(const FFANodePtr &root)
{
  assert(root->name() == "sparsity");

  uint ip = root->findChild("row_pointer");
  if (ip == NotFound)
    return false;

  std::vector<int> tmp;
  tmp.resize(root->child(ip)->numel());
  root->child(ip)->retrieve(&tmp[0]);
  irow.resize(tmp.size());
  for (size_t i=0; i<tmp.size(); ++i)
    irow[i] = tmp[i] - 1;

  ip = root->findChild("column_index");
  if (ip == NotFound)
    return false;

  tmp.clear();
  tmp.resize(root->child(ip)->numel());
  root->child(ip)->retrieve(&tmp[0]);
  icol.resize(tmp.size());
  for (size_t i=0; i<tmp.size(); ++i)
    icol[i] = tmp[i] - 1;

  return true;
}

bool ConnectMap::checkPattern(uint nr, uint nc) const
{
  bool status = true;
  const int n = size();
  if (uint(n) > nr) {
    dbprint("ConnectMap size > nr");
    status = false;
  }

  for (int i=0; i<n; ++i) {
    const int m = size(i);
    if (m == 0) {
      dbprint("ConnectMap: empty row",i);
      status = false;
    }
    const uint *jc = first(i);
    for (int k=0; k<m; ++k) {
      if (jc[k] >= nc) {
        dbprint("ConnectMap: element",i,k," out of bounds: ",jc[k]);
        status = false;
      }
    }
  }
  return status;
}
