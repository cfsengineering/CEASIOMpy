
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
 
#ifndef GENUA_RADIALSORT_H
#define GENUA_RADIALSORT_H

#include "point.h"
#include "algo.h"
#include "parallel_loop.h"
#include "parallel_algo.h"
#include "atomicop.h"

namespace detail {
template <typename FloatType>
class RiCmp {
public:
  RiCmp(const DVector<FloatType> &r) : m_radius(r) {}
  bool operator() (uint a, FloatType b) const {
    return m_radius[a] < b;
  }
  bool operator() (FloatType a, uint b) const {
    return a < m_radius[b];
  }
private:
  const DVector<FloatType> &m_radius;
};

template <uint N, typename FloatType>
class RadiusWorker
{
public:
  RadiusWorker(const PointList<N,FloatType> &pts, DVector<FloatType> &radius)
    : m_pts(pts), m_radius(radius) {}
  void operator() (uint a, uint b) {
    for (uint i=a; i<b; ++i)
      m_radius[i] = norm(m_pts[i]);
  }
private:
  const PointList<N,FloatType> &m_pts;
  DVector<FloatType> &m_radius;
};

} // detail

/** Radial sorting for point de-duplication.
 *
 * This free function can be used to identify and replace duplicate points in
 * a set. It is meant as an alternative for NDPointTree which provides the
 * same functionality, albeit with significantly higher memory overhead. If
 * nearest neighbor or radius queries are not required, this function can be
 * useful.
 *
 * \ingroup geometry
 * \sa NDPointTree
 */
template <uint N, typename FloatType>
void radial_repldup(const PointList<N,FloatType> &pts,
                    Indices &repl, Indices &keep,
                    FloatType threshold = gmepsilon)
{
  const int np = pts.size();
  DVector<FloatType> radius;
  radius.allocate(np);

  Indices rorder(np);
  std::iota(rorder.begin(), rorder.end(), 0);

  // determine center
  SVector<N,FloatType> ctr;
  for (int i=0; i<np; ++i)
    ctr += pts[i];
  ctr *= FloatType(1)/np;

  // Note: parallel radius computation does not help
  for (int i=0; i<np; ++i)
    radius[i] = norm(pts[i] - ctr);

  auto rless = [&](uint a, uint b) {
    return radius[a] < radius[b];
  };
  parallel::sort(rorder.begin(), rorder.end(), rless);

  repl = Indices(np, NotFound);
  keep.clear();
  keep.reserve(np/2);

  detail::RiCmp<FloatType> rcmp(radius);
  const FloatType sqdmax = sq(threshold);
  uint count = 0;

  for (int i=0; i<np; ++i) {

    // skip if already tagged as replaced
    if (repl[i] != NotFound)
      continue;

    // otherwise, mark as kept
    repl[i] = count;
    keep.push_back(i);

    // search nodes in radius range for matches, tag them
    FloatType ri = radius[i];
    int first = std::distance( rorder.begin(),
                               std::lower_bound(rorder.begin(), rorder.end(),
                                                 ri - threshold, rcmp) );
    for (int j=first; j < np; ++j) {
      int k = rorder[j];
      FloatType rk = radius[k];
      if ( rk > (ri + threshold) )
        break;
      if (k <= i)
        continue;
      FloatType sqd = sq(pts[i] - pts[k]);
      if (sqd < sqdmax)
        repl[k] = count;
    }
    ++count;
  }
}

class RadialOrdering
{
public:

  /// initialize ordering
  template <uint N, typename FloatType>
  void sort(const PointList<N,FloatType> &pts) {
    m_order.resize( pts.size() );
    std::iota(m_order.begin(), m_order.end(), 0);

    auto cmp = [&](const uint &a, const uint &b) {
      return (sq(pts[a]) < sq(pts[b]));
    };
    std::sort(m_order.begin(), m_order.end(), cmp);
    assert(this->sorted(pts));
  }

  /// update the ordered sequence assuming new points where added to the end
  template <uint N, typename FloatType>
  void update(const PointList<N,FloatType> &pts) {
    const size_t noff = m_order.size();
    const size_t np = pts.size();
    if (np <= noff)
      return;
    auto cmp = [&](const uint &a, const uint &b) {
      return (sq(pts[a]) < sq(pts[b]));
    };
    m_order.resize(np);
    std::iota( m_order.begin()+noff, m_order.end(), noff );
    std::sort( m_order.begin()+noff, m_order.end(), cmp );
    std::inplace_merge( m_order.begin(), m_order.begin()+noff, m_order.end() );
    assert(this->sorted(pts));
  }

  /// append a new point if different from all existing ones
  template <uint N, typename FloatType>
  uint insert(PointList<N,FloatType> &pts, const SVector<N,FloatType> &pn,
              FloatType sqtol) {
    FloatType sqp = sq(pn);
    auto cmp = [&](const uint &a, FloatType rsq) {
      return (sq(pts[a]) < rsq);
    };

    Indices::iterator ip1 = std::lower_bound(m_order.begin(), m_order.end(),
                                             sqp-sqtol, cmp);
    if (ip1 == m_order.end()) {
      uint idx = pts.size();
      pts.push_back(pn);
      m_order.push_back(idx);
      assert(this->sorted(pts));
      return idx;
    } else if (ip1 != m_order.begin()) {
      --ip1;
    }

    Indices::iterator ip2 = ip1 + 1;
    while ((ip2 != m_order.end()) and (sq(pts[*ip2]) <= sqp+sqtol))
      ++ip2;

    // one of the points in (ip1,ip2] could match pn
    assert(ip2 != ip1);
    for (auto itr = ip1; itr != ip2; ++itr) {
      FloatType dsq = sq(pts[*itr] - pn);
      if (dsq < sqtol)
        return *itr;
    }

    // no, it didn't - insert point in sorted order
    uint idx = pts.size();
    pts.push_back(pn);
    ip1 = std::lower_bound(m_order.begin(), m_order.end(), sqp, cmp);
    m_order.insert(ip1, idx);
    assert(this->sorted(pts));
    return idx;
  }

  /// diagnosis : check if the current ordering holds
  template <uint N, typename FloatType>
  bool sorted(const PointList<N,FloatType> &pts) const {
    auto cmp = [&](const uint &a, const uint &b) {
      return (sq(pts[a]) < sq(pts[b]));
    };
    return std::is_sorted(m_order.begin(), m_order.end(), cmp);
  }

private:

  /// indices sorted by squared radius from origin
  Indices m_order;
};

#endif // RADIALSORT_H
