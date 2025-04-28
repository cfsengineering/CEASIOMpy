
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
 
#include "steptransform.h"
#include "svector.h"
#include "xcept.h"
#include "parallel_loop.h"
#include "timing.h"
#include "smallqr.h"
#include "smatrix.h"
#include "fftbase.h"
#include "dbprint.h"
#include "ioglue.h"
#include "parallel_loop.h"

const CpxMatrix &StepTransform::transform(Real T, const Vector &time,
                                          const Matrix &yt, const CpxVector &s)
{
  m_time = time;
  m_yt = yt;
  m_svalue = s;
  m_tramp = T;
  m_gs.resize(m_svalue.size(), m_yt.ncols());

  m_iramp = std::distance(m_time.begin(),
                          std::lower_bound(m_time.begin(), m_time.end(), T) );

  if (size_t(m_iramp) >= m_time.size())
    throw Error("StepTransform: End of ramp not inside simulation time.");

  const int n = m_time.size();

  // start timer and progress indicator
  Wallclock clk;
  clk.start();
  log("[i] Transforming", m_yt.ncols(), "step response columns.");
  Logger::nextStage(n);

  BEGIN_PARLOOP_CHUNK(0, int(m_yt.ncols()), 512)
  for (int jcol=a; jcol<b; ++jcol) {

    // indicate progress, spin through the rest if interrupt flag set
    Logger::increment();

    const Real *y = m_yt.colpointer(jcol);

    // parameter set, initialize with zero
    SVector<3> p;
    Vector et(n);

    // first pass : step contribution only
    p[0] = y[n-1] - y[0];
    teval(y, p.pointer(), et.pointer());

    speedCoefficients(et.pointer(), &p[1]);
    teval(y, p.pointer(), et.pointer());

    // evaluate Laplace-domain result
    seval(p.pointer(),et.pointer(), m_gs.colpointer(jcol));

  }
  END_PARLOOP

      clk.stop();
  log("[t] Completed: ", clk.elapsed());

  return m_gs;
}

void StepTransform::speedCoefficients(const Real f[], Real p[])
{
  // number of evaluation points
  const int M(8);
  SMatrix<M,2> A;
  SVector<M> b;

  Real omega = M_PI / m_tramp;
  for (int i=0; i<M; ++i) {
    size_t ik = (m_iramp/M)*i;
    b[i] = f[ik];
    sincosine( m_time[ik]*omega, A(i,0), A(i,1) );
  }
  qrlls<M,2>( A.pointer(), b.pointer() );

  p[0] = - b[0];
  p[1] = - b[1];
}

void StepTransform::seval(const Real p[], const Real fmy[], Complex ys[]) const
{
  const size_t m = m_svalue.size();
  const Real T = m_tramp;
  const Real a = M_PI / T;
  const Real dt = m_time[1] - m_time[0];
  // Real sbeta, cbeta;
  // sincosine(p[2], sbeta, cbeta);
  for (size_t i=0; i<m; ++i) {
    Complex s = m_svalue[i];
    if (s != 0.0) {

      Complex et1 = (1.0 - std::exp(-T*s));              // switch off at T
      Complex et2 = 1.0 / (sq(s) + sq(a));               // cosine denom.

      // unit smoothed step
      Complex xu = 0.5*et1*(1.0/s - s*et2) + std::exp(-T*s)/s;

      // evaluate low-frequency model function and add numerical laplace
      // transform of the high-frequency error term which is known to be
      // zero beyond the simulated interval, at least if parameters were
      // chosen properly.
      Complex yi;
      yi = p[0] * xu
           // + p[1] * et1 * (a*sbeta + s*cbeta) * et2
           + et1 * ( a*p[1] + s*p[2] ) * et2
          - laplaceTransform(s, dt, fmy);
      ys[i] = yi / xu;
    } else {
      // limit value of low-frequency contribution
      ys[i] = p[0];
    }
  }
}

Complex StepTransform::laplaceTransform(Complex s, const Real f[]) const
{
  const size_t n = m_time.size();
  Complex F(0.0);
  // TODO : vectorize, call to exp(Complex) -> exp(real) * sincos(Real,Real)
  for (size_t i=1; i<n; ++i) {
    Real fmid = 0.5*( f[i] + f[i-1] );
    Real dt = m_time[i] - m_time[i-1];
    Real tmid = 0.5*(m_time[i] + m_time[i-1]);
    F += fmid * dt * std::exp(-tmid*s);
  }
  return F;
}

Complex StepTransform::laplaceTransform(Complex s, Real dt,
                                        const Real f[]) const
{
  const size_t n = m_time.size();

  // constants
  Real sdphi, cdphi;
  sincosine( s.imag()*dt, sdphi, cdphi );
  const Real edt = std::exp( -s.real()*dt );

  // accumulators
  Complex F(0.0);
  Real sphi(0.0), cphi(1.0), expt(1.0);
  Real fprev(f[0]);
  for (size_t i=1; i<n; ++i) {

    // segment contribution, 0.5*dt pulled out of loop
    Real fi = f[i];
    Real fet = (fi + fprev)*expt;
    F += Complex( fet*sphi, fet*cphi );
    fprev = fi;

    // update trigonometric terms
    expt *= edt;
    Real tmp = sphi*cdphi + cphi*sdphi;
    cphi = cphi*cdphi - sphi*sdphi;
    sphi = tmp;
  }

  return 0.5*F*dt;
}

class ColumnBlockTask
{
public:
    ColumnBlockTask(StepTransform &st, const CpxVector &xs, Real dt, Real df)
      : m_trafo(st), m_xs(xs), m_dt(dt), m_df(df) {}
    void operator() (int a, int b) {
      m_trafo.fftTransform(m_dt, m_df, m_xs, a, b);
    }
private:
    StepTransform &m_trafo;
    const CpxVector &m_xs;
    Real m_dt, m_df;
};

const CpxMatrix & StepTransform::transform(Real dt, Real df, Real fmax,
                                           const Vector &xt, const Matrix &yt)
{
  // this is only possible if an FFT implementation is available
  m_fftengine = FftBase::create();
  if (m_fftengine == nullptr)
    throw Error("StepTransform requires an FFT implementation such as FFTW3.");

  // number of time points needed in order to achieve required
  // frequency step df
  Real tend = 1.0 / df;
  size_t nt = tend/dt;
  if (nt*dt < tend)
    ++nt;

  m_fftengine->plan(nt, true);

  // actual frequency step achieved
  df = 1.0 / (nt*dt);

  // Laplace variables
  int nf = fmax/df;
  if (nf*df < fmax)
    ++nf;
  m_svalue.resize(nf);
  for (int i=0; i<nf; ++i)
    m_svalue[i] = Complex(0.0, i*df*2*M_PI);

  m_yt = yt;
  m_gs.resize(nf, m_yt.ncols());

  // start timer and progress indicator
  Wallclock clk;
  clk.start();
  log("[i] Transforming", m_yt.ncols(), "step response columns.");
  Logger::nextStage(m_yt.ncols());

  // compute scaled transform of input signal
  CpxVector Xin(nt), Xs(nt);
  Real xshift = shiftpad(xt.size(), xt.pointer(), Xin);
  scaledTransform(*m_fftengine, dt, df, xshift, Xin, Xs);

  // process columns
  const int ncol = m_yt.ncols();
  fftTransform(dt, df, Xs, 0, ncol);

  // FIXME:
  // to parallelize, fftengine must allow concurrent access; it does not
  // allow that right now; therefore, each thread needs it's own engine

  // parallel::block_loop_r(0, ncol, 512,
  //                        [&](int a, int b) {fftTransform(dt,df,Xs,a,b);});

//  ColumnBlockTask task(*this, Xs, dt, df);
//  parallel::block_loop(task, 0, ncol, 512);

  clk.stop();
  log("[t] Completed: ", clk.elapsed());

  return m_gs;
}

Real StepTransform::shiftpad(size_t n, const Real x[], CpxVector &ps) const
{
  Real shift = x[n-1];

  const size_t n1 = std::min(n, ps.size());
  for (size_t i=0; i<n1; ++i)
    ps[i] = Complex(x[i] - shift, 0.0);

  const size_t n2 = ps.size();
  for (size_t i=n1; i<n2; ++i)
    ps[i] = Complex(0.0, 0.0);

  return shift;
}

void StepTransform::scaledTransform(FftBase &engine,
                                    Real dt, Real df, Real xshift,
                                    const CpxVector &xt, CpxVector &Xs) const
{
  assert(engine.length() == xt.size());
  assert(xt.size() == Xs.size());

  const Real scale = dt*2.0*M_PI*df;
  const size_t n = xt.size();
  engine.execute( xt.pointer(), Xs.pointer() );
  for (size_t i=0; i<n; ++i) {
    Xs[i] *= Complex(0.0, i * scale);
    Xs[i] += Complex(xshift, 0.0);
  }
}

void StepTransform::fftTransform(Real dt, Real df,
                                 const CpxVector &Xs, size_t a, size_t b)
{
  const size_t nf = m_svalue.size();
  const size_t nt = Xs.size();
  CpxVector ypad(nt), Ys(nt);

  // TODO: Tell engine we'll execute (b-a) transforms in this sub-task
  FftBasePtr pengine = FftBase::create();
  assert(pengine != nullptr);
  pengine->plan(nt, true);

  for (size_t jcol=a; jcol<b; ++jcol) {

    // indicate progress
    Logger::increment();

    // shift, pad, transform and scale
    Real yshift = shiftpad(m_yt.nrows(), m_yt.colpointer(jcol), ypad);
    scaledTransform(*pengine, dt, df, yshift, ypad, Ys);

    // transfer function G(s) = Y(s) / X(s)
    for (size_t i=0; i<nf; ++i)
      m_gs(i, jcol) = Ys[i] / Xs[i];
  }
}
