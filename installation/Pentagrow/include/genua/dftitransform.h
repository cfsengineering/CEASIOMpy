
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
 
#ifndef DFTITRANSFORM_H
#define DFTITRANSFORM_H

#include "fftbase.h"
#include <mkl_dfti.h>

/** Interface to FFT interface in MKL.
 *
 * When the Math Kernel Library is available, this class provides an interface
 * to the 1-D FFT transform contained there. This may then be an alternative to
 * the FFTW3 interface when the GPL license is not acceptable.
 *
 *
 * \ingroup numerics
 * \sa FftBase
 */
class DftiTransform : public FftBase
{
public:

  enum ConfigFlags { Multithreaded = 1 };

  /// create empty transform without a plan
  DftiTransform() : m_work(0) {}

  /// deallocate
  ~DftiTransform();

  /// prepare a plan for execution
  void plan(size_t n, bool forward=true, int flags=0);

  /// perform 1D transform
  void execute(const Complex in[], Complex out[]);

private:

  /// free resources
  void destroy();

  /// handle error message from MKL
  void check(int status);

private:

  /// local workspace
  MKL_Complex16 *m_work;

  /// plan
  DFTI_DESCRIPTOR_HANDLE m_handle;

  /// forward or backward transform?
  bool m_forward;
};

#endif // DFTITRANSFORM_H
