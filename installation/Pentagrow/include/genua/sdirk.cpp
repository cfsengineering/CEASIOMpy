
/* Copyright (C) 2018 David Eller <david@larosterna.com>
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

#include "sdirk.h"

#include <iostream>

using namespace std;

OwrenSimonsen22::OwrenSimonsen22() : SdirkBase<2>()
{
  m_gamma = 1.0 - 0.5 * sqrt(2.0);
  m_order = 2.0;

  m_a(0, 0) = m_a(1, 1) = m_gamma;
  m_a(1, 0) = 1.0 - m_gamma;

  // no embedded rule, must use Richardson for adaptive stepping
  m_estage = 0;

  initOwrenSimonsen();
}

OwrenSimonsen23::OwrenSimonsen23(Real gamma) : SdirkBase<3>()
{
  m_gamma = gamma;
  m_order = 2.0;

  const Real t1 = sq(m_gamma) - 2 * m_gamma + 0.5;
  const Real t2 = cb(m_gamma) - 3 * sq(m_gamma) + 2 * m_gamma - 1. / 3.;
  const Real sigma = t2 / t1;

  const Real b0 = 1 - m_gamma - t1 / sigma;
  const Real b1 = t1 / sigma;

  m_a(0, 0) = m_a(1, 1) = m_a(2, 2) = m_gamma;
  m_a(1, 0) = sigma;
  m_a(2, 0) = b0;
  m_a(2, 1) = b1;

  m_estage = 2;
  m_bhat[0] = (2 * sigma - (1 - 2 * gamma)) / (2 * sigma);
  m_bhat[1] = (1 - 2 * gamma) / (2 * sigma);

  initOwrenSimonsen();
}

OwrenSimonsen34::OwrenSimonsen34(Real gamma) : SdirkBase<4>()
{
  m_gamma = gamma;
  m_order = 3.0;

  Real g2 = sq(m_gamma);
  Real g3 = cb(m_gamma);
  Real g4 = sq(g2);
  Real t1 = 1. / 6. - 1.5 * m_gamma + 3 * g2 - g3;
  Real sigma = (1. / 12. - m_gamma + 3.5 * g2 - 4 * g3 + g4) / t1;
  Real phi = (0.125 - 4. / 3. * m_gamma + 4 * g2 - 4 * g3 + g4) / t1;
  Real t2 = sigma * (g3 + (sigma - 3) * g2 + (2 - 2 * sigma) * m_gamma -
                     1. / 3. + 0.5 * sigma);
  Real nu = t1 * phi * (sigma - phi) / t2;
  Real mu = phi - nu;

  Real b0, b1, b2;
  b0 = ((1 - m_gamma) * sigma * phi - sigma * (0.5 - 2 * m_gamma + g2) + 1. / 3. - 2 * m_gamma + 3 * g2 - g3 - (0.5 - 2 * m_gamma + g2) * phi) / (sigma * phi);
  b1 = (1. / 3. - 2 * m_gamma + 3 * g2 - g3 - (.5 - 2 * m_gamma + g2) * phi) / (sigma * (sigma - phi));
  b2 = -(1. / 3. - 2 * m_gamma + 3 * g2 - g3 - sigma * (0.5 - 2 * m_gamma + g2)) / (phi * (sigma - phi));

  m_a(0, 0) = m_a(1, 1) = m_a(2, 2) = m_a(3, 3) = m_gamma;
  m_a(1, 0) = sigma;
  m_a(2, 0) = mu;
  m_a(2, 1) = nu;
  m_a(3, 0) = b0;
  m_a(3, 1) = b1;
  m_a(3, 2) = b2;

  m_estage = 2;
  m_bhat[0] = (2 * sigma - (1 - 2 * gamma)) / (2 * sigma);
  m_bhat[1] = (1 - 2 * gamma) / (2 * sigma);

  initOwrenSimonsen();
}

// --------------- Interfaces ------------------------------------------------

void StdSecondOrderSystem::aSolve(Real hg, Real t, const Vector &u,
                                  const Vector &v, Vector &a)
{
  // assemble and factor whenever hg changed
  if (hg != m_hglast)
  {
    m_rhs.allocate(u.size());
    m_T.allocate(m_M.nrows(), m_M.ncols());
    if (m_C.nrows() == m_M.nrows())
      m_T.mmap() = m_M.cmap() + hg * m_C.cmap() + sq(hg) * m_K.cmap();
    else
      m_T.mmap() = m_M.cmap() + sq(hg) * m_K.cmap();
    m_llt.compute(m_T.cmap().selfadjointView<eeigen::Lower>());
    // m_llt.compute(m_T.cmap());
    assert(m_llt.info() == eeigen::Success);
    m_hglast = hg;

    // debug
    // cout << "RCOND: " << m_llt.rcond() << endl;
  }

  m_rhs = 0.0;
  this->force(t, u, v, m_rhs);
  if (m_C.nrows() > 0)
    m_rhs.mmap() -= m_C.cmap() * v.cmap();
  m_rhs.mmap() -= m_K.cmap() * u.cmap();

  a.allocate(u.size());
  a.mmap() = m_llt.solve(m_rhs.cmap());
  assert(m_llt.info() == eeigen::Success);
}
