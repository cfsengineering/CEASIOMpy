
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
 
#ifndef GENUA_FFTW3INTERFACE_H
#define GENUA_FFTW3INTERFACE_H

#include "fftbase.h"
#include <fftw3.h>
#include <cstring>

/** C++ Interface for FFTW3

    This class implements the interface of FftBase and links against the
    FFTW3 implementation. Hence, this interface is only available if FFTW3
    is detected by the qmake run.

    Note that the use of FFTW3 implies GPL license unless you have obtained
    another license for that library.

    \ingroup numerics
    \sa FftBase, DftiTransform
  */
class Fftw3Transform : public FftBase
{
public:

  /// initialize
  Fftw3Transform() : m_in(0), m_out(0) {}

  /// destruct
  ~Fftw3Transform() { destroy(); }

  /// create a plan - this call is not thread-safe!
  void plan(size_t n, bool forward=true, int flags = 0);

  /// perform FFT according to plan - thread-safe.
  void execute(const Complex in[], Complex out[]);

private:

  /// deallocate, destroy plan
  void destroy();

private:

  /// the plan
  fftw_plan m_plan;

  /// work arrays for the library
  fftw_complex *m_in, *m_out;
};


#endif // FFTW3INTERFACE_H
