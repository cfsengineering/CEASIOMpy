
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
 #ifndef GENUA_FFTBASE_H
#define GENUA_FFTBASE_H

#include "forward.h"
#include "dvector.h"

/** Base class for FFT library interfaces.
 *
 *  The purpose of this class is to hide an underlying FFT implementation
 *  behind a common interface.
 *
 *  TODO: Switch primitive Laplace transform implementation to Talbot's
 *        method or Wiedeman's.
 *
 *
 * \ingroup numerics
 * \sa Fftw3Transform, DftiTransform
 */
class FftBase
{
public:

  enum WindowFunction { Boxcar, Hann, FlatTop, Kaiser4, Kaiser9 };

  enum Scaling {PowerDensity, PowerSpectrum};

  /// initialize
  FftBase() : m_size(0) {}

  /// virtual destructor
  virtual ~FftBase() {}

  /// create a plan for size n and with library-dependent flags
  virtual void plan(size_t n, bool forward=true, int flags = 0) = 0;

  /// length for which the transform was planned
  size_t length() const {return m_size;}

  /// perform FFT on in, write to out
  virtual void execute(const Complex in[], Complex out[]) = 0;

  /// numerical Laplace transform build using forward fft (unreliable)
  virtual Real directLaplace(Real dt, Complex ft[], Complex Fs[]);

  /// inverse numerical Laplace transform (unreliable)
  virtual Real inverseLaplace(Real dt, Complex Fs[], Complex ft[]);

  /// instantiate the best available FFT implementation
  static FftBasePtr create();

  /// determine window function coefficients
  void computeWindow(WindowFunction wf, Real w[]) const;

  /// compute scaling factors S1, S2 for a windowing function
  void windowScaling(const Real w[], Real &S1, Real &S2) const;

  /// compute a periodogram, return frequency resolution
  Real periodogram(Real fs, const Complex in[], Real psd[],
                   WindowFunction wf=Boxcar, Scaling scl=PowerDensity);

protected:

  /// compute damping constant for numerical Laplace transform
  Real damping(Real dt) const {
    //return 4*M_PI/(m_size*dt);
    return std::log(sq(Real(m_size))) / (m_size*dt);
  }

protected:

  /// number of elements in 'm_in', out; passed to plan()
  size_t m_size;

  /// work array for periodogram
  DVector<Complex> m_psdwork;

  /// window function used by periodogram
  DVector<Real> m_psdwindow;

  /// window function stored
  WindowFunction m_wfun;
};

#endif // FFTBASE_H
