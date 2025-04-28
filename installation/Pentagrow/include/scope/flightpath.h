
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
 
#ifndef SCOPE_FLIGHTPATH_H
#define SCOPE_FLIGHTPATH_H

#include <genua/dvector.h>
#include <genua/xmlelement.h>
#include <genua/splinebasis.h>

struct TdlSpec;

/** Contains data passed in from flight simulation.
 *
 */
class FlightPath
{
public:

  /// empty path
  FlightPath() : m_duration(0.0), m_altini(0.0) {}

  /// indices of elastic states present
  const Indices & elasticStates() const {return m_jcelast;}

  /// indices of control states present
  const Indices & controlStates() const {return m_jcaerc;}

  /// number of time steps imported from file
  uint niptime() const {return m_iptime.size();}

  /// maneuver duration
  Real duration() const {return m_duration;}

  /// subsample time vector
  void resampledTime(int nt, Vector &rst,
                     uint nSmooth=3, Real wSmooth=0.5) const;

  /// evaluate interpolation for states
  void eval(Real t, Vector &x) const;

  /// evaluate interpolation for states and time derivatives
  void eval(Real t, Vector &x, Vector &dx, Vector &ddx) const;

  /// interpolate values, first and second time derivatives mapped states
  void eval(const Vector &t, const Indices &map,
            Matrix &xt, Matrix &dxt, Matrix &ddxt) const;

  /// convert rigid-body states from [u,v,w..] to [M,alpha,beta..]
  void toAlpha(const TdlSpec &tspec, const Vector &x, Vector &mab) const;

  /// determine dynamic pressure from rigid-body state
  Real dynamicPressure(const Vector & x) const;

  /// initialize time-domain state specification (resizing etc)
  void initSpec(TdlSpec &tspec) const;

  /// generate time-domain representation for all states
  void extractSpec(const Vector &ipolTime, TdlSpec &tspec) const;

  /// read from XML file as written by matlab flight sim
  void fromXml(const XmlElement &xe);

  /// dump in plain text format


  /// clear out everything
  void clear();

private:

  /// construct interpolation
  void interpolate();

private:

  /// spline basis for interpolation
  SplineBasis m_spl;

  /// original time values at interpolation points
  Vector m_iptime, m_cptime;

  /// state history
  Matrix m_ipx, m_cpx;

  /// elastic states
  Indices m_jcelast;

  /// aerodynamic control states
  Indices m_jcaerc;

  /// maneuver duration
  Real m_duration;

  /// initial flight altitude (meter)
  Real m_altini;
};

#endif // FLIGHTPATH_H
