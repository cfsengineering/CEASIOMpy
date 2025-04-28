
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
 
#include "fftw3interface.h"

void Fftw3Transform::plan(size_t n, bool forward, int flags)
{
  if (n == 0)
    return;
  int dir = forward ? FFTW_FORWARD : FFTW_BACKWARD;
  if (n == m_size) {
    m_plan = fftw_plan_dft_1d(m_size, m_in, m_out, dir, flags);
  } else {
    destroy();
    m_size = n;
    m_in = (fftw_complex*) fftw_malloc( n*sizeof(Complex) );
    m_out = (fftw_complex*) fftw_malloc( n*sizeof(Complex) );
    m_plan = fftw_plan_dft_1d(m_size, m_in, m_out, dir, flags);
  }
}

void Fftw3Transform::execute(const Complex in[], Complex out[])
{
  size_t bytes = m_size*sizeof(Complex);
  memcpy(m_in, in, bytes);
  fftw_execute(m_plan);
  memcpy(out, m_out, bytes);
}

void Fftw3Transform::destroy()
{
  if (m_size > 0) {
    fftw_destroy_plan(m_plan);
    fftw_free(m_in);
    fftw_free(m_out);
    m_size = 0;
  }
}
