
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
 
#ifndef SIGNALLINGLOGGER_H
#define SIGNALLINGLOGGER_H

#include <genua/forward.h>
#include <QObject>
#include <QStringList>

class QTimer;

class SignallingLogger :  public QObject
{
  Q_OBJECT

public:

  /// initialize
  SignallingLogger(Logger *client);

  /// setup progress reporting for a single-stage process with n steps
  void startReporting(long n, long pollingInterval = 500);

  /// append message
  int appendMessage(const std::string &s);

  /// clear message log
  void clearMessages() { m_messages.clear(); }

  /// access all messages
  const QStringList & messages() const { return m_messages; }

signals:

  /// fired whenever a new log message was received
  void message(const QString &s);

  /// reports progress as a fraction of the work scheduled
  void currentProgress(float fraction);

  /// reports that scheduled work was completed
  void allCompleted();

public slots:

  /// terminate operation at the next opportunity (if lib object checks)
  void interruptProcessing();

private slots:

  /// connected to timer
  void checkProgress();

private:

  /// log messages end up here
  QStringList m_messages;

  /// timer to allow for regular progress updates
  QTimer *m_ticker;

  /// client to use for library interaction
  Logger *m_logger;
};


/** Facility for gathering log and progress data from library call.
 *
 *  For objects in libgenua and libsurf which perform long-running computations
 *  and inherit from class Logger in libgenua. The intention is to allow GUI
 *  objects to be updated from wthin the GUI thread concurrently with some
 *  expensive computation which may run for minutes or longer.
 *
 *  \verbatim
 *  class ComplexProcedure : public Logger {};
 *  typedef SignallingProcess<ComplexProcedure> ProcedureWrapper;
 *
 *  ProcedureWrapper a;
 *  connect( a.logger(), SIGNAL(currentProgress(float)),
 *           this, SLOT(showProgress(float)) );
 *  connect( m_abortButton, SIGNAL(clicked()),
 *           a.logger(), SLOT(interruptProcessing()) );
 *  a.startReporting( n );
 *
 *  // might want to do this in another thread
 *  a.process();
 *  \endverbatim
 *
 */
template <class LoggingObject>
class SignallingProcess : public LoggingObject
{
public:

  /// initialize logger
  SignallingProcess() : LoggingObject() {
    m_logger = new SignallingLogger(this);
  }

  /// delete logger
  virtual ~SignallingProcess() {
    delete m_logger;
  }

  /// access signalling logger
  SignallingLogger *logger() const {return m_logger;}

  /// setup progress reporting for a single-stage process with n steps
  void startReporting(long n, long pollingInterval = 500) {
    m_logger->startReporting(n, pollingInterval);
  }

protected:

  /// overload of LoggingObject::log(s)
  void log(const std::string &s) const {
    m_logger->appendMessage(s);
  }

private:

  /// interfacing object
  mutable SignallingLogger *m_logger;
};

#endif // SIGNALLINGLOGGER_H
