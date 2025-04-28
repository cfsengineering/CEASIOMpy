
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
 
#ifndef GENUA_STOPWATCH_H
#define GENUA_STOPWATCH_H

#include "logger.h"
#include <chrono>
#include <iostream>

/** Simple wallclock timing.
 *
 *
 *
 * \ingroup utility
 */
class Wallclock
{
public:

  /// create a wallclock and set start time
  Wallclock(Logger *lgr = 0) : m_logger(lgr) { start(); }

  /// initialize clock
  void start() { m_tstart = m_clock.now(); }

  /// print message and initialize clock
  void start(const std::string & msg) {
    log(msg);
    start();
  }

  /// elapsed time since start
  double stop() {
    m_tstop = m_clock.now();
    return elapsed();
  }

  /// print message and time since start, return elapsed time
  double stop(const std::string & msg) {
    double dt = stop();
    log(msg, dt);
    return dt;
  }

  /// print message and time since start, return elapsed time
  double stop(std::ostream & os, const std::string & msg) {
    double dt = stop();
    os << msg << dt << 's' << std::endl;
    return dt;
  }

  /// return elapsed time (after stop) in seconds
  double elapsed() {
    MicroSeconds dt = m_tstop - m_tstart;
    return dt.count() * 1e-6;
  }

  /// return elapsed time (after stop)
  double elapsedMicroSeconds() {
    MicroSeconds dt = m_tstop - m_tstart;
    return dt.count() * 1e-6;
  }

  /// return elapsed time, do not stop clock
  double lap() const {
    MicroSeconds dt = m_clock.now() - m_tstart;
    return dt.count() * 1e-6;
  }

private:

  /// pass log message on to logger or write to std::clog
  void log(const std::string &s) const {
    if (m_logger)
      m_logger->log(s);
    else
      std::clog << s << std::endl;
  }

  /// pass log message on to logger or write to std::clog
  void log(const std::string &s, double dt) const {
    if (m_logger)
      m_logger->log(s, dt, "s");
    else
      std::clog << s << dt << 's' << std::endl;
  }

private:

  typedef std::chrono::steady_clock Clock;
  typedef std::chrono::duration<double, std::micro> MicroSeconds;

  /// a steady clock
  Clock m_clock;

  /// time at which clock was started
  Clock::time_point m_tstart;

  /// time at which clock was stopped
  Clock::time_point m_tstop;

  /// optionally, a logger
  Logger *m_logger;
};

/** Record time for the execution of a scoped block.
 *
 * A ScopeTimer object is meant to be created on the stack at the beginning of
 * a basic block to be times; the clock starts in the constructor. On
 * destruction, the elapsed time in seconds is added to the floating-point
 * value passed as a reference to the constructor, so that an object can keep
 * track of time spend in particular blocks or functions over many calls.
 *
 * \ingroup utility
 * \sa Wallclock
 */
class ScopeTimer {
public:
  ScopeTimer(float &result) : m_result(result) { m_clk.start(); }
  double lap() const {return m_clk.lap();}
  ~ScopeTimer() { m_result += m_clk.stop(); }
private:
  Wallclock m_clk;
  float &m_result;
};

#endif // GENUA_TIMING_H
