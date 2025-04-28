
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
 
#include "logger.h"
#include <mutex>
#include <iostream>

static std::mutex s_clog_guard;

void Logger::log(const std::string &s) const
{
  std::unique_lock<std::mutex> slock(s_clog_guard);
  std::clog << s << std::endl;
  std::clog.flush();
  if (m_storeLogMessages)
    m_logMessages.push_back(s);
}

void Logger::reset()
{
  m_progress = 0;
  m_stage = 0;
  m_interrupt = 0;
  m_logMessages.clear();
}

bool Logger::nextStage(int steps)
{
  m_stage++;
  m_progress = 0;
  m_stepsInStage = steps;
  return m_interrupt;
}

