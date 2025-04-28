
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
 
#ifndef GENUA_STEPTRANSFORM_H
#define GENUA_STEPTRANSFORM_H

#include "forward.h"
#include "dmatrix.h"
#include "trigo.h"
#include "logger.h"

class ColumnBlockTask;

/** Laplace transform of response to smoothed step input.
 *
 *  This is a low-level computational class which evaluates the Laplace-domain
 *  transfer function G(s) of a signal y(t) caused by a smoothed step input
 *  of the form
 *  \f[
 *     x(t) = \frac{1}{2} ( 1 - \cos \frac{\pi t}{T} ) \; \forall t \le T \\
 *     x(t) = 1  \; \forall t > T
 *  \f]
 *
 *  by numerically evaluating the Laplace transform Y(s) of y(t) and dividing
 *  by the analytically known Laplace transform X(s) of x(t) for a prescribed
 *  set of frequencies. In order to increase robustness, Y(s) is determined by
 *  fitting a low-frequency parametrized term f(p,t) with known Laplace
 *  transform to y(t), which allows to achieve very high accuracy for the most
 *  relevant low-frequency range. Finally, the Laplace transform of the
 *  remaining high frequency error \f[ y(t) - f(t) \] is computed by numerical
 *  integration.
 *
 *
 */
class StepTransform : public Logger
{
public:

  /// empty initialization
  StepTransform() : Logger() {}

  /// base class, need virtual destruction
  virtual ~StepTransform() {}

  /// assign data to transform, return reference to results
  const CpxMatrix & transform(Real T,
                              const Vector &time, const Matrix &yt,
                              const CpxVector &s);

  /// perform transform for general signal x(t) using scaled FFTs only
  const CpxMatrix & transform(Real dt, Real df, Real fmax,
                              const Vector &xt, const Matrix &yt);

  /// access results for export
  const CpxMatrix & result() const {return m_gs;}

  /// value of the laplace variable used for row i of the result matrix
  Complex laplaceVariable(uint i) const {return m_svalue[i];}

private:

  /// evaluate e = f(t) - y for given set of parameters p
  void teval(const Real y[], const Real p[], Real e[]) const {
    const int n = m_time.size();
    Real ft, yo = y[0];
    for (int i=0; i<m_iramp; ++i) {
      Real ti = m_time[i];
      Real phi = M_PI*ti/m_tramp;
      Real sphi, cphi;
      sincosine(phi, sphi, cphi);
      ft = 0.5*p[0] *(1.0 - cphi)
         + p[1]*sphi + p[2]*cphi;
      e[i] = ft - (y[i] - yo);
    }
    for (int i=m_iramp; i<n; ++i) {
      ft = p[0];
      e[i] = ft - (y[i] - yo);
    }
  }

  /// determine coefficients for velocity term
  void speedCoefficients(const Real f[], Real p[]);

  /// compute Laplace-domain terms
  void seval(const Real p[], const Real fmy[], Complex ys[]) const;

  /// numerical Laplace transform of the error term f, for irregular time steps
  Complex laplaceTransform(Complex s, const Real f[]) const;

  /// numerical Laplace transform of the error term f, equidistant time steps
  Complex laplaceTransform(Complex s, Real dt, const Real f[]) const;

  /// preprocess vector for scaled transform, return offset
  Real shiftpad(size_t n, const Real x[], CpxVector &ps) const;

  /// scaled transform, Xs = s * FFT(x(t)), presumes FFT plan exists
  void scaledTransform(FftBase &engine, Real dt, Real df, Real xshift,
                       const CpxVector &xt, CpxVector &Xs) const;

  /// use FFT-based transform to process columns (a,b]
  void fftTransform(Real dt, Real df, const CpxVector &Xs, size_t a, size_t b);

protected:

  /// FFT implementation
  FftBasePtr m_fftengine;

  /// time steps; may be irregular in the general case
  Vector m_time;

  /// values of the Laplace variable
  CpxVector m_svalue;

  /// time domain data; rows are time steps; columns are data points
  Matrix m_yt;

  /// Laplace-domain data, row i belongs to s = m_svalue[i]
  CpxMatrix m_gs;

  /// length of the step flank/ramp
  Real m_tramp;

  /// first index where input reaches plateau
  int m_iramp;

  friend class ColumnBlockTask;
};

#endif // STEPTRANSFORM_H
