
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
 
#ifndef GENUA_LOGGER_H
#define GENUA_LOGGER_H

#include <sstream>
#include <vector>
#include <string>
#include <atomic>

/** Interface layer for monitoring long computations.
 *
 *  This class is to be overloaded by in order to display progress status
 *  and log messages to the user. Usually, this would be done to allow
 *  monitoring of int-running, hopefully multithreaded computations which
 *  regularly update the progress status indicator and check for the value
 *  of a termination flag.
 *
 *  This class is thread-safe as implemented. Note that child objects which
 *  overload the virtual log() function must permit concurrent calls to that
 *  function.
 *
 *  \todo Convert to use variadic templates.
 *
 *  \ingroup io, utility, concurrency
 *
 */
class Logger
{
public:

  /// initialize progress variables
  Logger() : m_progress(0), m_stepsInStage(100), m_stage(0),
    m_interrupt(false), m_storeLogMessages(false) {}

  /// copy construction
  Logger(const Logger &a) {*this = a;}

  /// explicit copy assignment
  Logger & operator= (const Logger &a) {
    if (this != &a) {
      m_progress = a.m_progress;
      m_stepsInStage = a.m_stepsInStage;
      m_stage = a.m_stage.load();
      m_interrupt = a.m_interrupt.load();
      m_storeLogMessages = a.m_storeLogMessages;
      m_logMessages = a.m_logMessages;
    }
    return *this;
  }

  /// virtual destruction
  virtual ~Logger() {}

  /// switch log storage on/off
  void storeLogMessages(bool flag) {m_storeLogMessages = flag;}

  /// access stored messages
  const std::vector<std::string> &logMessages() const {return m_logMessages;}

  /// called by all convenience interfaces, overloaded by display client
  virtual void log(const std::string &s) const;

  /// called by all convenience interfaces, overloaded by display client
  template<typename FirstType, typename... MoreTypes>
  void log(const FirstType& a1, MoreTypes... as) const {
    std::stringstream ss;
    this->appendArg(ss, a1, as...);
    this->log(ss.str());
  }

  /// reset progress and interrupt flag
  void reset();

  /// increment progress, return true if interruption flag is set
  bool increment(int step = 1) {
    m_progress += step;
    return m_interrupt;
  }

  /// proceed to next stage, return true if interruption flag is set
  virtual bool nextStage(int steps);

  /// query current progress
  int progress() const { return m_progress; }

  /// number of steps in present stage
  int nsteps() const { return m_stepsInStage; }

  /// percentage of work completed in present stage
  float percentage() const { return float(100*progress())/(nsteps()-1); }

  /// query current processing stage
  int stage() const { return m_stage; }

  /// set interruption flag
  void interrupt(bool flag) {
    m_interrupt = flag;
  }

  /// query interrupt flag
  bool interrupted() const {
    return (m_interrupt);
  }

private:

  template <typename T1>
  void appendArg(std::stringstream &ss, T1 &a1) const {
    ss << ' ' << a1;
  }

  template <typename T1, typename ...Args>
  void appendArg(std::stringstream &ss, T1 &a1, Args... as) const {
    this->appendArg(ss, a1);
    this->appendArg(ss, as...);
  }

private:

  /// fine-grained progress status
  int m_progress;

  /// number of steps in current stage
  int m_stepsInStage;

  /// coarse-grained progress
  std::atomic<int> m_stage;

  /// interruption flag
  std::atomic<bool> m_interrupt;

  /// whether to store log message in list
  bool m_storeLogMessages;

  /// one string per line if storage is switched on
  mutable std::vector<std::string> m_logMessages;
};

#endif // LOGGER_H
