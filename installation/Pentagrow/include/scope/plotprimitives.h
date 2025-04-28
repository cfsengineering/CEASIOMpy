
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
 
#ifndef SCOPE_PLOTPRIMITIVES_H
#define SCOPE_PLOTPRIMITIVES_H

#include "forward.h"
#include <genua/defines.h>
#include <genua/parallel_algo.h>

/** Intermediate object used for plotting.
 *
 * \sa SectionPlotter
 */
struct PlotTriangle
{
public:

  /// undefined triangle
  PlotTriangle() {}

  /// initialize
  PlotTriangle(uint idx, const uint vlm[]) : eix(idx)
  {
    assign(vlm[0], vlm[1], vlm[2]);
  }

  /// initialize
  PlotTriangle(uint idx, const uint vlm[], const int map[]) : eix(idx)
  {
    assign(vlm[map[0]], vlm[map[1]], vlm[map[2]]);
  }

  /// initialize
  void assign(uint a, uint b, uint c) {
    if (a < b and a < c) {
      vix[0] = a;
      vix[1] = b;
      vix[2] = c;
    } else if (b < a and b < c) {
      vix[0] = b;
      vix[1] = c;
      vix[2] = a;
    } else {
      vix[0] = c;
      vix[1] = a;
      vix[2] = b;
    }
  }

  /// optionally, sort indices (drops directional information)
  void sort() {
    // 0 is aleady the smallest index after assign()
    if (vix[1] > vix[2])
      std::swap(vix[1], vix[2]);
  }

  /// sorting criterion
  bool operator< (const PlotTriangle & a) const {
    if (vix[0] < a.vix[0])
      return true;
    else if (vix[0] > a.vix[0])
      return false;
    else if (vix[1] < a.vix[1])
      return true;
    else if (vix[1] > a.vix[1])
      return false;
    else
      return (vix[2] < a.vix[2]);
  }

  /// equivalence
  bool operator== (const PlotTriangle & a) const {
    if (vix[0] != a.vix[0])
      return false;
    else if (vix[1] != a.vix[1])
      return false;
    else if (vix[2] != a.vix[2])
      return false;
    else
      return true;
  }

  /// difference
  bool operator!= (const PlotTriangle & a) const {
    return !(*this == a);
  }

  /// comparison operator using element index
  struct IndexLess {
    bool operator() (const PlotTriangle &a, const PlotTriangle &b) const {
      return (a.eix < b.eix);
    }
  };

public:

  /// vertex indices
  uint vix[3];

  /// generated from element with local index eix
  uint eix;
};

/** Intermediate object used for plotting.
 *
 * \sa SectionPlotter
 */
struct PlotEdge
{
public:

  /// undefined edge
  PlotEdge() {}

  /// initialize
  PlotEdge(uint idx, const uint vlm[]) : eix(idx)
  {
    assign(vlm[0], vlm[1]);
  }

  /// initialize
  PlotEdge(uint idx, const uint vlm[], const int map[]) : eix(idx)
  {
    assign(vlm[map[0]], vlm[map[1]]);
  }

  /// initialize
  void assign(uint a, uint b) {
    src = std::min(a, b);
    trg = std::max(a, b);
  }

  /// define ordering
  bool operator< (const PlotEdge & a) const {
    if (src < a.src)
      return true;
    else if (src > a.src)
      return false;
    else
      return trg < a.trg;
  }

  /// define equality
  bool operator== (const PlotEdge & a) const {
    return ((src == a.src) and (trg == a.trg));
  }

  /// comparison operator using element index
  struct IndexLess {
    bool operator() (const PlotEdge &a, const PlotEdge &b) const {
      return (a.eix < b.eix);
    }
  };

public:

  /// vertex indices
  uint src, trg;

  /// generated from element with index eix
  uint eix;
};

template <class Primitive>
inline uint sort_primitives(std::vector<Primitive> &ptri)
{
  if (ptri.size() > 8192)
    parallel::sort(ptri.begin(), ptri.end());
  else
    std::sort(ptri.begin(), ptri.end());
  typename std::vector<Primitive>::iterator last;
  last = std::unique(ptri.begin(), ptri.end());
  ptri.erase(last, ptri.end());

  typename Primitive::IndexLess cmp;
  if (ptri.size() > 8192)
    parallel::sort(ptri.begin(), ptri.end(), cmp);
  else
    std::sort(ptri.begin(), ptri.end(), cmp);
  return ptri.size();
}

#endif // PLOTPRIMITIVES_H
