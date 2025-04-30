
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
 
#include "fftbase.h"
#include <boost/math/special_functions/bessel.hpp>

#ifdef HAVE_FFTW3
#include "fftw3interface.h"
#endif

#ifdef HAVE_MKL_PARDISO
#include "dftitransform.h"
#endif

Real FftBase::directLaplace(Real dt, Complex ft[], Complex Fs[])
{
  // determine damping constant
  const Real c = damping(dt);

  // scale ft to exploit fft
  const Complex k(-c*dt, -M_PI/m_size);
  for (size_t i=0; i<m_size; ++i)
    ft[i] *= dt*std::exp( Real(i)*k );

  // perform forward FFT on scaled array
  execute(ft, Fs);

  return c;
}

Real FftBase::inverseLaplace(Real dt, Complex Fs[], Complex ft[])
{
  const Real T = m_size*dt;
  const Real dw = 2*M_PI*(1.0/T);
  const Real c = damping(dt);
  const Real wtrunc = 2*M_PI/dt;

  // scale with Blackman window function
  for (size_t i=0; i<m_size; ++i) {
    Real phi = i*dw*M_PI/wtrunc;
    Fs[i] *= 0.42 + 0.5*std::cos(phi) + 0.08*std::cos(2*phi);
  }

  // perform inverse FFT
  execute(Fs, ft);

  // scale output
  const Real k1 = 2.0 / T;
  const Complex k2(c*dt, M_PI/m_size);
  for (size_t i=0; i<m_size; ++i)
    ft[i] *= k1*std::exp(k2*Real(i));

  return c;
}

FftBasePtr FftBase::create()
{
#ifdef HAVE_FFTW3
  return boost::make_shared<Fftw3Transform>();
#else
  return FftBasePtr();
#endif
}

inline static Real Io(Real x) {
  return boost::math::cyl_bessel_i(0,x);
}

void FftBase::computeWindow(FftBase::WindowFunction wf, Real w[]) const
{
  const size_t N = m_size;
  Real dphi = M_PI/N;
  Real api, b, c;
  const Real a[] = {0.21557895, -0.41663158, 0.277263158,
                    -0.083578947, 0.006947368};

  if (wf == Kaiser4)
    api = 4.0;
  else if (wf == Kaiser9)
    api = 9.0;

  switch (wf) {
  case Boxcar:
    CPHINT_SIMD_LOOP
    for (size_t i=0; i<N; ++i)
      w[i] = 1.0;
    break;
  case Hann:
    CPHINT_SIMD_LOOP
    for (size_t i=0; i<N; ++i)
      w[i] = sq(std::sin(i*dphi));
    break;
  case FlatTop:
    CPHINT_SIMD_LOOP
    for (size_t i=0; i<N; ++i) {
      Real phi = M_PI*i/(N-1);
      w[i] = a[0];
      for (int j=1; j<=4; ++j)
        w[i] += a[j]*std::cos(2*j*phi);
    }
    break;
  case Kaiser4:
  case Kaiser9:
    b = 1.0 / Io(api);
    c = 2.0/N;
    CPHINT_SIMD_LOOP
    for (size_t i=0; i<N; ++i) {
      w[i] = b*Io( api* std::sqrt(1 - sq(c*i - 1)) );
    }
    break;
  }
}

void FftBase::windowScaling(const Real w[], Real &S1, Real &S2) const
{
  S1 = S2 = 0;
  for (size_t i=0; i<m_size; ++i) {
    S1 += w[i];
    S2 += sq(w[i]);
  }
}

Real FftBase::periodogram(Real fs, const Complex in[], Real psd[],
                          FftBase::WindowFunction wf, FftBase::Scaling scl)
{
  // construct window
  if (m_wfun != wf or m_psdwindow.size() != m_size) {
    m_psdwindow.allocate(m_size);
    computeWindow(wf, m_psdwindow.pointer());
    m_wfun = wf;
  }

  Real S1, S2;
  windowScaling(m_psdwindow.pointer(), S1, S2);

  // detrending - remove DC
  Complex xmean(0);
  CPHINT_SIMD_LOOP
  for (size_t i=0; i<m_size; ++i)
    xmean += in[i];
  xmean /= m_size;

  m_psdwork.allocate(m_size);
  CPHINT_SIMD_LOOP
  for (size_t i=0; i<m_size; ++i)
    m_psdwork[i] = (in[i] - xmean) * m_psdwindow[i];

  this->execute(m_psdwork.pointer(), m_psdwork.pointer());

  Real S;
  if (scl == PowerDensity) {
    S = 2.0 / (fs * S2);
  } else {
    S = 2.0 / sq(S1);
  }

  for (size_t i=0; i<m_size/2; ++i) {
    psd[i] = S *  (m_psdwork[i] * std::conj(m_psdwork[i])).real();
  }

  return fs/m_size;
}
