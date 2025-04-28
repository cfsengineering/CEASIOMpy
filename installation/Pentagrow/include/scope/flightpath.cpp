
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
 
#include "flightpath.h"
#include "tdlspec.h"
#include <genua/xcept.h>
#include <genua/pattern.h>
#include <genua/lu.h>
#include <genua/atmosphere.h>
#include <sstream>

#include <iostream>
using namespace std;

void FlightPath::eval(Real t, Vector &x) const
{
  const int nstate = m_cpx.ncols();
  x.resize( nstate );

  Vct4 b;
  Real to = m_iptime.front();
  Real tn = m_iptime.back();
  Real s = (t - to) / (tn - to);
  if (s > 1)
    s -= int(s);
  int span = m_spl.eval(s, b) - 3;
  for (int j=0; j<nstate; ++j) {
    x[j] = 0.0;
    for (int i=0; i<4; ++i)
      x[j] += b[i] * m_cpx(span+i,j);
  }
}

void FlightPath::eval(Real t, Vector &x, Vector &dx, Vector &ddx) const
{
  const int nstate = m_cpx.ncols();
  x.resize( nstate );
  dx.resize( nstate );
  ddx.resize( nstate );

  SMatrix<3,4> b;
  Real to = m_iptime.front();
  Real tn = m_iptime.back();
  Real idt = 1.0 / (tn - to);
  Real iddt = sq(idt);
  Real s = (t - to) / (tn - to);
  if (s > 1)
    s -= int(s);
  int span = m_spl.derive(s, b) - 3;
  for (int j=0; j<nstate; ++j) {
    x[j] = dx[j] = ddx[j] = 0.0;
    for (int i=0; i<4; ++i) {
      x[j] += b(0,i) * m_cpx(span+i,j);
      dx[j] += b(1,i) * m_cpx(span+i,j);
      ddx[j] += b(2,i) * m_cpx(span+i,j);
    }
    dx[j] *= idt;
    ddx[j] *= iddt;
  }
}

void FlightPath::eval(const Vector &t, const Indices &map,
                      Matrix &xt, Matrix &dxt, Matrix &ddxt) const
{
  const int nt = t.size();
  const int nx = map.size();
  const int nstate = m_cpx.ncols();
  xt.resize(nt,nx);
  dxt.resize(nt,nx);
  ddxt.resize(nt,nx);

#pragma omp parallel
  {
    Vector x(nstate), dx(nstate), ddx(nstate);

#pragma omp for
    for (int i=0; i<nt; ++i) {
      eval(t[i], x, dx, ddx);
      for (int j=0; j<nx; ++j) {
        xt(i,j) = x[map[j]];
        dxt(i,j) = dx[map[j]];
        ddxt(i,j) = ddx[map[j]];
      }
    }
  }
}

void FlightPath::toAlpha(const TdlSpec &tspec, const Vector &x, Vector &mab) const
{
  assert(x.size() >= 12);
  assert(mab.size() >= 6);

  Real alt = m_altini + x[2];
  Real b = tspec.refSpan;
  Real c = tspec.refChord;
  Atmosphere atm(alt);

  Real u = x[6];
  Real v = x[7];
  Real w = x[8];
  Real va = sqrt(sq(u) + sq(v) + sq(w));
  mab[0] = va / atm.Aoo;
  mab[1] = atan2( -w, -u ) - tspec.refAlpha;
  mab[2] = asin( v/va );
  mab[3] = 0.5*b*x[9]/va; // phat = b*p/2*uo
  mab[4] = 0.5*c*x[10]/va; // qhat = c*q/2*uo
  mab[5] = 0.5*b*x[11]/va; // rhat = b*r/2*uo
}

Real FlightPath::dynamicPressure(const Vector &x) const
{
  assert(x.size() >= 12);
  Real alt = m_altini + x[2];
  Atmosphere atm(alt);

  Real u = x[6];
  Real v = x[7];
  Real w = x[8];
  Real vsq = sq(u) + sq(v) + sq(w);
  return 0.5*vsq*atm.Rho;
}

void FlightPath::resampledTime(int nt, Vector &rst,
                               uint nSmooth, Real wSmooth) const
{
  rst.resize(nt);
  interpolate_pattern(m_iptime, nt, rst);

  // smooth time step distance a little, since plain resampling
  // often ends up fairly irregular
  for (uint j=0; j<nSmooth; ++j) {
    for (int i=1; i<nt-1; ++i)
      rst[i] = (1.0-wSmooth)*rst[i] + 0.5*wSmooth*(rst[i-1] + rst[i+1]);
  }
}

void FlightPath::initSpec(TdlSpec &tspec) const
{
  const int nelast = m_jcelast.size();
  const int naerc = m_jcaerc.size();
  const uint nstates = 5 + nelast + naerc;
  tspec.clear();
  tspec.states.resize(nstates);

  for (int i=0; i<5; ++i)
    tspec.states[i].flag = TdlState::RigidBody;
  for (int i=0; i<nelast; ++i) {
    tspec.states[5+i].flag = TdlState::Elastic;
    tspec.states[5+i].modeindex = i;
  }
  for (int i=0; i<naerc; ++i) {
    tspec.states[5+nelast+i].flag = TdlState::AerodynControl;
    tspec.states[5+nelast+i].ctrlindex = i;
  }
}

void FlightPath::extractSpec(const Vector &ipolTime, TdlSpec &tspec) const
{
  // allocate all states to generate
  const uint nstates = 5 + m_jcelast.size() + m_jcaerc.size();
  if (tspec.states.size() != nstates)
    initSpec(tspec);
  tspec.time = ipolTime;
  const int nt = ipolTime.size();
  tspec.qoo.resize(nt);

  // first, extract rigid-body states; always the first 12 states
  Indices rbmap(12);
  for (int i=0; i<12; ++i)
    rbmap[i] = i;

  Matrix x, dx, ddx;
  eval(ipolTime, rbmap, x, dx, ddx);
  for (int i=0; i<5; ++i) {
    TdlState & s( tspec.states[i] );
    s.flag = TdlState::RigidBody;
    s.xi.resize( nt );
    s.dxi.clear();
    s.ddxi.clear();
  }

  // convert to alpha, beta, p, q, r
  // mach number ignored for now
  Vector xrb(12), mab(6);
  for (int i=0; i<nt; ++i) {
    for (int j=0; j<12; ++j)
      xrb[j] = x(i,j);
    tspec.qoo[i] = dynamicPressure(xrb);
    toAlpha(tspec, xrb, mab);
    for (int j=0; j<5; ++j)
      tspec.states[j].xi[i] = mab[j+1];

    // debug
    cout << ipolTime[i] << " alpha = " << deg(tspec.states[0].xi[i]) << " deg" << endl;
  }

  // process elastic states
  const int nelast = m_jcelast.size();
  eval(ipolTime, m_jcelast, x, dx, ddx);
  for (int i=0; i<nelast; ++i) {
    TdlState & s( tspec.states[5+i] );
    s.flag = TdlState::Elastic;
    s.xi = Vector( x.colpointer(i), nt );
    s.dxi = Vector( dx.colpointer(i), nt );
    s.ddxi = Vector( ddx.colpointer(i), nt );
  }

  // process aerodynamic control states
  const int ncontrol = m_jcaerc.size();
  eval(ipolTime, m_jcaerc, x, dx, ddx);
  for (int i=0; i<ncontrol; ++i) {
    TdlState & s( tspec.states[5+nelast+i] );
    s.flag = TdlState::AerodynControl;
    s.xi = Vector( x.colpointer(i), nt );
    s.dxi = Vector( dx.colpointer(i), nt );
    s.ddxi = Vector( ddx.colpointer(i), nt );
  }
}

void FlightPath::fromXml(const XmlElement &xe)
{
  clear();

  m_altini = xe.attr2float("altitude", m_altini);
  uint ntime = xe.attr2int("ntime", 0);
  uint nstate = xe.attr2int("nstate", 0);

  XmlElement::const_iterator pos;
  pos = xe.findChild("ElasticStateColumns");
  if (pos != xe.end()) {
    stringstream ss;
    ss.str( pos->text() );
    uint idx;
    while (ss >> idx)
      m_jcelast.push_back(idx-1);
  }

  pos = xe.findChild("AeroControlStateColumns");
  if (pos != xe.end()) {
    stringstream ss;
    ss << pos->text();
    uint idx;
    while (ss >> idx)
      m_jcaerc.push_back(idx-1);
  }

  m_iptime.resize(ntime);
  m_ipx.resize(ntime, nstate);

  uint rrows(0);
  stringstream ss;
  ss << xe.text();
  for (uint i=0; i<ntime; ++i) {
    ss >> m_iptime[i];
    for (uint j=0; j<nstate; ++j)
      ss >> m_ipx(i,j);
    ++rrows;
    if (not ss)
      break;
  }

  if (rrows != ntime) {
    stringstream ss;
    ss << "Failed to read promised number of time steps; ";
    ss << "Expected " << ntime << " rows with " << nstate << " states, ";
    ss << "found only " << rrows << " rows.";
    throw Error(ss.str());
  }

  // check for increasing time values
  for (uint i=1; i<ntime; ++i)
    if (m_iptime[i] <= m_iptime[i-1])
      throw Error("FlightPath::fromXml() : Time values must increase "
                  "strictly monotonically.");

  interpolate();
}

void FlightPath::interpolate()
{
  const int nstep = m_iptime.size();
  Vector t(m_iptime);
  m_duration = t.back() - t.front();
  t -= t.front();
  t *= 1.0 / t.back();
  m_spl.init(3, t);

  // solve banded system for control points
  Vct4 b;
  const int ku(3);
  const int kl(3);
  Matrix bcf(2*kl+ku+1, nstep);
  for (int i=0; i<nstep; ++i) {
    int span = m_spl.eval(t[i], b);
    for (int j=0; j<4; j++) {
      int col = span-3+j;
      int row = kl+ku+i-col;
      bcf(row, col) = b[j];
    }
  }

  // build right-hand side
  m_cpx = m_ipx;

  // solve banded system
  int stat = banded_lu_solve(kl, ku, bcf, m_cpx);
  if (stat != 0) {
    string msg("Lapack: Banded LU solve failed ");
    msg += "in FlightPath::interpolate() ";
    if (stat < 0 and -stat-1 < 10) {
      const char *args[] = {"N", "KL", "KU", "NRHS", "AB", "LDAB",
                            "IPIV", "B", "LDB", "INFO"};
      msg += "Argument '" + string(args[-stat-1]) + "' is illegal.";
    } else {
      msg += "Interpolation problem is singular in equation " + str(stat);
    }
    throw Error(msg);
  }
}

void FlightPath::clear()
{
  m_iptime.clear();
  m_cptime.clear();
  m_ipx.clear();
  m_cpx.clear();
  m_jcelast.clear();
  m_jcaerc.clear();
  m_altini = 0.0;
}
