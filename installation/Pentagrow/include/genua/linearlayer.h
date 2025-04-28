
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

#ifndef GENUA_LINEARLAYER_H
#define GENUA_LINEARLAYER_H

#include "forward.h"
#include "dmatrix.h"

/** Linear NN layer.
 *
 *  Primitive linear layer (usually the last), applies
 *  \f[
 *  y = A x + b
 *  \f]
 *
 * \ingroup experimental
 */
class LinearLayer
{
public:

  /// make space
  void allocate(size_t nx, size_t ny);

  /// compute forward pass, return reference to output
  const DVector<float> &forward(const DVector<float> &x);

private:

  /// weight matrix A, size ny-by-nx
  DMatrix<float> m_wgt;

  /// bias vector, length nout
  DVector<float> m_bias;

  /// storage for output
  DVector<float> m_y;
};

#endif // LINEARLAYER_H
