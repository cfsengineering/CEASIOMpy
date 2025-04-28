
/* Copyright (C) 2019 David Eller <david@larosterna.com>
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

#ifndef GENUA_GRULAYER_H
#define GENUA_GRULAYER_H

#include "forward.h"
#include "dmatrix.h"

/** Gated Recurrent Unit.
 *
 *
 *
 * \ingroup experimental
 */
class GRULayer
{
public:

  /// allocate storage
  void allocate(size_t nx, size_t nh);

  /// evaluate, return reference to updated internal (hidden) state
  const DVector<float> &forward(const DVector<float> &x);

private:

  /// input size
  size_t m_nx;

  /// number of internal states h
  size_t m_nh;

  /// weight matrix, size 3*nh by nx/nh, row order rt, zt, nt
  DMatrix<float> m_wx, m_wh;

  /// bias vectors, size 3*nh, order is rt, zt, nt
  DVector<float> m_bx, m_bh;

  /// work array h-gates and x-gates
  DVector<float> m_hg, m_xg;

  /// internal state from previous step
  DVector<float> m_h;
};

#endif // GRULAYER_H
