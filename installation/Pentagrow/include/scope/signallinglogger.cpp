
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
 
#include "signallinglogger.h"
#include "util.h"
#include <genua/logger.h>
#include <boost/thread/mutex.hpp>

#include <QTimer>

static boost::mutex s_message_guard;

SignallingLogger::SignallingLogger(Logger *client) : m_logger(client)
{
  m_ticker = new QTimer(this);
  m_ticker->setSingleShot(false);
  connect(m_ticker, SLOT(timeout()), this, SLOT(checkProgress()));
}

void SignallingLogger::startReporting(long n, long pollingInterval)
{
  m_logger->nextStage(n);
  m_ticker->start(pollingInterval);
}

int SignallingLogger::appendMessage(const std::string &s)
{
  QString qs( qstr(s) );
  emit message( qs );
  s_message_guard.lock();
  m_messages.append( qs );
  s_message_guard.unlock();
  return m_messages.size() - 1;
}

void SignallingLogger::interruptProcessing()
{
  m_logger->interrupt(true);
}

void SignallingLogger::checkProgress()
{
  int p = m_logger->progress();
  int n = m_logger->nsteps();
  float f = (p < n) ? (float(p) / float(n)) : 1.0f;
  emit currentProgress(f);
  if (p >= n) {
    m_ticker->stop();
    emit allCompleted();
  }
}
